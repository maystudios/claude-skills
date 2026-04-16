# Gameplay Effects & Attributes -- Detailed Reference

## Table of Contents
- [Effect Duration Types](#effect-duration-types)
- [Modifiers](#modifiers)
- [Modifier Math (Aggregation)](#modifier-math)
- [SetByCaller](#setbycaller)
- [Modifier Magnitude Calculation (MMC)](#mmc)
- [Execution Calculation (ExecCalc)](#execcalc)
- [Stacking](#stacking)
- [Costs & Cooldowns](#costs--cooldowns)
- [GE Tags](#ge-tags)
- [GameplayEffectSpec](#gameplayeffectspec)
- [GameplayEffectContext](#gameplayeffectcontext)
- [Dynamic GEs](#dynamic-ges)
- [Attribute Design Patterns](#attribute-design-patterns)
- [Listening for Attribute Changes](#listening-for-attribute-changes)

---

## Effect Duration Types

| Type | Modifies | Tracked | Reverts | Use Case |
|------|----------|---------|---------|----------|
| Instant | BaseValue | No | No | Damage, healing, permanent pickups |
| Duration | CurrentValue | Yes | On expiry | Buffs, debuffs, timed effects |
| Infinite | CurrentValue | Yes | On removal | Passive gear bonuses, auras |

Periodic effects (on Duration/Infinite) execute their modifiers repeatedly. Each period tick is treated as Instant (modifies BaseValue).

## Modifiers

Four modifier types on a GE:
1. **Scalable Float** -- static value, optionally scaled by a curve table
2. **Attribute Based** -- reads an attribute from source or target
3. **Custom Calculation Class (MMC)** -- `UGameplayModMagnitudeCalculation` subclass
4. **SetByCaller** -- runtime value set on the spec before application

Four modifier operations: `Add`, `Multiply`, `Divide`, `Override`.

## Modifier Math

Aggregation formula per attribute:
```
FinalValue = (BaseValue + Sum(Additive)) * Product(Multiplicative) / Product(Division)
```

**Multiplicative/Division gotcha:** Uses `1 + Sum(ModValues - 1)` internally.
- Two +50% multipliers: `1 + (0.5 + 0.5) = 2.0` (100% increase, NOT 1.5 * 1.5 = 2.25)
- This is "additive stacking of percentage modifiers", not true multiplication

See tranek docs Section 4.5.3 for a code patch to enable true multiplication if needed.

## SetByCaller

Pass runtime values (damage amounts, durations, etc.) into a GE spec:

```cpp
FGameplayEffectSpecHandle Spec = ASC->MakeOutgoingSpec(DamageGE, 1, Context);

// Set by GameplayTag (preferred)
Spec.Data->SetSetByCallerMagnitude(
    FGameplayTag::RequestGameplayTag("Data.Damage"), DamageAmount);

// Read back
float Val = Spec.Data->GetSetByCallerMagnitude(
    FGameplayTag::RequestGameplayTag("Data.Damage"), true, 0.f);
```

In the GE Blueprint, set modifier magnitude to "SetByCaller" and assign the matching tag.

## MMC

`UGameplayModMagnitudeCalculation` -- predictable custom calculation. Can capture attributes from source/target.

```cpp
UMyMMC::UMyMMC()
{
    // Capture source's Strength attribute
    FGameplayEffectAttributeCaptureDefinition StrengthDef;
    StrengthDef.AttributeToCapture = UMyAttributeSet::GetStrengthAttribute();
    StrengthDef.AttributeSource = EGameplayEffectAttributeCaptureSource::Source;
    StrengthDef.bSnapshot = false; // false = live value, true = snapshot at application

    RelevantAttributesToCapture.Add(StrengthDef);
}

float UMyMMC::CalculateBaseMagnitude_Implementation(const FGameplayEffectSpec& Spec) const
{
    const FGameplayTagContainer* SourceTags = Spec.CapturedSourceTags.GetAggregatedTags();
    const FGameplayTagContainer* TargetTags = Spec.CapturedTargetTags.GetAggregatedTags();

    FAggregatorEvaluateParameters EvalParams;
    EvalParams.SourceTags = SourceTags;
    EvalParams.TargetTags = TargetTags;

    float Strength = 0.f;
    GetCapturedAttributeMagnitude(RelevantAttributesToCapture[0], Spec, EvalParams, Strength);

    return Strength * 1.5f; // Example: 150% of strength
}
```

**Key:** MMCs are predictable (can run on client). Use for cost calculations, scaling formulas.

## ExecCalc

`UGameplayEffectExecutionCalculation` -- most powerful calculation. Can modify multiple output attributes. NOT predictable (server only).

```cpp
// Declare capture structs (must have unique variable names per capture)
struct FDamageStatics
{
    DECLARE_ATTRIBUTE_CAPTUREDEF(Armor);
    DECLARE_ATTRIBUTE_CAPTUREDEF(Damage);

    FDamageStatics()
    {
        DEFINE_ATTRIBUTE_CAPTUREDEF(UMyAttributeSet, Armor, Target, false);
        DEFINE_ATTRIBUTE_CAPTUREDEF(UMyAttributeSet, Damage, Source, true);
    }
};

static const FDamageStatics& DamageStatics()
{
    static FDamageStatics Statics;
    return Statics;
}

UMyExecCalc::UMyExecCalc()
{
    RelevantAttributesToCapture.Add(DamageStatics().ArmorDef);
    RelevantAttributesToCapture.Add(DamageStatics().DamageDef);
}

void UMyExecCalc::Execute_Implementation(
    const FGameplayEffectCustomExecutionParameters& Params,
    FGameplayEffectCustomExecutionOutput& OutOutput) const
{
    FAggregatorEvaluateParameters EvalParams;

    float Armor = 0.f;
    Params.AttemptCalculateCapturedAttributeMagnitude(DamageStatics().ArmorDef, EvalParams, Armor);

    float Damage = 0.f;
    Params.AttemptCalculateCapturedAttributeMagnitude(DamageStatics().DamageDef, EvalParams, Damage);

    // Custom formula
    float FinalDamage = FMath::Max(Damage - Armor, 0.f);

    // Output to the Damage meta attribute
    OutOutput.AddOutputModifier(
        FGameplayModifierEvaluatedData(
            UMyAttributeSet::GetDamageAttribute(),
            EGameplayModOp::Additive,
            FinalDamage));
}
```

**Four ways to pass data to ExecCalcs:** SetByCaller, Backing Data Attribute Calculation Modifier, Backing Data Temporary Variable Calculation Modifier, GameplayEffectContext.

## Stacking

Two stacking policies:
- **Aggregate by Source** -- each source (caster) gets its own stack count
- **Aggregate by Target** -- all sources share one stack count on the target

Key stacking properties: Stack Limit, Stack Duration Refresh Policy, Stack Period Reset Policy, Stack Expiration Policy.

## Costs & Cooldowns

**Cost GE:** An Instant GE that reduces a resource attribute. Set on the ability's `CostGameplayEffect`.

**Cooldown GE:** A Duration GE that grants a `Cooldown.*` tag. Set on the ability's `CooldownGameplayEffect`. The ability checks for this tag before activation.

**Reusable cooldown pattern with SetByCaller:**
```cpp
// In ability constructor or defaults
CooldownGameplayEffectClass = UGE_SharedCooldown::StaticClass();

// Override GetCooldownTags to add ability-specific cooldown tag
const FGameplayTagContainer* UMyAbility::GetCooldownTags() const
{
    // Return the GE's cooldown tags + this ability's specific cooldown tag
}

// Override ApplyCooldown to set duration via SetByCaller
void UMyAbility::ApplyCooldown(const FGameplayAbilitySpecHandle Handle,
    const FGameplayAbilityActorInfo* ActorInfo,
    const FGameplayAbilityActivationInfo ActivationInfo) const
{
    FGameplayEffectSpecHandle Spec = MakeOutgoingGameplayEffectSpec(CooldownGameplayEffectClass);
    Spec.Data->SetSetByCallerMagnitude(FGameplayTag::RequestGameplayTag("Data.Cooldown"), CooldownDuration);
    ApplyGameplayEffectSpecToOwner(Handle, ActorInfo, ActivationInfo, Spec);
}
```

**Getting cooldown remaining:**
```cpp
float TimeRemaining = 0.f;
float Duration = 0.f;
ASC->GetCooldownRemainingForTag(CooldownTag, TimeRemaining, Duration);
```

## GE Tags

Tags on a GameplayEffect serve different purposes:
- **Asset Tags** -- describe the GE itself (for queries/filtering)
- **Granted Tags** -- added to target while GE is active
- **Ongoing Tag Requirements** -- GE only active while target has/doesn't have these tags
- **Application Tag Requirements** -- GE only applies if target meets tag conditions
- **Remove GEs with Tags** -- removes other active GEs matching these tags on application

## GameplayEffectSpec

Runtime instance wrapping a UGameplayEffect CDO. Carries:
- Level, SetByCaller values, captured attributes, source/target tags
- Created via `ASC->MakeOutgoingSpec(GEClass, Level, Context)`

## GameplayEffectContext

Carries contextual data about who caused the effect. Subclass for custom data:

```cpp
USTRUCT()
struct FMyGameplayEffectContext : public FGameplayEffectContext
{
    // Add custom fields (hit result, critical hit flag, etc.)
    // Override GetScriptStruct(), Duplicate(), NetSerialize()
    // Override UAbilitySystemGlobals::AllocGameplayEffectContext()
};
```

See tranek docs Section 4.5.17 for the full 6-step subclassing process.

## Dynamic GEs

Only Instant GEs can be created dynamically at runtime:

```cpp
UGameplayEffect* DynEffect = NewObject<UGameplayEffect>(GetTransientPackage(), FName("DynamicDamage"));
DynEffect->DurationPolicy = EGameplayEffectDurationType::Instant;
// Add modifiers...
```

Duration/Infinite GEs cannot be created dynamically -- they need proper class definitions for replication.

## Attribute Design Patterns

**Meta Attributes:** Non-replicated placeholder attributes (e.g., `Damage`, `Healing`) that are processed in `PostGameplayEffectExecute` and then zeroed out. Allows clean separation of the damage pipeline from health management.

**Derived Attributes:** Use an Infinite GE with Attribute Based modifiers to create attributes that auto-update when their source changes (e.g., `MaxHealth = BaseMaxHealth + Vitality * 10`).

**Attribute initialization:** Via DataTable with `FAttributeMetaData` row type, or in C++ via `InitX()` functions from `ATTRIBUTE_ACCESSORS`.

## Listening for Attribute Changes

```cpp
// Bind to attribute value changes
ASC->GetGameplayAttributeValueChangeDelegate(
    UMyAttributeSet::GetHealthAttribute())
    .AddUObject(this, &AMyCharacter::OnHealthChanged);

void AMyCharacter::OnHealthChanged(const FOnAttributeChangeData& Data)
{
    // Data.OldValue, Data.NewValue, Data.Attribute
    UpdateHealthBar(Data.NewValue / GetMaxHealth());
}
```
