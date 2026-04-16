# Integrating llama.cpp with Unreal Engine 5.x

A comprehensive guide to running local LLM inference inside Unreal Engine projects using llama.cpp, covering plugin-based, custom C++, and HTTP server approaches.

## Table of Contents

- [1. Integration Options Overview](#1-integration-options-overview)
- [2. Llama-Unreal Plugin (Recommended)](#2-llama-unreal-plugin-recommended)
- [3. Custom C++ Integration (Build llama.cpp as Static Library for UE)](#3-custom-c-integration-build-llamacpp-as-static-library-for-ue)
  - [3.1 Build llama.cpp as Static Library](#31-build-llamacpp-as-static-library)
  - [3.2 Create External Module in UE Plugin](#32-create-external-module-in-ue-plugin)
  - [3.3 LlamaCpp.Build.cs](#33-llamacppbuildcs)
  - [3.4 Consumer Module Build.cs](#34-consumer-module-buildcs)
  - [3.5 Wrapper Class Pattern](#35-wrapper-class-pattern)
- [4. HTTP Server Approach (Decoupled)](#4-http-server-approach-decoupled)
- [5. Performance Considerations in UE](#5-performance-considerations-in-ue)
- [6. Common Pitfalls](#6-common-pitfalls)
- [7. Use Cases in Games](#7-use-cases-in-games)

---

## 1. Integration Options Overview

| Approach | Complexity | Features | Maintenance |
|---|---|---|---|
| **Llama-Unreal plugin (getnamo)** | Low | Full Blueprint + C++, streaming, multimodal, GPU offload | Active, MIT licensed |
| **UELlama plugin (mika314)** | Low | Basic text generation, Blueprint nodes | Less active |
| **Custom C++ integration** | High | Full control over build, API, and threading | Self-maintained |
| **HTTP server + REST calls** | Medium | Decoupled architecture, no native linking | Easy to maintain |
| **AI Chat Plus (Marketplace)** | Low | Multi-provider (OpenAI, Claude, local LLM) | Commercial, vendor-supported |

**Recommendation:** Use the Llama-Unreal plugin for most projects. Fall back to custom C++ integration only when you need fine-grained control over the inference pipeline, custom sampling strategies, or need to embed llama.cpp in a shipping title without plugin dependencies. The HTTP server approach is ideal for prototyping or when inference runs on a separate machine.

---

## 2. Llama-Unreal Plugin (Recommended)

**Repository:** <https://github.com/getnamo/Llama-Unreal>
**License:** MIT
**llama.cpp version:** tag b8586
**Engine support:** UE 5.3 -- 5.5+ (check releases for your version)

### Setup

1. Download the latest release from the GitHub Releases page.
2. Extract and copy the `Plugins/` folder into your project root so the path is `YourProject/Plugins/LlamaUnreal/`.
3. Regenerate project files and rebuild.
4. Place a GGUF model file somewhere accessible (e.g., `YourProject/Content/Models/`).

### Core API

The plugin exposes two primary types:

- **`ULlamaComponent`** -- An ActorComponent you attach to any Actor. This is the main interface for Blueprint users.
- **`ULlamaSubsystem`** -- A GameInstanceSubsystem for global access without needing a specific Actor.

### Blueprint Usage

```
// In Blueprint:
// 1. Add LlamaComponent to your Actor
// 2. Set PathToModel to your .gguf file
// 3. Call "Send Message" with a prompt string
// 4. Bind to "On Response" delegate for streaming tokens
```

### C++ Usage

```cpp
#include "LlamaComponent.h"

void AMyActor::BeginPlay()
{
    Super::BeginPlay();

    ULlamaComponent* Llama = FindComponentByClass<ULlamaComponent>();
    if (Llama)
    {
        Llama->PathToModel = TEXT("/Game/Models/my-model-q4_k_m.gguf");
        Llama->SystemPrompt = TEXT("You are a helpful NPC shopkeeper in a medieval fantasy world.");
        Llama->MaxContextLength = 4096;
        Llama->GPULayers = 33; // -1 for all layers on GPU

        Llama->OnResponseFinished.AddDynamic(this, &AMyActor::OnLlamaResponse);
        Llama->SendMessage(TEXT("What potions do you have for sale today?"));
    }
}

void AMyActor::OnLlamaResponse(const FString& Response)
{
    UE_LOG(LogTemp, Log, TEXT("LLM Response: %s"), *Response);
}
```

### Key Settings

| Setting | Default | Description |
|---|---|---|
| `PathToModel` | (empty) | Absolute or project-relative path to a `.gguf` model file |
| `SystemPrompt` | (empty) | System message prepended to every conversation |
| `MaxContextLength` | 4096 | Maximum token context window size |
| `GPULayers` | -1 | Number of layers to offload to GPU (-1 = all) |
| `Temperature` | 0.8 | Sampling temperature |
| `TopP` | 0.95 | Nucleus sampling threshold |
| `MinP` | 0.05 | MinP sampling threshold |
| `MirostatMode` | 0 | 0 = disabled, 1 = Mirostat, 2 = Mirostat 2.0 |

### Features

- **Streaming responses:** Tokens arrive via delegate as they are generated, enabling real-time text display.
- **Chat history:** Automatic KV cache management with conversation history.
- **Jinja templates:** Chat template support for instruction-tuned models.
- **Multimodal (mtmd):** Vision and audio input support for multimodal models (LLaVA, etc.).
- **Sampling options:** MinP, Mirostat, Top-K, Top-P, Temperature, Repeat penalty.
- **GPU backends (Windows):** Vulkan (default), CUDA (requires CUDA toolkit), CPU fallback.

---

## 3. Custom C++ Integration (Build llama.cpp as Static Library for UE)

Use this approach when you need full control over the llama.cpp build, want to ship without plugin dependencies, or need to customize the inference pipeline.

### 3.1 Build llama.cpp as Static Library

Clone and build llama.cpp as a set of static libraries that UE can link against.

**Windows (MSVC):**

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build -G "Visual Studio 17 2022" \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DLLAMA_BUILD_SERVER=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_TOOLS=OFF \
    -DLLAMA_BUILD_EXAMPLES=OFF \
    -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL
cmake --build build --config Release
```

**Linux:**

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DLLAMA_BUILD_SERVER=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_TOOLS=OFF \
    -DLLAMA_BUILD_EXAMPLES=OFF
cmake --build build --config Release
```

**macOS (Apple Silicon with Metal):**

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DGGML_METAL=ON \
    -DLLAMA_BUILD_SERVER=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_TOOLS=OFF \
    -DLLAMA_BUILD_EXAMPLES=OFF
cmake --build build --config Release
```

**Output files (Windows):** After building, collect these from `build/src/Release/` and `build/ggml/src/Release/`:
- `llama.lib`
- `ggml.lib`
- `ggml-base.lib`
- `ggml-cpu.lib`
- (optional) `ggml-vulkan.lib`, `ggml-cuda.lib`, `ggml-metal.lib`

**Output files (Linux/macOS):** Corresponding `.a` files from `build/src/` and `build/ggml/src/`.

### 3.2 Create External Module in UE Plugin

Organize the plugin with a ThirdParty external module for the prebuilt libraries and a runtime module for the UE wrapper code.

```
MyLlamaPlugin/
  MyLlamaPlugin.uplugin
  Source/
    ThirdParty/
      LlamaCpp/
        LlamaCpp.Build.cs
        include/
          llama.h
          llama-cpp.h
          ggml.h
          ggml-alloc.h
          ggml-backend.h
        lib/
          Win64/
            llama.lib
            ggml.lib
            ggml-base.lib
            ggml-cpu.lib
          Linux/
            libllama.a
            libggml.a
            libggml-base.a
            libggml-cpu.a
          Mac/
            libllama.a
            libggml.a
            libggml-base.a
            libggml-cpu.a
    MyLlamaPlugin/
      MyLlamaPlugin.Build.cs
      Public/
        LlamaInference.h
      Private/
        LlamaInference.cpp
        MyLlamaPluginModule.cpp
```

### 3.3 LlamaCpp.Build.cs

This is the External module that tells UBT how to find the headers and link the static libraries.

```csharp
using UnrealBuildTool;
using System.IO;

public class LlamaCpp : ModuleRules
{
    public LlamaCpp(ReadOnlyTargetRules Target) : base(Target)
    {
        Type = ModuleType.External;

        string ThirdPartyPath = ModuleDirectory;
        string IncludePath = Path.Combine(ThirdPartyPath, "include");
        string LibPath = Path.Combine(ThirdPartyPath, "lib");

        PublicIncludePaths.Add(IncludePath);

        // Suppress warnings from third-party headers
        PublicDefinitions.Add("THIRD_PARTY_INCLUDES_START=THIRD_PARTY_INCLUDES_START");
        PublicDefinitions.Add("THIRD_PARTY_INCLUDES_END=THIRD_PARTY_INCLUDES_END");

        if (Target.Platform == UnrealTargetPlatform.Win64)
        {
            string PlatformLibPath = Path.Combine(LibPath, "Win64");

            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "llama.lib"));
            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "ggml.lib"));
            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "ggml-base.lib"));
            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "ggml-cpu.lib"));

            // Uncomment for Vulkan GPU support:
            // PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "ggml-vulkan.lib"));

            // Uncomment for CUDA GPU support:
            // PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "ggml-cuda.lib"));
        }
        else if (Target.Platform == UnrealTargetPlatform.Linux)
        {
            string PlatformLibPath = Path.Combine(LibPath, "Linux");

            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "libllama.a"));
            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "libggml.a"));
            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "libggml-base.a"));
            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "libggml-cpu.a"));
        }
        else if (Target.Platform == UnrealTargetPlatform.Mac)
        {
            string PlatformLibPath = Path.Combine(LibPath, "Mac");

            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "libllama.a"));
            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "libggml.a"));
            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "libggml-base.a"));
            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "libggml-cpu.a"));

            // Metal backend for Apple Silicon
            PublicAdditionalLibraries.Add(Path.Combine(PlatformLibPath, "libggml-metal.a"));
            PublicFrameworks.Add("Metal");
            PublicFrameworks.Add("MetalKit");
            PublicFrameworks.Add("Foundation");
        }
    }
}
```

### 3.4 Consumer Module Build.cs

The runtime plugin module that contains your wrapper code adds the external module as a dependency.

```csharp
using UnrealBuildTool;

