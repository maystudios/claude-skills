---
name: unreal-thirdparty
description: >
  Expert guide for integrating third-party C/C++ libraries into Unreal Engine 5.x projects and plugins.
  Covers static linking, dynamic linking (DLL/SO/dylib), Build.cs configuration, ModuleType.External,
  delay loading, runtime dependency staging, wrapping patterns, cross-platform considerations
  (Windows/macOS/Linux), ABI compatibility, RTTI/exceptions, header inclusion with
  THIRD_PARTY_INCLUDES_START/END, and common pitfalls. Use when the user asks about adding
  external libraries, third-party code, linking .lib/.a/.dll/.so/.dylib files, Build.cs
  PublicAdditionalLibraries, PublicDelayLoadDLLs, RuntimeDependencies, ModuleType.External,
  wrapping a C++ library for UE, FPlatformProcess::GetDllHandle, cross-compiling libraries
  for UE on Linux, or troubleshooting linker errors / DLL load failures with third-party code.
---

# Unreal Engine Third-Party Library Integration -- C++ Guide

## Official Documentation (always consult for latest details)

| Source | URL |
|--------|-----|
| **Epic: Integrating Third-Party Libraries** | https://dev.epicgames.com/documentation/unreal-engine/integrating-third-party-libraries-into-unreal-engine |
| **Epic Community: Static Lib + Blueprint Tutorial** | https://dev.epicgames.com/community/learning/tutorials/0yJy/unreal-engine-fab-c-creating-your-own-3rd-party-function-library-and-using-it-in-blueprints |
| **UE Forums: Understanding How This Works** | https://forums.unrealengine.com/t/adding-third-party-libraries-to-unreal-understanding-how-this-works/211244 |
| **georgy.dev: Third-Party Integration** | https://georgy.dev/posts/third-party-integration/ |
| **unrealcode.net: Wrapping A Library** | https://www.unrealcode.net/WrappingALibrary/ |
| **Linux ABI / Sysroot Guide** | https://pgaleone.eu/2023/06/18/unreal-engine-third-party-linux-sysroot-dependencies/ |
| **GitHub: Boost/PCL Plugin Example** | https://github.com/ValentinKraft/Boost_PCL_UnrealThirdPartyPlugin |
| **GitHub: UnrealImGui (reference impl)** | https://github.com/IDI-Systems/UnrealImGui |
| **Engine ThirdParty Sources** | `Engine/Source/ThirdParty/` (check here before bundling -- Epic ships libcurl, zlib, libpng, OpenSSL, etc.) |

### Additional Community Resources

