# The Two-Pass Compile Pattern

This is the single most important non-obvious pattern in UE Blueprint codegen. Skipping it produces silent bugs (default values where data should flow, dropped nodes) and assertion crashes (`FindPinChecked` failing on pins that "should" exist).

## Why it exists

Blueprint nodes resolve their pins by introspecting `UFunction` / `FProperty` reflection on the **generated class**. That reflection is rebuilt by `CompileBlueprint`. So:

- A `UK2Node_CallFunction` referencing a function on its own BP can only allocate parameter pins after that function is compiled into the generated class.
- A `UK2Node_VariableGet` referencing a UMG animation can only allocate its output pin after the UMG compiler has baked the animation as an `FProperty` on the WBP's generated class.

If you spawn the call/get node *before* that has happened, `AllocateDefaultPins` introspects an empty/missing reflection slot and creates no parameter pins. Subsequent `FindPinChecked` then asserts.

## The fix: split the build into two compile passes

**Pass 1**: build the content the wiring will reference (function graphs, animations, member variables) and compile.

**Pass 2**: build the wiring that references that content (call nodes, variable-get nodes for animations) and compile again.

Total cost: one extra `CompileBlueprint` call. Both passes use `MarkBlueprintAsStructurallyModified` because both add nodes/properties.

## Concrete cases

### Case A: Event graph calls a user-defined function on the same BP

```cpp
// PASS 1 -------------------------------------------------------------
// Add the variable.
FEdGraphPinType IntT;
IntT.PinCategory = UEdGraphSchema_K2::PC_Int;
FBlueprintEditorUtils::AddMemberVariable(BP, FName("Multiplier"), IntT, TEXT("3"));

// Build the Compute(InValue:int) -> int function graph.
UEdGraph* FnGraph = FBlueprintEditorUtils::CreateNewGraph(
    BP, FName("Compute"), UEdGraph::StaticClass(), UEdGraphSchema_K2::StaticClass());
FBlueprintEditorUtils::AddFunctionGraph<UClass>(BP, FnGraph, /*bUserCreated*/ true, nullptr);
// ... add Entry input pin, spawn Result node, wire math, etc. ...

// COMPILE so Compute exists on the generated UClass as a UFunction.
FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
FKismetEditorUtilities::CompileBlueprint(BP);

// PASS 2 -------------------------------------------------------------
// Now build the event graph. CallCompute can resolve pins because
// Compute is reflected on the generated class.
UEdGraph* EventGraph = FBlueprintEditorUtils::FindEventGraph(BP);

UK2Node_CallFunction* CallCompute = NewObject<UK2Node_CallFunction>(EventGraph);
CallCompute->CreateNewGuid();
EventGraph->AddNode(CallCompute, false, false);
CallCompute->FunctionReference.SetSelfMember(FName("Compute"));
CallCompute->AllocateDefaultPins();   // <-- now this finds InValue + ReturnValue

// ... wire exec + data ...

// FINAL COMPILE
FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
FKismetEditorUtilities::CompileBlueprint(BP);
```

### Case B: WBP event graph plays a UMG animation

The UMG compiler creates an `FProperty` on the generated class for each entry in `WBP->Animations`, named after the animation's `FName`. `UK2Node_VariableGet::AllocateDefaultPins` only finds that property after the WBP has been compiled.

