# Linking Patterns -- Detailed Reference

## Table of Contents
- [Approach 1: Static Library](#approach-1-static-library)
- [Approach 2: Dynamic Library with Import Library](#approach-2-dynamic-library-with-import-library)
- [Approach 3: Dynamic Library without Import Library](#approach-3-dynamic-library-without-import-library)
- [Approach 4: Multi-Platform Static Library](#approach-4-multi-platform-static-library)
- [Manual DLL Loading at Runtime](#manual-dll-loading-at-runtime)
- [DLL Load Order and Dependencies](#dll-load-order-and-dependencies)
- [DLL Search Locations](#dll-search-locations)
- [Forward Declarations to Hide Third-Party Headers](#forward-declarations-to-hide-third-party-headers)
- [Multi-Module Architecture](#multi-module-architecture)

---

## Approach 1: Static Library

The simplest approach. Library code is compiled directly into the executable. No DLL distribution needed.

**Build.cs:**
```csharp
using System.IO;
using UnrealBuildTool;

public class MyPlugin : ModuleRules
{
    public MyPlugin(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject" });

        PublicAdditionalLibraries.Add(
            Path.Combine(ModuleDirectory, "..", "ThirdParty", "mylib.lib"));

        PublicIncludePaths.Add(
            Path.Combine(ModuleDirectory, "..", "ThirdParty", "include"));
    }
}
```

**When to use:**
- Library is small or medium-sized
- You want a single executable with no DLL distribution concerns
- The library provides static `.lib` / `.a` files
- You control the library build and can compile for Release/x64

---

## Approach 2: Dynamic Library with Import Library

Uses a `.lib` import library at compile time for symbol resolution. The `.dll` is loaded at runtime.

**Build.cs:**
```csharp
using System.IO;
using UnrealBuildTool;

public class MyPlugin : ModuleRules
{
    public MyPlugin(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Projects" });

        // Import library for compile-time symbol resolution
        PublicAdditionalLibraries.Add(
            Path.Combine(ModuleDirectory, "..", "ThirdParty", "mylib.lib"));

        // Stage DLL alongside executable
        RuntimeDependencies.Add("$(PluginDir)/ThirdParty/mylib.dll");

        // Enable Windows delay-loading
        PublicDelayLoadDLLs.Add("mylib.dll");
    }
}
```

**Module startup (load DLL):**
```cpp
#include "Interfaces/IPluginManager.h"

void FMyPluginModule::StartupModule()
{
    const FString BaseDir = IPluginManager::Get().FindPlugin("MyPlugin")->GetBaseDir();
    const FString LibPath = FPaths::Combine(*BaseDir, TEXT("Source/ThirdParty/mylib.dll"));

    DllHandle = FPlatformProcess::GetDllHandle(*LibPath);
    if (!DllHandle)
    {
        UE_LOG(LogTemp, Fatal, TEXT("Failed to load mylib.dll from %s"), *LibPath);
    }
}

void FMyPluginModule::ShutdownModule()
{
    if (DllHandle)
    {
        FPlatformProcess::FreeDllHandle(DllHandle);
        DllHandle = nullptr;
    }
}
```

**Module header:**
```cpp
class FMyPluginModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;
private:
    void* DllHandle = nullptr;
};
```

**When to use:**
- Library is only available as DLL
- You want smaller executable size (DLL loaded separately)
- Library has a proper import library (`.lib` on Windows)

**Important:** Requires `"Projects"` module dependency for `IPluginManager`.

---

## Approach 3: Dynamic Library without Import Library

When no import library exists, you must resolve function pointers manually at runtime using `FPlatformProcess::GetDllExport()`.

**Build.cs:**
```csharp
using UnrealBuildTool;

public class MyPlugin : ModuleRules
{
    public MyPlugin(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Projects" });

        // Only RuntimeDependencies -- no import lib, no delay-load
        RuntimeDependencies.Add("$(PluginDir)/ThirdParty/mylib.dll");
    }
}
```

**Function export macro:**
```cpp
// Macro to look up and call exported functions by name
#define CALL_MYLIB_FUNC(FunctionName) \
    []() { \
        using FuncType = decltype(&FunctionName); \
        const FName ModuleName(TEXT("MyPlugin")); \
        const FMyPluginModule& Module = \
            FModuleManager::GetModuleChecked<FMyPluginModule>(ModuleName); \
        static FuncType FuncPtr = (FuncType)( \
            FPlatformProcess::GetDllExport(Module.DllHandle, TEXT(#FunctionName))); \
        return FuncPtr; \
    }()

// Usage:
bool Result = CALL_MYLIB_FUNC(getInvertedBool)(true);
```

**When to use:**
- Library only provides a DLL with no import library
- C-style exported functions (`extern "C" __declspec(dllexport)`)
- You need maximum control over function loading

---

## Approach 4: Multi-Platform Static Library

Selects the correct library per target platform at build time:

```csharp
using System.IO;
using UnrealBuildTool;

public class MyPlugin : ModuleRules
{
    private string GetLibraryPath(ReadOnlyTargetRules Target)
    {
        string ThirdParty = Path.Combine(ModuleDirectory, "..", "ThirdParty");
        if (Target.Platform == UnrealTargetPlatform.Win64)
            return Path.Combine(ThirdParty, "lib_win64.lib");
        if (Target.Platform == UnrealTargetPlatform.Linux)
            return Path.Combine(ThirdParty, "libmylib_linux.a");
        if (Target.Platform == UnrealTargetPlatform.Mac)
            return Path.Combine(ThirdParty, "libmylib_mac.a");
        return null;
    }

    public MyPlugin(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });

        string LibPath = GetLibraryPath(Target);
        if (LibPath != null)
        {
            PublicAdditionalLibraries.Add(LibPath);
        }
    }
}
```

---

## Manual DLL Loading at Runtime

For cases where DLLs are in non-standard locations or must be loaded in a specific order:

```cpp
void FMyModule::StartupModule()
{
    // DLLs must be loaded in dependency order
    const FString DLLs[] = {
        "dependency_a.dll",
        "dependency_b.dll",
        "main_library.dll"
    };

    FString SearchDir = FPaths::Combine(
        IPluginManager::Get().FindPlugin("MyPlugin")->GetBaseDir(),
        TEXT("Binaries/ThirdParty/Win64"));

    for (const FString& DLL : DLLs)
    {
        FString FullPath = FPaths::Combine(SearchDir, DLL);
        void* Handle = FPlatformProcess::GetDllHandle(*FullPath);
        if (!Handle)
        {
            UE_LOG(LogTemp, Error, TEXT("Failed to load %s"), *FullPath);
        }
        DllHandles.Add(Handle);
    }
}

void FMyModule::ShutdownModule()
{
    // Free in reverse order
    for (int32 i = DllHandles.Num() - 1; i >= 0; --i)
    {
        if (DllHandles[i])
        {
            FPlatformProcess::FreeDllHandle(DllHandles[i]);
        }
    }
    DllHandles.Empty();
}
```

## DLL Load Order and Dependencies

**Critical rule:** Dependencies must be loaded before the libraries that depend on them. For example, if `main.dll` depends on `utils.dll` and `math.dll`, load `utils.dll` and `math.dll` first.

To diagnose load failures:
- **Windows:** Check the debugger's `dli->szDLL` variable during delay-load exceptions to see which DLL failed
- **`FPlatformProcess::GetDllHandle()`** produces verbose log output on failure -- check the UE log

## DLL Search Locations

UE automatically searches these directories when loading DLLs:
- Engine's `Binaries/Win64/`
- Project's `Binaries/Win64/`
- Each plugin's `Binaries/Win64/`

It does **NOT** search `ThirdParty/` subdirectories by default. To load from custom paths, use `FPlatformProcess::GetDllHandle()` with the full path before any library functions are called.

## RuntimeDependencies: Copy vs Stage

**Single-argument form** (stages an existing file from the specified location):
```csharp
RuntimeDependencies.Add(Path.Combine(PluginDirectory, "Binaries/Win64/Foo.dll"));
```

**Two-argument form** (copies source to destination at build time):
```csharp
RuntimeDependencies.Add(
    "$(TargetOutputDir)/Foo.dll",                              // destination
    Path.Combine(PluginDirectory, "Source/ThirdParty/Foo.dll") // source
);
```

The two-argument form is particularly useful when DLLs live in a `Source/ThirdParty/` directory but need to be alongside the executable. It copies the file during the build, ensuring the DLL is always where the OS expects it.

## Build-Time DLL Copying Pattern

Some projects copy DLLs to the project's Binaries directory during build rather than relying solely on RuntimeDependencies:

```csharp
if (Target.Platform == UnrealTargetPlatform.Win64)
{
    string DllSource = Path.Combine(ThirdPartyPath, "lib", "Win64", "mylib.dll");
    string BinariesDir = Path.Combine(ModuleDirectory, "..", "..", "Binaries", "Win64");

    if (!Directory.Exists(BinariesDir))
        Directory.CreateDirectory(BinariesDir);

    File.Copy(DllSource, Path.Combine(BinariesDir, "mylib.dll"), overwrite: true);

    PublicAdditionalLibraries.Add(Path.Combine(ThirdPartyPath, "lib", "Win64", "mylib.lib"));
    RuntimeDependencies.Add(Path.Combine(BinariesDir, "mylib.dll"));
    PublicDelayLoadDLLs.Add("mylib.dll");
}
```

## Forward Declarations to Hide Third-Party Headers

To avoid exposing third-party headers to consuming modules, use forward declarations in your plugin's public header:

```cpp
// MyPluginPublic.h -- no #include of third-party headers here
namespace ThirdPartyLib {
class SomeClass; // Forward declaration only
}

class MYPLUGIN_API FMyWrapper
{
public:
    void Initialize(const FString& Config);
    FString DoWork(const FString& Input) const;

private:
    TUniquePtr<ThirdPartyLib::SomeClass> Instance;
};
```

The actual `#include` of third-party headers goes only in the `.cpp` file:
```cpp
// MyPluginPublic.cpp
THIRD_PARTY_INCLUDES_START
#include <thirdpartylib/SomeClass.h>
THIRD_PARTY_INCLUDES_END
```

**String conversions** at the UE/third-party boundary:
```cpp
// FString -> std::string (UTF-8)
std::string StdStr = TCHAR_TO_UTF8(*MyFString);

// std::string -> FString
FString UEStr = UTF8_TO_TCHAR(StdStr.c_str());
```

## Multi-Module Architecture

For complex libraries with many dependencies, use a layered architecture:

```
Plugin/
  Source/
    ThirdParty/
      MyExternalLib.Build.cs      # ModuleType.External -- headers + libs
    MyPlugin/
      MyPlugin.Build.cs           # Runtime module, depends on MyExternalLib
    MyPluginEditor/
      MyPluginEditor.Build.cs     # Editor module, depends on MyPlugin
```

**Dependency chain:** `MyPluginEditor` --> `MyPlugin` --> `MyExternalLib` (External)

This keeps the third-party library isolated. Only `MyPlugin` touches the library headers directly. `MyPluginEditor` and other consumers interact through `MyPlugin`'s public API.
