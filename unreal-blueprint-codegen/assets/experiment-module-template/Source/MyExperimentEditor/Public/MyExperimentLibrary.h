// Skeleton BlueprintFunctionLibrary exposing codegen entry points to Python /
// Editor Utility Widgets. Add UFUNCTIONs for each generator you need.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MyExperimentLibrary.generated.h"

class UBlueprint;
class UWidgetBlueprint;

UCLASS()
class UMyExperimentLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * Example: create a basic Blueprint with a Counter variable + an OnPing custom event
	 * that sets Counter and prints a string. Returns the generated BP or nullptr on failure.
	 */
	UFUNCTION(BlueprintCallable, Category = "MyExperiment", meta = (DisplayName = "Create Demo Blueprint"))
	static UBlueprint* CreateDemoBlueprint(
		const FString& PackagePath = TEXT("/Game/Generated"),
		const FString& AssetName   = TEXT("BP_Demo"));

	/**
	 * Example: create a Widget Blueprint with a CanvasPanel root, a TextBlock, and a SlideIn animation.
	 */
	UFUNCTION(BlueprintCallable, Category = "MyExperiment", meta = (DisplayName = "Create Demo Widget"))
	static UWidgetBlueprint* CreateDemoWidget(
		const FString& PackagePath = TEXT("/Game/Generated"),
		const FString& AssetName   = TEXT("WBP_Demo"));
};
