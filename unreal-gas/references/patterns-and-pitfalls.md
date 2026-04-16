# GAS Common Patterns & Pitfalls

## Table of Contents
- [Implementation Recipes](#implementation-recipes)
- [Critical Pitfalls](#critical-pitfalls)
- [Troubleshooting](#troubleshooting)
- [Debugging Tools](#debugging-tools)
- [Common Acronyms](#common-acronyms)

---

## Implementation Recipes

### Stun Effect
Apply a GE that grants a `State.Stunned` tag. Configure abilities to have `ActivationBlockedTags` including `State.Stunned`. The tag blocks ability activation systemically without per-ability code.

### Sprint
Predicted ability that applies an Infinite GE granting movement speed buff. Drain stamina with a periodic Instant GE. End ability when stamina reaches zero.

### Damage Pipeline with Meta Attributes
1. ExecCalc computes final damage (factors in armor, resistances, buffs)
2. ExecCalc outputs to `Damage` meta attribute (non-replicated)
3. `PostGameplayEffectExecute` reads `Damage`, subtracts from `Health`, clears `Damage` to 0
4. Health clamping happens in `PostGameplayEffectExecute` (BaseValue), NOT in `PreAttributeChange` (CurrentValue only)

### Passive Abilities
Grant on `OnAvatarSet` and activate immediately:
```cpp
void UGA_Passive::OnAvatarSet(const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilitySpec& Spec)
{
    Super::OnAvatarSet(ActorInfo, Spec);
    ActorInfo->AbilitySystemComponent->TryActivateAbility(Spec.Handle);
}
```

### Non-Stacking Debuff (Greatest Magnitude Only)
Override `OnAttributeAggregatorCreated` on your AttributeSet to use `EGameplayModEvaluationChannel` with a custom evaluation that keeps only the most negative modifier among all sources.

### Combo Attack Chain
Use `PlayMontageAndWait` AbilityTask with montage sections. On `CheckCombo` AnimNotify, check input buffer. Advance to next section or end ability.

### Listening for Cooldown Begin/End
```cpp
// Cooldown begin -- listen on the ASC for tag added
ASC->RegisterGameplayTagEvent(CooldownTag, EGameplayTagEventType::NewOrRemoved)
    .AddUObject(this, &UMyWidget::OnCooldownTagChanged);

// Cooldown remaining -- poll or use timer
float Remaining, Duration;
ASC->GetCooldownRemainingForTag(CooldownTag, Remaining, Duration);
```

### Interaction System
One-button interact: activate interaction ability, use `WaitTargetData` task with a trace-based TargetActor to find interactable, send GameplayEvent to the target's ASC.

---

## Critical Pitfalls

### PreAttributeChange vs PostGameplayEffectExecute
- `PreAttributeChange(Attribute, NewValue)` clamps the **queried CurrentValue** only. It does NOT permanently change the modifier. If you clamp health to max here, the underlying modifier still exceeds max, and the next modifier recalculation will ignore your clamp.
- `PostGameplayEffectExecute(Data)` is where you clamp the **BaseValue** permanently. Always clamp health/resources here.
- **Rule:** Use `PreAttributeChange` for UI-facing clamps. Use `PostGameplayEffectExecute` for authoritative clamping.

### Multiply/Divide Modifier Math
GAS uses `1 + Sum(ModValues - 1)`, not true multiplication. Two +50% buffs give +100% (2x), not +125% (2.25x). If you need true multiplication, see the engine code patch in tranek docs Section 4.5.3.

### Animation Montage Replication
Direct `PlayMontage()` calls on the AnimInstance do NOT replicate through GAS. Always use `UAbilityTask_PlayMontageAndWait` for abilities that need montage replication.

### Server Respects Remote Ability Cancellation
This ability property "causes trouble more often than not" (Epic). Disable it. If a client can cancel a server ability, it opens exploit vectors and race conditions.

### Replication Policy on GameplayAbility
Despite its name, this property does NOT control what you think. Epic has stated they want to remove it. Do not enable it.

### Replicate Input Directly
Epic recommends NOT using this ability property. Use Generic Replicated Events instead.

### PlayerState NetUpdateFrequency
When ASC is on PlayerState, the default `NetUpdateFrequency` is often too low (1-2 Hz). This causes perceived lag for attribute and tag changes. Increase it or enable Adaptive Network Update Frequency in project settings.

### Removing AttributeSets at Runtime
Can crash the client if the server removes an AttributeSet and the client tries to replicate an attribute on that set before processing the removal. Avoid runtime removal; if necessary, ensure strict ordering.

### CancelAllAbilities Bug
`CancelAllAbilities()` has a known bug with Non-Instanced abilities -- it may not cancel them properly. Use explicit ability handle cancellation instead.

### Dynamic GE Limitations
Only Instant GEs can be created via `NewObject` at runtime. Duration/Infinite GEs require a proper UCLASS for replication to function. Design your GEs as Blueprint assets in the editor.

### Blueprint Actor Duplication
Known engine bug (UE-81109): duplicating Blueprint actors with AttributeSets can set them to nullptr. Verify AttributeSet references after duplication.

### Cooldown Prediction
Cooldowns cannot be truly predicted because server and client timestamps differ. High-latency players get lower effective fire rates. Fortnite bypasses GAS cooldown prediction with custom bookkeeping for fire-rate-sensitive abilities.

### GE Removal Prediction
GE removal is NOT predictable. If you remove a GE on the client predictively, there is no rollback mechanism. Only the server should remove GEs authoritatively.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `unresolved external symbol MarkPropertyDirty` | Add `"NetCore"` to `Build.cs` PublicDependencyModuleNames |
| `ScriptStructCache` assertion/crash | Call `UAbilitySystemGlobals::Get().InitGlobalData()` (pre-5.3) |
| Attributes not replicating | Ensure `SetIsReplicated(true)`, use `DOREPLIFETIME_CONDITION_NOTIFY` with `REPNOTIFY_Always` |
| Abilities not activating on client | Verify `InitAbilityActorInfo()` called on client (OnRep_PlayerState) |
| Predicted GEs not rolling back | Only non-Instant GEs support rollback. Instant GEs (damage) never roll back |
| Montages not playing on remote clients | Use `PlayMontageAndWait` AbilityTask, not direct `PlayMontage` |

## Debugging Tools

1. **`showdebug abilitysystem`** -- Console command showing active abilities, attributes, and effects on the targeted actor
2. **Gameplay Debugger** (apostrophe key) -- Visual overlay with GAS category showing tags, effects, attributes
3. **`AbilitySystemComponent->SetVerbose(true)`** -- Enables verbose logging for the ASC

## Common Acronyms

| Acronym | Full Name |
|---------|-----------|
| GAS | Gameplay Ability System |
| ASC | AbilitySystemComponent |
| GA | GameplayAbility |
| GE | GameplayEffect |
| GC | GameplayCue |
| AT | AbilityTask |
| MMC | ModifierMagnitudeCalculation |
| ExecCalc | ExecutionCalculation |
| CAR | CustomApplicationRequirement |
