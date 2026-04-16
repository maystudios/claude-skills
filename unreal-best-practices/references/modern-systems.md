# Modern UE5 Systems -- Detailed Reference

This document covers every major modern Unreal Engine system, what it replaces, why it is better, when to use it, and key implementation notes. Systems are grouped by domain.

---

## Epic's Strategic Direction

Epic communicates their preferred architecture through actions:

- **Lyra Sample Project**: Uses GAS, Enhanced Input, Game Feature Plugins, CommonUI, Gameplay Tags, GameplayMessageSubsystem, and modular gameplay. Derived from Fortnite's production codebase.
- **Template Evolution**: UE 5.1+ templates use Enhanced Input by default. Lyra serves as the "modern template" showing the full recommended stack.
- **Conference Talks**: Epic consistently presents StateTree, Smart Objects, PCG, and MetaSounds as the future direction at Unreal Fest and GDC.
- **Plugin Maturity Promotions**: Each release promotes systems from Experimental → Beta → Production, signaling readiness.

**The pattern**: Data-driven, tag-based, modular architectures replacing hardcoded, tightly-coupled, monolithic designs.

---

## INPUT

### Enhanced Input System

| Aspect | Details |
|--------|---------|
| **Replaces** | Legacy `BindAction`/`BindAxis`, Action/Axis Mappings in Project Settings |
| **Status** | Production-ready, default since UE 5.1. Legacy deprecated with warnings in 5.2+ |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/enhanced-input-in-unreal-engine |

**Why it is better:**
- Separates "what" (Input Actions) from "how" (Input Mapping Contexts)
- Built-in complex patterns: hold, double-tap, chord, combo -- no custom code needed
- Runtime context switching (add/remove mapping contexts per gameplay state)
- Extensible via custom Modifiers and Triggers
- First-class support for multiple input devices

**Key concepts:**
- **Input Actions (IA_)**: Data Assets defining abstract intentions (IA_Move, IA_Jump). Carry value types (bool, float, Vector2D, Vector3D)
- **Input Mapping Contexts (IMC_)**: Map physical inputs to Actions. Multiple IMCs active simultaneously with priority ordering
- **Modifiers**: Transform values (dead zones, negate, swizzle, scalar). Subclass `UInputModifier` for custom
- **Triggers**: Activation conditions (Pressed, Released, Hold, Tap, Combo). Subclass `UInputTrigger` for custom

**Setup:**
1. Set Default Player Input Class to `EnhancedPlayerInput` in Project Settings
2. Set Default Input Component Class to `EnhancedInputComponent`
3. Register contexts via `UEnhancedInputLocalPlayerSubsystem`

**Lyra pattern**: Input Actions mapped to Gameplay Abilities via Gameplay Tags (not direct function calls). See `ULyraInputConfig`.

---

## GAMEPLAY FRAMEWORK

### Gameplay Ability System (GAS)

| Aspect | Details |
|--------|---------|
| **Replaces** | Ad-hoc ability implementations using booleans, timers, custom state machines |
| **Status** | Production-ready. Battle-tested in Paragon, Fortnite. Lyra reference implementation |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-ability-system-for-unreal-engine |
| **Community Docs** | https://github.com/tranek/GASDocumentation |

**When appropriate:**
- RPGs, MOBAs, action games, shooters with ability systems
- Multiplayer games needing client-side prediction
- Games with status effects, buffs/debuffs, attribute-based progression
- Projects where designers need to create abilities without programmer help

**When potentially overkill:**
- Very simple single-player games with no abilities or attributes
- Pure puzzle games, walking simulators, narrative experiences
- Prototypes where setup cost exceeds benefit

**Key architecture decisions:**
- **ASC on PlayerState vs Pawn**: PlayerState preserves attributes across respawns (recommended for multiplayer hero games)
- **Replication Modes**: Full (single-player), Mixed (player-controlled MP), Minimal (AI-controlled MP)

**Setup requirements:**
1. Enable Gameplay Abilities plugin
2. Add modules: `GameplayAbilities`, `GameplayTags`, `GameplayTasks`
3. UE 5.3+: `InitGlobalData()` called automatically. Earlier: call in AssetManager/GameInstance

### Gameplay Tags

| Aspect | Details |
|--------|---------|
| **Replaces** | Hardcoded enums, boolean flags, string comparisons |
| **Status** | Production-ready. Foundation of most modern UE systems |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/using-gameplay-tags-in-unreal-engine |

