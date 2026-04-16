# Common Patterns & Pitfalls

## Table of Contents
- [Implementation Recipes](#implementation-recipes)
- [Critical Pitfalls](#critical-pitfalls)
- [Troubleshooting](#troubleshooting)
- [Debugging Tools](#debugging-tools)
- [Key UE API Functions](#key-ue-api-functions)
- [Engine-Bundled Third-Party Libraries](#engine-bundled-third-party-libraries)

---

## Implementation Recipes

### Wrapping a Static Library (Minimal)

The simplest integration -- two additions to an existing module's Build.cs:

```csharp
PublicAdditionalLibraries.Add(Path.Combine(ModuleDirectory, "..", "ThirdParty", "mylib.lib"));
PublicIncludePaths.Add(Path.Combine(ModuleDirectory, "..", "ThirdParty", "include"));
```

In C++:
```cpp
THIRD_PARTY_INCLUDES_START
#include <mylib/api.h>
THIRD_PARTY_INCLUDES_END

void UMyComponent::DoWork()
{
    mylib::Result R = mylib::Process(TCHAR_TO_UTF8(*InputString));
    OutputString = UTF8_TO_TCHAR(R.c_str());
}
```

### Wrapping a DLL with Delay Loading (Windows)

```csharp
// Build.cs
PublicAdditionalLibraries.Add(Path.Combine(ModuleDirectory, "..", "ThirdParty", "mylib.lib"));
PublicDelayLoadDLLs.Add("mylib.dll");
RuntimeDependencies.Add("$(PluginDir)/Binaries/ThirdParty/Win64/mylib.dll");
```

```cpp
// Module startup
void FMyModule::StartupModule()
{
    FString DllPath = FPaths::Combine(
        IPluginManager::Get().FindPlugin("MyPlugin")->GetBaseDir(),
        TEXT("Binaries/ThirdParty/Win64/mylib.dll"));
    DllHandle = FPlatformProcess::GetDllHandle(*DllPath);
}
```

### Blueprint Function Library Exposing Third-Party Functions

```cpp
UCLASS()
class MYPLUGIN_API UMyLibBPFL : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category = "MyLib")
    static double AddNumbers(double A, double B);
};

// Implementation includes third-party header
THIRD_PARTY_INCLUDES_START
#include <mylib/math.h>
THIRD_PARTY_INCLUDES_END

double UMyLibBPFL::AddNumbers(double A, double B)
{
    return mylib::add(A, B);
}
```

### Conditional Compilation for Platform Support

```csharp
// Build.cs
PublicDefinitions.Add(string.Format("WITH_MYLIB={0}",
    Target.Platform == UnrealTargetPlatform.Win64 ? 1 : 0));
```

```cpp
// C++ usage
#if WITH_MYLIB
THIRD_PARTY_INCLUDES_START
#include <mylib/api.h>
THIRD_PARTY_INCLUDES_END
#endif

void UMyComponent::DoWork()
{
#if WITH_MYLIB
    mylib::Process();
#else
    UE_LOG(LogTemp, Warning, TEXT("MyLib not available on this platform"));
#endif
}
```

### Module Interface Pattern for Library Access

Expose library functionality through `IModuleInterface` so other modules don't need third-party headers:

```cpp
// Public interface (no third-party includes)
class IMyLibModule : public IModuleInterface
{
public:
    static IMyLibModule& Get()
    {
        return FModuleManager::GetModuleChecked<IMyLibModule>("MyLibPlugin");
    }
    static bool IsAvailable()
    {
        return FModuleManager::Get().IsModuleLoaded("MyLibPlugin");
    }

    virtual FString ProcessData(const FString& Input) = 0;
};
```

```cpp
// Private implementation (has third-party includes)
class FMyLibModule : public IMyLibModule
{
    THIRD_PARTY_INCLUDES_START
    #include <mylib/api.h>
    THIRD_PARTY_INCLUDES_END

    virtual FString ProcessData(const FString& Input) override
    {
        auto Result = mylib::process(TCHAR_TO_UTF8(*Input));
        return UTF8_TO_TCHAR(Result.c_str());
    }
};
```

### Building a Static Library in Visual Studio for UE

1. Create **Empty C++ Project** in Visual Studio
2. Set **Configuration Properties > General > Configuration Type** to **Static library (.lib)**
3. Build in **Release** mode for **x64** platform
4. Output: `YourLib.lib` in `x64/Release/`
5. Copy `.lib` and headers to your plugin's `ThirdParty/` directory

**Critical:** Build with **/MD** (Multi-threaded DLL) runtime to match UE:
- Project Properties > C/C++ > Code Generation > Runtime Library > **Multi-threaded DLL (/MD)**

### Barrier Module Pattern (isolating compiler setting conflicts)

When a third-party library requires RTTI and exceptions but you want to minimize their impact across your project, use a **barrier module**:

```
Plugin/Source/
  ThirdParty/MyLib/           # ModuleType.External (headers + libs)
    MyLib.Build.cs
  MyLibBarrier/               # Barrier module
    MyLibBarrier.Build.cs     # bUseRTTI = true; bEnableExceptions = true
    Public/
      MyLibBarrierTypes.h     # Clean types ONLY -- no third-party includes, no UObject.h
    Private/
      MyLibBarrierImpl.cpp    # Wraps third-party includes
  MyPlugin/                   # Main module -- depends on MyLibBarrier, NOT on MyLib
    MyPlugin.Build.cs
```

**Barrier Build.cs:**
```csharp
PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
bUseRTTI = true;
bEnableExceptions = true;
PrivateDependencyModuleNames.Add("MyLib");
```

**Rules for barrier public headers:**
- Must NOT include any third-party headers
- Must NOT trigger `UObject.h` inclusion
- Math types (`FVector`, `FTransform`) are acceptable
- All third-party object references must be opaque barrier types
- `FPlatformMemory` / allocator boundaries must be respected: container objects returned by value from the third-party library must be freed with the library's deallocator before going out of scope

### Header-Only Library Integration

For header-only libraries (nlohmann JSON, EnTT, stb_image, etc.):

```csharp
// Build.cs -- no External module needed
PublicIncludePaths.Add(Path.Combine(ModuleDirectory, "..", "ThirdParty", "nlohmann"));
bEnableExceptions = true; // If the library uses exceptions
```

```cpp
THIRD_PARTY_INCLUDES_START
#include "json.hpp"
THIRD_PARTY_INCLUDES_END
using FJson = nlohmann::json;
```

**No `.lib`/`.a` files needed.** But a Build.cs is still required, and `bEnableExceptions` or `bUseRTTI` must be set if the library needs them.

### DLL Export Macro Pattern for Custom Libraries

When building your own DLL for UE consumption:

**Library header:**
```cpp
#pragma once
#if defined _WIN64
    #include <string>
    #define MYLIB_IMPORT __declspec(dllimport)
#else
    #define MYLIB_IMPORT
#endif
MYLIB_IMPORT std::string MyFunction();
```

**Library source:**
```cpp
#if defined _WIN64
    #define MYLIB_EXPORT __declspec(dllexport)
#else
    #define MYLIB_EXPORT
#endif
#include "MyLib.h"
MYLIB_EXPORT std::string MyFunction() { return "Hello from DLL"; }
```

**Post-build automation (VS):**
Set in MyLib Project > Properties > Build Events > Post-Build Event:
```
copy "$(TargetPath)" "$(SolutionDir)..\..\..\..\Binaries\ThirdParty\MyLib\Win64"
```

### Comprehensive Macro Decontamination

For libraries with many macro conflicts beyond `check`, use the full decontamination pattern:

```cpp
// Method 1: Manual push/pop of specific macros
#pragma push_macro("check")
#pragma push_macro("CONSTEXPR")
#pragma push_macro("dynamic_cast")
#pragma push_macro("PI")
#undef check
#undef CONSTEXPR
#undef dynamic_cast
#undef PI

PRAGMA_PUSH_PLATFORM_DEFAULT_PACKING
THIRD_PARTY_INCLUDES_START
#include <problematic_library.h>
THIRD_PARTY_INCLUDES_END
PRAGMA_POP_PLATFORM_DEFAULT_PACKING

#pragma pop_macro("PI")
#pragma pop_macro("dynamic_cast")
#pragma pop_macro("CONSTEXPR")
#pragma pop_macro("check")
```

```cpp
// Method 2: UnrealMacroNuke (auto-generated headers)
#pragma warning(push)
#pragma warning(disable: <codes>)
#include "UndefineMacros_UE_5.3.h"
#include <problematic_library.h>
#include "RedefineMacros_UE_5.3.h"
#pragma warning(pop)
```

UnrealMacroNuke scans all Runtime/ headers, generates undefine/redefine pairs, and deliberately excludes underscore-prefixed macros to avoid breaking VS internals.

### Conan Package Manager for UE-Compatible Builds

When a third-party library depends on libraries also bundled by UE (zlib, libpng, OpenSSL), **symbol interposition** occurs: the linker picks the first symbol it finds, causing version mismatches. The solution is to build each library from source against UE's bundled versions.

**Build.cs Conan integration:**
```csharp
// Launch conan install as child process
Process.Start(new ProcessStartInfo {
    FileName = "conan",
    Arguments = "install . --profile ue4",
    WorkingDirectory = ModuleRoot
}).WaitForExit();
// Parse conanbuildinfo.json for include paths, lib paths, definitions
```

**Conanfile.txt:**
```
[requires]
opencv-ue4/3.3.0@adamrehn/4.19

[generators]
json
```

**Conan wrapper packages** query UE's `ue4cli` for build flags at install time, ensuring compiled libraries use UE's exact toolchain and bundled dependency versions.

---

## Critical Pitfalls

### Visual Studio Project Settings Are Ignored
UBT completely ignores VS project property pages. All include paths, library paths, and definitions **must** be set in `.Build.cs`. If you add a path in VS properties, UBT will not use it.

### Compile Third-Party Libs with /MD (Release)
UE uses the Release CRT (`/MD`). Linking a debug-built library (`/MDd`) causes `_ITERATOR_DEBUG_LEVEL` mismatch errors and access violations. Always build third-party libs in Release mode.

### RTTI and Exceptions Must Propagate
Setting `bUseRTTI = true` and `bEnableExceptions = true` in only the External module is insufficient. **Every module that includes the third-party headers** must also set these flags, or you get `#pragma pack(pop)` errors (C4103) and link failures.

### UE's check Macro Collision
UE defines `check(expr)` globally. Third-party libraries using `check` as an identifier (e.g., Armadillo, some math libs) will get cryptic errors: `C2988`, `C4003`. Fix: `#undef check` before the include.

### Binaries/ThirdParty Is Not Regenerated
The `Binaries/ThirdParty/` folder created by the plugin template is copied from the engine install, not built. Deleting it and rebuilding will **not** restore it. Keep backups or use source control.

### bUsePrecompiled Gotcha
Setting `bUsePrecompiled = true` makes UBT skip compilation entirely. If no prebuilt binaries exist, the module silently fails to load. Only set this for genuinely precompiled distributions.

### Linux ABI: libstdc++ vs libc++
C++ libraries compiled with system `libstdc++` are ABI-incompatible with UE's `libc++`. You must recompile with UE's Clang toolchain. C libraries (pure C API) are unaffected.

### DLL Load Order
DLL dependencies must be loaded before the libraries that need them. Loading `main.dll` before its dependency `utils.dll` causes unresolved symbol errors. Load in dependency order.

### vcpkg Does Not Integrate with UBT
vcpkg uses MSBuild integration which UBT ignores. Manually wire paths in `.Build.cs` instead. Delete `DerivedDataCache`, `Intermediate`, `Binaries` and regenerate project files after changes.

### macOS: Delay Loading Not Supported
There is no equivalent of Windows `/DELAYLOAD` on macOS. Only weak linking (for optionally-present libraries) is available.

### Symlinks Not Supported (Linux)
UBT does not follow symlinks. Place actual library files in the expected locations, not symlinks.

### C++ Standard Mismatch (UE5)
UE5 compiles with C++17 (or C++20 from UE 5.3 with BuildSettingsVersion.V4). Libraries compiled without matching C++ standard produce different symbol names for `std::optional`, `std::string_view`, and other STL types. For example, `optional_HAVE_STD_OPTIONAL` evaluates differently with/without C++17, causing `nonstd::optional` symbols in the library vs `std::optional` in UE code. Fix: rebuild with `-DCMAKE_CXX_STANDARD=17` (or 20 for V4+).

### Symbol Interposition with Bundled Libraries
When your third-party library depends on zlib/libpng/OpenSSL/etc. AND UE also bundles these, the linker picks the first symbols found. This causes crashes when function signatures differ between versions. Solution: build your library against UE's bundled versions using `AddEngineThirdPartyPrivateStaticDependencies`, or use `conan-ue4cli` to force UE-compatible builds.

### Linux libc++ Compiler Flag Order
On Linux, `-nostdinc++` must appear before include flags, and UE's libc++ libraries must link in correct order. Build systems that reorder flags break symbol resolution. The `conan-ue4cli` libcxx package provides Python wrapper scripts that intercept compiler invocations via `CC`/`CXX` env vars to enforce correct flag ordering.

### UE 5.4+ Warning Level Increase
UE 5.4 changed default MSVC warning level to `/W4`, which generates more warnings from third-party headers. Use `THIRD_PARTY_INCLUDES_START/END` or `PublicSystemIncludePaths` (suppresses warnings) instead of `PublicIncludePaths`.

### Must Have At Least One .cpp File
The plugin or module must contain at least one `.cpp` file or UBT will not compile it. For External modules this does not apply (no compilation), but consumer modules wrapping the library need at least a stub `.cpp`.

### Project File Regeneration Required
After adding a new `.Build.cs` file, you must regenerate project files (`GenerateProjectFiles.bat` or the equivalent). Failing to do so means UBT won't discover the new module.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `unresolved external symbol` | Missing library, wrong CRT, symbol not exported | Check `PublicAdditionalLibraries` path; rebuild lib with `/MD`; verify symbols with `dumpbin /exports` |
| `Failed to load DLL` | DLL not found in search path | Load with full path via `GetDllHandle()` in `StartupModule()` |
| `_ITERATOR_DEBUG_LEVEL mismatch` | Debug lib linked against Release CRT | Rebuild third-party lib in Release mode |
| `C2988 / C4003` (check macro) | UE's `check` macro collides with third-party code | `#undef check` before third-party include |
| `#pragma pack(pop)` / C4103 | Missing RTTI/exceptions flags | Set `bUseRTTI = true; bEnableExceptions = true` in **all** consuming modules |
| `BOOST_DISABLE_ABI_HEADERS` error | Boost ABI header conflicts | Add `PublicDefinitions.Add("BOOST_DISABLE_ABI_HEADERS=1")` |
| `abi:cxx11` symbol mismatch (Linux) | Library built with `libstdc++`, UE uses `libc++` | Recompile with UE's Clang toolchain and `-nostdinc++` |
| `modules are missing or built with a different engine version` | Stale intermediate files | Delete `Intermediate/`, `Binaries/`, `Saved/`; regenerate project files |
| DLL loads but functions crash | Memory/heap corruption between UE and DLL allocators | Use static linking instead; ensure same CRT version |
| `dynamic_cast` error with RTTI off | Non-UObject dynamic_cast with RTTI disabled | Enable `bUseRTTI = true` or avoid `dynamic_cast` for non-UObject types |
| macOS dylib not found | Install name not using `@rpath` | Run `install_name_tool -id @rpath/libfoo.dylib libfoo.dylib` |
| Linux multiple global symbol definitions | `RTLD_LOCAL` vs `RTLD_GLOBAL` causing symbol duplication | Use `gdb` to check pointer addresses; restructure to avoid duplicate globals |
| LNK2019 after UE5 upgrade | C++ standard mismatch (lib compiled without C++17/20) | Rebuild third-party lib with `CMAKE_CXX_STANDARD=17` (or 20 for V4+) |
| Heap corruption / access violation across DLL boundary | Mismatched memory allocators between UE and DLL | Free container memory with library's deallocator; prefer static linking; or use barrier module pattern |
| `PublicLibraryPaths` deprecated | Renamed in UE 4.24+ | Use `PublicSystemLibraryPaths` instead |
| `bEnforceIWYU` compilation error (UE 5.2+) | Changed from bool to enum | Use `IWYUSupport = IWYUSupport.None` (or `.KeepAsIs` / `.Full`) |
| `/W4` warnings from third-party headers (UE 5.4+) | Default warning level increased | Use `PublicSystemIncludePaths` instead of `PublicIncludePaths`, or wrap with `THIRD_PARTY_INCLUDES_START/END` |
| Android link failure: missing architecture | Libraries not provided for all required ABIs | Provide libs for both `armeabi-v7a` and `arm64-v8a`; use APL XML for SO deployment |

## Debugging Tools

### Windows
- **Dependency Walker** -- examine DLL imports/exports
- **`dumpbin /exports mylib.dll`** -- list exported symbols
- **`dumpbin /dependents mylib.dll`** -- list DLL dependencies
- **UE Log** -- `GetDllHandle` verbose output on failure

### macOS
- **`otool -L libfoo.dylib`** -- list dependencies and install names
- **`otool -l libfoo.dylib`** -- show load commands (LC_LOAD_DYLIB, LC_RPATH)

### Linux
- **`ldd libfoo.so`** -- show runtime dependencies
- **`nm -D libfoo.so | c++filt`** -- show/demangle exported symbols
- **`readelf -d libfoo.so`** -- dump RPATH, NEEDED entries
- **`LD_DEBUG=libs`** -- trace library loading at runtime
- **`strace -e openat`** -- see which paths `dlopen` tries

## Key UE API Functions

| Function | Purpose |
|----------|---------|
| `FPlatformProcess::GetDllHandle(Path)` | Load a DLL/SO/dylib, returns `void*` |
| `FPlatformProcess::FreeDllHandle(Handle)` | Unload a previously loaded library |
| `FPlatformProcess::GetDllExport(Handle, Name)` | Get function pointer by name from loaded library |
| `FModuleManager::GetModuleChecked<T>(Name)` | Access a loaded module instance by type |
| `IPluginManager::Get().FindPlugin(Name)->GetBaseDir()` | Get plugin root directory at runtime |
| `FPaths::Combine(...)` | Build file paths safely (cross-platform) |
| `TCHAR_TO_UTF8(*FString)` | Convert UE string to UTF-8 C string |
| `UTF8_TO_TCHAR(const char*)` | Convert UTF-8 C string to UE TCHAR |

## Engine-Bundled Third-Party Libraries

Before bundling a library, check `Engine/Source/ThirdParty/`. Epic ships many common libraries:

| Library | Engine Path |
|---------|-------------|
| libcurl | `Engine/Source/ThirdParty/libcurl/` |
| zlib | `Engine/Source/ThirdParty/zlib/` |
| libpng | `Engine/Source/ThirdParty/libPNG/` |
| OpenSSL | `Engine/Source/ThirdParty/OpenSSL/` |
| FreeType | `Engine/Source/ThirdParty/FreeType2/` |
| Lua | `Engine/Source/ThirdParty/Lua/` |
| ICU | `Engine/Source/ThirdParty/ICU/` |
| libc++ (Linux) | `Engine/Source/ThirdParty/Unix/LibCxx/` |

To use an engine-bundled library in your Build.cs:
```csharp
AddEngineThirdPartyPrivateStaticDependencies(Target, "zlib");
```

**Multi-library usage (common on Linux/PS4):**
```csharp
AddEngineThirdPartyPrivateStaticDependencies(Target, "OpenSSL", "libWebSockets", "libcurl");
```

## Linux Toolchain Versions by Engine Version

When building third-party libraries for Linux, the Clang version must match the engine:

| UE Version | Clang Version | Sysroot Path Fragment |
|------------|---------------|----------------------|
| UE 4.25 | v16_clang-9.0.1 | `v16_clang-9.0.1-centos7` |
| UE 4.26 | v17_clang-10.0.1 | `v17_clang-10.0.1-centos7` |
| UE 4.27 | v19_clang-11.0.1 | `v19_clang-11.0.1-centos7` |
| UE 5.x | v22_clang-16.0.6 | `v22_clang-16.0.6-centos7` |

Retrieve correct flags programmatically with `ue4cli`:
- `ue4 cmakeflags` -- CMake configuration flags
- `ue4 cxxflags` -- C++ compiler flags
- `ue4 ldflags` -- linker flags
- `ue4 libfiles` -- library file paths
- `ue4 version short` -- engine version string

## Linux Compilation Flags Reference

Flags output by `ue4cli` for building compatible libraries:

**Compilation flags:**
```
-nostdinc++
-I$ENGINE/Engine/Source/ThirdParty/Unix/LibCxx/include
-I$ENGINE/Engine/Source/ThirdParty/Unix/LibCxx/include/c++/v1
-fPIC
```

**Linking flags:**
```
-nodefaultlibs
$ENGINE/Engine/Source/ThirdParty/Unix/LibCxx/lib/Linux/x86_64-unknown-linux-gnu/libc++.a
$ENGINE/Engine/Source/ThirdParty/Unix/LibCxx/lib/Linux/x86_64-unknown-linux-gnu/libc++abi.a
-lm -lc -lgcc_s -lgcc
```
