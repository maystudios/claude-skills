# Data-Driven Design -- Detailed Reference

This document covers Data Tables, Data Assets, Primary Data Assets, the Asset Manager, Gameplay Tags as data backbone, and async loading patterns.

---

## Core Principle

**Separate data from logic.** Let designers configure gameplay without touching code. Use data assets for configuration, tags for classification, and the Asset Manager for lifecycle control.

---

## Data Tables (UDataTable)

**Best for**: Large quantities of homogeneous data (100+ items with the same structure).

**Sources:**
- https://dev.epicgames.com/documentation/en-us/unreal-engine/data-driven-gameplay-elements-in-unreal-engine
- https://unreal-garden.com/tutorials/data-driven-design/

### Key characteristics:
- Row structs inherit from `FTableRowBase`
- Support CSV/JSON import/export for batch editing in external tools (Excel, Google Sheets)
- Binary storage format -- difficult to diff in version control
- Backed by `TMap` internally -- row ordering is undefined
- Cannot contain UObject instances (only structs, primitives, and asset references)
- Cross-references use `FDataTableRowHandle` with type safety (UE 5.0+)

### C++ row definition:
```cpp
USTRUCT(BlueprintType)
struct FWeaponData : public FTableRowBase
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float BaseDamage = 10.f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float FireRate = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    TSoftObjectPtr<UStaticMesh> WeaponMesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FGameplayTagContainer WeaponTags;
};
```

### Runtime lookup:
```cpp
if (UDataTable* WeaponTable = LoadObject<UDataTable>(nullptr, TEXT("/Game/Data/DT_Weapons")))
{
    if (FWeaponData* Row = WeaponTable->FindRow<FWeaponData>(RowName, TEXT("WeaponLookup")))
    {
        float Damage = Row->BaseDamage;
    }
}
```

### When to use:
- Weapon stat tables, loot tables, NPC databases, item catalogs
- Any dataset where designers need to bulk-edit in spreadsheets
- Localization strings, level progression data

### When NOT to use:
- Unique complex definitions with inheritance (use Data Assets)
- Small numbers of highly distinct items (overhead not worth it)

---

## Data Assets (UDataAsset)

**Best for**: Unique, complex data definitions (boss configurations, skill trees, biome definitions).

### Key characteristics:
- Full subclassing support with inheritance-based value sharing
- Can contain UObject instances and complex nested structures
- Each instance is a separate `.uasset` file -- version control friendly
- "Bulk Edit via Property Matrix" enables tabular multi-asset editing
- No automatic asset discovery -- requires manual list management or Asset Manager

### C++ definition:
```cpp
UCLASS(Abstract)
class MYGAME_API UAbilityDefinition : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
    FText AbilityName;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
    FGameplayTag AbilityTag;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
    TSoftClassPtr<UGameplayAbility> AbilityClass;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
    float Cooldown = 5.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
    TArray<FGameplayTag> RequiredTags;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
    TArray<FGameplayTag> BlockedByTags;
};
```

### When to use:
- Boss/enemy definitions with unique behaviors
- Skill tree configurations
- Level/biome definitions
- Anything needing inheritance or complex nested data

---

## Primary Data Assets (UPrimaryDataAsset)

**Best for**: Assets requiring lifecycle management via the Asset Manager.

**Source**: https://tomlooman.com/unreal-engine-asset-manager-async-loading/

### Key characteristics:
- Extend `UDataAsset` with Asset Manager integration
- Controlled async loading and unloading
- Bundle-based memory management
- Asset auditing and discovery support

### C++ definition:
```cpp
UCLASS()
class MYGAME_API UItemDefinition : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    // Required: define the primary asset type for Asset Manager discovery
    virtual FPrimaryAssetId GetPrimaryAssetId() const override
    {
        return FPrimaryAssetId("Item", GetFName());
    }

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
    FText ItemName;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)
    FGameplayTagContainer ItemTags;

    // Soft references with asset bundles for selective loading
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, meta = (AssetBundles = "UI"))
    TSoftObjectPtr<UTexture2D> Icon;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, meta = (AssetBundles = "World"))
    TSoftObjectPtr<UStaticMesh> WorldMesh;
};
```

### Asset Manager setup:
1. Configure in Project Settings → Asset Manager with PrimaryAssetType entries
2. Set `Should Guess Type and Name in Editor` to OFF
3. Override `GetPrimaryAssetId()` returning `FPrimaryAssetId("Type", GetFName())`

### Async loading:
```cpp
UAssetManager& Manager = UAssetManager::Get();
FPrimaryAssetId AssetId("Item", "Sword_Fire");
TArray<FName> Bundles = { "World" };  // Only load World bundle (mesh, not UI icon)

Manager.LoadPrimaryAsset(AssetId, Bundles,
    FStreamableDelegate::CreateLambda([this, AssetId]()
    {
        UItemDefinition* Item = Manager.GetPrimaryAssetObject<UItemDefinition>(AssetId);
        // Use item...
    })
);
```