**Why they are better:**
- Hierarchical: `Damage.Fire` is child of `Damage`; querying `Damage` matches all subtypes
- No hard class dependencies -- decouple systems that would otherwise need casting
- Replicate efficiently via indices (enable Fast Replication in Project Settings)
- Designers can create new tags without programmer intervention
- Eliminate cascade asset loading caused by hard references

**Best practices for hierarchy:**
- Plan tag hierarchy early: `Category.SubCategory.SpecificTag`
- Examples: `Ability.Fire.Fireball`, `State.Debuff.Stunned`, `Damage.DoT.Fire`
- Use `FGameplayTagContainer` (not `TArray<FGameplayTag>`) for helper functions
- Define native tags in C++ using `UE_DEFINE_GAMEPLAY_TAG` / `UE_DECLARE_GAMEPLAY_TAG_EXTERN`
- Use `UE_DEFINE_GAMEPLAY_TAG_STATIC()` for file-scoped tags
- Implement `IGameplayTagAssetInterface` on actors for built-in tag operations

### Game Feature Plugins & Modular Gameplay

| Aspect | Details |
|--------|---------|
| **Replaces** | Monolithic game modules with tightly coupled features |
| **Status** | Production-ready (used in Fortnite and Lyra) |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/game-features-and-modular-gameplay-in-unreal-engine |

**What they do:**
Self-contained plugins that inject components, abilities, input mappings, and content into existing actors at runtime. Enforce unidirectional dependency -- core game is entirely unaware of Game Feature Plugins.

**Key concepts:**
- **UGameFrameworkComponentManager**: Game Instance Subsystem managing runtime component injection
- **GameFeatureActions**: Actions executed on activation (Add Components, Add Cheats, Add Data Registry, custom)
- **States**: Installed → Registered → Loaded → Active

**Directory structure:**
```
/{ProjectName}/Plugins/GameFeatures/{FeatureName}/
```

**Rules:**
- Game Features must NEVER be referenced by the base game
- Add `GameFeatures` to PublicDependencyModuleNames in Build.cs
- Enable "Game Features" and "Modular Gameplay" plugins

### GameplayMessageSubsystem

| Aspect | Details |
|--------|---------|
| **Replaces** | Direct delegate binding, manual reference management, tightly-coupled events |
| **Status** | Production-ready (used in Lyra) |
| **Documentation** | https://unrealcommunity.wiki/gameplaymessagesystem-74b916 |

**How it works:**
- Publish-subscribe messaging using Gameplay Tags as channels
- Broadcasters send USTRUCT messages on tag channels
- Listeners subscribe with typed callbacks
- No direct references needed between sender and receiver
- Messages are NOT network replicated by default (local-client scope)

**Lyra pattern**: Single `FLyraVerbMessage` struct for nearly all messages (Verb tag, Instigator/Target pointers, Magnitude).

---

## AI

### StateTree

| Aspect | Details |
|--------|---------|
| **Replaces/Supplements** | Behavior Trees (not full replacement -- BTs still supported) |
| **Status** | Production-ready since UE 5.1. Significant improvements in 5.5 (utility-based selection) |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/state-tree-in-unreal-engine |

**Advantages over Behavior Trees:**
- Usable for non-AI logic (doors, chests, interactive objects, UI flow, quest systems)
- Full flexibility in state transitions (not limited to tree traversal)
- Data-binding (direct memory access, no blackboard keys)
- Utility-based state selection (UE 5.5+)
- Works on any actor (no AI controller required)

**Key concepts**: States, Tasks, Transitions, Conditions, Evaluators, Schemas (AI, Actor, standalone).

**Known gotchas**: Linked asset subtrees may have state change detection issues; global tasks in subtrees with parameters can crash; GameplayTag updates may use stale cached values.

### Smart Objects

| Aspect | Details |
|--------|---------|
| **Replaces** | Manual scripting of AI interaction points, custom interaction volumes |
| **Status** | Production-ready since UE 5.1 |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/smart-objects-in-unreal-engine---overview |

Reservation-based system for defining interactive world points. Characters claim and use Smart Object slots. Uses Mass Entity (ECS) internally. Integrates with StateTree for defining behavior at each slot.

**When to use**: Open-world ambient AI, environmental interactions, background NPC behaviors.

### Mass Entity / Mass AI

| Aspect | Details |
|--------|---------|
| **Replaces** | Actor-based simulation for massive entity counts |
| **Status** | Available since UE 5.0, still evolving. Production-ready for crowds/traffic |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/mass-entity-in-unreal-engine |

