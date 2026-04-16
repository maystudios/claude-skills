# C++ and Blueprint Best Practices -- Detailed Reference

This document covers the C++ vs Blueprint decision framework, communication patterns, the abstract base + Blueprint subclass pattern, and performance guidelines for Blueprint code.

---

## The Core Philosophy

Unreal Engine is designed so that C++ and Blueprints are complementary. C++ handles low-level systems; Blueprints handle high-level behaviors and designer iteration. The professional standard is always a hybrid approach.

**Sources:**
- https://dev.epicgames.com/documentation/en-us/unreal-engine/coding-in-unreal-engine-blueprint-vs-cplusplus
- https://dev.epicgames.com/community/learning/tutorials/qM2K/unreal-engine-comparing-blueprints-and-c-use-cases

---

## Decision Matrix

### Use C++ When:
- Writing core engine systems, base classes, and framework code
- Performance-critical logic (physics, AI decision-making, large loops, complex math)
- Networking: custom serialization, replication graphs, fast array replication, virtual overrides like `IsNetRelevantFor()`
- Editor tools, standalone utilities, external library integration, custom rendering
- Code needs source control diffing and code review
- Compile-time type safety matters

### Use Blueprints When:
- Implementing gameplay logic, level scripting, event-driven behaviors
- Designer-facing configuration (tuning values, asset references, visual setup)
- Rapid prototyping and iteration
- VFX triggers, audio events, cosmetic one-off behaviors
- UI widget layout (UMG visual designers work in Blueprint)
- Fast iteration speed matters more than raw performance

### The Gray Zone:
- **Blueprint-heavy gameplay logic**: Start in Blueprint, move to C++ when it becomes a bottleneck or too complex
- **Prototyping**: Blueprint first, then migrate validated systems to C++
- **Simple AI**: Blueprint for simple behaviors, C++ for complex AI systems

---

## The Abstract C++ Base + Blueprint Subclass Pattern

This is the gold standard pattern used throughout professional UE5 development.

### Structure:
```
UCLASS(Abstract)
class MYGAME_API AMyBaseClass : public AActor
{
    GENERATED_BODY()

public:
    // Properties exposed to Blueprint subclasses for configuration
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Config")
    float MaxHealth = 100.f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Config")
    TSoftObjectPtr<UStaticMesh> MeshAsset;

protected:
    // Blueprint MUST implement (no C++ body)
    UFUNCTION(BlueprintImplementableEvent, Category = "Events")
    void OnDamageReceived(float Damage, AActor* Instigator);

    // Blueprint CAN override (has C++ default via _Implementation)
    UFUNCTION(BlueprintNativeEvent, Category = "Events")
    void OnDeath();
    virtual void OnDeath_Implementation();

    // Internal C++ logic not exposed to Blueprint
    void ProcessDamageInternal(float RawDamage);
};
```

### Rules:
1. Mark C++ base classes as `UCLASS(Abstract)` to prevent direct instantiation
2. Use `BlueprintImplementableEvent` for pure virtual-like functions Blueprint must implement
3. Use `BlueprintNativeEvent` for functions with C++ defaults that Blueprint can optionally override
4. Expose properties with `EditDefaultsOnly` for configuration, `BlueprintReadOnly` for runtime access
5. Use `TSoftObjectPtr<>` / `TSoftClassPtr<>` for optional asset references
6. Create Blueprint subclasses that provide visual/gameplay details

### Blueprint Nativization:
- Removed in UE 5.0. There is no automatic Blueprint → C++ conversion
- Manually convert performance-critical Blueprint logic to C++ when needed
- Community tool "BP2CPP" exists but is not officially supported

---

## Blueprint Communication Patterns

### 1. Blueprint Interfaces (Preferred)

**Best for**: Cross-system communication without coupling.

Eliminate hard references entirely. Both sender and receiver implement the interface without knowing about each other's concrete type.

**Advantages:**
- No casting needed
- No hard references (prevents memory bloat from dependency chains)
- Polymorphic -- any actor implementing the interface responds
- Scales well across many actor types

**When to use**: Default choice for inter-Blueprint communication.

### 2. Event Dispatchers (Delegates)

**Best for**: Observer/Publisher-Subscriber patterns where listeners need to react to events.

Custom events that one Blueprint dispatches and others bind to.

**Advantages:**
- One-to-many communication
- Decoupled logic flow

**Caveats:**
- Binding to an Event Dispatcher requires a hard reference to the dispatching Blueprint
- Always unbind when the listener is destroyed to prevent memory leaks
- Available in C++ as `DECLARE_DYNAMIC_MULTICAST_DELEGATE`

### 3. Direct References / Casting

**Best for**: Communication between objects that are guaranteed to always be loaded together.

**Caveats:**
- Creates hard references that load the entire referenced Blueprint and ALL its dependencies
- Use sparingly -- only when the referenced class is guaranteed to always be loaded anyway
- Audit with Reference Viewer (right-click asset → Reference Viewer) to check dependency chains

### 4. GameplayMessageSubsystem (Modern Alternative)

**Best for**: Decoupled fire-and-forget communication across gameplay systems.

Uses Gameplay Tags as channels. No references needed. See modern-systems.md for details.

### Communication Priority Order:
1. Blueprint Interfaces (no hard references)
2. GameplayMessageSubsystem (tag-based, fully decoupled)
3. Event Dispatchers (one-to-many events)
4. Direct References (last resort, when coupling is acceptable)

---

## Avoiding Hard References

