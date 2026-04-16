# Performance and Debugging -- Detailed Reference

This document covers tick optimization, object pooling, garbage collection, networking performance, profiling with Unreal Insights, and debugging tools.

---

## Tick Optimization

**Primary rule: Avoid Event Tick whenever possible.** Migrating from tick-based to event-driven patterns yields 20-30% performance improvement.

### Alternatives to Tick

| Instead of... | Use... |
|---------------|--------|
| Tick + distance check | Overlap events (sphere collision) |
| Tick + periodic check | `FTimerManager::SetTimer()` |
| Tick + condition polling | Event Dispatchers / Delegates |
| Tick + waiting for state | Gameplay Events / Tags |
| Tick + animation update | Animation Notifies |
| Tick + UI update | Delegate binding (OnValueChanged) |

### Disabling Tick

```cpp
// In constructor -- best approach
AMyActor::AMyActor()
{
    PrimaryActorTick.bCanEverTick = false;
    // Also disable on components:
    // MyComponent->PrimaryComponentTick.bCanEverTick = false;
}

// At runtime -- for actors that sometimes need tick
SetActorTickEnabled(false);
SetComponentTickEnabled(false);
```

### Timer-Based Periodic Checks

```cpp
// Instead of checking every frame, check every 0.5 seconds
FTimerHandle TimerHandle;
GetWorldTimerManager().SetTimer(
    TimerHandle,
    this,
    &AMyActor::PeriodicCheck,
    0.5f,   // Interval in seconds
    true    // Looping
);

// Or with a lambda
GetWorldTimerManager().SetTimer(TimerHandle, FTimerDelegate::CreateLambda([this]()
{
    // Periodic logic here
}), 0.5f, true);
```

### Tick Interval (when tick is unavoidable)

```cpp
// Reduce tick frequency for non-frame-critical updates
PrimaryActorTick.TickInterval = 0.1f;  // 10 times per second instead of every frame
```

### Tick Groups (execution ordering)

```
TG_PrePhysics → TG_DuringPhysics → TG_PostPhysics → TG_PostUpdateWork
```

Use `SetTickGroup()` to control when an actor ticks relative to physics.

---

## Object Pooling

**Critical for**: Projectiles, particles, decals, hit effects, pickups -- anything frequently spawned/destroyed.

### Pattern: World Subsystem Pool

```cpp
UCLASS()
class UProjectilePool : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    AProjectile* Acquire();
    void Release(AProjectile* Projectile);

private:
    UPROPERTY()
    TArray<TObjectPtr<AProjectile>> AvailablePool;

    UPROPERTY()
    TArray<TObjectPtr<AProjectile>> ActivePool;

    int32 InitialPoolSize = 50;
};
```

### Poolable Actor Interface

```cpp
UINTERFACE()
class UPoolable : public UInterface { GENERATED_BODY() };

class IPoolable
{
    GENERATED_BODY()
public:
    // Called when taken from pool
    virtual void OnPoolAcquire() = 0;
    // Called when returned to pool
    virtual void OnPoolRelease() = 0;
};
```

### Pool implementation notes:
- Pre-spawn estimated maximum at level load
- Allow automatic expansion if pool exhausted (log a warning)
- On release: disable tick, disable collision, hide, teleport to origin
- On acquire: enable tick, enable collision, show, set position/rotation
- Use delegates to broadcast pool events for monitoring
- Implement as `UWorldSubsystem` for automatic per-world lifecycle

---

## Garbage Collection

**Source**: https://forums.unrealengine.com/t/community-tutorial-unreal-engine-performance-deep-dive-memory-object-pooling-and-tick-optimization/2701185

### Key facts:
- Default purge interval: every 60 seconds (`gc.TimeBetweenPurgingPendingKillObjects`)
- `UPROPERTY()` marking keeps objects from being GC'd
- Circular references prevent GC -- use `TWeakObjectPtr<>` to break cycles
- `ForceGarbageCollection()` -- avoid except in controlled situations (level transitions)

