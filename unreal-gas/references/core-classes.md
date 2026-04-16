# GAS Core Classes & Setup

## Table of Contents
- [AbilitySystemComponent (ASC)](#abilitysystemcomponent)
- [IAbilitySystemInterface](#iabilitysysteminterface)
- [GameplayAbility](#gameplayability)
- [AttributeSet](#attributeset)
- [GameplayEffect](#gameplayeffect)
- [AbilityTask](#abilitytask)
- [GameplayCue](#gameplaycue)
- [GameplayTags in GAS](#gameplaytags-in-gas)
- [Setup: ASC on Character](#setup-asc-on-character)
- [Setup: ASC on PlayerState](#setup-asc-on-playerstate)

---

## AbilitySystemComponent

`UAbilitySystemComponent` -- the central ActorComponent that manages abilities, attributes, effects, tags, and cues.

```cpp
// Header
UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Abilities")
UAbilitySystemComponent* AbilitySystemComponent;

// Constructor
AbilitySystemComponent = CreateDefaultSubobject<UAbilitySystemComponent>(TEXT("AbilitySystemComponent"));
```

**Key concepts:**
- **OwnerActor** vs **AvatarActor**: Owner is the logical owner (PlayerState or Pawn), Avatar is the physical representation (Pawn). Critical for respawning -- ASC on PlayerState survives death.
- One ASC per Actor. Multiple ASCs on one owner is not recommended.
- Three **Replication Modes**:
  - `Full` -- single player or server-only. Replicates GEs to all clients.
  - `Mixed` -- multiplayer player-controlled. GEs replicated to owner only. Predicted GEs replicated to simulated proxies via Gameplay Tags/Cues.
  - `Minimal` -- AI-controlled. GEs never replicated to clients.

```cpp
// Set replication mode (typically in constructor or BeginPlay)
AbilitySystemComponent->SetReplicationMode(EGameplayEffectReplicationMode::Mixed);
```

## IAbilitySystemInterface

Any Actor using GAS must implement this interface:

```cpp
#include "AbilitySystemInterface.h"

UCLASS()
class AMyCharacter : public ACharacter, public IAbilitySystemInterface
{
    GENERATED_BODY()
public:
    virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override
    {
        return AbilitySystemComponent;
    }
};
```

## GameplayAbility

`UGameplayAbility` -- defines what an ability does. Override `ActivateAbility()` for logic.

```cpp
UCLASS()
class UGA_FireAbility : public UGameplayAbility
{
    GENERATED_BODY()
public:
    UGA_FireAbility();

    virtual void ActivateAbility(
        const FGameplayAbilitySpecHandle Handle,
        const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo,
        const FGameplayEventData* TriggerEventData) override;

    virtual void EndAbility(
        const FGameplayAbilitySpecHandle Handle,
        const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo,
        bool bReplicateEndAbility,
        bool bWasCancelled) override;
};
```

**Granting and activating:**
```cpp
// Grant (server only -- auto-replicates spec to owning client)
FGameplayAbilitySpecHandle Handle = ASC->GiveAbility(
    FGameplayAbilitySpec(AbilityClass, Level, InputID, SourceObject));

// Activate
ASC->TryActivateAbility(Handle);

// Activate by class
ASC->TryActivateAbilityByClass(UGA_FireAbility::StaticClass());

// Activate by tag
ASC->TryActivateAbilitiesByTag(FGameplayTagContainer(Tag));

// Revoke
ASC->ClearAbility(Handle);
```

**Tag containers on abilities (10 total):**
- `AbilityTags` -- tags that describe this ability
- `CancelAbilitiesWithTag` -- cancel other active abilities with these tags
- `BlockAbilitiesWithTag` -- block activation of abilities with these tags
- `ActivationOwnedTags` -- tags granted to owner while ability is active
- `ActivationRequiredTags` / `ActivationBlockedTags` -- owner must have/not have
- `SourceRequiredTags` / `SourceBlockedTags` -- source must have/not have
- `TargetRequiredTags` / `TargetBlockedTags` -- target must have/not have

## AttributeSet

`UAttributeSet` -- container for gameplay attributes. Must be defined in C++.

```cpp
#include "AttributeSet.h"
#include "AbilitySystemComponent.h"

// Macro for auto-generating accessor functions
#define ATTRIBUTE_ACCESSORS(ClassName, PropertyName) \
    GAMEPLAYATTRIBUTE_PROPERTY_GETTER(ClassName, PropertyName) \
    GAMEPLAYATTRIBUTE_VALUE_GETTER(PropertyName) \
    GAMEPLAYATTRIBUTE_VALUE_SETTER(PropertyName) \
    GAMEPLAYATTRIBUTE_VALUE_INITTER(PropertyName)

UCLASS()
class UMyAttributeSet : public UAttributeSet
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_Health, Category = "Attributes")
    FGameplayAttributeData Health;
    ATTRIBUTE_ACCESSORS(UMyAttributeSet, Health)

    UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_MaxHealth, Category = "Attributes")
    FGameplayAttributeData MaxHealth;
    ATTRIBUTE_ACCESSORS(UMyAttributeSet, MaxHealth)

    // Meta attribute -- not replicated, used as temporary damage bucket
    UPROPERTY(BlueprintReadOnly, Category = "Attributes")
    FGameplayAttributeData Damage;
    ATTRIBUTE_ACCESSORS(UMyAttributeSet, Damage)

    UFUNCTION()
    void OnRep_Health(const FGameplayAttributeData& OldHealth);

    UFUNCTION()
    void OnRep_MaxHealth(const FGameplayAttributeData& OldMaxHealth);

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual void PreAttributeChange(const FGameplayAttribute& Attribute, float& NewValue) override;
    virtual void PostGameplayEffectExecute(const FGameplayEffectModCallbackData& Data) override;
};
```

```cpp
// Implementation
void UMyAttributeSet::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION_NOTIFY(UMyAttributeSet, Health, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UMyAttributeSet, MaxHealth, COND_None, REPNOTIFY_Always);
}

void UMyAttributeSet::OnRep_Health(const FGameplayAttributeData& OldHealth)
{
    GAMEPLAYATTRIBUTE_REPNOTIFY(UMyAttributeSet, Health, OldHealth);
}

void UMyAttributeSet::OnRep_MaxHealth(const FGameplayAttributeData& OldMaxHealth)
{
    GAMEPLAYATTRIBUTE_REPNOTIFY(UMyAttributeSet, MaxHealth, OldMaxHealth);
}

void UMyAttributeSet::PreAttributeChange(const FGameplayAttribute& Attribute, float& NewValue)
{
    Super::PreAttributeChange(Attribute, NewValue);
    // Clamp CurrentValue (does NOT change modifier, only the query result)
    if (Attribute == GetMaxHealthAttribute())
    {
        NewValue = FMath::Max(NewValue, 1.0f);
    }
}

void UMyAttributeSet::PostGameplayEffectExecute(const FGameplayEffectModCallbackData& Data)
{
    Super::PostGameplayEffectExecute(Data);
    // Process meta damage attribute and clamp BaseValue here
    if (Data.EvaluatedData.Attribute == GetDamageAttribute())
    {
        const float LocalDamage = GetDamage();
        SetDamage(0.f); // Clear meta attribute
        if (LocalDamage > 0.f)
        {
            const float NewHealth = GetHealth() - LocalDamage;
            SetHealth(FMath::Clamp(NewHealth, 0.f, GetMaxHealth()));
        }
    }
}
```

**Registering:** Create AttributeSet as a default subobject on the Actor that owns the ASC:
```cpp
// In Actor constructor
AttributeSet = CreateDefaultSubobject<UMyAttributeSet>(TEXT("AttributeSet"));
```

## GameplayEffect

`UGameplayEffect` -- data-only Blueprint asset (no C++ subclassing needed for most cases). Created in the editor.

**Applying effects from C++:**
```cpp
// Create spec from a GE class
FGameplayEffectSpecHandle SpecHandle = ASC->MakeOutgoingSpec(
    DamageEffectClass, Level, ASC->MakeEffectContext());

// Set magnitude via SetByCaller
SpecHandle.Data->SetSetByCallerMagnitude(FGameplayTag::RequestGameplayTag("Data.Damage"), 50.f);

// Apply to self
ASC->ApplyGameplayEffectSpecToSelf(*SpecHandle.Data.Get());

// Apply to target
ASC->ApplyGameplayEffectSpecToTarget(*SpecHandle.Data.Get(), TargetASC);

// Remove active effect
ASC->RemoveActiveGameplayEffect(ActiveGEHandle);
```

**Custom calculations (MMC):**
```cpp
UCLASS()
class UMyDamageMMC : public UGameplayModMagnitudeCalculation
{
    GENERATED_BODY()
public:
    UMyDamageMMC();
    virtual float CalculateBaseMagnitude_Implementation(const FGameplayEffectSpec& Spec) const override;
};
```

**Execution Calculations (ExecCalc) -- most powerful, can modify multiple attributes:**
```cpp
UCLASS()
class UMyDamageExecCalc : public UGameplayEffectExecutionCalculation
{
    GENERATED_BODY()
public:
    UMyDamageExecCalc();
    virtual void Execute_Implementation(
        const FGameplayEffectCustomExecutionParameters& ExecutionParams,
        FGameplayEffectCustomExecutionOutput& OutExecutionOutput) const override;
};
```

## AbilityTask

`UAbilityTask` -- async tasks within abilities. Common built-in tasks: `UAbilityTask_PlayMontageAndWait`, `UAbilityTask_WaitGameplayEvent`, `UAbilityTask_WaitTargetData`.

```cpp
// In ActivateAbility:
UAbilityTask_PlayMontageAndWait* MontageTask = UAbilityTask_PlayMontageAndWait::CreatePlayMontageAndWaitProxy(
    this, NAME_None, AttackMontage, 1.0f, NAME_None, false);
MontageTask->OnCompleted.AddDynamic(this, &UGA_Attack::OnMontageCompleted);
MontageTask->OnCancelled.AddDynamic(this, &UGA_Attack::OnMontageCancelled);
MontageTask->ReadyForActivation();
```

## GameplayCue

Cosmetic-only effects triggered by tags matching `GameplayCue.*`. Unreliable replication -- never put gameplay logic here.

```cpp
// Trigger a cue manually (execute = fire-and-forget)
ASC->ExecuteGameplayCue(FGameplayTag::RequestGameplayTag("GameplayCue.Impact.Fire"));

// Add a persistent cue (active while GE is active)
// This happens automatically when a GE has a matching GameplayCue tag
```

## GameplayTags in GAS

Tags are the universal control mechanism: ability blocking/cancellation, effect requirements, cue association, event matching.

```cpp
// Check tags on ASC
bool bHasTag = ASC->HasMatchingGameplayTag(FGameplayTag::RequestGameplayTag("State.Stunned"));

// Listen for tag changes
ASC->RegisterGameplayTagEvent(
    FGameplayTag::RequestGameplayTag("State.Dead"),
    EGameplayTagEventType::NewOrRemoved)
    .AddUObject(this, &AMyCharacter::OnDeadTagChanged);
```

## Setup: ASC on Character

Simplest setup -- ASC lives on the Pawn. ASC is destroyed on death/respawn.

```cpp
AMyCharacter::AMyCharacter()
{
    AbilitySystemComponent = CreateDefaultSubobject<UAbilitySystemComponent>(TEXT("ASC"));
    AbilitySystemComponent->SetIsReplicated(true);
    AbilitySystemComponent->SetReplicationMode(EGameplayEffectReplicationMode::Mixed);

    AttributeSet = CreateDefaultSubobject<UMyAttributeSet>(TEXT("AttributeSet"));
}

void AMyCharacter::PossessedBy(AController* NewController)
{
    Super::PossessedBy(NewController);
    AbilitySystemComponent->InitAbilityActorInfo(this, this);
    // Grant default abilities here (server only)
}

void AMyCharacter::OnRep_PlayerState()
{
    Super::OnRep_PlayerState();
    AbilitySystemComponent->InitAbilityActorInfo(this, this);
}
```

## Setup: ASC on PlayerState

Recommended for respawning characters -- ASC survives Pawn death. Used by Lyra and Fortnite.

```cpp
// PlayerState header
UCLASS()
class AMyPlayerState : public APlayerState, public IAbilitySystemInterface
{
    GENERATED_BODY()
public:
    AMyPlayerState();
    virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override;

    UPROPERTY()
    TObjectPtr<UAbilitySystemComponent> AbilitySystemComponent;

    UPROPERTY()
    TObjectPtr<UMyAttributeSet> AttributeSet;
};

// Character -- delegates to PlayerState
void AMyCharacter::PossessedBy(AController* NewController)
{
    Super::PossessedBy(NewController);
    if (AMyPlayerState* PS = GetPlayerState<AMyPlayerState>())
    {
        PS->GetAbilitySystemComponent()->InitAbilityActorInfo(PS, this);
    }
}

void AMyCharacter::OnRep_PlayerState()
{
    Super::OnRep_PlayerState();
    if (AMyPlayerState* PS = GetPlayerState<AMyPlayerState>())
    {
        PS->GetAbilitySystemComponent()->InitAbilityActorInfo(PS, this);
    }
}
```
