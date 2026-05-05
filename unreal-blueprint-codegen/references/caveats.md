# Caveats & Version-Specific Gotchas

Things you only learn after losing time to them. Validated against UE 5.7.

## API surface

### `UUserWidget::PlayAnimationByName` does not exist in 5.7

Some online tutorials reference `PlayAnimationByName(FName, ...)`. That overload is gone (or never shipped publicly) in UE 5.7. Only `PlayAnimation(UWidgetAnimation* InAnimation, ...)` exists. So the in-graph node must take a `UWidgetAnimation*` reference, not a name string.

Workaround: `UK2Node_VariableGet` resolving the auto-generated animation property → wired into `InAnimation`. Requires two-pass compile (see [two-pass-compile.md](two-pass-compile.md)).

### `FBlueprintEditorUtils::AddFunctionGraph` does not spawn a Result node

Only Entry. If your function returns a value, manually add the Result node:

```cpp
FGraphNodeCreator<UK2Node_FunctionResult> Creator(*FnGraph);
UK2Node_FunctionResult* Result = Creator.CreateNode();
Result->FunctionReference = Entry->FunctionReference;
Result->NodePosX = 600;
Creator.Finalize();
Result->CreateUserDefinedPin(FName("ReturnValue"), IntT, EGPD_Input, true);
```

### Plugin compiler classes are usually NOT DLL-exported

If you try to call a plugin's static compiler class (e.g. `FMayDialogueCompiler::CompileDialogueAsset`) from another module, you'll get a linker error:

```
unresolved external symbol "FMayDialogueCompiler::CompileDialogueAsset(...)"
```

The class doesn't have `MAYDIALOGUEEDITOR_API`. **Workaround**: use the plugin's `UEdGraph` subclass's update method instead — those are usually `UCLASS API` and therefore exported. Pattern:

```cpp
UMayDialogueGraph* Graph = ...;
Graph->UpdateAsset();   // public method on the API'd UClass; calls compiler internally
```

This works for any plugin whose graph class is exported and exposes a public compile/refresh method.

## Python limitations

### Python cannot author event graphs

`UEdGraph`, `UEdGraphNode`, and the entire `UK2Node_*` hierarchy are **not exposed to Python**. Confirmed by Epic forum responses ("How to add nodes to event graph via python"). The only sanctioned graph authoring path is C++.

What Python *can* do: create asset shells (`unreal.WidgetBlueprintFactory`), construct widgets via `WidgetTree.construct_widget`, set property values via `set_editor_property`, save assets. Anything that reads a typed pin or wires a node — C++ only.

**Pattern**: write a `UBlueprintFunctionLibrary` in C++ with `BlueprintCallable` UFUNCTIONs that do the codegen, then call those from Python:

```python
import unreal
unreal.MyEditorLibrary.create_my_blueprint("/Game/Generated", "BP_X")
```

### `unreal.SequencerTools` does not cover UMG animations

`SequencerTools` works on `ULevelSequence` / generic `UMovieSceneSequence` but has no UMG-specific helpers. `UWidgetAnimation::AnimationBindings` cannot be populated from Python in any clean way — direct UPROPERTY array manipulation isn't reflected. Stick to C++ for UMG animation generation.

## Gameplay tags

### Runtime `AddNativeGameplayTag` is too late for the editor UI

`UGameplayTagsManager::Get().AddNativeGameplayTag(FName("X"), ...)` from inside a generator function appears to register the tag (and `RequestGameplayTag(name, false)` may even return it) — but the editor's tag picker, the asset's tag dropdown, etc. all built their tag tree at editor startup. Tags registered at function-call time show as **invalid / yellow-warning** in the UI, even though `FGameplayTag` comparison still works internally.

Symptom: speakers in your generated dialogue asset have empty or "invalid" tags despite the generator code seeming to set them.

**Fix**: register tags at module load via `UE_DEFINE_GAMEPLAY_TAG_STATIC`:

```cpp
#include "NativeGameplayTags.h"

UE_DEFINE_GAMEPLAY_TAG_STATIC(TAG_MyDomain_Speaker_NPC, "MyDomain.Speaker.NPC");

// ... later in any function:
SomeStruct.SpeakerTag = TAG_MyDomain_Speaker_NPC.GetTag();
```

The tag is now part of the project's tag tree before any UI sees it. For shareable code (multiple .cpp need it), use `UE_DECLARE_GAMEPLAY_TAG_EXTERN` in a header + `UE_DEFINE_GAMEPLAY_TAG` in one .cpp.

For shipping content: register tags in the runtime module (or a dedicated content module) so they exist outside the editor too.

## Auto-spawned default events

### Both BP and WBP graphs spawn placeholder events at (0, 0)

- `AActor`-derived BPs: `Event BeginPlay`, `Event ActorBeginOverlap`, `Event Tick` (all "disabled and will not be called" placeholders the user can drag off to enable).
- `UUserWidget`-derived WBPs: `Event PreConstruct`, `Event Construct`, `Event Tick`.

If you spawn your own nodes at `(0, 0)`, they overlap visually with these placeholders — opening the asset shows a tangled mess and "This node is disabled" warnings on top of your nodes.

**Fix**: position generated nodes well away from origin. `Y=-300` (above) or `X=-400` (left) works. Convention: place an event-graph chain at `Y=-300` with X starting at `-400` and incrementing by 300 per node.

## Outer hierarchy

