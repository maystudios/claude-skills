# llama.cpp Build and Integration Guide

Comprehensive reference for building llama.cpp from source, enabling GPU backends, and integrating the library into your own CMake projects.

## Table of Contents

- [1. Prerequisites](#1-prerequisites)
- [2. Basic Build from Source](#2-basic-build-from-source)
- [3. GPU Backend Build Options](#3-gpu-backend-build-options)
- [4. All Key CMake Options](#4-all-key-cmake-options)
- [5. Integration Method 1: add_subdirectory (Embedding)](#5-integration-method-1-add_subdirectory-embedding)
- [6. Integration Method 2: find_package (After Install)](#6-integration-method-2-find_package-after-install)
- [7. Integration Method 3: Static Library with PIC](#7-integration-method-3-static-library-with-pic)
- [8. Package Manager Installation](#8-package-manager-installation)
- [9. Docker Images](#9-docker-images)
- [10. Cross-Compilation Notes](#10-cross-compilation-notes)
- [11. Runtime Backend Selection](#11-runtime-backend-selection)
- [12. Directory Structure After Build](#12-directory-structure-after-build)

---

## 1. Prerequisites

### Required

| Requirement | Minimum Version | Notes |
|---|---|---|
| CMake | 3.14+ | 3.21+ recommended for presets support |
| C++ compiler | C++17 capable | GCC 8+, Clang 7+, MSVC 2019+ (v142 toolset) |
| Git | Any recent | For cloning the repository |

### Optional (GPU acceleration)

| SDK | For Backend | Install Notes |
|---|---|---|
| CUDA Toolkit | NVIDIA GPUs | 11.7+ recommended; includes nvcc compiler |
| Vulkan SDK | Cross-platform GPU | Install from LunarG; set `VULKAN_SDK` env var |
| ROCm / HIP | AMD GPUs | 5.0+; install via AMD package repos |
| oneAPI / SYCL | Intel GPUs | Install Intel oneAPI Base Toolkit |
| Xcode Command Line Tools | Apple Metal | Included with macOS; Metal is auto-detected |
| MUSA Toolkit | Moore Threads GPUs | Vendor-provided SDK |
| CANN Toolkit | Huawei Ascend NPUs | Vendor-provided SDK |
| Android NDK | Android (Vulkan/OpenCL) | For cross-compilation to Android targets |

### Platform-specific notes

- **Windows**: Visual Studio 2019 or 2022 with "Desktop development with C++" workload. The MSVC compiler (`cl.exe`) must be on PATH, or use a Developer Command Prompt.
- **macOS**: Xcode Command Line Tools (`xcode-select --install`). Metal support is automatic on Apple Silicon and recent Intel Macs.
- **Linux**: `build-essential` (Debian/Ubuntu) or `gcc gcc-c++ make` (Fedora/RHEL). For GPU backends, install the corresponding SDK and ensure drivers are loaded.

---

## 2. Basic Build from Source

### Clone and build

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j $(nproc)
```

On Windows (cmd or PowerShell), replace `$(nproc)` with the number of CPU cores or use:

```powershell
cmake --build build --config Release -j %NUMBER_OF_PROCESSORS%
```

### Install to a custom prefix

```bash
cmake --install build --prefix /usr/local/llama-cpp
```

This installs headers, libraries, executables, and CMake package config files to the specified prefix directory.

### Quick verification

After building, verify the build succeeded by running:

```bash
# List built binaries
ls build/bin/

# Run the CLI with --help
./build/bin/llama-cli --help

# Run the server with --help
./build/bin/llama-server --help
```

### Debug build (for development)

```bash
cmake -B build-debug -DCMAKE_BUILD_TYPE=Debug
cmake --build build-debug --config Debug -j $(nproc)
```

### Minimal build (library only, no tools)

```bash
cmake -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLAMA_BUILD_TOOLS=OFF \
  -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_SERVER=OFF
cmake --build build --config Release -j $(nproc)
```

---

## 3. GPU Backend Build Options

### Backend reference table

| Backend | CMake Flag | Target Hardware | Notes |
|---|---|---|---|
| CUDA | `GGML_CUDA=ON` | NVIDIA GPUs (Kepler+) | Requires CUDA Toolkit; set `CMAKE_CUDA_ARCHITECTURES` for specific GPUs |
| Metal | Automatic on macOS | Apple Silicon / Intel Macs | Enabled by default when building on macOS; no flag needed |
| Vulkan | `GGML_VULKAN=ON` | Cross-platform (NVIDIA, AMD, Intel, mobile) | Requires Vulkan SDK; good cross-platform fallback |
| HIP / ROCm | `GGML_HIP=ON` | AMD GPUs (RDNA, CDNA) | Requires ROCm; set `AMDGPU_TARGETS` for specific architectures |
| SYCL | `GGML_SYCL=ON` | Intel GPUs (Arc, Data Center) | Requires Intel oneAPI toolkit |
| MUSA | `GGML_MUSA=ON` | Moore Threads GPUs | Requires MUSA toolkit from Moore Threads |
| CANN | `GGML_CANN=ON` | Huawei Ascend NPUs | Requires CANN toolkit |
| OpenCL | `GGML_OPENCL=ON` | Adreno GPUs, other OpenCL devices | Primarily targets Qualcomm Adreno on Android |
| WebGPU | `GGML_WEBGPU=ON` | Browser / Dawn / wgpu | For WebAssembly and native WebGPU runtimes |
| ZenDNN | `GGML_ZENDNN=ON` | AMD EPYC CPUs | Optimized CPU inference for AMD server CPUs |
| KleidiAI | `GGML_CPU_KLEIDIAI=ON` | ARM CPUs (SVE/SME) | Optimized kernels for ARM Neoverse and similar |

### CUDA build

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON
cmake --build build --config Release -j $(nproc)
```

To target specific NVIDIA GPU architectures (reduces compile time and binary size):

```bash
# Ampere (RTX 30xx, A100) + Ada Lovelace (RTX 40xx)
cmake -B build -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES="86;89"
cmake --build build --config Release -j $(nproc)
```

Common `CMAKE_CUDA_ARCHITECTURES` values:

| Architecture | Value | Example GPUs |
|---|---|---|
| Kepler | 35 | GTX 780, K80 |
| Pascal | 61 | GTX 1080, P40 |
| Volta | 70 | V100 |
| Turing | 75 | RTX 2080, T4 |
| Ampere | 86 | RTX 3090, A100 |
| Ada Lovelace | 89 | RTX 4090, L40 |
| Hopper | 90 | H100 |
| Blackwell | 100 | B200 |

### Vulkan build

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=ON
cmake --build build --config Release -j $(nproc)
```

On Windows, ensure the Vulkan SDK is installed and `VULKAN_SDK` is set:

```powershell
$env:VULKAN_SDK = "C:\VulkanSDK\1.3.xxx.x"
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=ON
cmake --build build --config Release
```

### HIP / ROCm build (AMD GPUs)

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release \
  -DGGML_HIP=ON \
  -DAMDGPU_TARGETS="gfx1100;gfx1030"
cmake --build build --config Release -j $(nproc)
```

Common `AMDGPU_TARGETS` values: `gfx906` (MI50), `gfx908` (MI100), `gfx90a` (MI210), `gfx1030` (RX 6800), `gfx1100` (RX 7900).

### SYCL build (Intel GPUs)

```bash
# Source the oneAPI environment first
source /opt/intel/oneapi/setvars.sh

cmake -B build -DCMAKE_BUILD_TYPE=Release \
  -DGGML_SYCL=ON \
  -DCMAKE_C_COMPILER=icx \
  -DCMAKE_CXX_COMPILER=icpx
cmake --build build --config Release -j $(nproc)
```

### Metal build (macOS)

Metal is automatically enabled on macOS. No special flags are needed:

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j $(sysctl -n hw.logicalcpu)
```

To explicitly disable Metal:

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_METAL=OFF
```

### Combined multi-backend build

You can enable multiple GPU backends simultaneously. The runtime will select the best available device:

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA=ON \
  -DGGML_VULKAN=ON
cmake --build build --config Release -j $(nproc)
```

This is useful for systems with multiple GPU vendors or for building a universal binary that works across different hardware configurations.

---

## 4. All Key CMake Options

### Build target options

| Option | Default | Description |
|---|---|---|
| `LLAMA_BUILD_SERVER` | `ON` | Build the `llama-server` HTTP server binary |
| `LLAMA_BUILD_TESTS` | `ON` | Build test executables |
| `LLAMA_BUILD_TOOLS` | `ON` | Build CLI tools (`llama-cli`, `llama-quantize`, `llama-bench`, etc.) |
| `LLAMA_BUILD_WEBUI` | `ON` | Bundle the web UI with `llama-server` (downloads at configure time) |
| `LLAMA_BUILD_COMMON` | `ON` | Build the `common` helper library (needed for tools and most integrations) |

### Library options

| Option | Default | Description |
|---|---|---|
| `BUILD_SHARED_LIBS` | `ON` | Build shared libraries (`.so`/`.dll`/`.dylib`). Set `OFF` for static libraries |
| `LLAMA_OPENSSL` | `OFF` | Enable HTTPS support in `llama-server` via OpenSSL |
| `CMAKE_POSITION_INDEPENDENT_CODE` | Varies | Enable `-fPIC` for static libs (required when embedding in shared libraries) |

### Backend and hardware options

| Option | Default | Description |
|---|---|---|
| `GGML_NATIVE` | `ON` | Enable native CPU optimizations (`-march=native`). Disable for portable binaries |
| `GGML_BACKEND_DL` | `OFF` | Build GPU backends as dynamically-loadable plugins (`.so`/`.dll`) instead of linking statically |
| `GGML_RPC` | `OFF` | Enable RPC backend for distributed inference across network nodes |
| `GGML_CUDA` | `OFF` | Enable NVIDIA CUDA backend |
| `GGML_VULKAN` | `OFF` | Enable Vulkan backend |
| `GGML_HIP` | `OFF` | Enable AMD HIP/ROCm backend |
| `GGML_SYCL` | `OFF` | Enable Intel SYCL backend |
| `GGML_METAL` | Auto | Enable Apple Metal backend (auto-detected on macOS) |
| `GGML_MUSA` | `OFF` | Enable Moore Threads MUSA backend |
| `GGML_CANN` | `OFF` | Enable Huawei Ascend CANN backend |
| `GGML_OPENCL` | `OFF` | Enable OpenCL backend |
| `GGML_WEBGPU` | `OFF` | Enable WebGPU backend |
| `GGML_ZENDNN` | `OFF` | Enable AMD ZenDNN optimizations |
| `GGML_CPU_KLEIDIAI` | `OFF` | Enable KleidiAI optimized kernels for ARM SVE/SME |
| `CMAKE_CUDA_ARCHITECTURES` | Auto | CUDA compute capability targets (e.g., `"86;89"`) |

### Example: fully customized build

```bash
cmake -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES="86;89" \
  -DGGML_NATIVE=OFF \
  -DLLAMA_BUILD_SERVER=ON \
  -DLLAMA_BUILD_TOOLS=ON \
  -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_WEBUI=ON \
  -DLLAMA_OPENSSL=ON \
  -DBUILD_SHARED_LIBS=ON
cmake --build build --config Release -j $(nproc)
```

---

## 5. Integration Method 1: add_subdirectory (Embedding)

This method includes llama.cpp directly in your CMake project tree. It gives you the most control and avoids a separate install step.

### Directory layout

```
my_project/
  CMakeLists.txt
  src/
    main.cpp
  externals/
    llama.cpp/          # git clone or git submodule
```

### Setup

```bash
cd my_project
git submodule add https://github.com/ggml-org/llama.cpp externals/llama.cpp
```

Or use a specific release tag:

```bash
git submodule add -b b5440 https://github.com/ggml-org/llama.cpp externals/llama.cpp
```

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.14)
project(my_app LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Configure llama.cpp build options before add_subdirectory
set(LLAMA_BUILD_COMMON ON CACHE BOOL "" FORCE)
set(LLAMA_BUILD_SERVER OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TESTS OFF CACHE BOOL "" FORCE)

# Optional: enable GPU backends
# set(GGML_CUDA ON CACHE BOOL "" FORCE)
# set(GGML_VULKAN ON CACHE BOOL "" FORCE)

add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/externals/llama.cpp")

add_executable(my_app src/main.cpp)
target_link_libraries(my_app PRIVATE common llama ggml)
```

### Available link targets

| Target | Description |
|---|---|
| `llama` | Core llama.cpp library (model loading, inference, sampling) |
| `ggml` | Tensor computation library (CPU + GPU backends) |
| `common` | Helper utilities (model params, sampling params, chat templates, CLI arg parsing). Only available when `LLAMA_BUILD_COMMON=ON` |

### Minimal example (without common)

If you only need the core API and want to minimize dependencies:

```cmake
set(LLAMA_BUILD_COMMON OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_SERVER OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TESTS OFF CACHE BOOL "" FORCE)

add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/externals/llama.cpp")

add_executable(my_app src/main.cpp)
target_link_libraries(my_app PRIVATE llama ggml)
```

### Minimal C++ example (src/main.cpp)

```cpp
#include "llama.h"
#include <cstdio>

int main() {
    // Initialize the llama.cpp backend
    llama_backend_init();

    // Load model parameters
    llama_model_params model_params = llama_model_default_params();
    model_params.n_gpu_layers = 99;  // offload all layers to GPU

    llama_model * model = llama_model_load_from_file("model.gguf", model_params);
    if (!model) {
        fprintf(stderr, "Failed to load model\n");
        return 1;
    }

    // Create context
    llama_context_params ctx_params = llama_context_default_params();
    ctx_params.n_ctx = 2048;
    ctx_params.n_batch = 512;

    llama_context * ctx = llama_init_from_model(model, ctx_params);
    if (!ctx) {
        fprintf(stderr, "Failed to create context\n");
        llama_model_free(model);
        return 1;
    }

    printf("Model loaded successfully! Vocab size: %d\n", llama_model_n_vocab(model));

    // Clean up
    llama_free(ctx);
    llama_model_free(model);
    llama_backend_free();

    return 0;
}
```

### With the common library

When linking `common`, you get access to higher-level utilities:

```cpp
#include "llama.h"
#include "common.h"
#include "sampling.h"
#include "chat.h"
#include <cstdio>
#include <string>
#include <vector>

int main(int argc, char ** argv) {
    common_params params;
    params.model.path = "model.gguf";
    params.cpuparams.n_threads = 8;
    params.n_ctx = 4096;
    params.n_batch = 2048;
    params.sampling.top_k = 40;
    params.sampling.top_p = 0.95f;
    params.sampling.temp = 0.8f;

    llama_backend_init();

    common_init_result init = common_init_from_params(params);
    llama_model * model = init.model.get();
    llama_context * ctx = init.context.get();

    if (!model || !ctx) {
        fprintf(stderr, "Failed to initialize\n");
        return 1;
    }

    printf("Model loaded. Context size: %d\n", llama_n_ctx(ctx));

    llama_backend_free();
    return 0;
}
```

---

## 6. Integration Method 2: find_package (After Install)

This method uses a pre-built and installed llama.cpp. Ideal for system-wide installations or when you want to decouple library building from application building.

### Step 1: Build and install llama.cpp

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/opt/llama-cpp \
  -DBUILD_SHARED_LIBS=ON
cmake --build build --config Release -j $(nproc)
cmake --install build
```

On Windows:

```powershell
cmake -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=C:/llama-cpp -DBUILD_SHARED_LIBS=ON
cmake --build build --config Release
cmake --install build --config Release
```

### Step 2: Use find_package in your project

```cmake
cmake_minimum_required(VERSION 3.14)
project(my_app LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(llama REQUIRED)

add_executable(my_app src/main.cpp)
target_link_libraries(my_app PRIVATE llama)
```

### Step 3: Configure with the install prefix

```bash
cmake -B build -DCMAKE_PREFIX_PATH=/opt/llama-cpp
cmake --build build --config Release
```

Or specify the package config directory directly:

```bash
cmake -B build -Dllama_DIR=/opt/llama-cpp/lib/cmake/llama
```

### Installed artifacts

After `cmake --install`, the prefix directory contains:

| Path | Contents |
|---|---|
| `include/llama.h` | Core C API header |
| `include/llama-cpp.h` | C++ convenience wrapper header |
| `include/ggml.h` | GGML tensor library header |
| `include/ggml-alloc.h` | GGML memory allocator header |
| `include/ggml-backend.h` | GGML backend interface header |
| `include/ggml-cpu.h` | GGML CPU backend header |
| `lib/libllama.so` (or `.dll`/`.dylib`) | Shared library (or static `.a`/`.lib`) |
| `lib/libggml.so` (or `.dll`/`.dylib`) | GGML shared library |
| `lib/cmake/llama/` | CMake package config files |
| `lib/cmake/ggml/` | CMake package config files for ggml |
| `lib/pkgconfig/llama.pc` | pkg-config file |
| `bin/` | Built executables (if tools were enabled) |

### Using pkg-config (alternative)

If you prefer pkg-config over CMake find_package:

```bash
export PKG_CONFIG_PATH=/opt/llama-cpp/lib/pkgconfig:$PKG_CONFIG_PATH
pkg-config --cflags --libs llama
```

In a Makefile:

```makefile
CFLAGS += $(shell pkg-config --cflags llama)
LDFLAGS += $(shell pkg-config --libs llama)
```

---

## 7. Integration Method 3: Static Library with PIC

When embedding llama.cpp into a shared library (`.so`, `.dll`, or `.dylib`) or a plugin system, the static library must be compiled with Position Independent Code (PIC). Without PIC, the linker will reject the static library when linking it into a shared object.

### Build llama.cpp as a static library with PIC

```bash
cmake -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DLLAMA_BUILD_TOOLS=OFF \
  -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_SERVER=OFF
cmake --build build --config Release -j $(nproc)
```

### Use case: embedding in a plugin / shared library

```cmake
cmake_minimum_required(VERSION 3.14)
project(my_plugin LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Build llama.cpp as static with PIC
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_COMMON ON CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_SERVER OFF CACHE BOOL "" FORCE)

add_subdirectory(externals/llama.cpp)

# Build our code as a shared library / plugin
add_library(my_plugin SHARED src/plugin.cpp)
target_link_libraries(my_plugin PRIVATE common llama ggml)
```

### Use case: Unreal Engine plugin integration

For embedding in an Unreal Engine plugin or module, build the static library externally and link it via the `.Build.cs` file:

```bash
# Build static lib with PIC (or /MD on Windows)
cmake -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
  -DLLAMA_BUILD_TOOLS=OFF \
  -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_SERVER=OFF \
  -DLLAMA_BUILD_COMMON=ON \
  -DGGML_NATIVE=OFF
cmake --build build --config Release -j $(nproc)
cmake --install build --prefix ./install
```

On Windows with MSVC, ensure the runtime library matches Unreal expectations (`/MD` for Release):

```powershell
cmake -B build -G "Visual Studio 17 2022" -A x64 `
  -DCMAKE_BUILD_TYPE=Release `
  -DBUILD_SHARED_LIBS=OFF `
  -DLLAMA_BUILD_TOOLS=OFF `
  -DLLAMA_BUILD_TESTS=OFF `
  -DLLAMA_BUILD_SERVER=OFF `
  -DLLAMA_BUILD_COMMON=ON `
  -DGGML_NATIVE=OFF `
  -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL
cmake --build build --config Release
cmake --install build --config Release --prefix ./install
```

### Important notes

- `CMAKE_POSITION_INDEPENDENT_CODE=ON` adds `-fPIC` on GCC/Clang. On MSVC, PIC is not applicable (Windows DLLs use `__declspec(dllexport/dllimport)` instead).
- When building static libraries, all transitive dependencies (e.g., CUDA runtime, Vulkan loader) must also be linked by the final shared library or executable.
- Set `GGML_NATIVE=OFF` if the resulting library needs to run on machines with different CPU features than the build machine.

---

## 8. Package Manager Installation

Pre-built packages are available for quick installation without building from source.

### Windows (winget)

```powershell
winget install llama.cpp
```

Installs the CLI tools and server. Binaries are added to PATH.

### macOS (Homebrew)

```bash
brew install llama.cpp
```

This installs with Metal support enabled by default on Apple Silicon.

### Linux (Homebrew)

```bash
brew install llama.cpp
```

Homebrew on Linux builds from source with CPU support. For GPU backends, build from source instead.

### Nix

```bash
# Install to user profile
nix profile install nixpkgs#llama-cpp

# Or use in a flake
nix run nixpkgs#llama-cpp -- --help

# With CUDA support (if nixpkgs is configured for it)
nix profile install nixpkgs#llama-cpp-cuda
```

### Limitations of package manager installs

- Package manager versions may lag behind the latest release.
- GPU backend support varies. Homebrew on macOS includes Metal; other backends may not be included.
- For `find_package` integration, you may still need to build from source and install to get the CMake config files.
- Package manager installs typically only provide the runtime binaries, not the development headers and libraries needed for C/C++ integration.

---

## 9. Docker Images

Official Docker images are published to `ghcr.io/ggml-org/llama.cpp`.

### Image variants

| Image Tag | Contents | Use Case |
|---|---|---|
| `:full` | CLI tools + Python conversion scripts + quantization tools | Full workflow: convert, quantize, and run models |
| `:light` | CLI tools only | Lightweight inference |
| `:server` | `llama-server` only | API server deployment |

### GPU-enabled variants

Append a GPU suffix to any base tag:

| Suffix | Backend |
|---|---|
| `-cuda` | NVIDIA CUDA |
| `-vulkan` | Vulkan |
| `-musa` | Moore Threads MUSA |
| `-intel` | Intel SYCL |

Examples: `:server-cuda`, `:full-cuda`, `:light-vulkan`, `:server-intel`

### Running the server with Docker

**CPU only:**

```bash
docker run -p 8080:8080 \
  -v /path/to/models:/models \
  ghcr.io/ggml-org/llama.cpp:server \
  -m /models/model.gguf \
  --host 0.0.0.0 --port 8080
```

**With NVIDIA GPU (requires nvidia-container-toolkit):**

```bash
docker run --gpus all -p 8080:8080 \
  -v /path/to/models:/models \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -m /models/model.gguf \
  --host 0.0.0.0 --port 8080 \
  -ngl 99
```

**With Vulkan:**

```bash
docker run --device /dev/dri -p 8080:8080 \
  -v /path/to/models:/models \
  ghcr.io/ggml-org/llama.cpp:server-vulkan \
  -m /models/model.gguf \
  --host 0.0.0.0 --port 8080 \
  -ngl 99
```

### Building a custom Docker image

```bash
# Clone the repo
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# Build the server image with CUDA
docker build -t my-llama-server -f .devops/llama-server-cuda.Dockerfile .
```

---

## 10. Cross-Compilation Notes

### Windows (MSVC)

- Use the Visual Studio generator or Ninja with a Developer Command Prompt.
- MSVC uses `/MD` (dynamic CRT) by default in Release. Ensure consistency across all linked libraries with `CMAKE_MSVC_RUNTIME_LIBRARY`:
  - `MultiThreadedDLL` (`/MD`) for Release
  - `MultiThreadedDebugDLL` (`/MDd`) for Debug
  - `MultiThreaded` (`/MT`) for static CRT linking
- When linking with other projects (e.g., Unreal Engine), match the CRT setting exactly or you will get linker errors or runtime crashes.

```powershell
cmake -B build -G "Visual Studio 17 2022" -A x64 `
  -DCMAKE_BUILD_TYPE=Release `
  -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL
```

### macOS

- Metal is auto-detected and enabled. To build a universal binary (x86_64 + arm64):

```bash
cmake -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64"
cmake --build build --config Release -j $(sysctl -n hw.logicalcpu)
```

- Minimum deployment target can be set with `CMAKE_OSX_DEPLOYMENT_TARGET`:

```bash
cmake -B build -DCMAKE_OSX_DEPLOYMENT_TARGET=13.0
```

### Linux

- Default compiler uses `libstdc++`. To use `libc++` (Clang):

```bash
cmake -B build \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_CXX_FLAGS="-stdlib=libc++"
```

- For portable binaries that run on different CPUs, disable native optimizations:

```bash
cmake -B build -DGGML_NATIVE=OFF
```

### Android

Cross-compile using the Android NDK:

```bash
export ANDROID_NDK=/path/to/android-ndk

cmake -B build-android \
  -DCMAKE_TOOLCHAIN_FILE=$ANDROID_NDK/build/cmake/android.toolchain.cmake \
  -DANDROID_ABI=arm64-v8a \
  -DANDROID_PLATFORM=android-28 \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLAMA_BUILD_TOOLS=OFF \
  -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_SERVER=OFF \
  -DBUILD_SHARED_LIBS=OFF \
  -DGGML_OPENCL=ON
cmake --build build-android --config Release -j $(nproc)
```

For Vulkan on Android:

```bash
cmake -B build-android \
  -DCMAKE_TOOLCHAIN_FILE=$ANDROID_NDK/build/cmake/android.toolchain.cmake \
  -DANDROID_ABI=arm64-v8a \
  -DANDROID_PLATFORM=android-28 \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_VULKAN=ON \
  -DLLAMA_BUILD_TOOLS=OFF \
  -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_SERVER=OFF
cmake --build build-android --config Release -j $(nproc)
```

### iOS

Cross-compile for iOS using the CMake Xcode generator:

```bash
cmake -B build-ios -G Xcode \
  -DCMAKE_SYSTEM_NAME=iOS \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=16.0 \
  -DBUILD_SHARED_LIBS=OFF \
  -DLLAMA_BUILD_TOOLS=OFF \
  -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_SERVER=OFF
cmake --build build-ios --config Release
```

Metal is automatically available on iOS.

---

## 11. Runtime Backend Selection

### The --device flag

When multiple backends are compiled in, use `--device` to select which device to use for inference:

```bash
# Use the first CUDA device
./llama-cli -m model.gguf --device CUDA0

# Use the Vulkan backend
./llama-cli -m model.gguf --device Vulkan0

# Use CPU only
./llama-cli -m model.gguf --device CPU
```

### Listing available devices

```bash
./llama-cli --list-devices
```

Example output:

```
Available devices:
  CPU: AMD Ryzen 9 7950X (32 threads)
  CUDA0: NVIDIA GeForce RTX 4090 (24564 MiB)
  Vulkan0: NVIDIA GeForce RTX 4090 (24564 MiB, Vulkan 1.3)
```

### GPU layer offloading

The `-ngl` (or `--n-gpu-layers`) flag controls how many transformer layers are offloaded to the GPU:

```bash
# Offload all layers to GPU
./llama-cli -m model.gguf -ngl 99

# Offload 20 layers (partial offload for large models)
./llama-cli -m model.gguf -ngl 20

# CPU only (no GPU offload)
./llama-cli -m model.gguf -ngl 0
```

### Dynamic backend loading (GGML_BACKEND_DL)

When built with `GGML_BACKEND_DL=ON`, GPU backends are compiled as separate shared libraries (`.so`/`.dll`) that are loaded at runtime. This allows a single binary distribution to support multiple GPU vendors without requiring all SDKs at build time on the end user machine:

```bash
# Build with dynamic backend loading
cmake -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_BACKEND_DL=ON \
  -DGGML_CUDA=ON \
  -DGGML_VULKAN=ON \
  -DGGML_NATIVE=OFF
cmake --build build --config Release -j $(nproc)
```

The backend plugins are built as separate shared libraries (e.g., `ggml-cuda.so`, `ggml-vulkan.so`) placed alongside the main binary. At runtime, llama.cpp scans for and loads available backend plugins automatically.

### RPC backend for distributed inference

The RPC backend allows distributing inference across multiple machines:

```bash
# Build with RPC support
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_RPC=ON
cmake --build build --config Release -j $(nproc)

# Start the RPC server on a remote machine
./llama-rpc-server --host 0.0.0.0 --port 50052

# Connect from the client
./llama-cli -m model.gguf --rpc 192.168.1.100:50052
```

---

## 12. Directory Structure After Build

### Build directory structure

After running `cmake --build build`, the build directory contains:

```
build/
  bin/
    llama-cli            # Main CLI inference tool
    llama-server         # HTTP API server (OpenAI-compatible)
    llama-quantize       # Model quantization tool
    llama-bench          # Benchmarking tool
    llama-perplexity     # Perplexity evaluation
    llama-embedding      # Embedding generation
    llama-cvector-generator  # Control vector generation
    llama-gguf           # GGUF metadata inspector
    llama-gguf-split     # Split/merge GGUF files
    llama-export-lora    # Export LoRA adapters
    llama-imatrix        # Importance matrix computation
    llama-lookup-*       # Speculative decoding lookup tools
    llama-run            # Simplified run command
  lib/
    libllama.so          # Core library (or .dll / .dylib)
    libggml.so           # Tensor library
    libggml-base.so      # GGML base library
    libggml-cpu.so       # CPU backend
    libggml-cuda.so      # CUDA backend (if enabled)
    libggml-vulkan.so    # Vulkan backend (if enabled)
    libggml-metal.so     # Metal backend (macOS)
    libcommon.a          # Common utilities (static)
  src/
    ...                  # Intermediate build artifacts
  ggml/
    ...                  # GGML build artifacts
```

### Installed directory structure

After running `cmake --install build --prefix /opt/llama-cpp`:

```
/opt/llama-cpp/
  bin/
    llama-cli
    llama-server
    llama-quantize
    llama-bench
    llama-gguf
    llama-gguf-split
    llama-embedding
    llama-perplexity
    llama-run
    ...                   # All enabled tool binaries
  include/
    llama.h               # Core C API
    llama-cpp.h           # C++ wrapper
    ggml.h                # GGML core header
    ggml-alloc.h          # GGML allocator
    ggml-backend.h        # GGML backend interface
    ggml-cpu.h            # CPU backend header
    ggml-cuda.h           # CUDA backend header (if built)
    ggml-vulkan.h         # Vulkan backend header (if built)
    ggml-metal.h          # Metal backend header (if built)
  lib/
    libllama.so           # (or .a for static builds)
    libllama.so.0         # Versioned symlink
    libggml.so
    libggml-base.so
    libggml-cpu.so
    cmake/
      llama/
        llama-config.cmake
        llama-config-version.cmake
        llama-targets.cmake
        llama-targets-release.cmake
      ggml/
        ggml-config.cmake
        ggml-config-version.cmake
        ggml-targets.cmake
        ggml-targets-release.cmake
    pkgconfig/
      llama.pc            # pkg-config file
  share/
    llama/
      ...                 # Miscellaneous data files
```

### Key file purposes

| File | Purpose |
|---|---|
| `llama.h` | Primary C API. All model loading, context creation, tokenization, and inference functions |
| `llama-cpp.h` | C++ RAII wrappers around the C API (smart pointers for model, context) |
| `ggml.h` | Low-level tensor operations. Rarely used directly unless extending backends |
| `ggml-backend.h` | Backend abstraction layer. Used when implementing custom backends or managing multi-device inference |
| `llama-config.cmake` | CMake package config. Enables `find_package(llama)` |
| `llama.pc` | pkg-config descriptor. Enables `pkg-config --cflags --libs llama` |
