# Widget Blueprint Cookbook — UMG Codegen

Build `UWidgetBlueprint` assets from C++ — full hierarchy, properties, slot config, and (the hard part) UMG animations with movie scene tracks/sections/keyframes. Validated against UE 5.7.

## Required module dependencies

Add these to your editor module's `.Build.cs`:

```csharp
PrivateDependencyModuleNames.AddRange(new[]
{
    "UMG", "UMGEditor",
    "MovieScene", "MovieSceneTracks",
    // ... plus the BP-codegen baseline:
    "UnrealEd", "BlueprintGraph", "Kismet", "KismetCompiler",
    "AssetTools", "AssetRegistry"
});
```

## Required includes

```cpp
#include "WidgetBlueprint.h"
#include "Blueprint/WidgetBlueprintGeneratedClass.h"
#include "Blueprint/WidgetTree.h"
#include "Blueprint/UserWidget.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/ProgressBar.h"

// For animations:
#include "Animation/WidgetAnimation.h"
#include "Animation/WidgetAnimationBinding.h"
#include "Animation/MovieScene2DTransformTrack.h"
#include "Animation/MovieScene2DTransformSection.h"
#include "MovieScene.h"
#include "Tracks/MovieSceneFloatTrack.h"
#include "Sections/MovieSceneFloatSection.h"
#include "Channels/MovieSceneFloatChannel.h"

// For event-graph wiring:
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "K2Node_Event.h"
#include "K2Node_VariableGet.h"
#include "K2Node_CallFunction.h"
#include "EdGraphSchema_K2.h"
```

## Creating the WBP asset

This mirrors `UWidgetBlueprintFactory::FactoryCreateNew` (engine source: `Engine/Source/Editor/UMGEditor/Private/WidgetBlueprintFactory.cpp`):

```cpp
UWidgetBlueprint* WBP = CastChecked<UWidgetBlueprint>(
    FKismetEditorUtilities::CreateBlueprint(
        UUserWidget::StaticClass(),                    // ParentClass — or your C++ subclass
        Package,
        FName(*AssetName),
        BPTYPE_Normal,
        UWidgetBlueprint::StaticClass(),
        UWidgetBlueprintGeneratedClass::StaticClass(),
        FName("MyGenerator")));
```

You can pass a custom `UUserWidget` subclass as the parent — that's how to give the WBP a C++ base with `BindWidget` / `BindWidgetAnim` slots that the hierarchy will fill.

## Building the widget hierarchy

Always go through `WBP->WidgetTree->ConstructWidget<T>(Class, FName("VarName"))`. Never `NewObject` widgets directly — they need the widget tree as outer.

```cpp
// 1) Root panel — UMG requires a UPanelWidget as root.
UCanvasPanel* Root = WBP->WidgetTree->ConstructWidget<UCanvasPanel>(
    UCanvasPanel::StaticClass(), FName("RootCanvas"));
WBP->WidgetTree->RootWidget = Root;
WBP->OnVariableAdded(Root->GetFName());   // exposes Root as a typed variable in the BP graph

// 2) TextBlock child.
UTextBlock* MyText = WBP->WidgetTree->ConstructWidget<UTextBlock>(
    UTextBlock::StaticClass(), FName("MyText"));
MyText->bIsVariable = true;                // important — needed for graph access AND animation binding
MyText->SetText(FText::FromString(TEXT("Hello!")));
{
    FSlateFontInfo Font = MyText->GetFont();
    Font.Size = 28;
    MyText->SetFont(Font);
}
if (UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(Root->AddChild(MyText)))
{
    Slot->SetAnchors(FAnchors(0.5f, 0.5f));   // centered
    Slot->SetAlignment(FVector2D(0.5f, 0.5f));
    Slot->SetPosition(FVector2D(0.f, 0.f));
    Slot->SetSize(FVector2D(500.f, 60.f));
}
WBP->OnVariableAdded(MyText->GetFName());
```

