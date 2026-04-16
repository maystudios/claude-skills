# GAS Networking & Prediction Reference

## Table of Contents
- [Replication Modes](#replication-modes)
- [Net Execution Policies](#net-execution-policies)
- [What Gets Replicated](#what-gets-replicated)
- [Prediction System](#prediction-system)
- [ASC Placement (Pawn vs PlayerState)](#asc-placement)
- [Multiplayer Setup Checklist](#multiplayer-setup-checklist)
- [Optimization Strategies](#optimization-strategies)

---

## Replication Modes

Set on `UAbilitySystemComponent::SetReplicationMode()`:

| Mode | Use Case | GE Replication |
|------|----------|----------------|
| `Full` | Single player / dedicated server | GEs replicated to all clients |
| `Mixed` | Multiplayer player-controlled | GEs replicated to owning client only |
| `Minimal` | AI-controlled actors | GEs never replicated to clients |

**Rule of thumb:** Mixed for player pawns, Minimal for AI. Full only for single player.

## Net Execution Policies

Set per GameplayAbility:

| Policy | Where it runs | Use case |
|--------|--------------|----------|
| `LocalPredicted` | Client predicts, server authoritative | Most player abilities |
| `LocalOnly` | Client only, never server | UI abilities, local cosmetics |
| `ServerOnly` | Server only, never client | AI abilities, authoritative-only logic |
| `ServerInitiated` | Server starts, replicates to client | Server-triggered abilities on players |

## What Gets Replicated

| Data | Replicated? | To whom? |
|------|-------------|----------|
| Gameplay Attributes | Yes | All clients |
| Gameplay Tags | Yes | All clients |
| Granted Ability Specs | Yes | Owning client only |
| Active Gameplay Effects | Depends on rep mode | See table above |
| Gameplay Cues | Yes (unreliable) | All clients |
| Ability activation/end | Yes | Owning client |

**Key:** Abilities and Effects are NOT fully replicated to all clients. Only the resulting Attributes and Tags are. This is intentional for bandwidth optimization and cheat prevention.

## Prediction System

GAS supports client-side prediction for responsive gameplay:

**What can be predicted:**
- Ability activation
- Triggered GameplayEvents
- GameplayEffect application (non-instant)
- Gameplay Tag modification (via predicted GEs)
- Gameplay Cue events (local prediction)
- Montages (via AbilityTask)
- Actor movement (via engine movement prediction)

**What CANNOT be predicted:**
- GameplayEffect removal
- Instant GameplayEffect application (damage) -- no rollback

**Prediction flow:**
1. Client activates ability locally, generates prediction key
2. Client applies predicted GEs, plays cues/montages locally
3. Server receives activation RPC, validates, executes authoritatively
4. Server sends back confirmation or rejection
5. On rejection: client rolls back predicted GEs and tags
6. On confirmation: predicted data is reconciled with server data

**Prediction key scope:**
```cpp
// Create a new prediction window within an ability
FScopedPredictionWindow ScopedPrediction(AbilitySystemComponent, true);
// Operations within this scope get their own prediction key
```

**Cooldown prediction caveat:** Cooldowns cannot be truly predicted because the server timestamp differs from client. High-latency players will experience lower effective fire rates. Fortnite uses custom bookkeeping instead of relying on GAS cooldown prediction.

## ASC Placement

**On Pawn:**
- Simplest setup
- ASC destroyed on Pawn death -- all abilities, effects, attributes lost
- Must re-initialize on respawn
- Good for: AI, non-respawning characters, simple games

**On PlayerState:**
- ASC persists across Pawn death/respawn
- Attributes, effects, and granted abilities survive respawn
- Must update AvatarActor on each possession
- Used by Lyra and Fortnite
- Good for: multiplayer games with respawning, persistent progression
- **Caveat:** PlayerState's `NetUpdateFrequency` defaults to low values -- increase it or enable Adaptive Network Update Frequency

**PlayerState ASC + Mixed replication requires:**
- OwnerActor = PlayerState
- AvatarActor = Pawn
- PlayerState's Owner must be the Controller (engine default)

## Multiplayer Setup Checklist

1. Set `AbilitySystemComponent->SetIsReplicated(true)`
2. Set replication mode (Mixed for players, Minimal for AI)
3. Call `InitAbilityActorInfo(OwnerActor, AvatarActor)` on both server and client:
   - Server: in `PossessedBy()`
   - Client: in `OnRep_PlayerState()` or `AcknowledgePossession()`
4. Grant abilities on server only (specs auto-replicate to owning client)
5. Apply GEs on server only (or use prediction for client-initiated)
6. Use `LocalPredicted` net execution policy for player abilities
7. Use `ServerOnly` for AI abilities
8. Never put gameplay logic in GameplayCues (unreliable replication)
9. Use `PlayMontageAndWait` AbilityTask for replicated animations
10. For server-owned actor interactions: route through player's locally owned Actor

## Optimization Strategies

From Fortnite/Paragon production experience (see tranek docs Section 7):

**Ability Batching:** Combine activation + target data + end RPCs into one:
```cpp
// Wrap in FScopedServerAbilityRPCBatcher to batch RPCs
FScopedServerAbilityRPCBatcher Batcher(ASC, AbilitySpecHandle);
// All RPCs within this scope are batched into a single call
```

**GameplayCue Batching:** Multiple cues in one RPC when triggered from same GE.

**Attribute Proxy Replication:** Fortnite pattern -- disable direct ASC attribute replication on simulated proxies, use a lightweight proxy struct on the Pawn instead:
```cpp
USTRUCT()
struct FAttributeReplicationProxy
{
    UPROPERTY()
    float Health;
    UPROPERTY()
    float MaxHealth;
    // ... only what simulated proxies need (health bars, etc.)
};
```

**ASC Lazy Loading:** Don't create ASCs on damageable world actors until they first take damage.

**Gameplay Tag Fast Replication:** Enable in Project Settings for optimized tag replication.
