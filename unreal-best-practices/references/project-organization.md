# Project Organization -- Detailed Reference

This document covers naming conventions, folder structure, plugin-based modular architecture, and testing/automation frameworks.

---

## Naming Conventions

**Sources:**
- https://dev.epicgames.com/documentation/en-us/unreal-engine/recommended-asset-naming-conventions-in-unreal-engine-projects
- https://github.com/Allar/ue5-style-guide
- https://tomlooman.com/unreal-engine-naming-convention-guide

### General naming structure:
`[TypePrefix]_[BaseName]_[Descriptor]_[OptionalVariant]`

Examples: `SM_Pipe_Short`, `T_Pipe_Long_D`, `BP_Enemy_Goblin_01`

### Standard Prefixes

| Prefix | Asset Type | Notes |
|--------|-----------|-------|
| `BP_` | Blueprint (general) | Actors, pawns, game modes |
| `BPI_` | Blueprint Interface | Interface-only assets |
| `WBP_` | Widget Blueprint | UI widgets |
| `DA_` | Data Asset | Data-only assets |
| `DT_` | Data Table | Tabular data |
| `E_` | Enumeration | Matches C++ convention |
| `S_` | Struct | Blueprint structures |
| `SM_` | Static Mesh | |
| `SK_` | Skeletal Mesh | |
| `M_` | Material | Base materials |
| `MI_` | Material Instance | Material instances |
| `MF_` | Material Function | Reusable material nodes |
| `T_` | Texture | With suffixes below |
| `NS_` | Niagara System | Particle effects |
| `NE_` | Niagara Emitter | Individual emitters |
| `S_` or `SW_` | Sound Wave | Audio files |
| `SC_` | Sound Cue | Legacy audio |
| `MS_` | MetaSound Source | Modern audio |
| `ABP_` | Animation Blueprint | Or `_AnimBP` suffix |
| `AM_` | Animation Montage | Or `_Montage` suffix |
| `BS_` | Blend Space | Blend spaces |
| `AS_` | Animation Sequence | Raw animations |
| `CR_` | Control Rig | Rig assets |

### GAS-Specific Prefixes (Lyra convention)

| Prefix | Asset Type |
|--------|-----------|
| `GA_` | Gameplay Ability |
| `GE_` | Gameplay Effect |
| `GC_` | Gameplay Cue |
| `AS_` | Attribute Set (C++ class) |

### Enhanced Input Prefixes

| Prefix | Asset Type |
|--------|-----------|
| `IA_` | Input Action |
| `IMC_` | Input Mapping Context |

### Texture Suffixes

| Suffix | Map Type |
|--------|---------|
| `_D` | Diffuse / Albedo |
| `_N` | Normal |
| `_E` | Emissive |
| `_M` | Metallic |
| `_R` | Roughness |
| `_AO` | Ambient Occlusion |
| `_MT` | Mask/Tint |
| `_H` | Height / Displacement |
| `_DP` | Displacement |
| `_F` | Flow Map |

### Lyra-style shorter prefixes:
Some modern projects adopt shorter prefixes: `B_` (Blueprint), `W_` (Widget). Choose one convention and be consistent.

---

## Folder Structure

### Feature-Based Organization (Recommended)

Group by game feature, not asset type:

```
Content/
  MyGame/
    Characters/
      Player/
        BP_PlayerCharacter.uasset
        SK_Player.uasset
        ABP_Player.uasset
        AM_Player_Attack.uasset
      Enemies/
        Goblin/
          BP_Enemy_Goblin.uasset
          SK_Goblin.uasset
          ABP_Goblin.uasset
        Dragon/
    Weapons/
      Sword/
        SM_Sword_Iron.uasset
        DA_Weapon_Sword_Iron.uasset
      Staff/
    Environment/
      Nature/
      Buildings/
    UI/
      HUD/
        WBP_HUD_Main.uasset
      Menus/
        WBP_Menu_Pause.uasset
    Core/
      BP_GameMode_Default.uasset
      BP_GameState_Default.uasset
      BP_PlayerController_Default.uasset
    AI/
    Audio/
      Music/
      SFX/
    Effects/
      Impacts/
      Environment/
    Input/
      IA_Move.uasset
      IA_Jump.uasset
      IMC_Default.uasset
      IMC_Vehicle.uasset
    Data/
      DT_Weapons.uasset
      DT_Items.uasset
    Maps/
      Gameplay/
      Dev/
        MAP_Dev_Combat.umap
```

### Anti-Pattern: Asset-Type-Based Organization

Avoid separating all meshes into one folder, all materials into another, etc. This makes it hard to find related assets and doesn't scale.

### Rules:
- All project content under a single top-level folder (e.g., `Content/MyGame/`)
- No assets in the root `Content/` folder
- `Dev/` folders for personal test content (excluded from builds)
- Use `_WIP` or `_Test` suffixes for work-in-progress assets
- Keep `Maps/` separate since they have special build significance

---

## Plugin-Based Modular Architecture

### Game Feature Plugins

**Source**: https://dev.epicgames.com/documentation/en-us/unreal-engine/game-features-and-modular-gameplay-in-unreal-engine

**Directory structure:**
```
MyProject/
  Plugins/
    GameFeatures/
      ShooterCore/
        ShooterCore.uplugin
        Content/
          Weapons/
          Characters/
        Source/
          ShooterCoreRuntime/
      HorrorMode/
        HorrorMode.uplugin
        Content/
        Source/
```