```cpp
// PASS 1 -------------------------------------------------------------
// Build hierarchy.
UCanvasPanel* Root = WBP->WidgetTree->ConstructWidget<UCanvasPanel>(...);
WBP->WidgetTree->RootWidget = Root;
WBP->OnVariableAdded(Root->GetFName());
UTextBlock* MyText = WBP->WidgetTree->ConstructWidget<UTextBlock>(...);
// ... add to Root, set bIsVariable=true, OnVariableAdded(MyText->GetFName()) ...

// Build the animation. FName MUST match what GetAnimationByName looks up.
UWidgetAnimation* Anim = NewObject<UWidgetAnimation>(WBP, FName("SlideIn"), RF_Public | RF_Transactional);
Anim->SetDisplayLabel(TEXT("SlideIn"));
// ... build MovieScene + tracks + sections + keyframes ...
WBP->Animations.Add(Anim);

// COMPILE so the UMG compiler emits an FProperty named "SlideIn" on the
// generated class. Without this, the VariableGet below cannot resolve.
FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);
FKismetEditorUtilities::CompileBlueprint(WBP);

// PASS 2 -------------------------------------------------------------
// Event graph: Construct -> Get(SlideIn) + PlayAnimation
UEdGraph* EventGraph = FBlueprintEditorUtils::FindEventGraph(WBP);

UK2Node_Event* ConstructEvt = SpawnNode<UK2Node_Event>(EventGraph, -400, -300);
ConstructEvt->EventReference.SetExternalMember(FName("Construct"), UUserWidget::StaticClass());
ConstructEvt->bOverrideFunction = true;
ConstructEvt->AllocateDefaultPins();

UK2Node_VariableGet* GetAnim = SpawnNode<UK2Node_VariableGet>(EventGraph, -50, -150);
GetAnim->VariableReference.SetSelfMember(FName("SlideIn"));
GetAnim->AllocateDefaultPins();   // <-- now finds the SlideIn property

UK2Node_CallFunction* PlayAnim = SpawnNode<UK2Node_CallFunction>(EventGraph, 250, -300);
PlayAnim->FunctionReference.SetExternalMember(
    GET_FUNCTION_NAME_CHECKED(UUserWidget, PlayAnimation),
    UUserWidget::StaticClass());
PlayAnim->AllocateDefaultPins();

// Wire.
ConstructEvt->FindPinChecked(UEdGraphSchema_K2::PN_Then)->MakeLinkTo(PlayAnim->GetExecPin());
GetAnim->FindPinChecked(FName("SlideIn"))->MakeLinkTo(PlayAnim->FindPinChecked(FName("InAnimation")));

// FINAL COMPILE
FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);
FKismetEditorUtilities::CompileBlueprint(WBP);
```

### Case C: Cross-asset references

Less common but follows the same rule: if asset A's event graph references a function on asset B, asset B must be compiled before asset A's event graph is wired. Generators that build asset families should compile each one fully before wiring others against it.

## When you do NOT need two-pass

You don't need an intermediate compile when:

- The wiring only references **engine functions** (`UKismetSystemLibrary::PrintString`, etc.) — those are always reflected.
- The wiring only references **already-compiled member variables** (`AddMemberVariable` doesn't need a compile pass for `UK2Node_VariableSet/Get` to resolve — `Variable->VariableReference.SetSelfMember(...)` resolves through `BP->NewVariables` directly).
- All you build are nodes that don't reference each other.

The cases that *need* it: self-function calls (`SetSelfMember` on a function you just created) and UMG animation variable-gets.

## Symptoms of forgetting

| Symptom | Almost certainly |
|---|---|
| Crash in `EdGraphNode.h ~ Line 586`, `FindPinChecked` assertion | Tried to wire a pin that wasn't allocated. Two-pass missing. |
| Compiler warning *"X was pruned because its Exec pin is not connected"* | Different bug — non-pure function not in exec chain. Not two-pass. |
| `Get SlideIn` node appears as a generic untyped-pin red box | UMG property not yet on the class. Two-pass missing. |
| `PlayAnimation` runs at runtime but the InAnimation parameter is null | VariableGet pin existed but wasn't actually wired (`MakeLinkTo` skipped because pin was null). Same root cause. |

## Cost / drawback

One extra compile per generated asset. For a generator producing dozens of assets, this is negligible. The alternative — manually computing whether a given wiring needs intermediate compile — is fragile. Default to two-pass any time event-graph wiring references content created in the same function.