public class MyLlamaPlugin : ModuleRules
{
    public MyLlamaPlugin(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "LlamaCpp"   // The external module from Section 3.3
        });

        // llama.cpp uses a C API, so RTTI and exceptions are generally not needed.
        // Uncomment only if you get linker errors related to typeinfo or exception handling:
        // bUseRTTI = true;
        // bEnableExceptions = true;
    }
}
```

### 3.5 Wrapper Class Pattern

A UObject-based wrapper that loads the model asynchronously and performs inference off the game thread.

**LlamaInference.h:**

```cpp
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"

THIRD_PARTY_INCLUDES_START
#include "llama.h"
THIRD_PARTY_INCLUDES_END

#include "LlamaInference.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnTokenGenerated, const FString&, Token);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnInferenceComplete, const FString&, FullResponse);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnModelLoaded);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnInferenceError, const FString&, ErrorMessage);

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class MYLLAMAPLUGIN_API ULlamaInference : public UActorComponent
{
    GENERATED_BODY()

public:
    ULlamaInference();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    /** Path to the GGUF model file (absolute or project-relative). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Llama")
    FString ModelPath;

    /** Number of GPU layers to offload. 0 = CPU only, -1 = all layers. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Llama")
    int32 GPULayers = 0;

    /** Maximum context length in tokens. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Llama")
    int32 MaxContextLength = 2048;

    /** Maximum tokens to generate per inference call. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Llama")
    int32 MaxTokens = 256;

    /** Sampling temperature. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Llama",
        meta = (ClampMin = "0.0", ClampMax = "2.0"))
    float Temperature = 0.8f;

    /** Load the model asynchronously. Fires OnModelLoaded when ready. */
    UFUNCTION(BlueprintCallable, Category = "Llama")
    void LoadModelAsync();

    /** Run inference on the given prompt. Results stream via delegates. */
    UFUNCTION(BlueprintCallable, Category = "Llama")
    void GenerateAsync(const FString& Prompt);

    /** Check if the model is currently loaded and ready. */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Llama")
    bool IsModelLoaded() const { return bModelLoaded; }

    /** Check if inference is currently running. */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Llama")
    bool IsGenerating() const { return bIsGenerating; }

    /** Fired for each generated token (streaming). */
    UPROPERTY(BlueprintAssignable, Category = "Llama")
    FOnTokenGenerated OnTokenGenerated;

    /** Fired when the full response is complete. */
    UPROPERTY(BlueprintAssignable, Category = "Llama")
    FOnInferenceComplete OnInferenceComplete;

    /** Fired when the model finishes loading. */
    UPROPERTY(BlueprintAssignable, Category = "Llama")
    FOnModelLoaded OnModelLoaded;

    /** Fired on any error. */
    UPROPERTY(BlueprintAssignable, Category = "Llama")
    FOnInferenceError OnInferenceError;

private:
    llama_model* Model = nullptr;
    llama_context* Context = nullptr;
    llama_sampler* Sampler = nullptr;

    TAtomic<bool> bModelLoaded{false};
    TAtomic<bool> bIsGenerating{false};

    void CleanupLlama();
};
```

**LlamaInference.cpp:**

```cpp
#include "LlamaInference.h"
#include "Async/Async.h"
#include "Misc/Paths.h"