`AddChild` returns a `UPanelSlot*`; cast to the panel-specific slot type to access layout properties.

### Panel-slot quick reference

| Panel | Slot class | Key methods |
|---|---|---|
| `UCanvasPanel` | `UCanvasPanelSlot` | `SetAnchors`, `SetAlignment`, `SetPosition`, `SetSize`, `SetZOrder` |
| `UVerticalBox` | `UVerticalBoxSlot` | `SetPadding`, `SetHorizontalAlignment`, `SetVerticalAlignment`, `SetSize` (Auto / Fill ratio) |
| `UHorizontalBox` | `UHorizontalBoxSlot` | same as VBoxSlot |
| `UGridPanel` | `UGridSlot` | `SetRow`, `SetColumn`, `SetRowSpan`, `SetColumnSpan` |
| `UOverlay` | `UOverlaySlot` | `SetHorizontalAlignment`, `SetVerticalAlignment`, `SetPadding` |

### `bIsVariable` matters

`bIsVariable = true` does two things:

1. The widget appears as a typed variable in the WBP graph's "My Blueprint → Variables" panel.
2. **Animation bindings can target it** — `FWidgetAnimationBinding::WidgetName` is matched against widget `FName`, but the runtime binding lookup also requires the widget to be exposed as a variable on the generated class. Without `bIsVariable = true`, animation playback silently does nothing.

Always set it on widgets you'll reference from the graph or animate.

## UMG animations from C++

The fully-correct pattern, derived from engine source (`UWidgetAnimation.h`, `UMovieScene2DTransformSection.h`).

### Outer hierarchy is critical

```
WBP
└─ UWidgetAnimation        Outer = WBP
   └─ UMovieScene          Outer = WidgetAnimation
      └─ UMovieScene*Track Outer = MovieScene
         └─ UMovieScene*Section Outer = Track
```

Wrong outer → animation does not appear in the WBP's Animations panel. The editor's animation list filters by `Outer == WBP`.

### FName must equal the display label

`UUserWidget::GetAnimationByName(FName)` matches against `Anim->GetFName()`. The Animations panel and graph display use `DisplayLabel`. Set both to the same value:

```cpp
UWidgetAnimation* Anim = NewObject<UWidgetAnimation>(
    WBP, FName("SlideIn"), RF_Public | RF_Transactional);
#if WITH_EDITOR
Anim->SetDisplayLabel(TEXT("SlideIn"));
#endif
```

Mismatched names work for one access path but break the other.

### Animation bindings are a plain UPROPERTY array

`UWidgetAnimation::AnimationBindings` is `TArray<FWidgetAnimationBinding>` — push to it directly. There is **no `AddAnimationBinding(...)` helper** despite what some online tutorials claim.

```cpp
USTRUCT()
struct FWidgetAnimationBinding
{
    FName WidgetName;        // FName of the target widget (MyText->GetFName())
    FName SlotWidgetName;    // NAME_None unless animating a slot property
    FGuid AnimationGuid;     // returned by MovieScene->AddPossessable
    bool  bIsRootWidget;     // true only when targeting the root
    FMovieSceneDynamicBinding DynamicBinding;
};
```

### Channel layout for `UMovieScene2DTransformSection`

The 2D transform section exposes channels as direct UPROPERTY arrays — bypass the channel proxy:

```cpp
UPROPERTY() FMovieSceneFloatChannel Translation[2];   // [0]=X, [1]=Y
UPROPERTY() FMovieSceneFloatChannel Rotation;
UPROPERTY() FMovieSceneFloatChannel Scale[2];         // [0]=X, [1]=Y
UPROPERTY() FMovieSceneFloatChannel Shear[2];
```

So `Section->Translation[0].AddCubicKey(Frame, Value)` works directly — no `GetChannelProxy()` dance needed.

### Complete: build a slide-in animation on a TextBlock's RenderTransform

