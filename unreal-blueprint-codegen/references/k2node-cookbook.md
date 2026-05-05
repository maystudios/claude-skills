# K2Node Cookbook — Blueprint Graph Authoring

Pasteable C++ patterns for spawning, configuring, and wiring K2Nodes in `UBlueprint` graphs. All snippets target UE 5.4–5.7. Validated against 5.7.

## Required includes

```cpp
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "EdGraph/EdGraph.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_Event.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_CallFunction.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "K2Node_Self.h"
#include "K2Node_FunctionEntry.h"
#include "K2Node_FunctionResult.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Kismet/KismetMathLibrary.h"
```

## The universal node-spawn helper

```cpp
template<typename TNode>
TNode* SpawnNode(UEdGraph* Graph, int32 PosX, int32 PosY)
{
    TNode* N = NewObject<TNode>(Graph);
    N->CreateNewGuid();   // mandatory; copy/paste later collides without it
    N->NodePosX = PosX;
    N->NodePosY = PosY;
    Graph->AddNode(N, /*bFromUI*/ false, /*bSelectNewNode*/ false);
    return N;
}
```

Use this for every K2Node. Position in graph-pixels. Lay out manually — there is no auto-layout. Convention: ~300px per logical column, ~160px per row.

## Adding member variables

```cpp
FEdGraphPinType IntT;
IntT.PinCategory = UEdGraphSchema_K2::PC_Int;
FBlueprintEditorUtils::AddMemberVariable(BP, FName("Counter"), IntT, FString(TEXT("0")));
```

For an object reference:

```cpp
FEdGraphPinType ActorRefT;
ActorRefT.PinCategory          = UEdGraphSchema_K2::PC_Object;
ActorRefT.PinSubCategoryObject = AActor::StaticClass();
FBlueprintEditorUtils::AddMemberVariable(BP, FName("TargetActor"), ActorRefT, FString());
```

Tweak flags (instance-editable, BP-readonly) on the just-added variable:

```cpp
const int32 Idx = FBlueprintEditorUtils::FindNewVariableIndex(BP, FName("Counter"));
if (Idx != INDEX_NONE)
{
    BP->NewVariables[Idx].PropertyFlags &= ~CPF_DisableEditOnInstance;  // make instance-editable
    BP->NewVariables[Idx].PropertyFlags |= CPF_BlueprintReadOnly;       // BlueprintReadOnly
}
FBlueprintEditorUtils::SetBlueprintVariableCategory(BP, FName("Counter"), NAME_None, FText::FromString("Stats"));
```

## Custom event (no parameters)

```cpp
UK2Node_CustomEvent* Evt = SpawnNode<UK2Node_CustomEvent>(EventGraph, -400, -300);
Evt->CustomFunctionName = FName("OnPing");
Evt->bIsEditable        = true;
Evt->AllocateDefaultPins();
```

## Custom event with input parameter

```cpp
UK2Node_CustomEvent* Evt = SpawnNode<UK2Node_CustomEvent>(EventGraph, -400, -300);
Evt->CustomFunctionName = FName("OnPing");
Evt->bIsEditable        = true;
Evt->AllocateDefaultPins();

FEdGraphPinType IntT;
IntT.PinCategory = UEdGraphSchema_K2::PC_Int;
Evt->CreateUserDefinedPin(FName("Amount"), IntT, EGPD_Output, /*bUseUniqueName*/ true);
Evt->ReconstructNode();   // refresh visual after pin add

// Later: Evt->FindPinChecked(FName("Amount")) is the data output for Amount.
```

`EGPD_Output` is correct — from the event's perspective the parameter flows OUT to the rest of the graph.

## Event override (e.g. UUserWidget::Construct, AActor::BeginPlay)

```cpp
UK2Node_Event* ConstructEvt = SpawnNode<UK2Node_Event>(EventGraph, -400, -300);
ConstructEvt->EventReference.SetExternalMember(FName("Construct"), UUserWidget::StaticClass());
ConstructEvt->bOverrideFunction = true;
ConstructEvt->AllocateDefaultPins();
```

This overrides the engine event. For BeginPlay use `FName("ReceiveBeginPlay"), AActor::StaticClass()`. The exact override name often differs from the display name — check the engine header. Receivers are usually `Receive*`.

