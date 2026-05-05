// Skeleton — flesh out with the patterns from the cookbooks.
// See:
//   references/k2node-cookbook.md           (variables / functions / events / wiring)
//   references/widget-blueprint-cookbook.md (WBP hierarchy + UMG animations)
//   references/two-pass-compile.md          (when an intermediate compile is required)

#include "MyExperimentLibrary.h"

// Asset / package
#include "AssetRegistry/AssetRegistryModule.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"
#include "Misc/PackageName.h"

// Blueprint authoring
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "EdGraph/EdGraph.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_VariableSet.h"
#include "K2Node_CallFunction.h"
#include "Kismet/KismetSystemLibrary.h"

// Widget Blueprint authoring
#include "WidgetBlueprint.h"
#include "Blueprint/WidgetBlueprintGeneratedClass.h"
#include "Blueprint/WidgetTree.h"
#include "Blueprint/UserWidget.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"

// UMG animation / movie scene
#include "Animation/WidgetAnimation.h"
#include "Animation/WidgetAnimationBinding.h"
#include "Animation/MovieScene2DTransformTrack.h"
#include "Animation/MovieScene2DTransformSection.h"
#include "MovieScene.h"
#include "Channels/MovieSceneFloatChannel.h"

namespace
{
	UPackage* CreateOrLoadPackage(const FString& PackagePath, const FString& AssetName, FString& OutFullPath)
	{
		OutFullPath = PackagePath / AssetName;
		UPackage* Package = CreatePackage(*OutFullPath);
		if (Package)
		{
			Package->FullyLoad();
		}
		return Package;
	}

	bool SaveAssetPackage(UPackage* Package, UObject* Asset)
	{
		if (!Package || !Asset) { return false; }
		FAssetRegistryModule::AssetCreated(Asset);
		Package->MarkPackageDirty();
		const FString Filename = FPackageName::LongPackageNameToFilename(
			Package->GetName(), FPackageName::GetAssetPackageExtension());
		FSavePackageArgs Args;
		Args.TopLevelFlags = RF_Public | RF_Standalone;
		Args.SaveFlags     = SAVE_NoError;
		return UPackage::SavePackage(Package, Asset, *Filename, Args);
	}

	template <typename TNode>
	TNode* SpawnNode(UEdGraph* Graph, int32 PosX, int32 PosY)
	{
		TNode* N = NewObject<TNode>(Graph);
		N->CreateNewGuid();
		N->NodePosX = PosX;
		N->NodePosY = PosY;
		Graph->AddNode(N, /*bFromUI*/ false, /*bSelectNewNode*/ false);
		return N;
	}
}

UBlueprint* UMyExperimentLibrary::CreateDemoBlueprint(const FString& PackagePath, const FString& AssetName)
{
	FString FullPath;
	UPackage* Package = CreateOrLoadPackage(PackagePath, AssetName, FullPath);
	if (!Package) { return nullptr; }

	UBlueprint* BP = FKismetEditorUtilities::CreateBlueprint(
		AActor::StaticClass(),
		Package,
		FName(*AssetName),
		BPTYPE_Normal,
		UBlueprint::StaticClass(),
		UBlueprintGeneratedClass::StaticClass(),
		FName("MyExperiment"));
	if (!BP) { return nullptr; }

	// Variable: Counter (int32)
	{
		FEdGraphPinType IntT;
		IntT.PinCategory = UEdGraphSchema_K2::PC_Int;
		FBlueprintEditorUtils::AddMemberVariable(BP, FName("Counter"), IntT, FString(TEXT("0")));
	}

	// Event graph: OnPing -> Set Counter (42) -> PrintString
	UEdGraph* EventGraph = FBlueprintEditorUtils::FindEventGraph(BP);
	if (!EventGraph && BP->UbergraphPages.Num() > 0)
	{
		EventGraph = BP->UbergraphPages[0];
	}

	if (EventGraph)
	{
		// Position OFF (0,0) — placeholder events live there.
		UK2Node_CustomEvent* OnPing = SpawnNode<UK2Node_CustomEvent>(EventGraph, -400, -300);
		OnPing->CustomFunctionName = FName("OnPing");
		OnPing->bIsEditable        = true;
		OnPing->AllocateDefaultPins();

		UK2Node_VariableSet* SetCounter = SpawnNode<UK2Node_VariableSet>(EventGraph, -50, -300);
		SetCounter->VariableReference.SetSelfMember(FName("Counter"));
		SetCounter->AllocateDefaultPins();

		UK2Node_CallFunction* PrintNode = SpawnNode<UK2Node_CallFunction>(EventGraph, 300, -300);
		// Function reference BEFORE pin allocation.
		PrintNode->FunctionReference.SetExternalMember(
			GET_FUNCTION_NAME_CHECKED(UKismetSystemLibrary, PrintString),
			UKismetSystemLibrary::StaticClass());
		PrintNode->AllocateDefaultPins();

		const UEdGraphSchema_K2* K2 = GetDefault<UEdGraphSchema_K2>();
		OnPing->FindPinChecked(UEdGraphSchema_K2::PN_Then)->MakeLinkTo(SetCounter->GetExecPin());
		SetCounter->GetThenPin()->MakeLinkTo(PrintNode->GetExecPin());
		K2->TrySetDefaultValue(*SetCounter->FindPinChecked(FName("Counter")), TEXT("42"));
		K2->TrySetDefaultValue(*PrintNode->FindPinChecked(FName("InString")), TEXT("Hello!"));
	}

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
	FKismetEditorUtilities::CompileBlueprint(BP);
	SaveAssetPackage(Package, BP);
	return BP;
}

