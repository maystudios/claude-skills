# GGUF Format and Quantization Guide

Comprehensive reference for the GGUF binary format, quantization types, conversion workflows, and hardware requirements for llama.cpp.

## Table of Contents

- [1. GGUF Format Overview](#1-gguf-format-overview)
- [2. Quantization Types -- Complete Reference](#2-quantization-types----complete-reference)
- [3. Recommended Quantization Choice](#3-recommended-quantization-choice)
- [4. Quantization Commands](#4-quantization-commands)
- [5. Converting Models to GGUF](#5-converting-models-to-gguf)
- [6. Model Sources](#6-model-sources)
- [7. Importance Matrix (imatrix) Generation](#7-importance-matrix-imatrix-generation)
- [8. Mixed-Precision and Per-Layer Quantization](#8-mixed-precision-and-per-layer-quantization)
- [9. Hardware Requirements by Model Size](#9-hardware-requirements-by-model-size)
- [10. Supported Model Architectures](#10-supported-model-architectures)

---

## 1. GGUF Format Overview

GGUF (GPT-Generated Unified Format) is the binary file format used by llama.cpp for storing quantized large language models. It supersedes the earlier GGML, GGMF, and GGJT formats, consolidating their capabilities into a single, self-contained format.

### Key Properties

- **Single-file deployment**: All model weights, tokenizer data, and metadata are stored in one file. No separate config files, tokenizer files, or vocabulary files are needed.
- **mmap-compatible**: The tensor data section is aligned so the file can be memory-mapped directly, enabling fast loading without copying data into a separate buffer. This allows the OS to page in weights on demand.
- **Self-contained metadata**: All information needed to load and run the model is embedded in the file header as key-value pairs.
- **Extensible**: New metadata keys and tensor types can be added without breaking backward compatibility.

### File Structure

The binary layout of a GGUF file follows this sequential structure:

```
+---------------------------+
| Magic Number ("GGUF")     |  4 bytes: 0x46475547
+---------------------------+
| Version (3)               |  4 bytes: uint32
+---------------------------+
| Tensor Count              |  8 bytes: uint64
+---------------------------+
| Metadata KV Count         |  8 bytes: uint64
+---------------------------+
| Metadata KV Pairs         |  Variable length
|   key (string)            |
|   value_type (uint32)     |
|   value (typed)           |
+---------------------------+
| Tensor Info Array          |  Variable length
|   name (string)           |
|   n_dimensions (uint32)   |
|   dimensions (uint64[])   |
|   type (uint32)           |
|   offset (uint64)         |
+---------------------------+
| Padding (to alignment)    |  Aligns to GGUF_DEFAULT_ALIGNMENT (32 bytes)
+---------------------------+
| Tensor Data               |  Bulk binary weight data
|   (contiguous, aligned)   |
+---------------------------+
```

### Metadata Keys

Metadata is stored as typed key-value pairs. Standard keys include:

| Key | Description |
|-----|-------------|
| `general.architecture` | Model architecture identifier (e.g., `llama`, `mistral`, `qwen2`) |
| `general.name` | Human-readable model name |
| `general.file_type` | Quantization type used for the file |
| `general.quantization_version` | Version of the quantization scheme |
| `{arch}.context_length` | Maximum sequence length the model supports |
| `{arch}.embedding_length` | Hidden size / embedding dimension |
| `{arch}.block_count` | Number of transformer blocks (layers) |
| `{arch}.feed_forward_length` | FFN intermediate size |
| `{arch}.attention.head_count` | Number of attention heads |
| `{arch}.attention.head_count_kv` | Number of key-value heads (for GQA/MQA) |
| `{arch}.rope.freq_base` | RoPE base frequency |
| `{arch}.rope.dimension_count` | RoPE embedding dimension |
| `tokenizer.ggml.model` | Tokenizer type (e.g., `llama`, `gpt2`, `rwkv`) |
| `tokenizer.ggml.tokens` | Token vocabulary array |
| `tokenizer.ggml.scores` | Token scores/priorities |
| `tokenizer.ggml.bos_token_id` | Beginning-of-sequence token ID |
| `tokenizer.ggml.eos_token_id` | End-of-sequence token ID |

The `{arch}` prefix is replaced with the value from `general.architecture` (e.g., `llama.context_length`).

### Value Types

GGUF supports 13 value types for metadata:

| Type ID | Type | Description |
|---------|------|-------------|
| 0 | `uint8` | 8-bit unsigned integer |
| 1 | `int8` | 8-bit signed integer |
| 2 | `uint16` | 16-bit unsigned integer |
| 3 | `int16` | 16-bit signed integer |
| 4 | `uint32` | 32-bit unsigned integer |
| 5 | `int32` | 32-bit signed integer |
| 6 | `float32` | 32-bit IEEE 754 float |
| 7 | `bool` | Boolean (1 byte) |
| 8 | `string` | Length-prefixed UTF-8 string |
| 9 | `array` | Typed array (type + count + elements) |
| 10 | `uint64` | 64-bit unsigned integer |
| 11 | `int64` | 64-bit signed integer |
| 12 | `float64` | 64-bit IEEE 754 double |

### File Naming Convention

The standard GGUF naming convention is:

```
<BaseName>-<SizeLabel>[-<FineTune>]-<Version>[-<Encoding>][-<Type>][-<Shard>].gguf
```

| Component | Description | Examples |
|-----------|-------------|---------|
| `BaseName` | Model family name | `Llama`, `Mistral`, `Qwen2.5` |
| `SizeLabel` | Parameter count | `7B`, `13B`, `70B`, `8x7B` (MoE) |
| `FineTune` | Fine-tune variant (optional) | `Chat`, `Instruct`, `Code` |
| `Version` | Version identifier | `v1.0`, `v2` |
| `Encoding` | Quantization type (optional) | `Q4_K_M`, `Q8_0`, `IQ4_XS` |
| `Type` | Model type (optional) | `LoRA`, `vocab` |
| `Shard` | Shard index (optional) | `00001-of-00003` |

Examples:
- `Llama-3.1-8B-Instruct-v1.0-Q4_K_M.gguf`
- `Mistral-7B-v0.3-Q5_K_M.gguf`
- `Qwen2.5-72B-Instruct-v1.0-IQ4_XS-00001-of-00003.gguf`

---

## 2. Quantization Types -- Complete Reference

Quantization reduces the precision of model weights from their original floating-point representation to lower bit widths, trading a small amount of quality for significantly reduced memory usage and often faster inference.

### Full Quantization Type Table

Sorted from highest quality (most bits) to lowest (fewest bits):

| Type | Bits/Weight | Size (8B model) | Speed | Quality | Use Case |
|------|-------------|-----------------|-------|---------|----------|
| **F32** | 32.0 | ~32 GB | Slowest | Reference | Debugging, reference comparisons only |
| **F16** | 16.0 | ~16 GB | Slow | Lossless* | Base for quantization, GPU inference |
| **BF16** | 16.0 | ~16 GB | Slow | Lossless* | Same as F16 but with larger dynamic range |
| **Q8_0** | 8.5 | ~8.5 GB | Fast | Excellent | Near-lossless, ample RAM/VRAM available |
| **Q6_K** | 6.6 | ~6.6 GB | Fast | Very Good | High quality with moderate savings |
| **Q5_K_M** | 5.7 | ~5.7 GB | Fast | Good+ | Quality-focused with meaningful compression |
| **Q5_K_S** | 5.5 | ~5.5 GB | Fast | Good | Slightly smaller than Q5_K_M |
| **Q4_K_M** | 4.8 | ~4.9 GB | Very Fast | Good | **Recommended default** -- best balance |
| **Q4_K_S** | 4.6 | ~4.6 GB | Very Fast | Good- | Slightly smaller than Q4_K_M |
| **Q4_1** | 5.0 | ~5.0 GB | Very Fast | Fair+ | Legacy, prefer Q4_K_M instead |
| **Q4_0** | 4.5 | ~4.5 GB | Very Fast | Fair | Legacy, prefer Q4_K_S instead |
| **Q3_K_L** | 3.9 | ~3.9 GB | Very Fast | Fair | Larger 3-bit variant |
| **Q3_K_M** | 3.4 | ~3.4 GB | Very Fast | Fair- | Moderate 3-bit with reasonable quality |
| **Q3_K_S** | 3.0 | ~3.0 GB | Very Fast | Low+ | Smallest 3-bit K-quant |
| **Q2_K** | 2.6 | ~2.6 GB | Very Fast | Low | Significant quality loss, emergency use |
| **IQ4_XS** | 4.3 | ~4.3 GB | Fast | Good+ | **Best quality at ~4 bits** (needs imatrix) |
| **IQ4_NL** | 4.5 | ~4.5 GB | Fast | Good | Non-linear 4-bit, improved quality |
| **IQ3_M** | 3.4 | ~3.4 GB | Fast | Fair | Best ~3-bit quality (needs imatrix) |
| **IQ3_XXS** | 3.1 | ~3.1 GB | Fast | Fair- | Ultra-small 3-bit importance quant |
| **IQ2_XS** | 2.3 | ~2.3 GB | Moderate | Low | Extreme compression, needs imatrix |
| **IQ2_XXS** | 2.1 | ~2.1 GB | Moderate | Low- | Near-minimum viable quality |
| **IQ1_M** | 1.75 | ~1.8 GB | Moderate | Very Low | Extreme compression, notable degradation |
| **IQ1_S** | 1.5 | ~1.5 GB | Moderate | Minimal | Near-limit of usable quantization |
| **TQ1_0** | 1.69 | ~1.7 GB | Moderate | Very Low | Ternary quantization (experimental) |
| **TQ2_0** | 2.06 | ~2.1 GB | Moderate | Low | Ternary 2-bit quantization (experimental) |
| **NVFP4** | 4.0 | ~4.0 GB | Very Fast** | Good | NVIDIA FP4 -- requires CUDA, RTX 40/50 series |
| **MXFP4** | 4.0 | ~4.0 GB | Very Fast** | Good | Microscaling FP4 -- hardware-accelerated |

*F16/BF16 are lossless relative to the original F16 weights; some models are trained in BF16 and converting to F16 introduces minimal rounding.

**NVFP4 and MXFP4 speed depends on hardware support; without compatible hardware they fall back to slower paths.

### K-Quant Naming Convention

The `_S`, `_M`, and `_L` suffixes on K-quant types denote quality levels within the same bit range:

| Suffix | Meaning | Description |
|--------|---------|-------------|
| `_S` | Small | Smallest size, lower quality. All layers use the base quantization level. |
| `_M` | Medium | **Recommended.** Important layers (attention Q/K/V, output) are quantized at a higher precision. Best quality-to-size ratio. |
| `_L` | Large | Largest size, highest quality. Even more layers promoted to higher precision. |

For example, `Q4_K_M` uses 4-bit quantization for most layers but promotes attention and output layers to Q5_K or Q6_K, preserving model quality where it matters most.

### Importance Quantization (IQ) Types

IQ types use **importance matrices** (imatrix) derived from calibration data to identify which weights are most important for model quality. During quantization:

1. An importance matrix is computed by running representative text through the model and measuring which weights have the greatest impact on output quality (via gradient-based sensitivity analysis).
2. More important weights receive higher precision; less important weights are compressed more aggressively.
3. Non-linear quantization grids are used instead of uniform spacing, better representing the actual weight distributions.

The result is significantly better quality at the same bit rate compared to uniform quantization. IQ types provide **10-30% perplexity improvement** over equivalently-sized K-quants, especially below 4 bits per weight.

IQ types **require** an importance matrix file to quantize. Without it, the quantizer will either refuse or produce poor results.

---

## 3. Recommended Quantization Choice

### Decision Guide

| Recommendation | Type | Bits/Wt | Why |
|----------------|------|---------|-----|
| **Default choice** | **Q4_K_M** | 4.8 | Best overall balance of quality, file size, and inference speed. Suitable for most use cases. |
| **Better quality** | **Q5_K_M** | 5.7 | ~20% larger than Q4_K_M but noticeably better for complex reasoning and long outputs. |
| **Near-lossless** | **Q8_0** | 8.5 | Approximately 2x the size of Q4_K_M. Virtually indistinguishable from F16 for most tasks. |
| **Best at ~4 bits** | **IQ4_XS** | 4.3 | Best quality achievable at approximately 4 bits per weight. Requires imatrix generation. Smaller than Q4_K_M with comparable or better quality. |
| **RAM-constrained** | **Q3_K_M** or **IQ3_M** | 3.4 | When the model barely fits in memory. IQ3_M is better quality but needs imatrix. |
| **Extreme compression** | **IQ2_XS** or **IQ1_M** | 2.3 / 1.75 | Significant quality loss. Useful only when nothing else fits. IQ2_XS is the minimum for coherent output on most models. |

### Rules of Thumb

- **Always use the largest quantization that fits in your available RAM/VRAM.** Quality scales directly with bits per weight.
- **Q4_K_M is the sweet spot** for consumer hardware (16-32 GB RAM). The quality difference versus F16 is minimal for most conversational and coding tasks.
- **IQ4_XS is worth the imatrix effort** if you want to squeeze maximum quality from limited memory.
- **Below 3 bits per weight**, expect noticeable degradation in reasoning, factual accuracy, and instruction following.
- **Q8_0 is the practical ceiling** for quantized inference. Going to F16 doubles size with negligible quality gain.
- **For GPU offloading**, smaller quants mean more layers fit in VRAM, potentially offsetting quality loss with speed gains from full GPU inference.

---

## 4. Quantization Commands

### Basic Quantization

```bash
# Quantize from F16/BF16 GGUF to a target quantization type
./llama-quantize model-f16.gguf model-q4km.gguf Q4_K_M

# Quantize with explicit thread count
./llama-quantize --threads 8 model-f16.gguf model-q4km.gguf Q4_K_M

# Show available quantization types
./llama-quantize --help
```

### Quantization with Importance Matrix (required for IQ types)

```bash
# Step 1: Generate the importance matrix from calibration data
./llama-imatrix \
  -m model-f16.gguf \
  -f calibration-data.txt \
  -o imatrix.dat \
  -ngl 99            # Offload to GPU for speed (optional)

# Step 2: Quantize using the importance matrix
./llama-quantize --imatrix imatrix.dat model-f16.gguf model-iq4xs.gguf IQ4_XS
```

### Common Quantization Examples

```bash
# Recommended default
./llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M

# High quality
./llama-quantize model-f16.gguf model-Q5_K_M.gguf Q5_K_M

# Near-lossless
./llama-quantize model-f16.gguf model-Q8_0.gguf Q8_0

# Best 4-bit (with imatrix)
./llama-quantize --imatrix imatrix.dat model-f16.gguf model-IQ4_XS.gguf IQ4_XS

# RAM-constrained (with imatrix)
./llama-quantize --imatrix imatrix.dat model-f16.gguf model-IQ3_M.gguf IQ3_M

# Extreme compression (with imatrix)
./llama-quantize --imatrix imatrix.dat model-f16.gguf model-IQ2_XS.gguf IQ2_XS

# Keep output layer at original precision for better quality
./llama-quantize --leave-output-tensor model-f16.gguf model-Q4_K_M.gguf Q4_K_M
```

### Output Tensor Options

```bash
# Keep the output (language model head) tensor at original precision
./llama-quantize --leave-output-tensor model-f16.gguf model-q4km.gguf Q4_K_M

# Keep token embedding tensor at original precision
./llama-quantize --token-embedding-type f16 model-f16.gguf model-q4km.gguf Q4_K_M
```

---

## 5. Converting Models to GGUF

### From HuggingFace Local Directory

```bash
# Convert a locally downloaded HuggingFace model to GGUF (F16)
python convert_hf_to_gguf.py /path/to/hf_model --outfile model-f16.gguf --outtype f16

# Convert to BF16
python convert_hf_to_gguf.py /path/to/hf_model --outfile model-bf16.gguf --outtype bf16

# Convert to F32 (largest, for reference)
python convert_hf_to_gguf.py /path/to/hf_model --outfile model-f32.gguf --outtype f32

# Convert directly to a quantized type (shortcut, skips intermediate F16 file)
python convert_hf_to_gguf.py /path/to/hf_model --outfile model-q8_0.gguf --outtype q8_0
```

### From HuggingFace Hub Directly

```bash
# Download and convert from HuggingFace Hub (requires huggingface_hub package)
python convert_hf_to_gguf.py --model username/model-name --outfile model-f16.gguf --outtype f16

# Example with a specific model
python convert_hf_to_gguf.py --model meta-llama/Llama-3.1-8B-Instruct --outfile llama-3.1-8b-f16.gguf --outtype f16
```

### Full Pipeline: Convert then Quantize

```bash
# Step 1: Convert to F16 GGUF
python convert_hf_to_gguf.py /path/to/model --outfile model-f16.gguf --outtype f16

# Step 2 (optional): Generate importance matrix
./llama-imatrix -m model-f16.gguf -f calibration-data.txt -o imatrix.dat -ngl 99

# Step 3: Quantize
./llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M

# Or with imatrix for IQ types:
./llama-quantize --imatrix imatrix.dat model-f16.gguf model-IQ4_XS.gguf IQ4_XS
```

### Requirements for Conversion

```bash
# Install Python dependencies
pip install -r requirements.txt
# Key packages: numpy, sentencepiece, transformers, torch (or safetensors)
```

---

## 6. Model Sources

### HuggingFace Hub

The primary source for both original and pre-quantized GGUF models.

```bash
# Search for GGUF files on HuggingFace
# Visit: https://huggingface.co/models?library=gguf

# Download a specific GGUF file using huggingface-cli
pip install huggingface-cli
huggingface-cli download bartowski/Llama-3.1-8B-Instruct-GGUF \
  Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  --local-dir ./models
```

### Pre-Quantized Model Providers

These community members regularly produce high-quality GGUF quantizations of popular models:

| Provider | HuggingFace Profile | Notes |
|----------|-------------------|-------|
| **bartowski** | [bartowski](https://huggingface.co/bartowski) | Wide range of quant types, imatrix-based IQ quants, fast releases |
| **TheBloke** | [TheBloke](https://huggingface.co/TheBloke) | Prolific quantizer (legacy, less active since 2024) |
| **QuantFactory** | [QuantFactory](https://huggingface.co/QuantFactory) | Automated quantization pipeline, broad coverage |
| **mradermacher** | [mradermacher](https://huggingface.co/mradermacher) | Extensive library including imatrix quants |
| **unsloth** | [unsloth](https://huggingface.co/unsloth) | Optimized quantizations, often includes dynamic quants |

### Direct Download Examples

```bash
# Using huggingface-cli (recommended)
huggingface-cli download bartowski/Qwen2.5-72B-Instruct-GGUF \
  Qwen2.5-72B-Instruct-Q4_K_M-00001-of-00002.gguf \
  Qwen2.5-72B-Instruct-Q4_K_M-00002-of-00002.gguf \
  --local-dir ./models

# Using wget
wget https://huggingface.co/bartowski/Llama-3.1-8B-Instruct-GGUF/resolve/main/Llama-3.1-8B-Instruct-Q4_K_M.gguf

# Using curl
curl -L -o model.gguf https://huggingface.co/bartowski/Llama-3.1-8B-Instruct-GGUF/resolve/main/Llama-3.1-8B-Instruct-Q4_K_M.gguf
```

---

## 7. Importance Matrix (imatrix) Generation

### What is an Importance Matrix?

An importance matrix captures the relative significance of each weight in the model by measuring how much each weight contributes to the model output during inference on representative text. During quantization, weights flagged as more important receive higher effective precision (finer quantization grid), while less important weights are compressed more aggressively.

### Why It Matters

- **10-30% perplexity improvement** for quantizations below 4 bits per weight (IQ2, IQ3 types)
- **5-15% improvement** for 4-bit IQ types (IQ4_XS, IQ4_NL) compared to non-imatrix equivalents
- **Minimal benefit** for Q4_K_M and above (these types already handle importance via the K-quant mixed precision scheme)
- **Required** for all IQ-series quantization types (IQ1_S through IQ4_XS)

### How to Generate

```bash
# Basic imatrix generation
./llama-imatrix \
  -m model-f16.gguf \
  -f calibration-data.txt \
  -o imatrix.dat \
  --chunks 200          # Number of chunks to process (more = better, diminishing returns after ~200)

# With GPU acceleration (recommended for large models)
./llama-imatrix \
  -m model-f16.gguf \
  -f calibration-data.txt \
  -o imatrix.dat \
  -ngl 99 \
  --chunks 300

# Resume a partial imatrix computation
./llama-imatrix \
  -m model-f16.gguf \
  -f calibration-data.txt \
  -o imatrix.dat \
  --in-file partial-imatrix.dat \
  --chunks 100
```

### Calibration Data Selection

The calibration dataset should be representative of the intended use for the model:

- **General purpose**: Use a diverse mix of text -- Wikipedia articles, books, code, conversations. The `groups_merged.txt` file commonly shared in the llama.cpp community (~200KB) works well.
- **Domain-specific**: If the model will primarily handle code, use code samples. For medical text, use medical literature.
- **Size**: A few megabytes of text is sufficient. Diminishing returns beyond ~5 MB.
- **Quality over quantity**: Clean, well-formed text that represents the target domain matters more than volume.

Common calibration sources:
- `wikitext-2-raw` test set
- `groups_merged.txt` (community standard, available in llama.cpp discussions)
- Custom domain-specific corpora

---

## 8. Mixed-Precision and Per-Layer Quantization

### How K-Quants Handle Mixed Precision

K-quant variants (`Q3_K_*`, `Q4_K_*`, `Q5_K_*`) do not apply uniform quantization across all layers. Instead, they automatically assign different quantization levels to different tensor types based on their sensitivity:

| Tensor Type | Q4_K_S | Q4_K_M | Q5_K_S | Q5_K_M |
|-------------|--------|--------|--------|--------|
| Attention Q, K, V | Q4_K | Q6_K | Q5_K | Q6_K |
| Attention output | Q4_K | Q4_K | Q5_K | Q5_K |
| Feed-forward gate | Q4_K | Q6_K | Q5_K | Q6_K |
| Feed-forward up | Q4_K | Q4_K | Q5_K | Q5_K |
| Feed-forward down | Q4_K | Q4_K | Q5_K | Q5_K |
| Output norm | Q6_K | Q6_K | Q6_K | Q6_K |
| Token embeddings | Q4_K | Q4_K | Q5_K | Q5_K |
| Output (LM head) | Q6_K | Q6_K | Q6_K | Q6_K |

This is why `_M` variants are larger than `_S` variants at the same base bit level -- they promote more layers to higher precision.

### Why Mixed Precision Matters

- **Attention layers** are the most sensitive to quantization error. Small errors in Q/K/V projections accumulate across the sequence length, degrading long-context performance.
- **The output (LM head) layer** directly produces token probabilities. Quantization noise here shifts the entire output distribution.
- **Feed-forward layers** are more robust to quantization because their errors are partially absorbed by subsequent normalization layers.

### Manual Per-Layer Quantization

For advanced users, llama.cpp supports specifying quantization types per tensor regex pattern:

```bash
# Example: keep attention layers at Q8_0, everything else at Q4_K
./llama-quantize model-f16.gguf model-custom.gguf Q4_K_M \
  --override-kv "attn.*=Q8_0"
```

---

## 9. Hardware Requirements by Model Size

### RAM/VRAM Requirements

These estimates include model weights plus a baseline KV cache for 2048 context tokens. Actual requirements increase with longer context lengths.

| Model Size | Q2_K | Q3_K_M | Q4_K_M | Q5_K_M | Q8_0 | F16 |
|------------|------|--------|--------|--------|------|-----|
| **1-3B** | ~1.0 GB | ~1.5 GB | ~2.0 GB | ~2.5 GB | ~3.5 GB | ~6 GB |
| **7-8B** | ~2.8 GB | ~3.6 GB | ~4.9 GB | ~5.7 GB | ~8.5 GB | ~16 GB |
| **13B** | ~5.0 GB | ~6.0 GB | ~7.9 GB | ~9.2 GB | ~14 GB | ~26 GB |
| **20-22B** | ~8.0 GB | ~9.5 GB | ~12.5 GB | ~14.5 GB | ~22 GB | ~42 GB |
| **34B** | ~12 GB | ~15 GB | ~19 GB | ~23 GB | ~34 GB | ~68 GB |
| **70B** | ~24 GB | ~30 GB | ~38 GB | ~45 GB | ~70 GB | ~140 GB |
| **8x7B (MoE)** | ~15 GB | ~19 GB | ~24 GB | ~29 GB | ~47 GB | ~90 GB |
| **8x22B (MoE)** | ~42 GB | ~52 GB | ~68 GB | ~80 GB | ~130 GB | ~260 GB |

### KV Cache Memory

Additional memory is required for the key-value cache during inference, scaling with context length:

| Context Length | 7-8B Model | 13B Model | 70B Model |
|---------------|-----------|-----------|-----------|
| 2,048 | ~0.25 GB | ~0.5 GB | ~1.25 GB |
| 4,096 | ~0.5 GB | ~1.0 GB | ~2.5 GB |
| 8,192 | ~1.0 GB | ~2.0 GB | ~5.0 GB |
| 32,768 | ~4.0 GB | ~8.0 GB | ~20 GB |
| 131,072 | ~16 GB | ~32 GB | ~80 GB |

KV cache can be quantized (Q8_0 or Q4_0) to reduce its memory footprint by 2-4x with minimal quality impact:

```bash
# Enable KV cache quantization during inference
./llama-cli -m model.gguf -ctk q8_0 -ctv q8_0
```

### Practical Hardware Mapping

| Hardware | RAM/VRAM | Recommended Max Model |
|----------|----------|----------------------|
| 8 GB RAM (CPU only) | ~6 GB usable | 7B Q4_K_M |
| 16 GB RAM (CPU only) | ~12 GB usable | 13B Q4_K_M or 7B Q8_0 |
| 32 GB RAM (CPU only) | ~28 GB usable | 34B Q4_K_M or 70B Q2_K |
| 64 GB RAM (CPU only) | ~58 GB usable | 70B Q4_K_M |
| 8 GB VRAM (GPU) | ~7 GB usable | 7B Q4_K_M (full offload) |
| 12 GB VRAM (GPU) | ~11 GB usable | 7B Q8_0 or 13B Q4_K_M |
| 16 GB VRAM (GPU) | ~15 GB usable | 13B Q5_K_M or 7B F16 |
| 24 GB VRAM (GPU) | ~22 GB usable | 13B Q8_0 or 34B Q4_K_M |
| 48 GB VRAM (GPU) | ~45 GB usable | 70B Q4_K_M |
| 80 GB VRAM (GPU, A100) | ~77 GB usable | 70B Q8_0 |

---

## 10. Supported Model Architectures

llama.cpp supports a wide and growing list of transformer architectures. The `general.architecture` metadata field in the GGUF file identifies which architecture decoder to use.

### Text / Language Models

| Architecture | Models | Architecture Key |
|-------------|--------|-----------------|
| **LLaMA** | LLaMA 1/2/3/3.1/3.2/3.3/4, CodeLlama | `llama` |
| **Mistral** | Mistral 7B, Mistral Small/Medium/Large, Codestral | `llama` (uses LLaMA arch) |
| **Mixtral (MoE)** | Mixtral 8x7B, Mixtral 8x22B | `llama` (with MoE extensions) |
| **Qwen** | Qwen 1/1.5/2/2.5/3 (all sizes) | `qwen2` |
| **DeepSeek** | DeepSeek V2/V3, DeepSeek-R1, DeepSeek Coder | `deepseek2` |
| **Phi** | Phi-1/1.5/2/3/3.5/4 | `phi2`, `phi3` |
| **Gemma** | Gemma 1/2/3/4 (2B, 7B, 9B, 12B, 27B) | `gemma`, `gemma2`, `gemma3` |
| **GPT-2** | GPT-2 (all sizes) | `gpt2` |
| **GPT-NeoX** | GPT-NeoX, Pythia, RedPajama | `gptneox` |
| **GPT-J** | GPT-J-6B | `gptj` |
| **Falcon** | Falcon 7B/40B/180B, Falcon 2 | `falcon` |
| **StarCoder** | StarCoder, StarCoder2 | `starcoder`, `starcoder2` |
| **Command-R** | Command R, Command R+ | `command-r` |
| **DBRX** | DBRX (MoE) | `dbrx` |
| **Mamba** | Mamba, Mamba-2, Jamba (hybrid) | `mamba` |
| **InternLM** | InternLM 1/2/2.5 | `internlm2` |
| **Jamba** | Jamba (hybrid Mamba-Transformer) | `jamba` |
| **RWKV** | RWKV v5/v6 | `rwkv` |
| **Yi** | Yi 1/1.5/Coder | `llama` |
| **OLMo** | OLMo 1B/7B | `olmo` |
| **StableLM** | StableLM 1/2, Zephyr | `stablelm` |
| **Bloom** | BLOOM (all sizes) | `bloom` |
| **MPT** | MPT-7B/30B | `mpt` |
| **Baichuan** | Baichuan 1/2 | `baichuan` |
| **Orion** | OrionStar | `orion` |
| **MiniCPM** | MiniCPM 1/2/3 | `minicpm` |
| **Persimmon** | Persimmon-8B | `persimmon` |
| **Refact** | Refact-1.6B | `refact` |
| **PLaMo** | PLaMo-13B | `plamo` |
| **CodeShell** | CodeShell-7B | `codeshell` |
| **Exaone** | LG Exaone 3.0 | `exaone` |
| **OLMoE** | OLMoE (MoE variant) | `olmoe` |
| **Granite** | IBM Granite | `granite` |
| **ChatGLM** | ChatGLM 2/3/4, GLM-4 | `chatglm` |
| **Bitnet** | BitNet b1.58 | `bitnet` |
| **T5 / Flan-T5** | T5, Flan-T5 (encoder-decoder) | `t5` |

### Multimodal / Vision-Language Models

| Architecture | Models | Notes |
|-------------|--------|-------|
| **LLaVA** | LLaVA 1.5/1.6, LLaVA-NeXT | Image + text |
| **Qwen2-VL** | Qwen2-VL (all sizes) | Image + video + text |
| **Gemma 3/4 Vision** | Gemma 3, PaliGemma | Image + text |
| **Phi-3 Vision** | Phi-3-Vision, Phi-3.5-Vision | Image + text |
| **MiniCPM-V** | MiniCPM-V 2/2.5 | Image + text |
| **InternVL** | InternVL 1/2 | Image + text |
| **Llama 3.2 Vision** | Llama 3.2 11B/90B Vision | Image + text |
| **SmolVLM** | SmolVLM | Lightweight vision-language |
| **Moondream** | Moondream 1/2 | Compact image understanding |
| **Obsidian** | NousResearch Obsidian | Multi-turn multimodal |

### Embedding Models

| Architecture | Models | Notes |
|-------------|--------|-------|
| **BERT** | BERT, RoBERTa, all-MiniLM | Encoder-only, embeddings |
| **Nomic Embed** | nomic-embed-text | Embedding model |
| **Jina** | Jina Embeddings v2/v3 | Embedding model |

### Notes on Architecture Support

- Many models share the `llama` architecture key (Mistral, Yi, Mixtral, etc.) because they use the same fundamental transformer structure with minor variations handled by metadata flags.
- New architectures are continuously added. Check the llama.cpp `convert_hf_to_gguf.py` source or `ggml` headers for the current full list.
- MoE (Mixture of Experts) models are supported but require more RAM because all expert weights must be loaded even though only a subset is active per token.
- Encoder-decoder models (T5) have partial support -- primarily for embedding/encoding tasks rather than full generative use.