## Calling an engine static function (e.g. PrintString)

```cpp
UK2Node_CallFunction* Print = SpawnNode<UK2Node_CallFunction>(EventGraph, 300, -300);
Print->FunctionReference.SetExternalMember(
    GET_FUNCTION_NAME_CHECKED(UKismetSystemLibrary, PrintString),
    UKismetSystemLibrary::StaticClass());
Print->AllocateDefaultPins();   // <-- AFTER SetExternalMember; reverse order = no pins
```

## Calling a function on self (a member function)

For functions defined on the same Blueprint, use `SetSelfMember`:

```cpp
UK2Node_CallFunction* CallCompute = SpawnNode<UK2Node_CallFunction>(EventGraph, 0, 0);
CallCompute->FunctionReference.SetSelfMember(FName("Compute"));
CallCompute->AllocateDefaultPins();
```

This requires `Compute` to exist on the generated class **before** this node's `AllocateDefaultPins` runs. See [two-pass-compile.md](two-pass-compile.md).

## VariableSet / VariableGet (member variables)

```cpp
// Set Counter = 42
UK2Node_VariableSet* SetNode = SpawnNode<UK2Node_VariableSet>(EventGraph, 100, 0);
SetNode->VariableReference.SetSelfMember(FName("Counter"));
SetNode->AllocateDefaultPins();
const UEdGraphSchema_K2* K2 = GetDefault<UEdGraphSchema_K2>();
K2->TrySetDefaultValue(*SetNode->FindPinChecked(FName("Counter")), TEXT("42"));

// Get Counter
UK2Node_VariableGet* GetNode = SpawnNode<UK2Node_VariableGet>(EventGraph, 100, 200);
GetNode->VariableReference.SetSelfMember(FName("Counter"));
GetNode->AllocateDefaultPins();
UEdGraphPin* CounterOut = GetNode->FindPinChecked(FName("Counter"));   // the output pin
```

The output pin of a VariableGet is named after the variable.

## Math nodes (e.g. multiply two ints)

`UKismetMathLibrary` exposes the math primitives. For int*int:

```cpp
UK2Node_CallFunction* Mul = SpawnNode<UK2Node_CallFunction>(Graph, 200, 50);
Mul->FunctionReference.SetExternalMember(
    GET_FUNCTION_NAME_CHECKED(UKismetMathLibrary, Multiply_IntInt),
    UKismetMathLibrary::StaticClass());
Mul->AllocateDefaultPins();

// Pins: "A" (in), "B" (in), PN_ReturnValue (out)
UEdGraphPin* A = Mul->FindPinChecked(FName("A"));
UEdGraphPin* B = Mul->FindPinChecked(FName("B"));
UEdGraphPin* Ret = Mul->FindPinChecked(UEdGraphSchema_K2::PN_ReturnValue);
```

Math node naming follows `Op_TypeAType` (e.g. `Add_FloatFloat`, `Subtract_DoubleDouble`, `Multiply_IntInt`). UE5 floats are doubles in the BP graph; if you have a `float` UPROPERTY use `Multiply_DoubleDouble`.

## User-defined function with input + return value