THIRD_PARTY_INCLUDES_START
#include "llama.h"
THIRD_PARTY_INCLUDES_END

ULlamaInference::ULlamaInference()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void ULlamaInference::BeginPlay()
{
    Super::BeginPlay();
}

void ULlamaInference::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    CleanupLlama();
    Super::EndPlay(EndPlayReason);
}

void ULlamaInference::LoadModelAsync()
{
    if (bModelLoaded || ModelPath.IsEmpty())
    {
        return;
    }

    // Resolve project-relative paths
    FString ResolvedPath = ModelPath;
    if (FPaths::IsRelativePath(ResolvedPath))
    {
        ResolvedPath = FPaths::Combine(FPaths::ProjectDir(), ResolvedPath);
    }
    ResolvedPath = FPaths::ConvertRelativePathToFull(ResolvedPath);

    // Capture values for the async lambda
    int32 LocalGPULayers = GPULayers;
    int32 LocalMaxContext = MaxContextLength;
    float LocalTemperature = Temperature;

    AsyncTask(ENamedThreads::AnyBackgroundThreadNormalTask,
        [this, ResolvedPath, LocalGPULayers, LocalMaxContext, LocalTemperature]()
    {
        // Initialize llama backend (safe to call multiple times)
        llama_backend_init();

        // Load model
        llama_model_params ModelParams = llama_model_default_params();
        ModelParams.n_gpu_layers = LocalGPULayers;

        std::string PathUtf8 = TCHAR_TO_UTF8(*ResolvedPath);
        llama_model* LoadedModel =
            llama_model_load_from_file(PathUtf8.c_str(), ModelParams);

        if (!LoadedModel)
        {
            AsyncTask(ENamedThreads::GameThread, [this]()
            {
                OnInferenceError.Broadcast(TEXT("Failed to load model file."));
            });
            return;
        }

        // Create context
        llama_context_params CtxParams = llama_context_default_params();
        CtxParams.n_ctx = LocalMaxContext;
        CtxParams.n_batch = 512;

        llama_context* LoadedContext =
            llama_context_new(LoadedModel, CtxParams);

        if (!LoadedContext)
        {
            llama_model_free(LoadedModel);
            AsyncTask(ENamedThreads::GameThread, [this]()
            {
                OnInferenceError.Broadcast(
                    TEXT("Failed to create llama context."));
            });
            return;
        }

        // Create sampler chain
        llama_sampler* LoadedSampler = llama_sampler_chain_init(
            llama_sampler_chain_default_params());
        llama_sampler_chain_add(LoadedSampler,
            llama_sampler_init_temp(LocalTemperature));
        llama_sampler_chain_add(LoadedSampler,
            llama_sampler_init_dist(LLAMA_DEFAULT_SEED));

        // Store on game thread
        AsyncTask(ENamedThreads::GameThread,
            [this, LoadedModel, LoadedContext, LoadedSampler]()
        {
            Model = LoadedModel;
            Context = LoadedContext;
            Sampler = LoadedSampler;
            bModelLoaded = true;
            OnModelLoaded.Broadcast();
        });
    });
}