**Plugin lifecycle:** Installed → Registered → Loaded → Active

**GameFeatureAction types:**
- `AddComponents` -- inject components into existing actors at runtime
- `AddCheats` -- add cheat manager extensions
- `AddDataRegistry` -- inject data registry sources
- Custom actions -- add abilities, input mappings, level instances

**Rules:**
1. Core game must NEVER reference Game Feature plugins (one-way dependency)
2. Game Features inject INTO the base game, not the reverse
3. Add `GameFeatures` and `ModularGameplay` to module dependencies
4. Enable both "Game Features" and "Modular Gameplay" plugins
5. Actors must register as receivers for component injection

### When to use Game Feature Plugins:
- Content packs (weapon sets, character packs, enemy packs)
- Game modes (shooter, horror, racing -- each as a plugin)
- Experimental features (enable/disable without affecting core)
- DLC and post-launch content

### When NOT to use:
- Very small projects with no modularity needs
- Systems tightly integrated with core gameplay loop

---

## Testing in UE5

### Automation Testing Framework (Base)

**Source**: https://dev.epicgames.com/documentation/en-us/unreal-engine/automation-test-framework-in-unreal-engine

```cpp
// Simple test
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMyTest, "MyProject.Unit.MyFeature",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMyTest::RunTest(const FString& Parameters)
{
    TestEqual("Health should be 100", Character->GetHealth(), 100.f);
    return true;
}
```

Access via: Tools → Session Frontend → Automation tab.

### Spec Framework (BDD-Style)

```cpp
BEGIN_DEFINE_SPEC(FWeaponSpec, "MyProject.Weapons",
    EAutomationTestFlags::ProductFilter | EAutomationTestFlags::ApplicationContextMask)
    AShooterWeapon* Weapon;
END_DEFINE_SPEC(FWeaponSpec)

void FWeaponSpec::Define()
{
    BeforeEach([this]()
    {
        Weapon = NewObject<AShooterWeapon>();
    });

    Describe("Firing", [this]()
    {
        It("should decrease ammo by one", [this]()
        {
            int32 InitialAmmo = Weapon->GetCurrentAmmo();
            Weapon->Fire();
            TestEqual("Ammo decreased", Weapon->GetCurrentAmmo(), InitialAmmo - 1);
        });
    });
}
```

Best for asset validation tests and structured test suites.

### CQTest (Gameplay Tests)

Upstream from Sea of Thieves' test system. Modern C++ testing with fixtures, PIE helpers, and actor spawn utilities. Best documentation: Lyra project source.

### Functional Tests

Place `AFunctionalTest` actors in levels to test gameplay scenarios in-context. Can be Blueprint-driven -- accessible to non-programmers.

### Gauntlet

Multi-process test orchestrator for multiplayer games. Launches N clients + server for soak testing and performance analysis.

### Map Check & Data Validation

```cpp
// Override on actors for edit-time validation
virtual void CheckForErrors() override;

// Override on UObjects for save-time validation
virtual EDataValidationResult IsDataValid(FDataValidationContext& Context) const override;

// Or create standalone validators
UCLASS()
class UMyValidator : public UEditorValidatorBase { ... };
```

### Recommendation:
- **Spec** for asset validation and unit tests
- **CQTest** for gameplay/functional tests
- **Functional Tests** for level-specific scenarios
- Understand the base Automation Framework fundamentals

---

## Editor Workflow Automation

### Editor Utility Widgets (EUW)

Blueprint-based editor tools with full UMG widget support. Create custom editor panels for level designers and artists.

Launch via: Content Browser right-click → Run Editor Utility Widget, or register as persistent tabs.

### Scripted Actions

Editor Utility Blueprints appearing in right-click context menus:
1. Create Editor Utility Blueprint
2. Add function with "Call In Editor" checked
3. Function appears in right-click menu for selected assets/actors
4. Supports user input prompts via function parameters

### Python Scripting

Execute Python from: Editor menu, console, startup scripts, or Editor Utility Widgets.

```python
import unreal

# Access editor subsystem
editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

# Batch asset operations
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
```

Place startup scripts in `Content/Python/init_unreal.py`.

### Remote Control API

HTTP/WebSocket server for exposing and controlling UProperties and UFunctions remotely. Useful for external tool integration, motion capture, virtual production.

---

## Build System Best Practices

### Build.cs Essentials

```csharp
public class MyGame : ModuleRules
{
    public MyGame(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] {
            "Core",
            "CoreUObject",
            "Engine",
            "EnhancedInput",       // Modern input (required)
            "GameplayTags",        // Tag system (recommended)
            "GameplayAbilities",   // GAS (if using)
            "GameplayTasks",       // GAS tasks (if using GAS)
            "AIModule",            // AI framework
            "StateTreeModule",     // StateTree (if using)
            "GameplayStateTreeModule",
            "UMG",                 // UI
            "Slate",               // Low-level UI
            "SlateCore",
        });
    }
}
```

### Target.cs Essentials

```csharp
public class MyGameTarget : TargetRules
{
    public MyGameTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V6;  // Latest as of 5.7
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7;
        // CppStandard = CppStandardVersion.Cpp20;  // Default for new projects since 5.3
    }
}
```

### Version-aware patterns:
- `BuildSettingsVersion.V6` is current for UE 5.7
- C++20 is default since 5.3; C++20 modules (import) NOT supported by UBT
- ThinLTO enabled by default for Clang in 5.7
- UBA (Unreal Build Accelerator) production-ready since 5.5 for distributed compilation