Hard references are the primary cause of memory bloat and long load times in UE projects.

### The Problem:
When Blueprint A has a hard reference to Blueprint B, loading A forces loading B AND everything B references. This cascades through the entire reference chain.

### Solutions:

**Soft References:**
```cpp
// C++ - loads on demand, not at package load time
UPROPERTY(EditDefaultsOnly)
TSoftObjectPtr<UStaticMesh> MeshAsset;

UPROPERTY(EditDefaultsOnly)
TSoftClassPtr<AActor> EnemyClass;
```

**Blueprint Interfaces:**
Replace casting with interface calls. Instead of:
```
Cast to BP_Enemy → Call TakeDamage()
```
Use:
```
Does Implement Interface: BPI_Damageable → Call TakeDamage (Message)
```

**Audit Tools:**
- Reference Viewer: Right-click any asset → "Reference Viewer"
- Size Map: Visualize memory footprint in a treemap
- Asset Audit: Right-click → "Audit Assets..." for size and frequency analysis

---

## Performance Best Practices for Blueprints

### 1. Eliminate Event Tick

Migrating from Event Tick to event-driven patterns yields 20-30% performance improvement.

**Instead of tick-based polling:**
```
Event Tick → Check Distance → If Close Enough → Do Thing
```

**Use events:**
```
Overlap Event → Do Thing
Timer (SetTimerByFunction, 0.5s) → Check Distance → Do Thing
Gameplay Event / Delegate → React
```

### 2. Disable Tick on Components and Actors

```cpp
// In constructor
PrimaryActorTick.bCanEverTick = false;

// Or at runtime
SetActorTickEnabled(false);
SetComponentTickEnabled(false);

// For periodic checks, use timers instead
GetWorldTimerManager().SetTimer(TimerHandle, this, &AMyActor::PeriodicCheck, 0.5f, true);
```

### 3. Cache References

Bad (every frame):
```
Get All Actors Of Class → Filter → Use
```

Good (once):
```
BeginPlay → Get All Actors Of Class → Store in variable
Event Tick → Use cached variable
```

Best (no tick):
```
BeginPlay → Register with Manager → Manager dispatches events
```

### 4. Minimize Blueprint Node Count in Hot Paths

- Collapse repeated patterns into Blueprint Functions or Macros
- Use Blueprint Function Libraries for shared utility functions
- Move complex math or large loops to C++ and expose via `BlueprintCallable`
- Keep individual Blueprint graphs small and focused -- avoid "god Blueprints"

### 5. Avoid Unnecessary Construction Script Work

- Construction Scripts run in the editor on every property change
- Heavy construction scripts slow down editor performance
- Use `OnConstruction()` in C++ for better control
- Avoid spawning actors or heavy operations in construction scripts

---

## UPROPERTY Specifier Quick Reference

| Specifier | Use Case |
|-----------|----------|
| `EditDefaultsOnly` | Editable in Blueprint defaults, not per-instance |
| `EditInstanceOnly` | Editable per-instance in level, not in defaults |
| `EditAnywhere` | Editable in both defaults and instances |
| `BlueprintReadOnly` | Readable in Blueprint graphs but not settable |
| `BlueprintReadWrite` | Readable and settable in Blueprint graphs |
| `VisibleAnywhere` | Shows in details panel but not editable |
| `Transient` | Not saved, not replicated -- runtime-only |
| `Replicated` | Replicated to clients |
| `ReplicatedUsing` | Replicated with a notification function |
| `meta=(AllowPrivateAccess)` | Allows Blueprint access to private C++ members |

### Combination patterns:
- `UPROPERTY(EditDefaultsOnly, BlueprintReadOnly)` -- Designer configures, Blueprint reads
- `UPROPERTY(VisibleAnywhere, BlueprintReadOnly)` -- Debug display, no editing
- `UPROPERTY(EditAnywhere, BlueprintReadWrite)` -- Full access (use sparingly)
- `UPROPERTY(Replicated, BlueprintReadOnly)` -- Network replicated, Blueprint reads

---

## UFUNCTION Specifier Quick Reference

| Specifier | Use Case |
|-----------|----------|
| `BlueprintCallable` | Can be called from Blueprint graphs |
| `BlueprintPure` | No side effects, no execution pin needed |
| `BlueprintImplementableEvent` | Blueprint must implement (no C++ body) |
| `BlueprintNativeEvent` | C++ default, Blueprint can override |
| `BlueprintAuthorityOnly` | Only runs on server |
| `Server` | RPC to server (requires `Reliable` or `Unreliable`) |
| `Client` | RPC to owning client |
| `NetMulticast` | RPC to all clients |
| `Reliable` | Guaranteed delivery for RPCs |
| `Unreliable` | Fire-and-forget for RPCs |
| `CallInEditor` | Can be called from editor details panel |
| `Category = "Name"` | Groups function in Blueprint action menu |

---

## TObjectPtr Migration

All `UPROPERTY()` raw `UObject*` pointers in headers should be replaced with `TObjectPtr<T>`:

```cpp
// Old (still works but discouraged)
UPROPERTY()
UStaticMeshComponent* MeshComp;

// New (recommended for all UPROPERTY members in .h files)
UPROPERTY()
TObjectPtr<UStaticMeshComponent> MeshComp;
```

**Rules:**
- Only applies to UPROPERTY members in `.h` files
- `.cpp` code continues using raw pointers
- Required for Incremental Reachability Analysis to work safely
- `TObjectPtr<>` is implicitly convertible to raw pointer -- minimal code change