```cpp
// 1) Create the function graph + Entry node.
UEdGraph* FnGraph = FBlueprintEditorUtils::CreateNewGraph(
    BP, FName("Compute"), UEdGraph::StaticClass(), UEdGraphSchema_K2::StaticClass());
FBlueprintEditorUtils::AddFunctionGraph<UClass>(BP, FnGraph, /*bUserCreated*/ true, nullptr);

TArray<UK2Node_FunctionEntry*> Entries;
FnGraph->GetNodesOfClass(Entries);
UK2Node_FunctionEntry* Entry = Entries[0];   // AddFunctionGraph spawns this
Entry->NodePosX = -400; Entry->NodePosY = 0;

// 2) Add input parameter to Entry (output direction = parameter flows out into the function body).
FEdGraphPinType IntT;
IntT.PinCategory = UEdGraphSchema_K2::PC_Int;
Entry->CreateUserDefinedPin(FName("InValue"), IntT, EGPD_Output, /*bUseUniqueName*/ true);

// 3) AddFunctionGraph does NOT spawn a Result node. Add one if the function returns a value.
UK2Node_FunctionResult* Result = nullptr;
{
    FGraphNodeCreator<UK2Node_FunctionResult> Creator(*FnGraph);
    Result = Creator.CreateNode();
    Result->FunctionReference = Entry->FunctionReference;
    Result->NodePosX = 600; Result->NodePosY = 0;
    Creator.Finalize();
}
Result->CreateUserDefinedPin(FName("ReturnValue"), IntT, EGPD_Input, /*bUseUniqueName*/ true);

// 4) Wire body: Entry.Then -> Result.Execute (mandatory exec pass-through).
Entry->FindPinChecked(UEdGraphSchema_K2::PN_Then)
     ->MakeLinkTo(Result->FindPinChecked(UEdGraphSchema_K2::PN_Execute));

// 5) Wire data: Entry.InValue -> ... -> Result.ReturnValue.
//    (Insert math, branches, sub-calls between Entry and Result.)
```

Crucial directional gotcha: on `UK2Node_FunctionEntry`, parameters use `EGPD_Output` (they flow out of Entry into the body). On `UK2Node_FunctionResult`, return values use `EGPD_Input` (they flow in). Counterintuitive but consistent with Epic's source.

## Pin connection patterns

```cpp
const UEdGraphSchema_K2* K2 = GetDefault<UEdGraphSchema_K2>();

// By-name pin lookup
UEdGraphPin* InString = PrintNode->FindPin(FName("InString"));   // null if not found
UEdGraphPin* InString = PrintNode->FindPinChecked(FName("InString"));   // asserts if not found

// Schema-defined exec pin names
UEdGraphPin* Then    = SomeNode->FindPin(UEdGraphSchema_K2::PN_Then);
UEdGraphPin* Exec    = SomeNode->FindPin(UEdGraphSchema_K2::PN_Execute);
UEdGraphPin* RetVal  = SomeNode->FindPin(UEdGraphSchema_K2::PN_ReturnValue);
UEdGraphPin* SelfPin = SomeNode->FindPin(UEdGraphSchema_K2::PN_Self);

// Common helpers on K2Nodes
SetNode->GetExecPin();   // input exec
SetNode->GetThenPin();   // output exec ("then")

// Connect
PinA->MakeLinkTo(PinB);

// Set a literal default on an unconnected input pin
K2->TrySetDefaultValue(*SomeInputPin, TEXT("42"));   // string form of the value
```

## Complete example: CustomEvent → SetVar → CallFunction

```cpp
UEdGraph* EventGraph = FBlueprintEditorUtils::FindEventGraph(BP);

UK2Node_CustomEvent* OnPing = SpawnNode<UK2Node_CustomEvent>(EventGraph, -400, -300);
OnPing->CustomFunctionName = FName("OnPing");
OnPing->bIsEditable        = true;
OnPing->AllocateDefaultPins();

UK2Node_VariableSet* SetCounter = SpawnNode<UK2Node_VariableSet>(EventGraph, -50, -300);
SetCounter->VariableReference.SetSelfMember(FName("Counter"));
SetCounter->AllocateDefaultPins();

UK2Node_CallFunction* PrintNode = SpawnNode<UK2Node_CallFunction>(EventGraph, 300, -300);
PrintNode->FunctionReference.SetExternalMember(
    GET_FUNCTION_NAME_CHECKED(UKismetSystemLibrary, PrintString),
    UKismetSystemLibrary::StaticClass());
PrintNode->AllocateDefaultPins();

// Exec chain
OnPing->FindPinChecked(UEdGraphSchema_K2::PN_Then)->MakeLinkTo(SetCounter->GetExecPin());
SetCounter->GetThenPin()->MakeLinkTo(PrintNode->GetExecPin());

// Defaults
const UEdGraphSchema_K2* K2 = GetDefault<UEdGraphSchema_K2>();
K2->TrySetDefaultValue(*SetCounter->FindPinChecked(FName("Counter")), TEXT("42"));
K2->TrySetDefaultValue(*PrintNode->FindPinChecked(FName("InString")), TEXT("Hello!"));
```