void ULlamaInference::GenerateAsync(const FString& Prompt)
{
    if (!bModelLoaded || bIsGenerating)
    {
        OnInferenceError.Broadcast(
            TEXT("Model not loaded or inference already in progress."));
        return;
    }

    bIsGenerating = true;

    // Capture raw pointers and settings
    llama_model* LocalModel = Model;
    llama_context* LocalContext = Context;
    llama_sampler* LocalSampler = Sampler;
    int32 LocalMaxTokens = MaxTokens;
    FString PromptCopy = Prompt;

    AsyncTask(ENamedThreads::AnyBackgroundThreadNormalTask,
        [this, LocalModel, LocalContext, LocalSampler,
         LocalMaxTokens, PromptCopy]()
    {
        // Tokenize the prompt
        std::string PromptUtf8 = TCHAR_TO_UTF8(*PromptCopy);
        const int MaxTokensBuf = PromptUtf8.length() + 128;
        TArray<llama_token> Tokens;
        Tokens.SetNum(MaxTokensBuf);

        const llama_vocab* Vocab = llama_model_get_vocab(LocalModel);
        int32 NumTokens = llama_tokenize(
            Vocab,
            PromptUtf8.c_str(),
            PromptUtf8.length(),
            Tokens.GetData(),
            MaxTokensBuf,
            true,   // add_special (BOS)
            true    // parse_special
        );

        if (NumTokens < 0)
        {
            AsyncTask(ENamedThreads::GameThread, [this]()
            {
                bIsGenerating = false;
                OnInferenceError.Broadcast(TEXT("Tokenization failed."));
            });
            return;
        }

        Tokens.SetNum(NumTokens);

        // Create a batch and evaluate the prompt
        llama_batch Batch = llama_batch_get_one(
            Tokens.GetData(), NumTokens);
        if (llama_decode(LocalContext, Batch) != 0)
        {
            AsyncTask(ENamedThreads::GameThread, [this]()
            {
                bIsGenerating = false;
                OnInferenceError.Broadcast(
                    TEXT("Failed to evaluate prompt."));
            });
            return;
        }

        // Generate tokens one at a time
        FString FullResponse;
        char TokenTextBuf[128];

        for (int32 i = 0; i < LocalMaxTokens; ++i)
        {
            llama_token NewToken = llama_sampler_sample(
                LocalSampler, LocalContext, -1);

            // Check for end of generation
            if (llama_vocab_is_eog(Vocab, NewToken))
            {
                break;
            }

            // Convert token to text
            int32 TextLen = llama_token_to_piece(
                Vocab, NewToken, TokenTextBuf,
                sizeof(TokenTextBuf), 0, true);
            if (TextLen > 0)
            {
                TokenTextBuf[TextLen] = '\0';
                FString TokenStr = UTF8_TO_TCHAR(TokenTextBuf);
                FullResponse += TokenStr;

                // Stream the token back to the game thread
                AsyncTask(ENamedThreads::GameThread,
                    [this, TokenStr]()
                {
                    OnTokenGenerated.Broadcast(TokenStr);
                });
            }

            // Prepare the next batch with the sampled token
            Batch = llama_batch_get_one(&NewToken, 1);
            if (llama_decode(LocalContext, Batch) != 0)
            {
                break;
            }
        }

        // Signal completion on game thread
        AsyncTask(ENamedThreads::GameThread,
            [this, FullResponse]()
        {
            bIsGenerating = false;
            OnInferenceComplete.Broadcast(FullResponse);
        });
    });
}