| Source | URL |
|--------|-----|
| **UE Community Wiki: Custom ThirdParty from Scratch** | https://unrealcommunity.wiki/adding-custom-third-party-library-to-plugin-from-scratch-867b28 |
| **Yulong He: DLL Plugin + Packaging (Medium)** | https://yulonghe.medium.com/ue5-how-to-create-a-plugin-that-works-with-dlls-packaging-and-external-files-11f8ff9d7491 |
| **Marieke van Neutigem: Updating Plugin for UE5** | https://mariekevanneutigem.nl/blog/pV20/updating-a-plugin-with-third-party-library-for-ue5 |
| **Adam Rehn: Cross-Platform + Conan** | https://adamrehn.com/articles/cross-platform-library-integration-in-unreal-engine-4/ |
| **Parallelcube: Mobile/Desktop ThirdParty** | https://www.parallelcube.com/2018/03/01/using-thirdparty-libraries-in-our-ue4-mobile-project/ |
| **AGX Dynamics: Barrier Module Pattern** | https://us.download.algoryx.se/AGXUnreal/documentation/current/agx-api-access.html |
| **GitHub: UE4CMake (CMake integration)** | https://github.com/caseymcc/UE4CMake |
| **GitHub: CMakeUnreal** | https://github.com/kaustubh138/CMakeUnreal |
| **GitHub: UnrealMacroNuke** | https://github.com/hiili/UnrealMacroNuke |
| **GitHub: UnrealNlohmannJson** | https://github.com/dclipca/UnrealNlohmannJson |
| **GitHub: shadowmint/ue4-static-plugin** | https://github.com/shadowmint/ue4-static-plugin |
| **GitHub: iFunFactory Funapi (multi-platform)** | https://github.com/iFunFactory/engine-plugin-ue4 |
| **Satisfactory Modding: ThirdParty** | https://docs.ficsit.app/satisfactory-modding/latest/Development/Cpp/thirdparty.html |
| **slowburn.dev: UE Upgrades (Build.cs changes)** | https://slowburn.dev/dataconfig/Advanced/UEUpgrades.html |
| **alain.xyz: Working with 3rd Party Libraries** | https://alain.xyz/blog/ue4-working-with-3rd-party-libraries |
| **dawnarc.com: Build.cs Notes** | https://dawnarc.com/2019/01/ue4build.cs-notes/ |
| **ikrima.dev: Build File Demystified** | https://ikrima.dev/ue4guide/archived_content/unreal-engine-4-build-file-demystified-dmitry-yanovsky/ |
| **ikrima.dev: Linking External DLLs** | https://ikrima.dev/ue4guide/build-guide/plugins-modules/linking-external-dlls-or-libraries/ |
| **gg-labs: Linking DLLs** | https://unreal.gg-labs.com/wiki-archives/devops/linking-dlls |
| **conan-ue4cli docs** | https://docs.adamrehn.com/conan-ue4cli/read-these-first/introduction-to-conan-ue4cli |

## Plugin Template

UE ships a **Third Party Library** plugin template. In the editor: **Plugins > New Plugin > Third Party Library** (scroll to bottom). This generates the scaffolding for a DLL-based integration. For static libraries, the two-line approach in Build.cs is simpler.

## Core Architecture

See [references/build-system.md](references/build-system.md) for the full Build.cs reference with all properties and path variables.

**Integration flow:**
```
Third-Party Source (or prebuilt binaries)
  |
  v
[Optional: Recompile with UE toolchain for ABI compat]
  |
  v
Place headers + libs in Plugin/Source/ThirdParty/
  |
  v
Create External Module (.Build.cs with ModuleType.External)
  |-- PublicIncludePaths        -> header directories
  |-- PublicAdditionalLibraries -> .lib / .a files
  |-- PublicDelayLoadDLLs       -> DLL names (Windows delay-load)
  |-- RuntimeDependencies       -> .dll / .so / .dylib staging
  |-- PublicDefinitions         -> preprocessor macros
  v
Consumer Module depends on External Module
  |-- PublicDependencyModuleNames.Add("MyThirdPartyLib")
  |-- #include with THIRD_PARTY_INCLUDES_START/END
  v
Use library API in UE C++ code
```

**Recommended directory layout:**
```
MyPlugin/
  MyPlugin.uplugin
  Source/
    MyPlugin/                        # Runtime module (your code)
      MyPlugin.Build.cs
      Private/
      Public/
    ThirdParty/
      MyLibrary/                     # External module (no source)
        MyLibrary.Build.cs           # Type = ModuleType.External
        include/                     # Library headers
        lib/
          Win64/  *.lib
          Linux/  *.a or *.so
          Mac/    *.a or *.dylib
  Binaries/
    ThirdParty/MyLibrary/Win64/      # DLLs (if dynamic linking)
```

## Four Integration Approaches

See [references/linking-patterns.md](references/linking-patterns.md) for detailed code examples of each approach.

| Approach | When to Use | Build.cs Properties |
|----------|-------------|---------------------|
| **Static library** | Simplest; single executable; no DLL distribution | `PublicAdditionalLibraries` |
| **Dynamic + import lib** | DLL with compile-time symbol resolution | `PublicAdditionalLibraries` + `PublicDelayLoadDLLs` + `RuntimeDependencies` |
| **Dynamic, no import lib** | Runtime function pointer lookup via `GetDllExport` | `RuntimeDependencies` only |
| **Multi-platform static** | Cross-platform plugin with per-platform libs | `PublicAdditionalLibraries` with `Target.Platform` switch |