## Complete example: event calls a user function

This is the case that usually needs **two-pass compile**. Build Compute first, compile, then build the event-graph call.

```cpp
// PASS 1: build Compute(InValue:int) -> int and compile.
//   ... (function-graph code from above) ...
FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
FKismetEditorUtilities::CompileBlueprint(BP);

// PASS 2: event graph
UEdGraph* EventGraph = FBlueprintEditorUtils::FindEventGraph(BP);

UK2Node_CustomEvent* OnPing = SpawnNode<UK2Node_CustomEvent>(EventGraph, -600, -300);
OnPing->CustomFunctionName = FName("OnPing");
OnPing->bIsEditable        = true;
OnPing->AllocateDefaultPins();
FEdGraphPinType IntT; IntT.PinCategory = UEdGraphSchema_K2::PC_Int;
OnPing->CreateUserDefinedPin(FName("Amount"), IntT, EGPD_Output, true);
OnPing->ReconstructNode();

UK2Node_CallFunction* CallCompute = SpawnNode<UK2Node_CallFunction>(EventGraph, -250, -300);
CallCompute->FunctionReference.SetSelfMember(FName("Compute"));
CallCompute->AllocateDefaultPins();   // resolves InValue + ReturnValue (Compute is now compiled)

UK2Node_VariableSet* SetCounter = SpawnNode<UK2Node_VariableSet>(EventGraph, 100, -300);
SetCounter->VariableReference.SetSelfMember(FName("Counter"));
SetCounter->AllocateDefaultPins();

// Exec chain — Compute is non-pure, MUST be in chain or it gets pruned.
OnPing->FindPinChecked(UEdGraphSchema_K2::PN_Then)->MakeLinkTo(CallCompute->GetExecPin());
CallCompute->GetThenPin()->MakeLinkTo(SetCounter->GetExecPin());

// Data: OnPing.Amount -> Compute.InValue -> SetCounter.Counter
OnPing->FindPinChecked(FName("Amount"))->MakeLinkTo(CallCompute->FindPinChecked(FName("InValue")));
CallCompute->FindPinChecked(UEdGraphSchema_K2::PN_ReturnValue)
           ->MakeLinkTo(SetCounter->FindPinChecked(FName("Counter")));

// Final compile.
FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
FKismetEditorUtilities::CompileBlueprint(BP);
```

## Lookup helpers

```cpp
UEdGraph*  EventGraph = FBlueprintEditorUtils::FindEventGraph(BP);   // or BP->UbergraphPages[0]
TArray<UEdGraph*> AllGraphs;
FBlueprintEditorUtils::GetAllGraphs(BP, AllGraphs);

// Iterate nodes by class
TArray<UK2Node_CustomEvent*> Events;
EventGraph->GetNodesOfClass(Events);
```

## Flags + edit conditions you may want

```cpp
// Make a function graph const (BlueprintPure-style)
Entry->AddExtraFlags(FUNC_BlueprintPure);

// Set a function category (so it groups in the My Blueprint panel)
FBlueprintEditorUtils::SetBlueprintFunctionMetaData(BP, FName("Compute"), FBlueprintMetadata::MD_Category, TEXT("Math"));
```

## Common pitfalls (paired with symptom → fix)

| Symptom | Fix |
|---|---|
| Node spawns with no pins | `SetExternalMember` / `SetSelfMember` was called AFTER `AllocateDefaultPins`. Swap. |
| `FindPinChecked` asserts | Pin doesn't exist. Either wrong name, or the function/var isn't compiled yet — see two-pass-compile.md. |
| *"Function X was pruned because its Exec pin is not connected"* | Non-pure function not wired into exec chain. Add `Func->GetExecPin()` and `Func->GetThenPin()` to the chain. |
| Variable Get returns 0 / empty | Either default value never set, or two-pass missing for animation/other late-bound property. |
| Event calls fire but parameters arrive as default | Same — variable / parameter wiring needs the property to exist on the generated class first. |
| Node duplicates collide on copy/paste later | `CreateNewGuid()` was skipped during spawn. |
| Visual stays stale after pin changes | `Node->ReconstructNode()` after the change. |