void ULlamaInference::CleanupLlama()
{
    // Wait for any in-flight generation to finish
    // In production, use a cancellation token instead of spinning
    while (bIsGenerating)
    {
        FPlatformProcess::Sleep(0.01f);
    }

    if (Sampler)
    {
        llama_sampler_free(Sampler);
        Sampler = nullptr;
    }
    if (Context)
    {
        llama_context_free(Context);
        Context = nullptr;
    }
    if (Model)
    {
        llama_model_free(Model);
        Model = nullptr;
    }

    bModelLoaded = false;
    llama_backend_free();
}
```

**Example usage in an Actor:**

```cpp
void AMyNPC::BeginPlay()
{
    Super::BeginPlay();

    LlamaComp = NewObject<ULlamaInference>(this);
    LlamaComp->ModelPath =
        TEXT("Content/Models/mistral-7b-instruct-q4_k_m.gguf");
    LlamaComp->GPULayers = 20;
    LlamaComp->MaxContextLength = 2048;
    LlamaComp->MaxTokens = 128;
    LlamaComp->Temperature = 0.7f;
    LlamaComp->RegisterComponent();

    LlamaComp->OnModelLoaded.AddDynamic(this, &AMyNPC::OnModelReady);
    LlamaComp->OnInferenceComplete.AddDynamic(
        this, &AMyNPC::OnDialogueGenerated);
    LlamaComp->LoadModelAsync();
}