UWidgetBlueprint* UMyExperimentLibrary::CreateDemoWidget(const FString& PackagePath, const FString& AssetName)
{
	FString FullPath;
	UPackage* Package = CreateOrLoadPackage(PackagePath, AssetName, FullPath);
	if (!Package) { return nullptr; }

	UWidgetBlueprint* WBP = CastChecked<UWidgetBlueprint>(
		FKismetEditorUtilities::CreateBlueprint(
			UUserWidget::StaticClass(),
			Package,
			FName(*AssetName),
			BPTYPE_Normal,
			UWidgetBlueprint::StaticClass(),
			UWidgetBlueprintGeneratedClass::StaticClass(),
			FName("MyExperiment")));

	// Hierarchy
	UCanvasPanel* Root = WBP->WidgetTree->ConstructWidget<UCanvasPanel>(
		UCanvasPanel::StaticClass(), FName("RootCanvas"));
	WBP->WidgetTree->RootWidget = Root;
	WBP->OnVariableAdded(Root->GetFName());

	UTextBlock* MyText = WBP->WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass(), FName("MyText"));
	MyText->bIsVariable = true;
	MyText->SetText(FText::FromString(TEXT("Hello!")));
	if (UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(Root->AddChild(MyText)))
	{
		Slot->SetAnchors(FAnchors(0.5f, 0.5f));
		Slot->SetAlignment(FVector2D(0.5f, 0.5f));
		Slot->SetSize(FVector2D(500.f, 60.f));
	}
	WBP->OnVariableAdded(MyText->GetFName());

	// Animation: SlideIn (translation X: -400 -> 0 over 0.5s)
	UWidgetAnimation* Anim = NewObject<UWidgetAnimation>(WBP, FName("SlideIn"), RF_Public | RF_Transactional);
#if WITH_EDITOR
	Anim->SetDisplayLabel(TEXT("SlideIn"));
#endif

	UMovieScene* Scene = NewObject<UMovieScene>(Anim, NAME_None, RF_Public | RF_Transactional);
	Anim->MovieScene = Scene;
	Scene->SetTickResolutionDirectly(FFrameRate(60000, 1));
	Scene->SetDisplayRate(FFrameRate(60, 1));

	const FFrameRate Tick = Scene->GetTickResolution();
	const FFrameNumber Start = Tick.AsFrameNumber(0.0);
	const FFrameNumber End   = Tick.AsFrameNumber(0.5);
	Scene->SetPlaybackRange(TRange<FFrameNumber>(Start, End));

	const FGuid Guid = Scene->AddPossessable(MyText->GetName(), UWidget::StaticClass());

	FWidgetAnimationBinding Binding;
	Binding.WidgetName    = MyText->GetFName();
	Binding.AnimationGuid = Guid;
	Anim->AnimationBindings.Add(Binding);

	UMovieScene2DTransformTrack* Track = Scene->AddTrack<UMovieScene2DTransformTrack>(Guid);
	Track->SetPropertyNameAndPath(FName("RenderTransform"), TEXT("RenderTransform"));
	UMovieScene2DTransformSection* Section = Cast<UMovieScene2DTransformSection>(Track->CreateNewSection());
	Section->SetRange(TRange<FFrameNumber>(Start, End));
	Track->AddSection(*Section);

	// Direct UPROPERTY channel access — Translation[0]=X, [1]=Y
	Section->Translation[0].AddCubicKey(Start, -400.f);
	Section->Translation[0].AddCubicKey(End,      0.f);

	WBP->Animations.Add(Anim);

	// To wire an Event Construct -> Get(SlideIn) -> PlayAnimation chain, do an
	// intermediate compile here, then add the K2Nodes. See widget cookbook +
	// two-pass-compile.md for the exact pattern.

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(WBP);
	FKismetEditorUtilities::CompileBlueprint(WBP);
	SaveAssetPackage(Package, WBP);
	return WBP;
}