### Best practices:
- Minimize `NewObject<>` calls in hot paths -- prefer pooling
- Remove references (set to `nullptr`) when no longer needed
- Cluster objects created/destroyed together for batch GC efficiency
- Use `TWeakObjectPtr<>` for references that should not prevent GC
- Profile GC with Unreal Insights `gc` trace channel

### Console commands:
```
gc.TimeBetweenPurgingPendingKillObjects 30    // Purge every 30s instead of 60s
obj list                                      // List all UObjects (leak detection)
obj gc                                        // Force GC
MemReport -full                               // Detailed memory report
```

---

## Network Replication Performance

**Source**: https://wizardcell.com/unreal/multiplayer-tips-and-tricks/

### Replication Conditions

```cpp
UPROPERTY(Replicated)
float Health;  // Replicates to everyone (expensive)

// Better: use conditions
void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    DOREPLIFETIME_CONDITION(AMyActor, Health, COND_OwnerOnly);    // Only to owner
    DOREPLIFETIME_CONDITION(AMyActor, TeamId, COND_InitialOnly);  // Only once
    DOREPLIFETIME_CONDITION(AMyActor, Cosmetic, COND_SkipOwner);  // Everyone except owner
}
```

### RPC Best Practices

| Pattern | Use |
|---------|-----|
| Replicated Properties | Stateful data (health, position, score) |
| RPCs | Transient events (play sound, spawn VFX) |
| `Server_` prefix | Client → Server calls |
| `Client_` prefix | Server → Owning Client calls |
| `Multicast_` prefix | Server → All Clients calls |
| `Reliable` | Guaranteed delivery (use sparingly -- can overflow) |
| `Unreliable` | Fire-and-forget (VFX, cosmetic events) |

### Critical rules:
- Never call RPCs in `BeginPlay()` -- use `ReadyForReplication()` (UE 5.1+) or possession events
- Pack related properties into structs with custom `NetSerialize()` for atomic replication
- Validate ALL client-supplied data on the server
- GameMode exists only on the server -- never access on clients
- Reliable RPCs guarantee delivery but overflow if called excessively

### PlayerState NetUpdateFrequency
Default is too low for GAS. Increase it:
```cpp
AMyPlayerState::AMyPlayerState()
{
    NetUpdateFrequency = 100.0f;  // Default is 1.0f -- way too low
}
```

---

## LOD and Culling

### Nanite (automatic for static meshes)
- Automatically handles LOD, geometry streaming, and rasterization
- Import film-quality assets directly -- no manual LOD setup needed
- Skinned mesh support added in UE 5.5 (`r.NaniteAllowSkinnedMesh`)
- Cannot be used on translucent materials (masked works since 5.3)

### HLOD (Hierarchical LOD)
- Reduces draw calls for distant actors
- Automatically generates simplified representations
- UE 5.7: Custom HLODs can be injected

### Distance Culling
```cpp
// Per-actor or per-component
MyComponent->SetCachedMaxDrawDistance(5000.f);  // Stop rendering beyond 50m
```

### For non-Nanite assets:
- Generate LODs using the built-in LOD generator (Mesh Editor)
- Set LOD screen sizes for smooth transitions
- Use Imposter LODs for very distant vegetation

---

## Profiling with Unreal Insights

**Sources:**
- https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-reference-in-unreal-engine-5
- https://tomlooman.com/unreal-engine-profiling-stat-commands/

### Launch with tracing:
```
# Command-line argument
-trace=cpu,gpu,frame,counters

# Or at runtime via console
trace.start
trace.stop
```

Traces save to `Saved/Profiling/`. Open `.utrace` files in standalone `UnrealInsights.exe`.

### Available trace channels:
`cpu`, `gpu`, `frame`, `counters`, `loadtime`, `file`, `net`, `memory`, `gc`, `task`, `rendercommands`

### Region tagging:
```cpp
// Mark named regions in trace
Trace.RegionBegin MyLabel
Trace.RegionEnd MyLabel
```