void AMyNPC::OnModelReady()
{
    UE_LOG(LogTemp, Log,
        TEXT("LLM model loaded and ready for inference."));
}

void AMyNPC::OnDialogueGenerated(const FString& Response)
{
    DialogueWidget->SetText(FText::FromString(Response));
}

void AMyNPC::PlayerInteracted(const FString& PlayerDialogue)
{
    FString Prompt = FString::Printf(
        TEXT("<|im_start|>system\n"
             "You are a blacksmith NPC. "
             "Keep responses under 2 sentences.<|im_end|>\n"
             "<|im_start|>user\n%s<|im_end|>\n"
             "<|im_start|>assistant\n"),
        *PlayerDialogue
    );
    LlamaComp->GenerateAsync(Prompt);
}
```

---

## 4. HTTP Server Approach (Decoupled)

Run `llama-server` as a standalone process and communicate with it from UE via HTTP. This avoids all native linking complexity.

### Starting the Server

```bash
# Build llama-server (or download a prebuilt release)
./llama-server \
    --model path/to/model.gguf \
    --host 127.0.0.1 \
    --port 8080 \
    --n-gpu-layers 33 \
    --ctx-size 4096
```

### UE HTTP Client

```cpp
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"

void UMyLlamaHttpClient::SendChatCompletion(const FString& UserMessage)
{
    FHttpModule& Http = FHttpModule::Get();
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request =
        Http.CreateRequest();

    Request->SetURL(TEXT("http://127.0.0.1:8080/v1/chat/completions"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));

    // Build JSON body
    TSharedPtr<FJsonObject> Body = MakeShareable(new FJsonObject());
    Body->SetStringField(TEXT("model"), TEXT("local-model"));
    Body->SetNumberField(TEXT("max_tokens"), 256);
    Body->SetNumberField(TEXT("temperature"), 0.8);

    TArray<TSharedPtr<FJsonValue>> Messages;

    TSharedPtr<FJsonObject> SystemMsg = MakeShareable(new FJsonObject());
    SystemMsg->SetStringField(TEXT("role"), TEXT("system"));
    SystemMsg->SetStringField(TEXT("content"),
        TEXT("You are a helpful NPC."));
    Messages.Add(MakeShareable(new FJsonValueObject(SystemMsg)));

    TSharedPtr<FJsonObject> UserMsg = MakeShareable(new FJsonObject());
    UserMsg->SetStringField(TEXT("role"), TEXT("user"));
    UserMsg->SetStringField(TEXT("content"), UserMessage);
    Messages.Add(MakeShareable(new FJsonValueObject(UserMsg)));

    Body->SetArrayField(TEXT("messages"), Messages);

    FString BodyString;
    TSharedRef<TJsonWriter<>> Writer =
        TJsonWriterFactory<>::Create(&BodyString);
    FJsonSerializer::Serialize(Body.ToSharedRef(), Writer);
    Request->SetContentAsString(BodyString);

    Request->OnProcessRequestComplete().BindLambda(
        [this](FHttpRequestPtr Req, FHttpResponsePtr Resp,
               bool bSuccess)
    {
        if (!bSuccess || !Resp.IsValid())
        {
            UE_LOG(LogTemp, Error,
                TEXT("HTTP request to llama-server failed."));
            return;
        }

        TSharedPtr<FJsonObject> JsonResponse;
        TSharedRef<TJsonReader<>> Reader =
            TJsonReaderFactory<>::Create(Resp->GetContentAsString());
        if (FJsonSerializer::Deserialize(Reader, JsonResponse))
        {
            const TArray<TSharedPtr<FJsonValue>>* Choices;
            if (JsonResponse->TryGetArrayField(TEXT("choices"), Choices)
                && Choices->Num() > 0)
            {
                TSharedPtr<FJsonObject> Choice =
                    (*Choices)[0]->AsObject();
                TSharedPtr<FJsonObject> Message =
                    Choice->GetObjectField(TEXT("message"));
                FString Content =
                    Message->GetStringField(TEXT("content"));

                UE_LOG(LogTemp, Log,
                    TEXT("LLM Response: %s"), *Content);
                OnResponseReceived.Broadcast(Content);
            }
        }
    });

    Request->ProcessRequest();
}
```

### Advantages

- No native compilation or linking against llama.cpp.
- Model can be swapped by restarting the server -- no UE rebuild needed.
- Server can run on a separate machine or even a cloud GPU instance.
- The OpenAI-compatible API (`/v1/chat/completions`) means you can swap in any provider later.

### Disadvantages

- Requires starting and managing an external process.
- Network latency (even on localhost, typically 1-5ms overhead per request).
- Harder to ship as a self-contained game -- need to bundle and launch the server executable.
- Streaming requires SSE or WebSocket handling for real-time token delivery.

---

## 5. Performance Considerations in UE

### GPU Contention

When llama.cpp and Unreal Engine share the same GPU, expect inference throughput to drop to roughly **1/3 to 1/2 of standalone performance**. The renderer and the LLM compete for GPU memory bandwidth and compute units.

Mitigation strategies:

- **Use the Vulkan backend** for llama.cpp when UE is using DirectX 12 (Windows default). This reduces driver-level contention compared to running both workloads on the same graphics API.
- **Limit GPU layers** (`GPULayers`): offload fewer transformer layers to the GPU, using CPU for the rest. Start with 50% of layers on GPU and tune from there.
- **Use a dedicated GPU** for inference in multi-GPU setups. Set `CUDA_VISIBLE_DEVICES` or the Vulkan device index to target the non-rendering GPU.
- **Reduce context size**: smaller `n_ctx` values use less VRAM, leaving more for the renderer. 2048 is often sufficient for NPC dialogue.

### Threading

- **Never call llama_decode or llama_sampler_sample on the game thread.** These are blocking operations that can take hundreds of milliseconds to seconds. Always use `AsyncTask`, `FRunnable`, or the task graph.
- `llama_context` is **not thread-safe**. Do not share a single context across multiple threads. Use one context per inference thread, or protect access with a mutex/critical section.
- If you need concurrent inference (e.g., multiple NPCs generating simultaneously), create separate `llama_context` instances that share the same `llama_model`. The model itself is read-only after loading and can be shared across threads safely.

### Quantization for Real-Time Use

For in-game use where VRAM is shared with the renderer:

| Quantization | Quality | Size (7B model) | Recommended For |
|---|---|---|---|
| Q4_K_M | Good | ~4.1 GB | Best balance for in-game use |
| Q4_K_S | Good | ~3.9 GB | Tight VRAM budgets |
| Q5_K_M | Better | ~4.8 GB | When quality matters more |
| Q3_K_M | Acceptable | ~3.3 GB | Minimum viable for dialogue |
| Q8_0 | Excellent | ~7.2 GB | Development/testing only |

For shipping games, Q4_K_M on a 7B parameter model is the sweet spot between quality and resource usage.

### Memory Budget

Rule of thumb for VRAM allocation:

- Reserve **at least 2-4 GB** of VRAM for the UE renderer (more for high-fidelity scenes).
- A Q4_K_M 7B model with 2048 context uses roughly **4-5 GB** of VRAM when fully offloaded.
- On an 8 GB GPU, offload only 50-70% of layers and use CPU for the rest.
- On a 12+ GB GPU, full GPU offload of a 7B Q4_K_M model alongside UE rendering is feasible.

---

## 6. Common Pitfalls

### UE `check` Macro Conflict

Unreal Engine defines a `check()` macro globally. Some third-party headers (including ggml internals) may define or use identifiers that collide. Always wrap third-party includes:

```cpp
THIRD_PARTY_INCLUDES_START
#include "llama.h"
#include "ggml.h"
THIRD_PARTY_INCLUDES_END
```

These macros push/pop warning pragmas and `#undef` conflicting macros like `check` and `verify`.

