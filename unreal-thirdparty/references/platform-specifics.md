# Platform-Specific Reference

## Table of Contents
- [Windows: DLL Loading](#windows-dll-loading)
- [Windows: Delay Loading](#windows-delay-loading)
- [Windows: Header Conflicts](#windows-header-conflicts)
- [Windows: Debugging DLL Issues](#windows-debugging-dll-issues)
- [macOS: Dylib and @rpath](#macos-dylib-and-rpath)
- [macOS: Debugging Dylib Issues](#macos-debugging-dylib-issues)
- [Linux: ABI Compatibility](#linux-abi-compatibility)
- [Linux: CMake Toolchain File](#linux-cmake-toolchain-file)
- [Linux: Sysroot Dependencies](#linux-sysroot-dependencies)
- [Linux: Debugging SO Issues](#linux-debugging-so-issues)
- [Android: Native Library Integration](#android-native-library-integration)
- [iOS: Framework and Library Linking](#ios-framework-and-library-linking)
- [Cross-Platform Header Inclusion](#cross-platform-header-inclusion)
- [RTTI and Exceptions](#rtti-and-exceptions)
- [Packing and Alignment](#packing-and-alignment)

---

## Windows: DLL Loading

Windows stores DLL dependencies by **name only** (no path) in the executable's import table. The OS searches a short list of paths to resolve them, which can cause obscure startup errors.

**`FPlatformProcess::GetDllHandle()`** has special UE logic to:
1. Read the DLL's import table before loading
2. Pre-resolve dependencies from engine/project/plugin `Binaries/` directories
3. Produce **verbose log output** on failure

```cpp
// Manual DLL loading
void* Handle = FPlatformProcess::GetDllHandle(TEXT("C:/path/to/mylib.dll"));
if (!Handle)
{
    UE_LOG(LogTemp, Error, TEXT("Failed to load mylib.dll"));
}

// Unloading
FPlatformProcess::FreeDllHandle(Handle);
```

**Search order:** When the OS loads a DLL, if one with the same name is already in memory, it links to the existing one instead of searching disk.

## Windows: Delay Loading

Delay loading defers DLL resolution until the first function call. This lets you load the DLL from a custom path first.

**How it works:**
1. Imported functions initially point to a **thunk function**
2. On first call, the thunk loads the real DLL
3. Import table is patched to point to real function addresses
4. All subsequent calls go directly to the library

**Build.cs:**
```csharp
PublicDelayLoadDLLs.Add("mylib.dll"); // Name only, no path
```

**Limitation:** Delay loading is **not possible if you access variables** exported from the DLL. The linker will error on variable imports with delay-load.

**Startup pattern:** Load the DLL in `StartupModule()` before any library function is called:
```cpp
void FMyModule::StartupModule()
{
    void* Handle = FPlatformProcess::GetDllHandle(TEXT("/path/to/mylib.dll"));
    // Now when delay-load triggers, it finds the DLL already in memory
}
```

## Windows: Header Conflicts

### Windows.h

UE does not include `Windows.h` by default. If needed:
```cpp
#include "Windows/WindowsHWrapper.h"
```

UE **undefines many Windows macros** (`TRUE`, `FALSE`, `check`, `TEXT`, `GetObject`, etc.) to prevent collisions. Use explicit ANSI/Unicode variants:
```cpp
// Instead of GetCommandLine() (macro)
GetCommandLineA();  // ANSI
GetCommandLineW();  // Unicode
```

### Restoring Windows Platform Types

When third-party code needs Windows macros like `TRUE`/`FALSE`:
```cpp
#include "Windows/AllowWindowsPlatformTypes.h"
int Foo = TRUE; // Windows TRUE macro, normally causes compile error in UE
#include "Windows/HideWindowsPlatformTypes.h"
```

### Restoring Windows Atomics

```cpp
#include "Windows/AllowWindowsPlatformAtomics.h"
// Code using InterlockedIncrement, InterlockedDecrement, etc.
#include "Windows/HideWindowsPlatformAtomics.h"
```

### UE's `check` Macro Collision

UE defines a `check(expr)` macro (via `UE_CHECK_IMPL`) that collides with third-party code using `check` as an identifier:
```cpp
// This will fail if the third-party header uses "check" as a variable/function name
#include <thirdparty.h> // ERROR: C2988, C4003

// Fix: undef check before including, restore after
#undef check
#include <thirdparty.h>
// Re-include UE check: #include "Misc/AssertionMacros.h"
```

## Windows: Debugging DLL Issues

| Tool | Usage |
|------|-------|
| **Dependency Walker** | Examine DLLs and functions imported by a module |
| **UE Log** | `FPlatformProcess::GetDllHandle` produces verbose output on failure |
| **Debugger** | Check `dli->szDLL` during delay-load exceptions for the failing DLL name |

---

## macOS: Dylib and @rpath

macOS dylibs store dependencies as **install names** which can use special prefixes:
- `@executable_path` -- relative to the executable
- `@loader_path` -- relative to the loading module
- `@rpath` -- searched via RPATH list (UE's approach)

**UBT auto-adds RPATH entries** for third-party dylibs outside `Engine/Source` and `Project/Source`.

**Setting install names:**
```bash
# When building the library
clang++ -dynamiclib -install_name @rpath/libmylib.dylib -o libmylib.dylib ...

# After building (modify existing dylib)
install_name_tool -id @rpath/libmylib.dylib /path/to/libmylib.dylib
```

**Build.cs for frameworks:**
```csharp
PublicFrameworks.Add("CoreVideo");  // Instead of PublicAdditionalLibraries
```

**Warning:** Storing dylibs in `Source/` subfolders works but is **not recommended** -- these folders are excluded from packaged games, forcing UBT to copy them elsewhere.

**Delay loading on macOS:** Not fully supported. Only weak linking is available (linking to a library that may be absent at runtime). No equivalent to Windows `/DELAYLOAD`.

## macOS: Debugging Dylib Issues

```bash
# List dependencies and their install names
otool -L libmylib.dylib

# Show all load commands (look for LC_LOAD_DYLIB and LC_RPATH)
otool -l libmylib.dylib
```

---

## Linux: ABI Compatibility

**The critical issue:** UE on Linux uses its own bundled **`libc++`** (Clang's standard library), NOT the system's **`libstdc++`** (GCC's standard library). C++ libraries compiled with `libstdc++` produce different symbol mangling and are ABI-incompatible.

**Example:** A library exports `sw::redis::Redis::ping[abi:cxx11]()` (libstdc++), but UE expects `sw::redis::Redis::ping()` (libc++). Linking fails with unresolved symbols.

**Solution:** Recompile C++ libraries with UE's Clang toolchain and `libc++`.

**Exception:** Pure **C libraries** have a stable ABI and do **not** need recompilation. Only C++ libraries are affected.

**Diagnosing ABI issues:**
```bash
nm -D libmylib.so | grep MyFunction | c++filt
# Look for [abi:cxx11] tags -- indicates libstdc++ was used
```

## Linux: CMake Toolchain File

To recompile a C++ library for UE on Linux, use this CMake toolchain file:

```cmake
# UEToolchain.cmake
set(ENGINE "/path/to/UnrealEngine/")

set(CMAKE_SYSROOT
    "${ENGINE}/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/v22_clang-16.0.6-centos7/x86_64-unknown-linux-gnu/")

set(CMAKE_C_COMPILER
    "${CMAKE_SYSROOT}/bin/clang")

set(CMAKE_CXX_COMPILER
    "${CMAKE_SYSROOT}/bin/clang++")

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)

# Suppress system libstdc++, use UE's libc++
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -nostdinc++ \
    -I${ENGINE}/Engine/Source/ThirdParty/Unix/LibCxx/include/ \
    -I${ENGINE}/Engine/Source/ThirdParty/Unix/LibCxx/include/c++/v1/")
```

**Build:**
```bash
mkdir build && cd build
cmake -DCMAKE_TOOLCHAIN_FILE=../UEToolchain.cmake ..
make
```

**Key flags:**
- **`-nostdinc++`** -- suppresses default C++ standard library headers
- Explicit `-I` paths point to UE's `libc++` headers at `Engine/Source/ThirdParty/Unix/LibCxx/`

**Note:** Adjust the sysroot version path (`v22_clang-16.0.6-centos7`) to match your UE version. Check `Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/` for the actual directory name.

## Linux: Sysroot Dependencies

When a library has its own dependencies (e.g., library A depends on library B depends on OpenSSL), those dependencies must be available in the sysroot for CMake's `find_package` to locate them:

```bash
# Copy dependency headers into sysroot
cp -r /path/to/dependency/include/hiredis/ $SYSROOT/include/

# Copy dependency libs into sysroot
cp /path/to/dependency/lib/libhiredis.so $SYSROOT/lib64/

# UE bundles OpenSSL -- reuse it
cp -r $ENGINE/Engine/Source/ThirdParty/OpenSSL/1.1.1n/include/Unix/x86_64-unknown-linux-gnu/openssl/ \
    $SYSROOT/include/
cp $ENGINE/Engine/Source/ThirdParty/OpenSSL/1.1.1n/lib/Unix/x86_64-unknown-linux-gnu/* \
    $SYSROOT/lib64/
```

**Caveats:**
- UBT only recognizes libraries within the engine tree, not system-installed ones
- Symlinks are **not supported** by UBT -- use actual files
- CMake toolchain files don't auto-propagate to subdirectory builds

## Linux: Debugging SO Issues

| Tool | Usage |
|------|-------|
| `ldd libmylib.so` | Show runtime dependencies, identify missing libs |
| `nm -D libmylib.so` | Show exported symbols (like Dependency Walker) |
| `readelf -d libmylib.so` | Dump RPATH, NEEDED entries, ELF section info |
| `LD_DEBUG=libs ./MyApp` | Trace which libraries are being loaded and from where |
| `strace -e openat ./MyApp` | See which file paths the loader attempts |

**UE's `dlopen` behavior:**
- UE modules: loaded as `RTLD_LAZY | RTLD_LOCAL`
- Non-UE modules: first loaded as `RTLD_LAZY | RTLD_LOCAL`, then re-opened as `RTLD_LAZY | RTLD_GLOBAL`
- This can cause issues with multiple global symbol definitions across modules

---

## Android: Native Library Integration

Android requires multi-architecture support and an APL (Android Packaging Layer) XML file for native library deployment.

### Build.cs Configuration

```csharp
if (Target.Platform == UnrealTargetPlatform.Android)
{
    string[] Architectures = new string[] { "ARMv7", "ARM64" };
    foreach (var Arch in Architectures)
    {
        PublicIncludePaths.Add(
            Path.Combine(ThirdPartyPath, "include", "Android", Arch));
        PublicAdditionalLibraries.Add(
            Path.Combine(ThirdPartyPath, "lib", "Android", Arch, "libmylib.so"));
    }

    // Register APL XML for packaging
    string RelAPLPath = Utils.MakePathRelativeTo(
        Path.Combine(ThirdPartyPath, "MYLIB_APL.xml"),
        Target.RelativeEnginePath);
    AdditionalPropertiesForReceipt.Add("AndroidPlugin", RelAPLPath);
}
```

### APL XML File

Controls binary deployment and Java integration during packaging:

```xml
<?xml version="1.0" encoding="utf-8"?>
<root xmlns:android="http://schemas.android.com/apk/res/android">
    <resourceCopies>
        <copyFile src="$S(PluginDir)/Libraries/Android/$S(Architecture)/libmylib.so"
                  dst="$S(BuildDir)/libs/$S(Architecture)/libmylib.so" />
        <!-- Optional: JAR dependency -->
        <copyFile src="$S(PluginDir)/Libraries/Android/mylib.jar"
                  dst="$S(BuildDir)/libs/mylib.jar" />
    </resourceCopies>

    <!-- Optional: Java initialization in GameActivity -->
    <gameActivityOnCreateAdditions>
        <insert>
        com.mylib.MyLib.init(this);
        </insert>
    </gameActivityOnCreateAdditions>

    <soLoadLibrary>
        <loadLibrary name="mylib" failmsg="mylib.so not loaded!" />
    </soLoadLibrary>
</root>
```

### Android Directory Structure

```
ThirdParty/MyLib/
  include/
    Android/
      ARMv7/    (architecture-specific headers, if any)
      ARM64/
  lib/
    Android/
      armeabi-v7a/  libmylib.so
      arm64-v8a/    libmylib.so
  MYLIB_APL.xml
```

### Android-Specific Notes
- Both `armeabi-v7a` and `arm64-v8a` architectures must be provided
- JAR files are deployed via APL XML, not through Build.cs
- `Utils.MakePathRelativeTo()` is required for APL path registration
- The `$S(Architecture)` variable in APL resolves to the current build architecture

---

## iOS: Framework and Library Linking

```csharp
if (Target.Platform == UnrealTargetPlatform.IOS)
{
    PublicIncludePaths.Add(Path.Combine(ThirdPartyPath, "include", "iOS"));

    // Static libraries
    PublicAdditionalLibraries.Add(
        Path.Combine(ThirdPartyPath, "lib", "iOS", "libmylib.a"));

    // System frameworks
    PublicFrameworks.Add("CoreVideo");
    PublicFrameworks.Add("Security");

    // Engine-bundled dependencies
    PrivateDependencyModuleNames.AddRange(new string[] { "OpenSSL", "libWebSockets" });
}
```

---

## Cross-Platform Header Inclusion

Always wrap third-party headers to suppress UE's strict warning/error settings:

```cpp
THIRD_PARTY_INCLUDES_START
#include <thirdparty/header.h>
THIRD_PARTY_INCLUDES_END
```

These macros disable treat-warnings-as-errors and relax compiler strictness for the enclosed includes.

## RTTI and Exceptions

UE disables both RTTI and C++ exceptions by default. Many third-party libraries (Boost, PCL, etc.) require them.

**Per-module (in Build.cs):**
```csharp
bUseRTTI = true;
bEnableExceptions = true;
```

**Must be set in EVERY module** that includes the third-party headers -- not just the External module.

**Engine-wide RTTI (in TargetRules):**
```csharp
bForceEnableRTTI = true; // Enables RTTI for entire engine -- use cautiously
```

**Linux caveat:** Linux does **not allow** mixing RTTI-on and RTTI-off modules. If any module needs RTTI, enable it engine-wide.

**`dynamic_cast` note:** UE redefines `dynamic_cast` in `CoreUObject/Public/Templates/Casts.h` to use its own reflection for UObject types. For non-UObject types with RTTI disabled, `dynamic_cast` will fail with a compile error.

## Packing and Alignment

UE forces **4-byte packing** on Win32 for legacy reasons. This can cause alignment bugs with `double` or `long` types in third-party structs:

```cpp
PRAGMA_PUSH_PLATFORM_DEFAULT_PACKING
#include <thirdparty_with_doubles.h>
PRAGMA_POP_PLATFORM_DEFAULT_PACKING
```

### Full Defensive Include Pattern

For maximum compatibility with problematic third-party headers, combine all protection mechanisms:

```cpp
// 1. Save and undefine conflicting macros
#pragma push_macro("check")
#pragma push_macro("CONSTEXPR")
#pragma push_macro("dynamic_cast")
#pragma push_macro("PI")
#undef check
#undef CONSTEXPR
#undef dynamic_cast
#undef PI

// 2. Restore default packing
PRAGMA_PUSH_PLATFORM_DEFAULT_PACKING

// 3. Suppress UE strict warnings
THIRD_PARTY_INCLUDES_START

// 4. Include the library
#include <problematic_library.h>

// 5. Restore in reverse order
THIRD_PARTY_INCLUDES_END
PRAGMA_POP_PLATFORM_DEFAULT_PACKING

#pragma pop_macro("PI")
#pragma pop_macro("dynamic_cast")
#pragma pop_macro("CONSTEXPR")
#pragma pop_macro("check")
```

### Windows Platform Types in Third-Party Code

When third-party code needs Windows macros like `TRUE`, `FALSE`, `DWORD`:

```cpp
#include "Windows/AllowWindowsPlatformTypes.h"
#include <thirdparty_using_windows_types.h>
#include "Windows/HideWindowsPlatformTypes.h"
```

For Windows atomics (`InterlockedIncrement`, etc.):
```cpp
#include "Windows/AllowWindowsPlatformAtomics.h"
#include <thirdparty_using_atomics.h>
#include "Windows/HideWindowsPlatformAtomics.h"
```

### Common Conflicting UE Macros

| Macro | Defined In | Conflict With |
|-------|-----------|---------------|
| `check(expr)` | `Misc/AssertionMacros.h` | Any library using `check` as identifier |
| `TEXT(x)` | `HAL/Platform.h` | Windows API, some string libraries |
| `PI` | `Math/UnrealMathUtility.h` | Math libraries defining their own PI |
| `CONSTEXPR` | Engine headers | Libraries defining their own CONSTEXPR |
| `dynamic_cast` | `Templates/Casts.h` | Libraries using standard dynamic_cast |
| `TRUE`/`FALSE` | Undefined by UE (Windows types) | Libraries expecting Windows BOOL values |
| `GetObject` | Undefined by UE (Windows types) | Libraries using Win32 GetObject |
