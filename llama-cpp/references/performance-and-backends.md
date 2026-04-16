# Performance and GPU Backends Guide

Comprehensive reference for optimizing llama.cpp inference performance across different hardware and configurations.

## Table of Contents

- [1. GPU Backends Overview](#1-gpu-backends-overview)
- [2. CUDA-Specific Optimization](#2-cuda-specific-optimization)
- [3. GPU Layer Offloading](#3-gpu-layer-offloading)
- [4. Key Performance Settings](#4-key-performance-settings)
- [5. Memory Optimization](#5-memory-optimization)
- [6. Throughput Optimization](#6-throughput-optimization)
- [7. Speculative Decoding](#7-speculative-decoding)
- [8. Dynamic Backend Loading](#8-dynamic-backend-loading)
- [9. Benchmarking](#9-benchmarking)
- [10. Hardware Recommendations](#10-hardware-recommendations)
- [11. Common Performance Issues](#11-common-performance-issues)

---

## 1. GPU Backends Overview

llama.cpp supports multiple GPU backends, each targeting different hardware. The backend is selected at build time via CMake flags.

| Backend | CMake Flag | Hardware | Relative Speed | Notes |
|---------|-----------|----------|----------------|-------|
| CUDA | `GGML_CUDA=ON` | NVIDIA GPUs | Fastest on NVIDIA | FlashAttention support, most mature GPU backend |
| Metal | Default on macOS | Apple Silicon | Native, very fast | Automatic when building on macOS with Clang |
| Vulkan | `GGML_VULKAN=ON` | Cross-platform | Good on AMD, Intel | Broadest GPU support, works on most discrete GPUs |
| HIP/ROCm | `GGML_HIP=ON` | AMD GPUs | Near-CUDA on AMD | Requires ROCm SDK installed |
| SYCL | `GGML_SYCL=ON` | Intel GPUs | Good | Targets Intel Arc and Data Center GPUs |
| OpenCL | `GGML_OPENCL=ON` | Qualcomm, others | Moderate | Useful for mobile/embedded GPUs |
| WebGPU | `GGML_WEBGPU=ON` | Browser | Moderate | Requires Dawn library, enables in-browser inference |

**Build example (CUDA):**

```bash
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j
```

**Build example (Vulkan):**

```bash
cmake -B build -DGGML_VULKAN=ON
cmake --build build --config Release -j
```

**Build example (Metal, macOS):**

```bash
# Metal is enabled automatically on macOS with Clang
cmake -B build
cmake --build build --config Release -j
```

**Choosing a backend:**

- NVIDIA GPU: Use CUDA. It is the most optimized and feature-complete backend.
- AMD GPU: Use HIP/ROCm if ROCm is installed; otherwise Vulkan is a solid fallback.
- Intel GPU: Use SYCL for Intel Arc/Data Center; Vulkan also works.
- Apple Silicon: Metal is automatic and well-optimized.
- Cross-platform or unknown GPU: Vulkan is the safest bet.

---

## 2. CUDA-Specific Optimization

### Target GPU Architecture

Set `CMAKE_CUDA_ARCHITECTURES` to your specific GPU compute capability to avoid generating code for architectures you do not have. This reduces build time and can improve performance.

```bash
# RTX 3090 (Ampere, SM 86)
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86"

# RTX 4090 (Ada Lovelace, SM 89)
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="89"

# Both RTX 30xx and 40xx series
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86;89"

# RTX 5090 (Blackwell, SM 100/120)
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="100;120"
```

Common compute capabilities:

| GPU Series | Compute Capability |
|------------|-------------------|
| RTX 20xx (Turing) | 75 |
| RTX 30xx (Ampere) | 86 |
| A100 | 80 |
| RTX 40xx (Ada Lovelace) | 89 |
| H100 | 90 |
| RTX 50xx (Blackwell) | 100, 120 |

### FlashAttention with All Quant Types

By default, FlashAttention CUDA kernels are compiled only for a subset of quantization types. To enable FlashAttention for all quantization formats (increases build time):

```bash
cmake -B build -DGGML_CUDA=ON -DGGML_CUDA_FA_ALL_QUANTS=ON
```

### Flash Attention Runtime Flag

Flash attention reduces memory usage and can improve speed, especially with long contexts:

```bash
# CLI usage
llama-cli -m model.gguf --flash-attn

# Server usage
llama-server -m model.gguf --flash-attn
```

The `--flash-attn` flag (or `-fa`) accepts values: `auto`, `on`, `off`. The default is `auto`, which enables it when the backend supports it.

In the API, set `flash_attn: true` in model parameters.

### NVFP4 and MXFP4 Quantization

For the latest NVIDIA hardware (Blackwell/RTX 50xx and newer), llama.cpp supports NVFP4 and MXFP4 quantization formats that leverage hardware-native 4-bit floating point operations:

```bash
# Quantize to NVFP4 format
llama-quantize model-f16.gguf model-nvfp4.gguf NVFP4

# Quantize to MXFP4 format
llama-quantize model-f16.gguf model-mxfp4.gguf MXFP4
```

These formats require SM 100+ (Blackwell) GPUs and offer excellent throughput with minimal quality loss compared to traditional 4-bit integer quantization.

---

## 3. GPU Layer Offloading

### The Single Most Impactful Setting

The `n_gpu_layers` parameter (CLI: `-ngl` or `--gpu-layers`) controls how many transformer layers are offloaded to the GPU. This is the single most important performance knob.

```bash
# Offload all layers to GPU (recommended if VRAM allows)
llama-cli -m model.gguf -ngl 99

# Use -1 to offload everything (all layers + output layer)
llama-cli -m model.gguf -ngl -1

# Partial offload: only first 20 layers on GPU, rest on CPU
llama-cli -m model.gguf -ngl 20
```

**Guidelines:**

- Always try `-ngl 99` or `-ngl -1` first. If the model fits in VRAM, this gives the best performance.
- If you get out-of-memory errors, reduce the number incrementally (e.g., try 40, then 35, then 30) until stable.
- Even partial offloading helps significantly. Having 80% of layers on GPU is much faster than 0%.
- The output layer is offloaded only when all transformer layers fit. Use `-ngl -1` to force full offload.

### Typical Layer Counts by Model Size

| Model Size | Approximate Layer Count |
|-----------|------------------------|
| 7-8B | 32 layers |
| 13B | 40 layers |
| 34B | 48-60 layers |
| 70B | 80 layers |
| 405B | 126 layers |

### Multi-GPU Split Modes

When using multiple GPUs, control how the model is distributed:

```bash
# Layer split (default): consecutive layers on different GPUs
llama-cli -m model.gguf -ngl 99 --split-mode layer

# Row split: tensor rows distributed across GPUs
llama-cli -m model.gguf -ngl 99 --split-mode row

# Tensor split: custom VRAM ratio between GPUs (e.g., 70% on GPU 0, 30% on GPU 1)
llama-cli -m model.gguf -ngl 99 --tensor-split 7,3

# Disable split (single GPU)
llama-cli -m model.gguf -ngl 99 --split-mode none
```

Split mode guidance:

- **LAYER** (default): Simplest and most compatible. Each GPU gets a contiguous block of layers. Good when GPUs have similar VRAM.
- **ROW**: Splits individual matrix operations across GPUs. Better GPU utilization but higher inter-GPU communication. Best for NVLink-connected GPUs.
- **TENSOR**: Use `--tensor-split` to specify the ratio of work for each GPU. Useful when GPUs have different VRAM amounts (e.g., a 24GB and a 12GB card).
- **NONE**: Force single GPU. Use when you want to avoid multi-GPU overhead for small models.

---

## 4. Key Performance Settings

### Context Window Size (`n_ctx`)

Controls the maximum number of tokens the model can process at once. Larger context uses more memory (KV cache scales linearly).

```bash
# Default is typically 4096 or model-dependent
llama-cli -m model.gguf -c 4096

# Large context for document processing
llama-cli -m model.gguf -c 32768

# Very large context (requires significant VRAM)
llama-cli -m model.gguf -c 131072
```

Memory impact: KV cache for a 7B model at F16 precision is roughly 1 GB per 4096 context tokens. At 128K context, that is ~32 GB just for the KV cache.

### Batch Size (`n_batch` and `n_ubatch`)

- `n_batch` (CLI: `-b`): Logical batch size for prompt processing. Determines how many tokens are processed per evaluation call. Default: 2048.
- `n_ubatch` (CLI: `-ub`): Physical micro-batch size. The actual number of tokens processed in one GPU kernel launch. Default: 512.

```bash
# Larger batch for faster prompt processing
llama-cli -m model.gguf -b 4096 -ub 1024

# Smaller batch to reduce memory usage
llama-cli -m model.gguf -b 512 -ub 256
```

The logical batch (`n_batch`) should be >= `n_ubatch`. Increasing `n_ubatch` improves prompt processing throughput but uses more memory.

### CPU Thread Count (`n_threads`)

Number of CPU threads used for computation (relevant for CPU-only layers or CPU-only inference).

```bash
# Set to number of physical cores (NOT hyperthreads)
llama-cli -m model.gguf -t 8

# For prompt processing, can use more threads
llama-cli -m model.gguf -t 8 -tb 16
```

**Important caveats:**

- Set this to the number of **physical cores**, not logical cores (hyperthreads).
- Diminishing returns past ~16 threads on most CPUs.
- On some systems, setting threads too high (e.g., matching all hyperthreads) causes a **10x slowdown** due to cache thrashing.
- `-t` sets threads for generation, `-tb` sets threads for batch/prompt processing.

### Flash Attention

Enables memory-efficient attention computation. Reduces VRAM usage and can improve speed, especially with long contexts.

```bash
llama-cli -m model.gguf --flash-attn
```

Requires backend support (CUDA, Metal, Vulkan with compatible hardware). Enabled by default in `auto` mode on supported backends.

### KV Cache Quantization

Reduce KV cache memory by quantizing the keys and values:

```bash
# Q8_0 KV cache (halves KV memory vs F16, minimal quality loss)
llama-cli -m model.gguf -ctk q8_0 -ctv q8_0

# Q4_0 KV cache (quarters KV memory, some quality loss)
llama-cli -m model.gguf -ctk q4_0 -ctv q4_0
```

- `-ctk` / `--cache-type-k`: Quantization type for keys. Options: `f32`, `f16`, `bf16`, `q8_0`, `q4_0`, `q4_1`, `iq4_nl`, `q5_0`, `q5_1`.
- `-ctv` / `--cache-type-v`: Quantization type for values. Same options.
- `q8_0` is generally safe and recommended as a default. It halves KV cache size with negligible quality impact.
- `q4_0` saves more memory but may reduce output quality on some tasks.

### KV Cache GPU Offload

Offload the KV cache to GPU memory for faster attention computation:

```bash
# Enabled by default when using GPU layers
# To explicitly control:
llama-server -m model.gguf -ngl 99 --no-kv-offload  # keep KV on CPU
```

The `--no-kv-offload` flag keeps the KV cache on CPU RAM even when layers are on GPU. This saves VRAM at the cost of speed. Useful when you want all model layers on GPU but cannot fit the KV cache too.

### KV Cache Defragmentation

```bash
# Set defragmentation threshold (0.0 to 1.0, default -1.0 = disabled)
llama-server -m model.gguf --defrag-thold 0.1
```

When the KV cache fragmentation ratio exceeds this threshold, the cache is compacted. Useful in server mode with many parallel requests that cause fragmentation. A value of 0.1 means defragment when 10% of KV cache is wasted.

---

## 5. Memory Optimization

### KV Cache Quantization

The single easiest way to save memory without changing the model:

| KV Type | Memory vs F16 | Quality Impact |
|---------|--------------|----------------|
| `f16` (default) | 1.0x | None |
| `q8_0` | 0.5x | Negligible |
| `q5_0` | ~0.35x | Minor |
| `q4_0` | 0.25x | Noticeable on some tasks |

```bash
# Recommended default: Q8_0 KV cache
llama-cli -m model.gguf -ctk q8_0 -ctv q8_0 -c 32768
```

### Context Size Reduction

If you do not need long context, reducing `n_ctx` directly reduces memory:

```bash
# 2048 context for simple Q&A (saves significant memory)
llama-cli -m model.gguf -c 2048

# vs 32768 context for document analysis
llama-cli -m model.gguf -c 32768
```

Each halving of context size roughly halves the KV cache memory requirement.

### Model Quantization Choices

Choose quantization based on available memory:

| Quantization | Bits/Weight | 7B Size | 13B Size | 70B Size | Quality |
|-------------|------------|---------|----------|----------|---------|
| Q2_K | ~2.5 | ~2.7 GB | ~5.0 GB | ~25 GB | Poor |
| Q3_K_M | ~3.3 | ~3.3 GB | ~6.3 GB | ~33 GB | Acceptable |
| Q4_K_M | ~4.5 | ~4.1 GB | ~7.9 GB | ~40 GB | Good |
| Q5_K_M | ~5.5 | ~4.8 GB | ~9.2 GB | ~48 GB | Very good |
| Q6_K | ~6.5 | ~5.5 GB | ~10.7 GB | ~55 GB | Excellent |
| Q8_0 | ~8.0 | ~6.7 GB | ~13.0 GB | ~67 GB | Near-perfect |
| F16 | 16.0 | ~13 GB | ~26 GB | ~130 GB | Reference |

**Practical examples:**

- Q4_K_M of a 70B model (~40 GB) fits on a single RTX 4090 (24 GB VRAM) with partial offload, or fully in 48 GB+ VRAM.
- Q4_K_M of a 7B model (~4.1 GB) fits entirely on almost any modern GPU.
- Q8_0 of a 70B model (~67 GB) requires 2x RTX 4090 or an Apple M4 Ultra with 128+ GB unified memory.

### Sleep on Idle

For server deployments, unload the model from memory when idle to free resources:

```bash
# Unload model after 300 seconds of inactivity
llama-server -m model.gguf --sleep-idle-seconds 300

# Disable idle sleep (keep model loaded always)
llama-server -m model.gguf --sleep-idle-seconds 0
```

When a new request arrives, the model is reloaded. This adds latency to the first request after idle but can be valuable on shared machines.

---

## 6. Throughput Optimization

### Understanding the Bottleneck

llama.cpp inference has two distinct phases:

1. **Prompt processing (prefill):** Processing all input tokens. Compute-bound for short prompts, memory-bandwidth-bound for long prompts. Benefits greatly from GPU offload and larger batch sizes.

2. **Token generation (decode):** Generating tokens one at a time. Almost always **memory-bandwidth-bound**. Each token requires reading the entire model weights. The key metric is memory bandwidth, not FLOPS.

**Typical throughput ranges (single user):**

| Hardware | 7B Q4_K_M | 13B Q4_K_M | 70B Q4_K_M |
|---------|-----------|------------|------------|
| CPU (8-core, DDR5) | 15-25 t/s | 8-15 t/s | 2-4 t/s |
| RTX 3090 (24GB) | 80-120 t/s | 50-80 t/s | 10-20 t/s (partial) |
| RTX 4090 (24GB) | 100-150 t/s | 70-100 t/s | 15-25 t/s (partial) |
| M2 Ultra (192GB) | 40-60 t/s | 30-45 t/s | 15-25 t/s |
| M4 Max (128GB) | 50-70 t/s | 35-55 t/s | 18-30 t/s |
| 2x RTX 4090 | 90-130 t/s | 80-110 t/s | 30-50 t/s |

### Batch Processing

For prompt processing, larger batch sizes improve throughput:

```bash
# Maximize prompt processing speed
llama-cli -m model.gguf -b 4096 -ub 1024 -ngl 99
```

### Parallel Requests (Server Mode)

Serve multiple users concurrently with continuous batching:

```bash
# 4 parallel request slots
llama-server -m model.gguf -ngl 99 --parallel 4

# 8 parallel slots with larger context
llama-server -m model.gguf -ngl 99 --parallel 8 -c 32768
```

Each parallel slot needs its own KV cache allocation. Total context is divided: with `-c 32768 --parallel 4`, each slot gets 8192 tokens.

To give each slot the full context:

```bash
# Each of 4 slots gets 8192 tokens of context
llama-server -m model.gguf -ngl 99 --parallel 4 -c 32768
```

### Continuous Batching

The server automatically uses continuous batching: new requests can begin processing while others are still generating. This maximizes GPU utilization. No special configuration needed -- it is the default behavior in `llama-server`.

---

## 7. Speculative Decoding

Speculative decoding uses a small "draft" model to propose multiple tokens, then the main model verifies them in a single batch. This can provide 2-3x speedup for token generation.

### Draft Model Method

```bash
# Use a small model as the draft
llama-speculative \
  -m large-model-70b-q4.gguf \
  -md small-model-7b-q4.gguf \
  --draft-max 8 \
  --draft-min 1 \
  --draft-p-min 0.5

# In server mode
llama-server \
  -m large-model-70b-q4.gguf \
  --model-draft small-model-7b-q4.gguf \
  --draft-max 8
```

**Requirements:**

- The draft model must share the same tokenizer/vocabulary as the main model.
- The draft model should be much smaller (e.g., 7B draft for 70B main).
- Best results when the draft model is from the same model family.

### N-gram Speculation

Zero-overhead speculation using patterns from the prompt itself -- no draft model needed:

```bash
# Lookup-based speculation from prompt n-grams
llama-cli -m model.gguf --lookup-ngram

# Use a precomputed lookup table
llama-cli -m model.gguf --lookup-file lookup.bin
```

N-gram speculation works best when the output is expected to repeat patterns from the input (e.g., translation, code completion, summarization).

### When Speculative Decoding Helps

- Generation-heavy workloads (long outputs).
- Large models where generation is slow (e.g., 70B on a single GPU).
- The draft model has a high acceptance rate (similar "style" to the main model).

It does NOT help with prompt processing speed, only token generation.

---

## 8. Dynamic Backend Loading

### Build Configuration

Build llama.cpp to load GPU backends as shared libraries at runtime:

```bash
cmake -B build -DGGML_BACKEND_DL=ON -DGGML_NATIVE=OFF
cmake --build build --config Release -j
```

This produces a single binary that can dynamically load any available backend at runtime. Useful for distributing a single build that works across different GPU configurations.

### Runtime Device Selection

```bash
# List all available devices
llama-cli --list-devices

# Use a specific device
llama-cli -m model.gguf --device CUDA0

# Specify device for multi-GPU
llama-cli -m model.gguf --device CUDA0,CUDA1
```

With dynamic loading, the binary detects available backends at startup and selects the best one automatically. You can override this with `--device`.

---

## 9. Benchmarking

### llama-bench Tool

The `llama-bench` utility provides standardized performance measurements:

```bash
# Basic benchmark with default settings
llama-bench -m model.gguf

# Benchmark with specific GPU layers
llama-bench -m model.gguf -ngl 99

# Benchmark multiple configurations
llama-bench -m model.gguf -ngl 0,99 -b 128,256,512

# Benchmark with specific context sizes
llama-bench -m model.gguf -ngl 99 -c 512,2048,8192

# Benchmark prompt processing and generation separately
llama-bench -m model.gguf -ngl 99 -p 512 -n 128

# Compare two models
llama-bench -m model-q4.gguf -m model-q8.gguf -ngl 99
```

### Key Metrics

- **pp (prompt processing):** Tokens per second for processing input. Reported as `pp512` (processing 512 tokens) etc.
- **tg (token generation):** Tokens per second for generating output. Reported as `tg128` (generating 128 tokens) etc.
- **Total time:** Wall clock time for the full benchmark run.

### Example Output

```
model                 size   params backend    ngl  test          t/s
llama-7b Q4_K_M       4.07 GiB  6.74 B  CUDA   99  pp512      2847.52 +/- 12.34
llama-7b Q4_K_M       4.07 GiB  6.74 B  CUDA   99  tg128       118.43 +/- 0.67
```

### Quick Performance Test with llama-cli

```bash
# Time prompt processing and generation
llama-cli -m model.gguf -ngl 99 -p "Write a detailed essay about..." -n 256 2>&1 | tail -5
```

The output includes timing information:

```
llama_print_timings: load time       =   234.56 ms
llama_print_timings: prompt eval time =   89.12 ms /   15 tokens (  5.94 ms per token,   168.32 tokens per second)
llama_print_timings: eval time       =  2156.78 ms /  255 runs   (  8.46 ms per token,   118.20 tokens per second)
```

---

## 10. Hardware Recommendations

### By Model Size

**7-8B models (Llama 3.1 8B, Mistral 7B, Gemma 2 9B, Qwen 2.5 7B):**

- CPU: Any modern quad-core or better. 8 GB RAM minimum.
- GPU: Any discrete GPU with 4+ GB VRAM. Even integrated GPUs help.
- Recommended: RTX 3060 12GB or better for comfortable speed.
- Q4_K_M fits in ~4.1 GB, runs entirely on most GPUs.
- Expected speed: 80-150 t/s on RTX 4090, 15-25 t/s on CPU.

**13-14B models (Llama 3.1 13B, Qwen 2.5 14B):**

- CPU: 16 GB+ RAM required, 32 GB recommended.
- GPU: 8 GB+ VRAM for full offload at Q4_K_M (~7.9 GB).
- Recommended: RTX 3080/4070 (12 GB) or better.
- Expected speed: 50-100 t/s on RTX 4090, 8-15 t/s on CPU.

**32-34B models (Qwen 2.5 32B, CodeLlama 34B):**

- CPU: 32 GB+ RAM. Slow but functional.
- GPU: 24 GB VRAM for Q4_K_M (~18-20 GB). RTX 3090/4090.
- Q3_K_M can squeeze into 16 GB VRAM cards.
- Expected speed: 40-70 t/s on RTX 4090, 5-10 t/s on CPU.

**70-72B models (Llama 3.1 70B, Qwen 2.5 72B):**

- CPU: 64 GB+ RAM. Very slow (~2-4 t/s) but works.
- GPU: 2x RTX 4090/5090 (48 GB total) for Q4_K_M (~40 GB).
- Apple M4 Ultra with 128+ GB unified memory is excellent (~18-30 t/s).
- Single RTX 4090: possible at Q3_K_M or Q2_K with reduced quality.
- Expected speed: 30-50 t/s on 2x RTX 4090, 18-30 t/s on M4 Ultra.

**405B models (Llama 3.1 405B):**

- Requires ~220 GB at Q4_K_M.
- Needs 8-10x RTX 4090, or large server-class GPUs (A100 80GB x4, H100 x3).
- Apple M4 Ultra 512GB is one consumer option (slow but functional).
- Not practical for most local setups.

### Key Principle: Memory Bandwidth Matters Most

Token generation speed is determined primarily by **memory bandwidth**, not compute FLOPS:

| Hardware | Memory Bandwidth | Approx. 7B Q4 t/s |
|---------|-----------------|-------------------|
| DDR4-3200 (dual channel) | ~50 GB/s | 10-15 t/s |
| DDR5-5600 (dual channel) | ~90 GB/s | 18-25 t/s |
| RTX 3090 (GDDR6X) | 936 GB/s | 80-120 t/s |
| RTX 4090 (GDDR6X) | 1008 GB/s | 100-150 t/s |
| RTX 5090 (GDDR7) | 1792 GB/s | 160-220 t/s |
| M4 Max (unified) | 546 GB/s | 50-70 t/s |
| M4 Ultra (unified) | 819 GB/s | 60-90 t/s |
| A100 80GB (HBM2e) | 2039 GB/s | 150-200 t/s |

The formula is roughly: `t/s = memory_bandwidth / model_size_bytes`. A 4 GB model on a 1000 GB/s GPU gives ~250 theoretical max t/s (real-world is ~50-60% of theoretical).

---

## 11. Common Performance Issues

### Thread Count Too High

**Symptom:** CPU inference is 5-10x slower than expected.

**Cause:** Setting `-t` to the total number of logical cores (including hyperthreads) causes cache thrashing and context switching overhead.

**Fix:** Set `-t` to the number of **physical cores**, or experiment to find the sweet spot:

```bash
# Bad: 32 hyperthreads on a 16-core CPU
llama-cli -m model.gguf -t 32  # SLOW

# Good: physical core count
llama-cli -m model.gguf -t 16  # FAST

# Sometimes even fewer is faster
llama-cli -m model.gguf -t 12  # Try this if 16 is slow
```

### VRAM Overflow (Partial CPU Offload)

**Symptom:** Model loads but generation is much slower than expected.

**Cause:** The model does not fully fit in VRAM, so some layers run on CPU. Each token generation requires a CPU-GPU roundtrip for every CPU-resident layer.

**Fix:**

- Use a smaller quantization (Q4_K_M instead of Q6_K).
- Reduce context size (`-c 2048` instead of `-c 8192`).
- Use KV cache quantization (`-ctk q8_0 -ctv q8_0`).
- Monitor VRAM usage to ensure no overflow:

```bash
# Check VRAM usage on NVIDIA
nvidia-smi

# Watch in real-time
watch -n 1 nvidia-smi
```

### Context Size Too Large

**Symptom:** Out-of-memory error or extreme slowdown when processing long inputs.

**Cause:** KV cache grows linearly with context size. A 70B model at 128K context can require 50+ GB just for the KV cache.

**Fix:**

- Reduce `-c` to the minimum needed for your use case.
- Enable KV cache quantization: `-ctk q8_0 -ctv q8_0`.
- Enable flash attention: `--flash-attn`.
- Use `--no-kv-offload` to keep KV cache on CPU if GPU VRAM is tight (slower but avoids OOM).

### Wrong Quantization for Hardware

**Symptom:** Model runs but quality is poor or speed is suboptimal.

**Guidance by use case:**

| Priority | Recommended Quant | Notes |
|----------|------------------|-------|
| Max quality, have VRAM | Q6_K or Q8_0 | Minimal quality loss |
| Balanced (default choice) | Q4_K_M | Best quality-to-size ratio |
| Tight on memory | Q3_K_M | Noticeable quality loss |
| Very tight on memory | Q2_K or IQ2_M | Significant quality loss, last resort |

- Avoid Q4_0 and Q5_0 (legacy formats) -- prefer the K-quant variants (Q4_K_M, Q5_K_M).
- IQ quants (IQ2_M, IQ3_M, IQ4_XS) offer better quality at the same size but are slower on some backends.
- For CUDA with FlashAttention, ensure `GGML_CUDA_FA_ALL_QUANTS=ON` if using non-standard quant types.

### NUMA and Memory Topology Issues

**Symptom:** CPU inference is slower than expected on multi-socket or large systems.

**Fix:** Use NUMA-aware settings:

```bash
# Distribute memory across NUMA nodes
llama-cli -m model.gguf --numa distribute

# Isolate to a single NUMA node
llama-cli -m model.gguf --numa isolate

# Mirror memory across nodes
llama-cli -m model.gguf --numa numactl
```

On single-socket consumer systems, NUMA settings are not needed.

### Miscellaneous Tips

- **Disable GPU power management:** On Linux, `nvidia-smi -pm 1` keeps the GPU at full clock speed.
- **Close other GPU applications:** VRAM used by other apps reduces what is available for llama.cpp.
- **Use `mlock`:** The `--mlock` flag locks model memory to prevent swapping to disk, avoiding stalls: `llama-cli -m model.gguf --mlock`.
- **Monitor thermals:** Sustained inference can cause thermal throttling. Ensure adequate cooling.
- **Check backend detection:** Run with `--verbose` or `-v` to confirm the correct backend is loaded and all layers are on the expected device.
