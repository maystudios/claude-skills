# Build System Reference -- Third-Party Library Integration

## Table of Contents
- [ModuleType.External](#moduletypeexternal)
- [Build.cs Property Reference](#buildcs-property-reference)
- [Additional Build.cs Compiler Settings](#additional-buildcs-compiler-settings)
- [RuntimeDependencies Path Variables](#runtimedependencies-path-variables)
- [StagedFileType Options](#stagedfiletype-options)
- [Minimal Static Library Setup](#minimal-static-library-setup)
- [Full External Module Template](#full-external-module-template)
- [Multi-Platform External Module](#multi-platform-external-module)
- [Consumer Module Setup](#consumer-module-setup)
- [uplugin Descriptor](#uplugin-descriptor)
- [Debug vs Release Library Selection](#debug-vs-release-library-selection)
- [Bulk Library Loading](#bulk-library-loading)
- [PreBuildSteps for CMake Libraries](#prebuildsteps-for-cmake-libraries)
- [CMakeTarget Integration (UE4CMake)](#cmaketarget-integration-ue4cmake)
- [AddEngineThirdPartyPrivateStaticDependencies](#addenginethirdpartyprivatestaticdependencies)
- [ExternalDependencies](#externaldependencies)
- [UE Version-Specific Build.cs Changes](#ue-version-specific-buildcs-changes)
- [Multi-Platform Real-World Example (Funapi)](#multi-platform-real-world-example-funapi)
- [Regex-Based Library Discovery](#regex-based-library-discovery)

---

## ModuleType.External

Setting `Type = ModuleType.External` tells UnrealBuildTool this module contains **no source code to compile**. It only imports headers, libraries, and definitions for other modules to consume.

```csharp
public class MyLibrary : ModuleRules
{
    public MyLibrary(ReadOnlyTargetRules Target) : base(Target)
    {
        Type = ModuleType.External;
        // ... include paths, libraries, definitions
    }
}
```

The `.Build.cs` file must be placed where UBT can discover it: inside `Engine/Source/`, `Project/Source/`, or `Plugin/Source/` trees.

## Build.cs Property Reference

| Property | Type | Purpose | Example |
|----------|------|---------|---------|
| `Type` | `ModuleType` | Module type | `ModuleType.External` |
| `PublicIncludePaths` | `List<string>` | Header directories added to compiler include path | `PublicIncludePaths.Add(Path.Combine(ModuleDirectory, "include"))` |
| `PublicSystemIncludePaths` | `List<string>` | Same as above but with warnings suppressed | `PublicSystemIncludePaths.Add(...)` |
| `PublicAdditionalLibraries` | `List<string>` | Full paths to `.lib` / `.a` files to link | `PublicAdditionalLibraries.Add(Path.Combine(..., "foo.lib"))` |
| `PublicDelayLoadDLLs` | `List<string>` | DLL filenames (name only, no path) for Windows delay-loading | `PublicDelayLoadDLLs.Add("foo.dll")` |
| `RuntimeDependencies` | `RuntimeDependencyList` | Files to stage alongside executable | See path variables below |
| `PublicDefinitions` | `List<string>` | Preprocessor defines | `PublicDefinitions.Add("WITH_MYLIB=1")` |
| `PublicFrameworks` | `List<string>` | macOS framework names | `PublicFrameworks.Add("CoreVideo")` |
| `bUseRTTI` | `bool` | Enable RTTI for this module | `bUseRTTI = true` |
| `bEnableExceptions` | `bool` | Enable C++ exceptions | `bEnableExceptions = true` |
| `PublicSystemLibraries` | `List<string>` | System library names (found via system paths) | `PublicSystemLibraries.Add("ws2_32")` |
| `PublicSystemLibraryPaths` | `List<string>` | Directories to search for system libraries (renamed from `PublicLibraryPaths` in UE 4.24) | `PublicSystemLibraryPaths.Add(...)` |
| `PublicRuntimeLibraryPaths` | `List<string>` | Runtime search directories for dynamic libs | `PublicRuntimeLibraryPaths.Add(...)` |
| `ExternalDependencies` | `List<string>` | External files that invalidate makefile if modified (relative paths resolved from .Build.cs) | `ExternalDependencies.Add("include/version.h")` |
| `CppStandard` | `CppStandardVersion` | C++ standard version | `CppStandard = CppStandardVersion.Cpp17` |
| `bUsePrecompiled` | `bool` | Use precompiled binaries; true for installed assemblies | `bUsePrecompiled = true` |
| `bPrecompile` | `bool` | Whether module should be precompiled (defaults from target) | `bPrecompile = false` |
| `bUseUnity` | `bool` | Enable unity (combined) builds; disable for better error localization | `bUseUnity = false` |
| `OptimizeCode` | `CodeOptimization` | Optimization level | `OptimizeCode = CodeOptimization.InNonDebugBuilds` |
| `bUseInlining` | `bool` | Enable function inlining | `bUseInlining = false` |
| `bAddDefaultIncludePaths` | `bool` | Add default include paths (Source/Classes, Source/Public subfolders) | `bAddDefaultIncludePaths = false` |
| `bLegacyPublicIncludePaths` | `bool` | Include subfolders of Public in include paths (false reduces compile cmdline length) | `bLegacyPublicIncludePaths = false` |
| `PrivatePCHHeaderFile` | `string` | Explicit PCH header file path | `PrivatePCHHeaderFile = "Private/MyPCH.h"` |
| `bEnableUndefinedIdentifierWarnings` | `bool` | Warn on undefined identifiers in `#if` expressions; disable for third-party SDK includes | `bEnableUndefinedIdentifierWarnings = false` |

## Additional Build.cs Compiler Settings

These properties are particularly relevant when consuming third-party libraries that trigger UE's strict compiler warnings:

| Property | Type | Purpose |
|----------|------|---------|
| `ShadowVariableWarningsLevel` | `WarningLevel` | Control shadow variable warnings from third-party code |
| `UnsafeTypeCastWarningLevel` | `WarningLevel` | Control unsafe type cast warnings |
| `bDisableStaticAnalysis` | `bool` | Disable static analysis for modules wrapping noisy third-party code |
| `bForceEnableRTTI` | `bool` | (TargetRules) Force RTTI for entire engine -- use cautiously |
| `IWYUSupport` | `IWYUSupport` enum | Include-What-You-Use support (replaced `bEnforceIWYU` bool in UE 5.2) |

## RuntimeDependencies Path Variables

| Variable | Description |
|----------|-------------|
| `$(EngineDir)` | Engine root directory |
| `$(ProjectDir)` | Directory containing the `.uproject` file |
| `$(ModuleDir)` | Directory containing the `.Build.cs` file |
| `$(PluginDir)` | Directory containing the `.uplugin` file |
| `$(BinaryOutputDir)` | Directory of the compiled binary (DLL for editor, exe for packaged) |
| `$(TargetOutputDir)` | Directory of the executable (including editor builds) |

**Single-argument form** -- stages an existing file from that location:
```csharp
RuntimeDependencies.Add(Path.Combine(PluginDirectory, "Binaries/Win64/Foo.dll"));
```

**Two-argument form** -- copies source to destination at build time:
```csharp
RuntimeDependencies.Add(
    "$(TargetOutputDir)/Foo.dll",                              // destination
    Path.Combine(PluginDirectory, "Source/ThirdParty/Foo.dll") // source
);
```

## StagedFileType Options

When staging non-DLL files via `RuntimeDependencies`:

| Value | Description |
|-------|-------------|
| `StagedFileType.UFS` | Accessed via UE filesystem, may go into PAK file |
| `StagedFileType.NonUFS` | Must remain as loose file on disk |
| `StagedFileType.DebugNonUFS` | Debug file, loose, only staged if debug staging enabled |
| `StagedFileType.SystemNonUFS` | System file, loose, not subject to platform renaming |

```csharp
RuntimeDependencies.Add(Path.Combine(PluginDirectory, "Extras/data.bin"), StagedFileType.NonUFS);
```

## Minimal Static Library Setup

The simplest possible integration -- two lines in Build.cs:

```csharp
using System.IO;
using UnrealBuildTool;

public class MyPlugin : ModuleRules
{
    public MyPlugin(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });

        // Link the static library
        PublicAdditionalLibraries.Add(
            Path.Combine(ModuleDirectory, "..", "ThirdParty", "mylib.lib"));

        // Add headers
        PublicIncludePaths.Add(
            Path.Combine(ModuleDirectory, "..", "ThirdParty", "include"));
    }
}
```

## Full External Module Template

A dedicated wrapper module for complex libraries:

```csharp
using System.IO;
using UnrealBuildTool;

public class MyThirdPartyLibrary : ModuleRules
{
    public MyThirdPartyLibrary(ReadOnlyTargetRules Target) : base(Target)
    {
        Type = ModuleType.External;

        // Preprocessor definitions
        PublicDefinitions.Add("WITH_MYTHIRDPARTYLIBRARY=1");

        // Include paths
        PublicIncludePaths.Add(Path.Combine(ModuleDirectory, "include"));

        if (Target.Platform == UnrealTargetPlatform.Win64)
        {
            // Static / import libraries
            PublicAdditionalLibraries.Add(
                Path.Combine(ModuleDirectory, "lib", "Win64", "mylib.lib"));

            // Delay-load DLLs (if dynamic linking)
            PublicDelayLoadDLLs.Add("mylib.dll");

            // Stage DLL for packaging
            RuntimeDependencies.Add(
                "$(PluginDir)/Binaries/ThirdParty/MyLibrary/Win64/mylib.dll");
        }
        else if (Target.Platform == UnrealTargetPlatform.Linux)
        {
            string LibPath = Path.Combine(ModuleDirectory, "lib", "Linux", "libmylib.so");
            PublicAdditionalLibraries.Add(LibPath);
            RuntimeDependencies.Add(LibPath);
        }
        else if (Target.Platform == UnrealTargetPlatform.Mac)
        {
            string LibPath = Path.Combine(ModuleDirectory, "lib", "Mac", "libmylib.dylib");
            PublicAdditionalLibraries.Add(LibPath);
            RuntimeDependencies.Add(LibPath);
        }
    }
}
```

## Multi-Platform External Module

Pattern with helper method for cleaner platform selection:

```csharp
using System.IO;
using UnrealBuildTool;

public class MyLibrary : ModuleRules
{
    private string GetLibraryPath(ReadOnlyTargetRules Target)
    {
        if (Target.Platform == UnrealTargetPlatform.Win64)
            return Path.Combine(ModuleDirectory, "lib", "Win64", "mylib.lib");
        if (Target.Platform == UnrealTargetPlatform.Linux)
            return Path.Combine(ModuleDirectory, "lib", "Linux", "libmylib.a");
        if (Target.Platform == UnrealTargetPlatform.Mac)
            return Path.Combine(ModuleDirectory, "lib", "Mac", "libmylib.a");
        return null;
    }

    public MyLibrary(ReadOnlyTargetRules Target) : base(Target)
    {
        Type = ModuleType.External;
        PublicIncludePaths.Add(Path.Combine(ModuleDirectory, "include"));

        string LibPath = GetLibraryPath(Target);
        if (LibPath != null)
        {
            PublicAdditionalLibraries.Add(LibPath);
            PublicDefinitions.Add("WITH_MYLIB=1");
        }
        else
        {
            PublicDefinitions.Add("WITH_MYLIB=0");
        }
    }
}
```

## Consumer Module Setup

Any module that uses the external library:

```csharp
public class MyGameModule : ModuleRules
{
    public MyGameModule(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] {
            "Core", "CoreUObject", "Engine", "MyThirdPartyLibrary"
        });

        // If the library requires RTTI/exceptions, the consumer must also enable them
        bUseRTTI = true;
        bEnableExceptions = true;
    }
}
```

**Important:** `bUseRTTI` and `bEnableExceptions` must be set in **every** module that includes the third-party headers, not just the External module.

## uplugin Descriptor

Register both the consumer module and the External module:

```json
{
    "FileVersion": 3,
    "Version": 1,
    "VersionName": "1.0",
    "FriendlyName": "My Third-Party Plugin",
    "Modules": [
        {
            "Name": "MyPlugin",
            "Type": "Runtime",
            "LoadingPhase": "Default"
        }
    ]
}
```

Note: `ModuleType.External` modules do **not** need to be listed in the `.uplugin` -- they are discovered by UBT through dependency resolution.

## Debug vs Release Library Selection

```csharp
string LibName = "mylib";
if (Target.Configuration == UnrealTargetConfiguration.Debug
    && Target.bDebugBuildsActuallyUseDebugCRT)
{
    LibName += "d"; // e.g., mylibd.lib
}
PublicAdditionalLibraries.Add(Path.Combine(ModuleDirectory, "lib", LibName + ".lib"));
```

**Warning:** UE uses Release CRT even in Debug editor builds by default. Only use debug libs if `bDebugBuildsActuallyUseDebugCRT` is true (rarely the case). Linking debug-built third-party libs against Release CRT causes `_ITERATOR_DEBUG_LEVEL` mismatch errors.

## Bulk Library Loading

When a library ships many `.lib` / `.dll` files (e.g., FFmpeg):

```csharp
// Load all .lib files from a directory
DirectoryInfo LibDir = new DirectoryInfo(Path.Combine(ModuleDirectory, "lib", "Win64"));
foreach (FileInfo File in LibDir.GetFiles("*.lib"))
{
    PublicAdditionalLibraries.Add(File.FullName);
}

// Stage all .dll files
foreach (FileInfo File in LibDir.GetFiles("*.dll"))
{
    RuntimeDependencies.Add(
        "$(PluginDir)/Binaries/ThirdParty/MyLib/Win64/" + File.Name,
        File.FullName);
    PublicDelayLoadDLLs.Add(File.Name);
}
```

## PreBuildSteps for CMake Libraries

If the library needs to be built from source before UBT runs:

In `.uplugin`:
```json
{
    "PreBuildSteps": {
        "Win64": ["powershell -File $(PluginDir)/Scripts/build_thirdparty.ps1"]
    }
}
```

The script runs CMake and produces the static/dynamic libraries that your `.Build.cs` then references. See also the [UE4CMake](https://github.com/caseymcc/UE4CMake) tool for automated CMake integration.

## CMakeTarget Integration (UE4CMake)

The [UE4CMake](https://github.com/caseymcc/UE4CMake) plugin provides a Build.cs API to invoke CMake builds as part of UBT. It sets itself up as an empty plugin, allowing its `.cs` build files to generate an Assembly included through the plugin system.

**Usage in Build.cs:**
```csharp
CMakeTarget.add(Target, this, "{cmake_target}",
    "{cmake_source_path}", "{cmake_args}", {use_system_compiler});
```

**Parameters:**
- `{cmake_target}`: Target name from `add_library()` in CMakeLists.txt
- `{cmake_source_path}`: Directory containing CMakeLists.txt (relative or absolute)
- `{cmake_args}`: Custom CMake flags and options
- `{use_system_compiler}`: Linux-only; forces system compiler instead of embedded clang (needed when embedded clang lacks `std::filesystem` support)

**How it works:**
1. Generates a wrapper CMakeLists.txt in `Intermediate/CMakeTarget/{LibName}/`
2. Invokes CMake to generate platform-specific build files
3. Executes CMake build
4. Auto-populates `PublicIncludePaths` and `PublicAdditionalLibraries` from build output
5. Registers source files in `ExternalDependencies` for automatic rebuild on changes

**Plugin registration** (in `.uproject` or `.uplugin`):
```json
"Plugins": [{"Name": "CMakeTarget", "Enabled": true}]
```

**Struct packing safety:** When including headers from CMake-built libraries, use:
```cpp
PRAGMA_PUSH_PLATFORM_DEFAULT_PACKING
#include <thirdparty.h>
PRAGMA_POP_PLATFORM_DEFAULT_PACKING
```
UE forces 4-byte struct packing on Win32, which can cause alignment issues with 8-byte types in third-party headers.

## AddEngineThirdPartyPrivateStaticDependencies

Helper method to depend on libraries already bundled with the engine (located in `Engine/Source/ThirdParty/`). This avoids maintaining your own copies and prevents symbol interposition issues.

```csharp
// Single library
AddEngineThirdPartyPrivateStaticDependencies(Target, "zlib");

// Multiple libraries
AddEngineThirdPartyPrivateStaticDependencies(Target, "OpenSSL", "libWebSockets", "libcurl");
```

The "Private" designation means these dependencies won't be exposed to modules that depend on your module. Use platform checks when availability varies:

```csharp
if (Target.Platform == UnrealTargetPlatform.Linux)
{
    AddEngineThirdPartyPrivateStaticDependencies(Target, "OpenSSL", "libWebSockets", "libcurl");
}
```

## ExternalDependencies

Register external files that should trigger makefile regeneration when modified. Paths are relative to the `.Build.cs` file location:

```csharp
// Track a version header -- rebuild when library is updated
ExternalDependencies.Add("include/version.h");

// Track the library binary itself
ExternalDependencies.Add(Path.Combine("lib", "Win64", "mylib.lib"));
```

This is essential for CMake-based integrations where UBT cannot otherwise detect when upstream sources change.

## UE Version-Specific Build.cs Changes

Breaking changes and new APIs relevant to third-party library integration across UE versions:

### UE 5.0
- `TObjectPtr` replaces raw UObject pointers (engine-transparent)
- `FVector` changed to 3 `double` values

### UE 5.2
- `bEnforceIWYU` (bool) replaced by `IWYUSupport` (enum: `None`, `KeepAsIs`, `Full`)

### UE 5.3
- `BuildSettingsVersion.V4` defaults to **C++20**
- `TRemoveConst` deprecated; use `std::remove_const`
- Third-party libraries compiled without C++20 support may produce linker errors due to different symbol mangling for `std::optional` and other template types

### UE 5.4
- Default MSVC warning level changed to `/W4` (more warnings from third-party headers)
- `FText` internal storage changed from `TSharedRef` to `TRefCountPtr`

### UE 5.5
- New `Engine/Build/BatchFiles/RunUBT` scripts; should replace direct `UnrealBuildTool` invocation
- `PER_MODULE_BOILERPLATE` no longer required; UBT handles automatically
- `StructUtils` plugin deprecated; functionality moved into engine
- Stricter module validation during project generation

### UE 5.6
- `FString::Appendf` and related functions enforce `static constexpr` format strings
- `GMalloc` access deprecated

### UE 5.7
- `FindObject` function series deprecates `bExactClass` parameter in favor of `EFindObjectFlags`

### C++ Standard Compatibility Critical Note
UE5 compiles with C++17 (or C++20 from UE 5.3 with BuildSettingsVersion.V4). Third-party libraries with dependencies that behave differently based on C++ version (e.g., `optional_HAVE_STD_OPTIONAL` evaluating differently with/without C++17) will produce LNK2019 linker errors if compiled with a different C++ standard. **Always recompile third-party libraries with matching `CMAKE_CXX_STANDARD`.**

## Multi-Platform Real-World Example (Funapi)

A comprehensive example from the iFunFactory plugin showing platform-specific handling for Windows, Mac, Linux, Android, iOS, and PS4:

```csharp
// Key patterns demonstrated:
// 1. Platform-conditional PublicDefinitions
if (Target.Platform == UnrealTargetPlatform.PS4) {
    PublicDefinitions.Add("FUNAPI_HAVE_RPC=0");
} else {
    PublicDefinitions.Add("FUNAPI_HAVE_RPC=1");
}

// 2. Windows: Use engine modules directly
if (Target.Platform == UnrealTargetPlatform.Win64) {
    PrivateDependencyModuleNames.AddRange(new string[] {
        "OpenSSL", "libcurl", "libWebSockets"
    });
}

// 3. Mac: Static linking with bundled libraries
if (Target.Platform == UnrealTargetPlatform.Mac) {
    PublicAdditionalLibraries.Add(Path.Combine(LibPath, "libcurl.a"));
    PublicAdditionalLibraries.Add(Path.Combine(LibPath, "libcrypto.a"));
    PublicAdditionalLibraries.Add(Path.Combine(LibPath, "libssl.a"));
}

// 4. Android: Multi-architecture with #if UE_4_24_OR_LATER guard
if (Target.Platform == UnrealTargetPlatform.Android) {
    string[] Architectures = new string[] { "ARMv7", "ARM64" };
    foreach (var Arch in Architectures) {
        PublicAdditionalLibraries.Add(
            Path.Combine(LibPath, "lib/Android", Arch, "libcrypto.a"));
    }
}

// 5. PS4/Linux: Use engine-bundled libraries
if (Target.Platform == UnrealTargetPlatform.Linux) {
    AddEngineThirdPartyPrivateStaticDependencies(Target,
        "OpenSSL", "libWebSockets", "libcurl");
}
```

## Regex-Based Library Discovery

For plugins that link to external build systems (C++, Rust, etc.) where library filenames may vary, use regex to discover the correct file:

```csharp
string[] fileEntries = Directory.GetFiles(fullBuildPath);
string pattern = ".*" + libraryName + ".*\\.";
if (Target.Platform == UnrealTargetPlatform.Win64)
    pattern += "lib";
else
    pattern += "a";

Regex r = new Regex(pattern, RegexOptions.IgnoreCase);
string fullLibraryPath = null;
foreach (var file in fileEntries)
{
    if (r.Match(file).Success)
    {
        fullLibraryPath = Path.Combine(fullBuildPath, file);
        break;
    }
}

if (fullLibraryPath == null)
    throw new Exception("Unable to locate build libraries in: " + fullBuildPath);

PublicAdditionalLibraries.Add(fullLibraryPath);
```

This pattern is useful for Rust (`extern.dll.lib`, `libextern.a`) and CMake projects where output names include configuration suffixes.