### Code instrumentation macros:
```cpp
// Cycle counters (low overhead, recommended)
DECLARE_CYCLE_STAT(TEXT("MyFunction"), STAT_MyFunc, STATGROUP_Game);
SCOPE_CYCLE_COUNTER(STAT_MyFunc);

// Custom counters for Insights
TRACE_DECLARE_INT_COUNTER(EnemyCount, TEXT("Game/EnemyCount"));
TRACE_COUNTER_SET(EnemyCount, ActiveEnemies);
TRACE_COUNTER_ADD(EnemyCount, 1);

// Named events (higher overhead ~20%, good for debugging)
SCOPED_NAMED_EVENT(SpawnWave, FColor::Green);

// Bookmarks (mark specific moments)
TRACE_BOOKMARK(TEXT("SpawnWave::%d"), WaveNumber);
```

### Legacy stat profiler (deprecated in 5.5, still functional):
```
stat unit          // Frame time breakdown (Game, Draw, GPU, RHIT)
stat fps           // Simple FPS display
stat game          // Game thread stats
stat scenerendering // Rendering pipeline
stat none          // Hide all stats
stat startfile     // Begin recording stat file
stat stopfile      // Stop recording
```

---

## Console Commands for Debugging

### Performance:
```
stat unit                     // Frame time breakdown
stat fps                      // FPS counter
stat game                     // Game thread breakdown
stat scenerendering           // Rendering pipeline stats
ProfileGPU                    // Single GPU frame cost breakdown
stat namedevents              // Detailed class-level event naming
ShowFlag.DynamicShadows 0     // Toggle rendering features for isolation
```

### Memory:
```
MemReport -full               // Detailed memory report
obj list                      // List all UObjects (leak detection)
obj gc                        // Force garbage collection
stat memory                   // Memory overview
```

### Network:
```
net.DrawDebugText 1           // Show replication debug info
stat net                      // Network stats
stat nettraffic               // Bandwidth per component
```

### AI:
```
ai.debug.show                 // Toggle AI debug visualization
ShowDebug AI                  // Detailed AI state overlay
EnableGDT                     // Enable Gameplay Debugger
```

---

## Additional Debugging Tools

### Reference Viewer
Right-click any asset → "Reference Viewer". Shows full dependency graph. Use to identify:
- Unexpected hard references causing memory bloat
- Circular dependencies
- Assets being loaded unnecessarily

### Size Map
Right-click asset → "Size Map". Treemap visualization of memory footprint. Use to find:
- Oversized textures
- Redundant assets
- Memory-heavy dependency chains

### Visual Logger
Record and replay AI decisions, perception, and gameplay events with 3D visualization.
```cpp
UE_VLOG(this, LogAI, Log, TEXT("Spotted enemy: %s"), *Enemy->GetName());
UE_VLOG_LOCATION(this, LogAI, Log, EnemyLocation, 50.f, FColor::Red, TEXT("Enemy"));
```

### Gameplay Debugger
Runtime overlay showing AI state, perception, EQS results, and navigation. Toggle with `'` key (apostrophe) by default.

### Network Profiler
Built-in tool for analyzing bandwidth consumption per-actor and per-property. Access via Tools → Network Profiler.

---

## Performance Checklist

Before shipping or during optimization passes, verify:

- [ ] No unnecessary Event Tick (use `stat game` to find tick-heavy actors)
- [ ] Object pooling for frequently spawned/destroyed actors
- [ ] Soft references for conditional assets (audit with Reference Viewer)
- [ ] Nanite enabled for eligible static meshes
- [ ] Lumen settings appropriate for target hardware
- [ ] Network replication uses `COND_*` conditions
- [ ] No reliable RPCs in tight loops
- [ ] GC not causing hitches (profile with Unreal Insights `gc` channel)
- [ ] Construction scripts are lightweight
- [ ] LOD/distance culling configured for non-Nanite meshes
- [ ] Blueprint hot paths moved to C++ if bottlenecking
- [ ] Timers used instead of tick for periodic checks
- [ ] Asset bundles configured for selective loading