### CRT Mismatch (Windows)

Unreal Engine links against the **dynamic** C runtime (`/MD` -- `MultiThreadedDLL`). If you build llama.cpp with `/MT` (static CRT), you will get linker errors or runtime crashes due to mismatched allocators.

Always build with:
```
-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL
```

Or equivalently in CMake presets:
```
CMAKE_MSVC_RUNTIME_LIBRARY: "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL"
```

### RTTI and Exceptions

The llama.cpp C API (`llama.h`) does not require RTTI or exceptions. However, if you include internal ggml headers or link against backends that use C++ features, you may need:

```csharp
// In your Build.cs
bUseRTTI = true;
bEnableExceptions = true;
```

Only enable these if you get specific linker errors about `__cxa_throw`, `typeinfo`, or similar symbols. Enabling them unnecessarily increases binary size.

### Thread Safety

- `llama_model`: **Thread-safe** for read operations after loading. Multiple contexts can share one model.
- `llama_context`: **NOT thread-safe**. Each thread needs its own context, or you must serialize access with a mutex.
- `llama_sampler`: **NOT thread-safe**. Create one per context/thread.

A common mistake is calling `GenerateAsync` from multiple places simultaneously with a shared context. Use a queue:

```cpp
// Simple inference queue pattern
FCriticalSection InferenceLock;

void ULlamaInference::GenerateAsync(const FString& Prompt)
{
    AsyncTask(ENamedThreads::AnyBackgroundThreadNormalTask,
        [this, Prompt]()
    {
        FScopeLock Lock(&InferenceLock);
        // Only one inference runs at a time
        RunInference(Prompt);
    });
}
```