```cpp
// Animation outered to WBP.
UWidgetAnimation* Anim = NewObject<UWidgetAnimation>(WBP, FName("SlideIn"), RF_Public | RF_Transactional);
#if WITH_EDITOR
Anim->SetDisplayLabel(TEXT("SlideIn"));
#endif

// MovieScene outered to the animation.
UMovieScene* Scene = NewObject<UMovieScene>(Anim, FName("SlideIn_MovieScene"), RF_Public | RF_Transactional);
Anim->MovieScene = Scene;
Scene->SetTickResolutionDirectly(FFrameRate(60000, 1));   // UMG default tick resolution
Scene->SetDisplayRate(FFrameRate(60, 1));

const FFrameRate Tick    = Scene->GetTickResolution();
const FFrameNumber Start = Tick.AsFrameNumber(0.0);
const FFrameNumber End   = Tick.AsFrameNumber(0.5);   // 0.5 second animation
Scene->SetPlaybackRange(TRange<FFrameNumber>(Start, End));

// Possessable for the target widget. The editor binds at runtime via WidgetName,
// so UWidget::StaticClass() is sufficient as the possessable type.
const FGuid Guid = Scene->AddPossessable(MyText->GetName(), UWidget::StaticClass());

// The piece nobody documents: mirror the GUID into FWidgetAnimationBinding
// so UWidgetAnimation::BindPossessableObject can resolve at runtime.
FWidgetAnimationBinding Binding;
Binding.WidgetName     = MyText->GetFName();
Binding.SlotWidgetName = NAME_None;
Binding.AnimationGuid  = Guid;
Binding.bIsRootWidget  = false;
Anim->AnimationBindings.Add(Binding);

// 2D transform track on RenderTransform.
UMovieScene2DTransformTrack* Track = Scene->AddTrack<UMovieScene2DTransformTrack>(Guid);
Track->SetPropertyNameAndPath(FName("RenderTransform"), TEXT("RenderTransform"));

UMovieScene2DTransformSection* Section = Cast<UMovieScene2DTransformSection>(Track->CreateNewSection());
Section->SetRange(TRange<FFrameNumber>(Start, End));
Track->AddSection(*Section);

// Direct channel access — Translation[0] is X, [1] is Y.
Section->Translation[0].AddCubicKey(Start, -400.f);
Section->Translation[0].AddCubicKey(End,      0.f);
Section->Translation[1].AddCubicKey(Start,    0.f);
Section->Translation[1].AddCubicKey(End,      0.f);

// Register on the WBP.
WBP->Animations.Add(Anim);
```

### Animating a single float property (e.g. RenderOpacity, fade-in)

For non-transform properties, use `UMovieSceneFloatTrack`:

```cpp
UMovieSceneFloatTrack* Track = Scene->AddTrack<UMovieSceneFloatTrack>(Guid);
Track->SetPropertyNameAndPath(FName("RenderOpacity"), TEXT("RenderOpacity"));

UMovieSceneFloatSection* Section = Cast<UMovieSceneFloatSection>(Track->CreateNewSection());
Section->SetRange(TRange<FFrameNumber>(Start, End));
Track->AddSection(*Section);

Section->GetChannel().AddCubicKey(Start, 0.f);
Section->GetChannel().AddCubicKey(End,   1.f);
```

`UMovieSceneFloatSection::GetChannel()` returns the section's single float channel.

## Wiring the Event Graph to play the animation

`UUserWidget::PlayAnimationByName` does **not exist** in UE 5.7 — only `PlayAnimation(UWidgetAnimation* InAnimation, ...)`. So you must wire the animation via a `UK2Node_VariableGet` resolving the animation's auto-generated UProperty.

This requires the **two-pass compile** (see [two-pass-compile.md](two-pass-compile.md)) because the UMG compiler creates the UProperty for each animation only on compile. Workflow:

```cpp
// PASS 1: build hierarchy + animations.
// ... (everything above) ...
WBP->Animations.Add(SlideIn);
WBP->Animations.Add(FadeIn);

// COMPILE so each animation becomes an FProperty on the generated class.
FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);
FKismetEditorUtilities::CompileBlueprint(WBP);

// PASS 2: event graph.
UEdGraph* EventGraph = FBlueprintEditorUtils::FindEventGraph(WBP);

UK2Node_Event* ConstructEvt = SpawnNode<UK2Node_Event>(EventGraph, -700, -300);
ConstructEvt->EventReference.SetExternalMember(FName("Construct"), UUserWidget::StaticClass());
ConstructEvt->bOverrideFunction = true;
ConstructEvt->AllocateDefaultPins();

auto SpawnPlayCall = [&](int32 PosX, FName AnimVarName) -> UK2Node_CallFunction*
{
    UK2Node_VariableGet* GetAnim = SpawnNode<UK2Node_VariableGet>(EventGraph, PosX - 50, -150);
    GetAnim->VariableReference.SetSelfMember(AnimVarName);
    GetAnim->AllocateDefaultPins();

    UK2Node_CallFunction* PlayAnim = SpawnNode<UK2Node_CallFunction>(EventGraph, PosX, -300);
    PlayAnim->FunctionReference.SetExternalMember(
        GET_FUNCTION_NAME_CHECKED(UUserWidget, PlayAnimation),
        UUserWidget::StaticClass());
    PlayAnim->AllocateDefaultPins();

    GetAnim->FindPinChecked(AnimVarName)
           ->MakeLinkTo(PlayAnim->FindPinChecked(FName("InAnimation")));
    return PlayAnim;
};

UK2Node_CallFunction* PlayFade  = SpawnPlayCall(-300, FName("FadeIn"));
UK2Node_CallFunction* PlaySlide = SpawnPlayCall( 100, FName("SlideIn"));

ConstructEvt->FindPinChecked(UEdGraphSchema_K2::PN_Then)->MakeLinkTo(PlayFade->GetExecPin());
PlayFade->FindPinChecked(UEdGraphSchema_K2::PN_Then)->MakeLinkTo(PlaySlide->GetExecPin());

// FINAL COMPILE
FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);
FKismetEditorUtilities::CompileBlueprint(WBP);
```

`PlayAnimation` is non-pure → must be in the exec chain (its `Then` pin chains to the next call's exec).

## When the Variable-Get pin doesn't resolve

Symptom: `Get FadeIn` shows up as a generic untyped node, the In Animation pin shows "Select Asset" with no connection. Cause: animation's `FName` doesn't match what `SetSelfMember` looks up, or two-pass compile was skipped.

Verify:

1. Animation's `FName` and `DisplayLabel` are identical (`FName("FadeIn")` and `SetDisplayLabel(TEXT("FadeIn"))`).
2. An intermediate `CompileBlueprint(WBP)` ran after `WBP->Animations.Add(...)` and before the `UK2Node_VariableGet` was spawned.
3. The widget targeted by the animation has `bIsVariable = true`.

## Saving

```cpp
FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);
FKismetEditorUtilities::CompileBlueprint(WBP);

FAssetRegistryModule::AssetCreated(WBP);
Package->MarkPackageDirty();
const FString Filename = FPackageName::LongPackageNameToFilename(
    Package->GetName(), FPackageName::GetAssetPackageExtension());
FSavePackageArgs SaveArgs;
SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
UPackage::SavePackage(Package, WBP, *Filename, SaveArgs);
```

## What about runtime-only widget construction?

If the goal is to build a widget at game time (not author a `.uasset`), use `CreateWidget<>()` plus `WidgetTree->ConstructWidget` directly on a runtime `UUserWidget`. None of the codegen / `WBP->Animations` / `CompileBlueprint` machinery applies — that's just normal UMG. This skill is for building **shippable WBP assets**.
