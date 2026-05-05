// Build.cs template for an editor-only Unreal codegen module.
// Rename "MyExperimentEditor" everywhere to your module name.

using UnrealBuildTool;

public class MyExperimentEditor : ModuleRules
{
	public MyExperimentEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage     = PCHUsageMode.UseExplicitOrSharedPCHs;
		IWYUSupport  = IWYUSupport.Full;
		CppStandard  = CppStandardVersion.Cpp20;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			// Core editor + BP authoring
			"UnrealEd",
			"BlueprintGraph",
			"Kismet",
			"KismetCompiler",
			"AssetTools",
			"AssetRegistry",
			"Slate",
			"SlateCore",

			// Widget Blueprints (drop if not generating WBPs)
			"UMG",
			"UMGEditor",
			"MovieScene",
			"MovieSceneTracks",

			// Gameplay tags (drop if your generator doesn't reference any)
			"GameplayTags",

			// Add your domain plugin's runtime + editor modules here, e.g.:
			// "MyDialoguePlugin",
			// "MyDialoguePluginEditor",
		});
	}
}