### `UWidgetAnimation` outer must be the WBP

`NewObject<UWidgetAnimation>(WBP, ...)` — passing the WBP as outer is what makes the editor's Animations panel list the animation. Pass the package or `GetTransientPackage()` and the animation exists but is invisible to the panel.

### `UMovieScene` outer must be the animation

`NewObject<UMovieScene>(Anim, ...)` — same logic. Wrong outer breaks the editor's track list.

These outer-relationships mirror what the editor's "+ Animation" button does internally.

## Designer-UX defaults

### Editor wrappers seed defaults via `PostPlacedNewNode`

Many domain-specific graph wrappers seed default values when a node is dropped in:

- `UMayDialogueGraphNode_Task` for `UMayDialogueNode_PlayerChoice` seeds two `UMayDialogueChoice` entries with text "Yes" / "No".
- `UMayDialogueGraphNode_Task` for `UMayDialogueNode_Branch` seeds `BranchOutputCount = 3`.
- `UMayDialogueGraphNode_Task` for `UMayDialogueNode_RandomLine` seeds two equal weights.
- Similar patterns exist in many third-party graph plugins.

The seeding hook is `UEdGraphNode::PostPlacedNewNode()`, which `FGraphNodeCreator::Finalize()` invokes. So your generator triggers the same designer-UX defaults that hand-dragging triggers.

**Convention for programmatic generation**: clear the relevant array right after `Finalize()`, before populating with your own data:

```cpp
auto* ChoiceNode = Cast<UMayDialogueNode_PlayerChoice>(WrappedNode->DialogueNodeInstance);
ChoiceNode->Choices.Empty();   // strip designer-UX defaults
// ... add your own choices ...
```

Don't remove the defaults from the plugin — they're correct UX for the designer-drag path. Just clear in the generator. The seeding hook checks `Choices.Num() == 0` so it only fires on initial spawn, never on subsequent reload.

## Compiler / save quirks

### `MarkBlueprintAsModified` is too weak for codegen

If you add nodes / variables / function graphs and then call only `MarkBlueprintAsModified` (not `...AsStructurallyModified`), the class layout doesn't regenerate and runtime code sees stale reflection. **Always use `MarkBlueprintAsStructurallyModified`** for codegen. The "Modified" form is for tweaks to existing pin defaults.

### Saving needs `RF_Public | RF_Standalone`

`FSavePackageArgs::TopLevelFlags` must include both. Missing `RF_Standalone` means the asset shows up in the registry but cannot be loaded by name as a top-level asset. Always:

```cpp
FSavePackageArgs Args;
Args.TopLevelFlags = RF_Public | RF_Standalone;
```

### `FAssetRegistryModule::AssetCreated(Asset)` before SavePackage

Without this call the asset registry doesn't know about the new asset, so the Content Browser doesn't show it until a manual rescan. Always call before `SavePackage`.

## Build / IWYU

### `bEnforceIWYU = true` in plugins requires every header explicitly

UE 5.x plugins typically enforce IWYU. You can't rely on PCH for `CoreMinimal.h` / `UObject.h` etc. — every `.cpp` must include exactly what it uses. The K2Node cookbook lists the standard set; copy that whole-cloth as a starting point.

Forward-declare `UPackage`, `UObject`, `FString` etc. in your own headers; pull full headers in `.cpp` only. Otherwise you incur huge transitive include costs.

### `Editor` vs `UncookedOnly` module type

- `Type=Editor` modules load only in the editor and are excluded from cooked builds. **Use this for codegen** — your generator code never needs to ship.
- `Type=UncookedOnly` is similar but loads in commandlets too. Useful if you want to run the generator from a build pipeline command.
- `Type=Runtime` modules load in cooked builds. **Don't put codegen UFUNCTIONs here** — they pull in `UnrealEd` / `BlueprintGraph` which aren't shipped.

### Live Coding can fail on cross-module changes

If you add new dependencies in a `.Build.cs` or change a module's load phase, Live Coding may refuse to patch ("Unable to build while Live Coding is active"). Close the editor and do a full UBT build. Live Coding works fine for in-method code edits within an existing module.

## Graph layout

### No auto-layout

There is no built-in auto-layout for `UEdGraph`. Plan node positions manually. Convention:

- 300px between columns
- 160px between rows
- Branches: place reactions at `Y = parent ± 200` to fan out

If the user complains the generated graph is messy, the fix is positioning math, not a layout call.

### `NodePosX` / `NodePosY` are int32 graph-pixels

The graph's coordinate system has no scale — these are pixel offsets. Default zoom shows roughly `1 unit = 1 pixel` at zoom 0.

## Misc

### `CreateNewGuid()` is mandatory on raw `NewObject` nodes

Skipping it causes copy-paste collisions later (two nodes with the same GUID). Always call after `NewObject<T>(Graph)`. Not needed when using `FGraphNodeCreator<T>` — that calls it internally.

### `bIsVariable` on widgets is required for both graph access AND animations

The animation runtime resolves `FWidgetAnimationBinding::WidgetName` against widgets exposed as variables on the generated class. `bIsVariable = false` widgets compile silently and play nothing.

### `ReconstructNode()` after pin-topology changes

If you `CreateUserDefinedPin` after `AllocateDefaultPins`, the node needs `ReconstructNode()` to refresh visually. The compile then bakes correctly either way, but the editor view is stale until reconstruction.