## Library File Types

| Platform | Static | Dynamic | Import Lib | Prefix |
|----------|--------|---------|------------|--------|
| Windows | `.lib` | `.dll` | `.lib` | none |
| Linux / Android | `.a` | `.so` | n/a | `lib` |
| macOS / iOS | `.a` | `.dylib` | n/a | `lib` |

## Build.cs Quick Reference

| Property | Purpose |
|----------|---------|
| `Type = ModuleType.External` | Module wraps prebuilt libs, no UE source compilation |
| `PublicIncludePaths` | Header search directories |
| `PublicSystemIncludePaths` | Same but suppresses warnings from these headers |
| `PublicAdditionalLibraries` | Static / import library file paths |
| `PublicDelayLoadDLLs` | DLL filenames for Windows delay-loading |
| `RuntimeDependencies` | Files to stage alongside executable for packaging |
| `PublicDefinitions` | Preprocessor defines (`"WITH_MYLIB=1"`) |
| `PublicFrameworks` | macOS frameworks |
| `bUseRTTI` | Enable RTTI (required by Boost, some C++ libs) |
| `bEnableExceptions` | Enable C++ exceptions (required by many libs) |
| `bForceEnableRTTI` | Force RTTI engine-wide (in TargetRules) |

## Platform-Specific Considerations

See [references/platform-specifics.md](references/platform-specifics.md) for Windows DLL loading, macOS @rpath/dylib, and Linux ABI/sysroot details.

**Key rules:**
- **Windows:** DLLs found by name only (no path in import table). Use `FPlatformProcess::GetDllHandle()` or delay-loading. UE searches Engine/Project/Plugin `Binaries/Win64/` directories.
- **macOS:** Dylibs use `@rpath` install names. Set with `install_name_tool -id @rpath/libfoo.dylib`. UBT auto-adds RPATH entries.
- **Linux:** Must recompile C++ libs with UE's Clang + `libc++` (not system `libstdc++`). C libs (stable ABI) don't need recompilation. Use UE's CMake toolchain file.

## Common Patterns & Pitfalls

See [references/patterns-and-pitfalls.md](references/patterns-and-pitfalls.md) for implementation recipes, critical pitfalls, and troubleshooting.

**Critical pitfalls:**
- **UE's `check` macro** collides with third-party code using `check` as an identifier -- `#undef check` or wrap includes
- **Compile with `/MD`** (Multi-threaded DLL) to match UE's runtime -- mismatched CRT causes linker errors
- **RTTI + Exceptions off by default** -- Boost, PCL, and many C++ libs require `bUseRTTI = true` and `bEnableExceptions = true` in BOTH the External module AND every consuming module
- **Release libs only** -- UE uses Release CRT; Debug-built libs cause `_ITERATOR_DEBUG_LEVEL` mismatch and access violations
- **VS project settings are ignored** -- only `.Build.cs` matters; Visual Studio properties have zero effect on UBT
- **`Binaries/ThirdParty/` is NOT regenerated** -- if deleted, the template's DLLs are gone; cannot be rebuilt by UBT
- **Linux ABI mismatch** -- C++ libs compiled with `libstdc++` produce different symbol mangling than UE's `libc++`

## UE Version-Specific Build.cs Changes

See [references/build-system.md](references/build-system.md) for the complete version-by-version changelog.