### Blueprint Latency

Never expose synchronous inference to Blueprint. A single `llama_decode` call on a 7B model can block for 50ms to several seconds depending on prompt length and hardware. Always use:

- Async Blueprint nodes (via `UBlueprintAsyncActionBase`)
- Delegate/event-based callbacks
- Latent actions

```cpp
UCLASS()
class UAsyncGenerateText : public UBlueprintAsyncActionBase
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintAssignable)
    FOnInferenceComplete OnComplete;

    UPROPERTY(BlueprintAssignable)
    FOnInferenceError OnFailed;

    UFUNCTION(BlueprintCallable,
        meta = (BlueprintInternalUseOnly = "true",
                WorldContext = "WorldContextObject"))
    static UAsyncGenerateText* GenerateText(
        UObject* WorldContextObject,
        ULlamaInference* Inference,
        const FString& Prompt);

    virtual void Activate() override;
};
```

### Model File Distribution

GGUF model files are large (3-8 GB for 7B models). Do not check them into version control. Options:

- Download at first launch via HTTP and cache locally.
- Distribute as a separate download alongside the game.
- Use Git LFS if the team needs them in the repo.
- Store in a `Content/Models/` directory that is `.gitignore`-d.

---

## 7. Use Cases in Games

### NPC Dialogue Generation

The most common use case. Generate contextual, dynamic dialogue responses for NPCs based on player input, game state, and character personality.

```cpp
FString BuildNPCPrompt(const FString& NPCName,
                        const FString& Personality,
                        const FString& GameContext,
                        const FString& PlayerSaid)
{
    return FString::Printf(
        TEXT("<|im_start|>system\n"
             "You are %s, %s. "
             "Current situation: %s. "
             "Respond in character. Keep responses to 1-2 sentences. "
             "Never break character or mention being an AI."
             "<|im_end|>\n"
             "<|im_start|>user\n%s<|im_end|>\n"
             "<|im_start|>assistant\n"),
        *NPCName, *Personality, *GameContext, *PlayerSaid
    );
}
```

### Dynamic Narrative / Quest Generation

Generate quest descriptions, lore entries, or branching narrative text at runtime. Use structured output (JSON mode) to produce machine-parseable quest data:

```cpp
FString QuestGenPrompt = TEXT(
    "<|im_start|>system\n"
    "Generate a side quest in JSON format with fields: "
    "title, description, objective, reward_type, reward_amount. "
    "Setting: dark fantasy. Difficulty: medium.<|im_end|>\n"
    "<|im_start|>user\n"
    "The player is in a haunted village.<|im_end|>\n"
    "<|im_start|>assistant\n"
);
```

### Player Intent Recognition

Use a small model to classify player text input into game actions, enabling natural language commands:

```cpp
FString IntentPrompt = FString::Printf(
    TEXT("<|im_start|>system\n"
         "Classify the player's intent into exactly one of: "
         "ATTACK, TALK, TRADE, EXPLORE, REST, USE_ITEM, UNKNOWN. "
         "Respond with only the classification word.<|im_end|>\n"
         "<|im_start|>user\n%s<|im_end|>\n"
         "<|im_start|>assistant\n"),
    *PlayerInput
);
```

### Procedural Description Generation

Generate descriptions for procedurally created items, locations, or characters to add variety without hand-authoring thousands of text entries.

### Content Moderation

In multiplayer games, use a local model to screen player-generated text (chat, custom names, signs) before it is broadcast to other players. Avoids sending player content to external APIs.

### In-Game AI Assistants

Tutorial helpers, hint systems, or in-game encyclopedias that can answer contextual questions about game mechanics, lore, or the player's current situation using a locally-running model.