Archetype-based ECS framework for large-scale simulation (Matrix Awakens demo). Handles ~100,000 entities with LOD-based ticking.

**When to use**: Crowds, traffic, batch processing with consistent update patterns.
**When NOT to use**: One-off gameplay, complex hierarchies, Blueprint-heavy projects.

---

## AUDIO

### MetaSounds

| Aspect | Details |
|--------|---------|
| **Replaces** | SoundCue (which is an execution graph for arranging pre-recorded audio) |
| **Status** | Production-ready (core). MetaSound Builder API is Experimental |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-in-unreal-engine |

Full DSP pipeline with sample-accurate timing. Generates audio in real-time via oscillators, filters, granular synthesis. Pushes computation onto audio thread.

**Asset types:**
- **MetaSound Source**: Standalone audio generators
- **MetaSound Patch**: Reusable encapsulated modules
- **MetaSound Preset**: Read-only graph with overridable inputs

**When to use**: All new audio work in UE5. SoundCue only for legacy compatibility. Excels at procedural/adaptive audio, engine sounds, environmental ambience.

### Audio Modulation Plugin

| Aspect | Details |
|--------|---------|
| **Replaces** | Static audio parameter configuration |
| **Status** | Production-ready |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-modulation-overview-in-unreal-engine |

Dynamic control over audio parameters (volume, pitch, frequency) via Control Buses and Control Bus Mixes. Must be enabled in Plugin settings.

**When to use**: Dynamic audio mixing -- combat intensity, underwater effects, vehicle RPM sounds, accessibility controls.

---

## RENDERING & VISUAL

### Niagara

| Aspect | Details |
|--------|---------|
| **Replaces** | Cascade (deprecated since UE 5.0, creation moved to "Miscellaneous" in 5.1) |
| **Status** | Production-ready. Cascade receives no updates |
| **Documentation** | https://dev.epicgames.com/community/learning/knowledge-base/dPm4/unreal-engine-faq-niagara-visual-effects |
| **Converter** | https://dev.epicgames.com/documentation/en-us/unreal-engine/cascade-to-niagara-effects-converter-plugin-for-unreal-engine |

Node-based, data-driven particle system with GPU compute, millions of particles, Simulation Stages, custom data interfaces, mesh rendering, fluid simulation.

**Rule**: All new VFX work must use Niagara. No reason to start new effects in Cascade.

### Nanite (Virtualized Geometry)

| Aspect | Details |
|--------|---------|
| **Replaces** | Manual LOD pipelines, retopology workflows |
| **Status** | Production-ready since UE 5.0. Skinned mesh support in 5.5. Nanite Foliage Experimental in 5.7 |

Automatic geometry streaming, LOD generation, and efficient rasterization. Import film-quality assets directly.

**Limitations**: No fully transparent materials (masked/opacity mask works since 5.3). Dense foliage can incur material bin overhead.

### Lumen (GI & Reflections)

| Aspect | Details |
|--------|---------|
| **Replaces** | Baked lightmaps (Lightmass), screen-space reflections as primary method |
| **Status** | Production-ready since UE 5.0. SWRT detail traces deprecated in 5.6 -- prefer HWRT |

Real-time global illumination and reflections reacting dynamically to movement, time-of-day, and material changes.

### Control Rig

| Aspect | Details |
|--------|---------|
| **Replaces** | External DCC-only rigging (Maya, Blender rigs for runtime adjustments) |
| **Status** | Core production-ready. Modular Control Rig and Control Rig Physics are Experimental |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/control-rig-in-unreal-engine |

Runtime rigging and procedural animation toolkit. IK/FK chains, constraints, space switching, retargeting.

**When to use**: In-engine rigging, procedural animation (turret tracking, IK locomotion), animation retargeting without external DCC.

---

## WORLD BUILDING

### World Partition

| Aspect | Details |
|--------|---------|
| **Replaces** | Level Streaming and World Composition (both deprecated) |
| **Status** | Production-ready, default for all new UE5 levels |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition-in-unreal-engine |

**Key concepts:**
- **One-File-Per-Actor (OFPA)**: Dramatically reduces merge conflicts, enables concurrent editing
- **Streaming Grid**: Automatic proximity-based loading
- **Data Layers**: Runtime-controlled actor group loading/visibility
- **HLOD**: Automatic simplified representations for distant content