### Asset Bundles:
- Categorize soft references for selective loading
- `meta = (AssetBundles = "UI")` -- only loaded when UI bundle requested
- `meta = (AssetBundles = "World")` -- only loaded when world representation needed
- `Load` keeps assets until explicit unload; `Preload` auto-unloads when handle lost

---

## Gameplay Tags as Data Backbone

**Source**: https://tomlooman.com/unreal-engine-gameplaytags-data-driven-design/

Gameplay Tags are the preferred replacement for enums, booleans, and string comparisons.

### Hierarchy design:
```
// Plan from day one
Ability.Fire.Fireball
Ability.Fire.FlameWall
Ability.Ice.FrostBolt
State.Buff.Shield
State.Debuff.Stunned
State.Debuff.Poisoned
Damage.Physical.Slash
Damage.DoT.Fire
Damage.DoT.Poison
Item.Weapon.Sword
Item.Weapon.Staff
Item.Consumable.Potion
Input.Action.PrimaryFire
Input.Action.SecondaryFire
```

### C++ native definition (UE 4.27+ syntax):
```cpp
// Header (.h)
UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_Damage_Fire);
UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_State_Stunned);

// Source (.cpp)
UE_DEFINE_GAMEPLAY_TAG(TAG_Damage_Fire, "Damage.Fire");
UE_DEFINE_GAMEPLAY_TAG(TAG_State_Stunned, "State.Debuff.Stunned");

// File-scoped (no extern needed, .cpp only)
UE_DEFINE_GAMEPLAY_TAG_STATIC(TAG_Internal, "Internal.MyTag");
```

### Container operations:
```cpp
// Use FGameplayTagContainer, NOT TArray<FGameplayTag>
FGameplayTagContainer Tags;
Tags.AddTag(TAG_Damage_Fire);

// Hierarchical matching -- Damage.Fire matches query for "Damage"
FGameplayTag DamageQuery = FGameplayTag::RequestGameplayTag("Damage");
bool bIsDamage = Tags.HasTag(DamageQuery);  // true

// Container matching
FGameplayTagContainer RequiredTags;
RequiredTags.AddTag(TAG_State_Stunned);
bool bHasAll = Tags.HasAll(RequiredTags);
bool bHasAny = Tags.HasAny(RequiredTags);
```

### Best practices:
- Always use `FGameplayTagContainer` over `TArray<FGameplayTag>`
- Enable Fast Replication in Project Settings for efficient network replication
- Implement `IGameplayTagAssetInterface` on actors for built-in tag operations
- Use `FGameplayTagCountContainer` for reference-counted tag stacking
- Query tags hierarchically instead of exact-matching -- supports future extension

---

## Hard vs Soft References

| Aspect | Hard Reference | Soft Reference |
|--------|---------------|----------------|
| **C++ Type** | `TSubclassOf<>`, raw/TObjectPtr pointers | `TSoftObjectPtr<>`, `TSoftClassPtr<>`, `FSoftObjectPath` |
| **Loading** | Immediate, at package load time | On-demand, at runtime |
| **Performance** | Faster access (no lookup) | Slower access (requires resolve) |
| **Memory** | Loads asset + ALL its references | No memory until explicitly loaded |
| **Use when** | Asset always needed (player character, core HUD) | Conditional (level-specific, optional features) |

**Sources:**
- https://www.quodsoler.com/blog/understanding-hard-references-and-soft-references-in-unreal-engine
- https://raharuu.github.io/unreal/hard-references-reasons-avoid/

### Audit tools:
- **Reference Viewer**: Right-click asset → Reference Viewer (dependency graph)
- **Size Map**: Visualize memory footprint in treemap
- **Asset Audit**: Right-click → Audit Assets for size/frequency analysis

---

## Data Registries

Plugin-based system for managing data across multiple sources.

- GameFeaturePlugins can inject data into registries via "Add Data Registry" actions
- Useful for modular content extending base game data without modification
- Each registry has a type and can aggregate rows from multiple data tables

### When to use:
- Modular game content (DLC, mods, Game Feature Plugins adding items/abilities)
- Centralized data management across independently developed features

---

## Decision Flowchart

```
Need to store gameplay data?
│
├── Is it a large set of similar items (50+)?
│   └── YES → Data Table (+ CSV/JSON for external editing)
│
├── Is it a unique/complex definition (boss, skill tree)?
│   └── YES → Data Asset (with inheritance)
│
├── Does it need controlled loading/memory management?
│   └── YES → Primary Data Asset (with Asset Manager)
│
├── Is it state/classification/category information?
│   └── YES → Gameplay Tags (hierarchical, no hard references)
│
└── Is it modular content from Game Feature Plugins?
    └── YES → Data Registry (aggregates across sources)
```