**Key breaking changes affecting third-party integration:**
- **UE 5.0:** `FVector` changed to 3 doubles; `TObjectPtr` replaces raw UObject pointers
- **UE 5.2:** `bEnforceIWYU` (bool) changed to `IWYUSupport` (enum)
- **UE 5.3:** `BuildSettingsVersion.V4` defaults to C++20; `TRemoveConst` deprecated for `std::remove_const`
- **UE 5.4:** Default MSVC warning level changed to `/W4`; `FText` internals changed from `TSharedRef` to `TRefCountPtr`
- **UE 5.5:** New `Engine/Build/BatchFiles/RunUBT` scripts replace direct UBT invocation; `PER_MODULE_BOILERPLATE` no longer required; `StructUtils` plugin deprecated (moved to engine)
- **UE 5.6:** `FString::Appendf` enforces `static constexpr` format strings; `GMalloc` access deprecated
- **UE 5.7:** `FindObject` deprecates `bExactClass` in favor of `EFindObjectFlags`

## Advanced Patterns

### Barrier Modules (isolating incompatible compiler settings)

When a third-party library requires `bUseRTTI = true` and `bEnableExceptions = true` but you want to minimize the blast radius, create a **barrier module** that isolates the library behind a clean interface:

```
Plugin/
  Source/
    ThirdParty/MyLib/          # ModuleType.External (headers + libs)
    MyLibBarrier/              # Barrier module (bUseRTTI=true, bEnableExceptions=true)
      Public/  -> clean types only, no third-party headers, no UObject.h
      Private/ -> wraps third-party includes with BeginIncludes/EndIncludes
    MyPlugin/                  # Main module, depends on MyLibBarrier (NOT on MyLib directly)
```

Public headers of barrier modules must NOT include third-party headers or trigger UObject.h inclusion. All third-party types are passed as opaque barrier types. See the AGX Dynamics documentation for a production example.

### CMake Integration via UE4CMake

The UE4CMake plugin provides `CMakeTarget.add()` in Build.cs to build CMake libraries as part of UBT:

```csharp
CMakeTarget.add(Target, this, "TargetName",
    Path.Combine(ModuleDirectory, "../Libs/Source"),
    "-DCUSTOM_OPTION=ON", false);
```

It automatically populates `PublicIncludePaths` and `PublicAdditionalLibraries` from CMake output, registers source files in `ExternalDependencies` for change detection, and handles struct packing via `PRAGMA_PUSH_PLATFORM_DEFAULT_PACKING` / `PRAGMA_POP_PLATFORM_DEFAULT_PACKING`.

### UnrealMacroNuke (comprehensive macro decontamination)

For libraries that conflict with many UE macros beyond just `check`, UnrealMacroNuke generates paired headers that undefine and redefine all conflicting macros:

```cpp
#pragma warning(push)
#pragma warning(disable: <codes>)
#include "UndefineMacros_UE_5.3.h"
#include "third_party/library.hpp"
#include "RedefineMacros_UE_5.3.h"
#pragma warning(pop)
```

### Conan Package Manager Integration

The `conan-ue4cli` package automates third-party library builds against UE's bundled dependencies. Build.cs spawns `conan install` and parses `conanbuildinfo.json` to extract include paths, library paths, and definitions. Critical for solving symbol interposition when both UE and a third-party library depend on different versions of the same library (e.g., zlib, libpng).

### Android APL (Android Packaging Layer)

Android third-party libraries require APL XML files for native library deployment and Java integration:

```csharp
// Build.cs -- Android
AdditionalPropertiesForReceipt.Add("AndroidPlugin",
    Utils.MakePathRelativeTo(
        Path.Combine(ThirdPartyPath, "LIBRARY_APL.xml"),
        Target.RelativeEnginePath));
```

### ExternalDependencies for Change Detection

Register external files that should trigger rebuilds when modified:

```csharp
ExternalDependencies.Add(Path.Combine(ModuleDirectory, "include", "version.h"));
```

This ensures UBT regenerates the makefile if the specified files change, useful for tracking header or library binary updates.

### AddEngineThirdPartyPrivateStaticDependencies

Use engine-bundled libraries without maintaining your own copies:

```csharp
AddEngineThirdPartyPrivateStaticDependencies(Target, "OpenSSL", "libWebSockets", "libcurl", "zlib");
```

This is the preferred way to consume libraries already shipped with the engine.