**When to use**: Always for new projects (default). Essential for open-world. Beneficial even for smaller games due to collaboration benefits.

### PCG Framework (Procedural Content Generation)

| Aspect | Details |
|--------|---------|
| **Replaces** | Ad-hoc Blueprint scripting, manual foliage painting |
| **Status** | Production-ready since UE 5.7. GPU generation 2x faster than 5.5 |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-overview |

Node-graph-based procedural world building. Spawning, filtering, transforming, distributing assets. Supports in-editor and runtime generation. Integrates with World Partition.

**When to use**: Open-world environment population, biome generation, foliage distribution, prop scattering, procedural layouts.

---

## UI

### CommonUI

| Aspect | Details |
|--------|---------|
| **Enhances** | Raw UMG (builds on top, not a replacement) |
| **Status** | Beta (used in Fortnite -- production-proven despite label) |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-advanced-multiplatform-user-interfaces-with-common-ui-for-unreal-engine |

Cross-platform UI framework: automatic input device detection, dynamic button icon switching, focus management, activatable widget stack, centralized style management.

**When to use**: Any game shipping on multiple platforms (console + PC + mobile). Essential for gamepad UI navigation and platform-specific button prompts. For PC-only mouse-driven UIs, raw UMG may suffice.

---

## ANIMATION

### Motion Matching (PoseSearch)

| Aspect | Details |
|--------|---------|
| **Replaces** | Complex animation state machines and blend trees for locomotion |
| **Status** | Experimental |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-matching-in-unreal-engine |

Selects animation poses from a database at runtime to match character trajectory and state. Uses `CharacterTrajectoryComponent`.

### Motion Warping

| Aspect | Details |
|--------|---------|
| **Replaces** | Manual animation variant creation for different obstacle sizes |
| **Status** | Production-usable |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-warping-in-unreal-engine |

Dynamically adjusts root motion so characters reach specific world positions (vaulting, landing, takedowns).

### Chooser Tables

| Aspect | Details |
|--------|---------|
| **Replaces** | Hardcoded switch/if chains for asset selection |
| **Status** | Beta since UE 5.4 |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/dynamic-asset-selection-in-unreal-engine |

Data-driven asset selection based on gameplay context (tags, floats, booleans, enums). Designers configure without touching code.

---

## NETWORKING

### Iris Replication System

| Aspect | Details |
|--------|---------|
| **Replaces** | Default replication for large-scale multiplayer |
| **Status** | Beta since UE 5.7 (31% higher framerate, 24% lower frame time at 100 players) |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/introduction-to-iris-in-unreal-engine |

Opt-in system for larger worlds and higher player counts. Ported from Fortnite Battle Royale.

**When to use**: Battle royale, large-scale PvP, MMO-like experiences. Not needed for small multiplayer games.

---

## MOVEMENT

### Mover 2.0

| Aspect | Details |
|--------|---------|
| **Replaces** | CharacterMovementComponent (eventual successor) |
| **Status** | Experimental since UE 5.4. NOT recommended for production |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/mover-features-and-concepts-in-unreal-engine |

Modular, extensible movement with rollback networking. Works with any Actor (not just ACharacter).

**Recommendation**: Stick with CharacterMovementComponent for production. Monitor Mover's progression.

---

## ASSET LOADING

### Zen Loader

| Aspect | Details |
|--------|---------|
| **Replaces** | Legacy `.pak`-only asset loading |
| **Status** | Production-ready since UE 5.5 |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/zen-loader-in-unreal-engine |

Optimized loading using `.utoc` + `.ucas` + `.pak` files. Default for cooked builds in 5.5+ -- no special opt-in needed.

### Virtual Assets

| Aspect | Details |
|--------|---------|
| **Replaces** | Full asset syncing in source control |
| **Status** | Beta/Experimental. Do NOT ship with it |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-virtual-assets-in-unreal-engine |

Decouples metadata from bulk payload for faster source control syncs. For large teams only.

---

## DIALOGUE

### CommonConversation (CommonConversationRuntime)

| Aspect | Details |
|--------|---------|
| **Status** | Experimental and NOT officially supported |
| **Documentation** | https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/CommonConversationRuntime |

Graph-based conversation trees. Significant limitations: requires C++, designed for multiplayer (single-player needs workarounds), not guaranteed to work across engine versions.

**Recommendation**: For production dialogue systems, use third-party solutions or custom implementations. Only use for prototyping if comfortable with C++ and the experimental risk.
