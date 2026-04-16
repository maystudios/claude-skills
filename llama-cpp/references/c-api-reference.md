# llama.cpp C/C++ API Reference

Comprehensive reference for the llama.cpp inference library C API (`llama.h`) and C++ RAII wrappers (`llama-cpp.h`).

Repository: https://github.com/ggml-org/llama.cpp

---

## Table of Contents

- [1. Core Types](#1-core-types)
- [2. Key Enumerations](#2-key-enumerations)
- [3. Parameter Structs](#3-parameter-structs)
- [4. Backend Initialization](#4-backend-initialization)
- [5. Model Loading and Management](#5-model-loading-and-management)
- [6. Context Creation](#6-context-creation)
- [7. Tokenization](#7-tokenization)
- [8. Batch and Decoding](#8-batch-and-decoding)
- [9. Output Access](#9-output-access)
- [10. Sampling API (Chain Pattern)](#10-sampling-api-chain-pattern)
- [11. Chat Templates](#11-chat-templates)
- [12. Memory / KV Cache Management](#12-memory--kv-cache-management)
- [13. State Serialization](#13-state-serialization)
- [14. LoRA Adapters](#14-lora-adapters)
- [15. Quantization](#15-quantization)
- [16. C++ RAII Wrappers (llama-cpp.h)](#16-c-raii-wrappers-llama-cpph)
- [17. Complete Working Examples](#17-complete-working-examples)

---

## 1. Core Types

### Primitive Typedefs

```c
typedef int32_t llama_pos;     // Token position in context
typedef int32_t llama_token;   // Token ID
typedef int32_t llama_seq_id;  // Sequence ID for parallel generation
```

### Predefined Constants

```c
#define LLAMA_DEFAULT_SEED  0xFFFFFFFF  // Default RNG seed (random)
#define LLAMA_TOKEN_NULL    -1          // Sentinel value for "no token"
```

### Opaque Structs

These are forward-declared types whose internals are hidden. You interact with them only through pointers and API functions.

```c
struct llama_vocab;           // Vocabulary (tokenizer) associated with a model
struct llama_model;           // Loaded model weights and metadata
struct llama_context;         // Inference context (KV cache, compute state, etc.)
struct llama_sampler;         // Token sampler or sampler chain
struct llama_adapter_lora;    // Loaded LoRA adapter
```

### Memory Handle

```c
typedef struct llama_memory_i * llama_memory_t;  // Opaque handle to context memory (KV cache)
```

`llama_memory_t` is obtained from a context via `llama_get_memory()` and is used for all KV cache manipulation functions.

### Callback Typedefs

```c
// Progress callback during model loading. Return false to cancel.
typedef bool (*llama_progress_callback)(float progress, void * user_data);
```

### Logit Bias

```c
typedef struct llama_logit_bias {
    llama_token token;
    float       bias;
} llama_logit_bias;
```

Used with `llama_sampler_init_logit_bias()` to add fixed biases to specific token logits before sampling.

---

## 2. Key Enumerations

### llama_vocab_type

Vocabulary/tokenizer type stored in the model file.

```c
enum llama_vocab_type {
    LLAMA_VOCAB_TYPE_NONE   = 0,  // No vocabulary
    LLAMA_VOCAB_TYPE_SPM    = 1,  // SentencePiece (LLaMA, Mistral, etc.)
    LLAMA_VOCAB_TYPE_BPE    = 2,  // Byte Pair Encoding (GPT-2, Falcon, etc.)
    LLAMA_VOCAB_TYPE_WPM    = 3,  // WordPiece (BERT)
    LLAMA_VOCAB_TYPE_UGM    = 4,  // Unigram (T5)
    LLAMA_VOCAB_TYPE_RWKV   = 5,  // RWKV tokenizer
    LLAMA_VOCAB_TYPE_PLAMO2 = 6,  // PLaMo-2 tokenizer
};
```

### llama_ftype

File quantization type. Determines the precision of stored weights.

```c
enum llama_ftype {
    LLAMA_FTYPE_ALL_F32              = 0,
    LLAMA_FTYPE_MOSTLY_F16           = 1,
    LLAMA_FTYPE_MOSTLY_Q4_0          = 2,
    LLAMA_FTYPE_MOSTLY_Q4_1          = 3,
    LLAMA_FTYPE_MOSTLY_Q8_0          = 7,
    LLAMA_FTYPE_MOSTLY_Q5_0          = 8,
    LLAMA_FTYPE_MOSTLY_Q5_1          = 9,
    LLAMA_FTYPE_MOSTLY_Q2_K          = 10,
    LLAMA_FTYPE_MOSTLY_Q3_K_S        = 11,
    LLAMA_FTYPE_MOSTLY_Q3_K_M        = 12,
    LLAMA_FTYPE_MOSTLY_Q3_K_L        = 13,
    LLAMA_FTYPE_MOSTLY_Q4_K_S        = 14,
    LLAMA_FTYPE_MOSTLY_Q4_K_M        = 15,
    LLAMA_FTYPE_MOSTLY_Q5_K_S        = 16,
    LLAMA_FTYPE_MOSTLY_Q5_K_M        = 17,
    LLAMA_FTYPE_MOSTLY_Q6_K          = 18,
    LLAMA_FTYPE_MOSTLY_IQ2_XXS       = 19,
    LLAMA_FTYPE_MOSTLY_IQ2_XS        = 20,
    LLAMA_FTYPE_MOSTLY_Q2_K_S        = 21,
    LLAMA_FTYPE_MOSTLY_IQ3_XS        = 22,
    LLAMA_FTYPE_MOSTLY_IQ3_XXS       = 23,
    LLAMA_FTYPE_MOSTLY_IQ1_S         = 24,
    LLAMA_FTYPE_MOSTLY_IQ4_NL        = 25,
    LLAMA_FTYPE_MOSTLY_IQ3_S         = 26,
    LLAMA_FTYPE_MOSTLY_IQ3_M         = 27,
    LLAMA_FTYPE_MOSTLY_IQ2_S         = 28,
    LLAMA_FTYPE_MOSTLY_IQ2_M         = 29,
    LLAMA_FTYPE_MOSTLY_IQ4_XS        = 30,
    LLAMA_FTYPE_MOSTLY_IQ1_M         = 31,
    LLAMA_FTYPE_MOSTLY_BF16          = 32,
    LLAMA_FTYPE_MOSTLY_TQ1_0         = 36,
    LLAMA_FTYPE_MOSTLY_TQ2_0         = 37,
    LLAMA_FTYPE_MOSTLY_MXFP4_MOE     = 38,
    LLAMA_FTYPE_MOSTLY_NVFP4         = 39,
    LLAMA_FTYPE_MOSTLY_Q1_0          = 40,
    LLAMA_FTYPE_GUESSED              = 1024,  // Not specified in the model file
};
```

### llama_split_mode

How to split the model across multiple GPUs.

```c
enum llama_split_mode {
    LLAMA_SPLIT_MODE_NONE   = 0,  // Single GPU only
    LLAMA_SPLIT_MODE_LAYER  = 1,  // Split layers across GPUs
    LLAMA_SPLIT_MODE_ROW    = 2,  // Split rows across GPUs (tensor parallelism)
    LLAMA_SPLIT_MODE_TENSOR = 3,  // Split individual tensors across GPUs
};
```

### llama_pooling_type

Pooling strategy for embedding models.

```c
enum llama_pooling_type {
    LLAMA_POOLING_TYPE_UNSPECIFIED = -1,  // Use model default
    LLAMA_POOLING_TYPE_NONE = 0,          // No pooling (per-token embeddings)
    LLAMA_POOLING_TYPE_MEAN = 1,          // Mean pooling over all tokens
    LLAMA_POOLING_TYPE_CLS  = 2,          // Use [CLS] token embedding
    LLAMA_POOLING_TYPE_LAST = 3,          // Use last token embedding
    LLAMA_POOLING_TYPE_RANK = 4,          // Ranking/reranking output
};
```

### llama_attention_type

```c
enum llama_attention_type {
    LLAMA_ATTENTION_TYPE_UNSPECIFIED = -1,  // Use model default
    LLAMA_ATTENTION_TYPE_CAUSAL      = 0,   // Causal (autoregressive) attention
    LLAMA_ATTENTION_TYPE_NON_CAUSAL  = 1,   // Non-causal (bidirectional, for embeddings)
};
```

### llama_flash_attn_type

```c
enum llama_flash_attn_type {
    LLAMA_FLASH_ATTN_TYPE_AUTO     = -1,  // Auto-detect
    LLAMA_FLASH_ATTN_TYPE_DISABLED = 0,   // Disable flash attention
    LLAMA_FLASH_ATTN_TYPE_ENABLED  = 1,   // Enable flash attention
};
```

### llama_rope_scaling_type

RoPE (Rotary Position Embedding) scaling for extended context.

```c
enum llama_rope_scaling_type {
    LLAMA_ROPE_SCALING_TYPE_UNSPECIFIED = -1,
    LLAMA_ROPE_SCALING_TYPE_NONE        = 0,   // No scaling
    LLAMA_ROPE_SCALING_TYPE_LINEAR      = 1,   // Linear interpolation
    LLAMA_ROPE_SCALING_TYPE_YARN        = 2,   // YaRN (Yet another RoPE extensioN)
    LLAMA_ROPE_SCALING_TYPE_LONGROPE    = 3,   // LongRoPE
    LLAMA_ROPE_SCALING_TYPE_MAX_VALUE   = LLAMA_ROPE_SCALING_TYPE_LONGROPE,
};
```

### llama_rope_type

```c
enum llama_rope_type {
    LLAMA_ROPE_TYPE_NONE   = -1,
    LLAMA_ROPE_TYPE_NORM   = 0,
    LLAMA_ROPE_TYPE_NEOX   = GGML_ROPE_TYPE_NEOX,
    LLAMA_ROPE_TYPE_MROPE  = GGML_ROPE_TYPE_MROPE,
    LLAMA_ROPE_TYPE_IMROPE = GGML_ROPE_TYPE_IMROPE,
    LLAMA_ROPE_TYPE_VISION = GGML_ROPE_TYPE_VISION,
};
```

### llama_token_type

```c
enum llama_token_type {
    LLAMA_TOKEN_TYPE_UNDEFINED    = 0,
    LLAMA_TOKEN_TYPE_NORMAL       = 1,
    LLAMA_TOKEN_TYPE_UNKNOWN      = 2,
    LLAMA_TOKEN_TYPE_CONTROL      = 3,
    LLAMA_TOKEN_TYPE_USER_DEFINED = 4,
    LLAMA_TOKEN_TYPE_UNUSED       = 5,
    LLAMA_TOKEN_TYPE_BYTE         = 6,
};
```

### llama_token_attr

Bitmask attributes for tokens.

```c
enum llama_token_attr {
    LLAMA_TOKEN_ATTR_UNDEFINED    = 0,
    LLAMA_TOKEN_ATTR_UNKNOWN      = 1 << 0,
    LLAMA_TOKEN_ATTR_UNUSED       = 1 << 1,
    LLAMA_TOKEN_ATTR_NORMAL       = 1 << 2,
    LLAMA_TOKEN_ATTR_CONTROL      = 1 << 3,
    LLAMA_TOKEN_ATTR_USER_DEFINED = 1 << 4,
    LLAMA_TOKEN_ATTR_BYTE         = 1 << 5,
    LLAMA_TOKEN_ATTR_NORMALIZED   = 1 << 6,
    LLAMA_TOKEN_ATTR_LSTRIP       = 1 << 7,
    LLAMA_TOKEN_ATTR_RSTRIP       = 1 << 8,
    LLAMA_TOKEN_ATTR_SINGLE_WORD  = 1 << 9,
};
```

### llama_model_kv_override_type

```c
enum llama_model_kv_override_type {
    LLAMA_KV_OVERRIDE_TYPE_INT,
    LLAMA_KV_OVERRIDE_TYPE_FLOAT,
    LLAMA_KV_OVERRIDE_TYPE_BOOL,
    LLAMA_KV_OVERRIDE_TYPE_STR,
};
```

---

## 3. Parameter Structs

### llama_model_params

Controls model loading behavior. Obtain defaults with `llama_model_default_params()`.

```c
struct llama_model_params {
    // Device configuration
    ggml_backend_dev_t * devices;                              // List of devices to use (NULL = auto)
    const struct llama_model_tensor_buft_override * tensor_buft_overrides; // Per-tensor buffer type overrides

    int32_t n_gpu_layers;                                      // Number of layers to offload to GPU (default: 0)
    enum llama_split_mode split_mode;                          // How to split across GPUs

    int32_t main_gpu;                                          // Main GPU index for single-GPU or coordination
    const float * tensor_split;                                // Proportion of model per GPU (array of floats, one per GPU)

    // Progress tracking
    llama_progress_callback progress_callback;                 // Called during loading; return false to cancel
    void * progress_callback_user_data;

    // KV metadata overrides
    const struct llama_model_kv_override * kv_overrides;       // Override GGUF metadata values

    // Boolean flags
    bool vocab_only;       // Only load the vocabulary (no weights)
    bool use_mmap;         // Memory-map the model file (default: true)
    bool use_direct_io;    // Use direct I/O for loading
    bool use_mlock;        // Lock model memory to prevent swapping
    bool check_tensors;    // Validate tensor data during loading
    bool use_extra_bufts;  // Use extra buffer types
    bool no_host;          // Do not allocate host memory
    bool no_alloc;         // Do not allocate memory (for advanced usage)
};
```

### llama_context_params

Controls inference context creation. Obtain defaults with `llama_context_default_params()`.

```c
struct llama_context_params {
    uint32_t n_ctx;             // Context window size in tokens (0 = use model default)
    uint32_t n_batch;           // Max tokens per llama_decode() call (prompt processing)
    uint32_t n_ubatch;          // Max tokens per internal micro-batch
    uint32_t n_seq_max;         // Max number of parallel sequences
    int32_t  n_threads;         // Number of threads for generation (single-token decode)
    int32_t  n_threads_batch;   // Number of threads for prompt processing

    // RoPE configuration
    enum llama_rope_scaling_type rope_scaling_type;
    enum llama_pooling_type      pooling_type;
    enum llama_attention_type    attention_type;
    enum llama_flash_attn_type   flash_attn_type;

    float    rope_freq_base;    // RoPE base frequency (0 = use model default)
    float    rope_freq_scale;   // RoPE frequency scaling factor (0 = use model default)

    // YaRN RoPE parameters
    float    yarn_ext_factor;   // YaRN extrapolation mix factor (-1 = use model default)
    float    yarn_attn_factor;  // YaRN attention magnitude scaling
    float    yarn_beta_fast;    // YaRN low correction dim
    float    yarn_beta_slow;    // YaRN high correction dim
    uint32_t yarn_orig_ctx;     // YaRN original context size

    float    defrag_thold;      // KV cache defragmentation threshold (-1 = disabled)

    // Compute callbacks
    ggml_backend_sched_eval_callback cb_eval;
    void * cb_eval_user_data;

    // KV cache quantization
    enum ggml_type type_k;      // Data type for K cache (default: GGML_TYPE_F16)
    enum ggml_type type_v;      // Data type for V cache (default: GGML_TYPE_F16)

    // Abort callback
    ggml_abort_callback abort_callback;
    void *              abort_callback_data;

    // Boolean flags
    bool embeddings;    // Extract embeddings instead of generating (default: false)
    bool offload_kqv;   // Offload KQV ops to GPU (default: true)
    bool no_perf;       // Disable performance counters (default: true)
    bool op_offload;    // Enable operator offloading
    bool swa_full;      // Full sliding window attention
    bool kv_unified;    // Unified KV cache

    // Backend sampling (experimental)
    struct llama_sampler_seq_config * samplers;
    size_t                            n_samplers;
};
```

### llama_batch

Represents a batch of tokens to be evaluated. Can be either token IDs or raw embeddings.

```c
typedef struct llama_batch {
    int32_t n_tokens;          // Number of tokens in this batch

    llama_token  *  token;     // Token IDs (mutually exclusive with embd)
    float        *  embd;      // Embedding data (mutually exclusive with token)
    llama_pos    *  pos;       // Token positions
    int32_t      *  n_seq_id;  // Number of sequence IDs per token
    llama_seq_id ** seq_id;    // Sequence IDs per token (array of arrays)
    int8_t       *  logits;    // Whether to compute logits for this token (1 = yes, 0 = no)
} llama_batch;
```

**Usage pattern:** For simple use cases, use `llama_batch_get_one()` which creates a batch from a contiguous token array (all assigned to sequence 0, logits enabled only for the last token). For fine-grained control over per-token positions, sequences, and which tokens produce logits, use `llama_batch_init()` and fill the fields manually.

### llama_chat_message

Represents a single message in a chat conversation.

```c
typedef struct llama_chat_message {
    const char * role;     // "system", "user", or "assistant"
    const char * content;  // Message text
} llama_chat_message;
```

### llama_sampler_chain_params

Parameters for creating a sampler chain.

```c
typedef struct llama_sampler_chain_params {
    bool no_perf;   // Disable performance timing for the sampler chain (default: true)
} llama_sampler_chain_params;
```

### llama_model_quantize_params

Controls model quantization. Obtain defaults with `llama_model_quantize_default_params()`.

```c
typedef struct llama_model_quantize_params {
    int32_t nthread;                            // Number of threads (0 = auto)
    enum llama_ftype ftype;                     // Target quantization type
    enum ggml_type output_tensor_type;          // Quantization type for output tensor
    enum ggml_type token_embedding_type;        // Quantization type for token embeddings
    bool allow_requantize;                      // Allow quantizing already-quantized tensors
    bool quantize_output_tensor;                // Quantize the output.weight tensor
    bool only_copy;                             // Copy tensors without quantizing
    bool pure;                                  // Disable k-quant mixtures (use ftype uniformly)
    bool keep_split;                            // Preserve split structure of the model
    bool dry_run;                               // Estimate output size without writing
    const struct llama_model_imatrix_data * imatrix;      // Importance matrix data
    const struct llama_model_kv_override * kv_overrides;  // KV metadata overrides
    const struct llama_model_tensor_override * tt_overrides; // Per-tensor type overrides
    const int32_t * prune_layers;               // Layer indices to prune (NULL-terminated)
} llama_model_quantize_params;
```

### Performance Data Structs

```c
struct llama_perf_context_data {
    double  t_start_ms;   // Time of context creation
    double  t_load_ms;    // Time spent loading
    double  t_p_eval_ms;  // Time spent in prompt evaluation
    double  t_eval_ms;    // Time spent in generation (decode)
    int32_t n_p_eval;     // Number of tokens in prompt evaluation
    int32_t n_eval;       // Number of tokens generated
    int32_t n_reused;     // Number of tokens reused from cache
};

struct llama_perf_sampler_data {
    double  t_sample_ms;  // Total time spent sampling
    int32_t n_sample;     // Number of tokens sampled
};
```

---

## 4. Backend Initialization

These functions initialize the compute backends (CPU, CUDA, Metal, Vulkan, etc.) and must be called before loading models.

```c
// Load all available dynamic backends (CUDA, Metal, Vulkan, etc.)
// Call this BEFORE llama_backend_init(). This is the recommended approach.
void ggml_backend_load_all(void);
```

```c
// Initialize the llama backend (call once at startup)
void llama_backend_init(void);
```

```c
// Free the llama backend (call once at shutdown, optional)
void llama_backend_free(void);
```

```c
// Initialize NUMA optimization (call after llama_backend_init if on NUMA systems)
void llama_numa_init(enum ggml_numa_strategy numa);
```

**Typical initialization sequence:**

```c
ggml_backend_load_all();   // Load dynamic GPU backends
llama_backend_init();      // Initialize llama internals (optional -- called automatically)
// ... use the library ...
llama_backend_free();      // Cleanup (optional)
```

Note: `llama_backend_init()` is called automatically by `llama_model_load_from_file()` if not already initialized, so explicit calls are optional in most cases. However, `ggml_backend_load_all()` must be called explicitly to enable GPU backends.

---

## 5. Model Loading and Management

### Loading Models

```c
// Load a model from a single GGUF file
struct llama_model * llama_model_load_from_file(
    const char * path_model,
    struct llama_model_params params
);
```

```c
// Load a model from multiple split GGUF files
struct llama_model * llama_model_load_from_splits(
    const char ** paths,      // Array of file paths
    size_t n_paths,           // Number of paths
    struct llama_model_params params
);
```

```c
// Save a model to a GGUF file
void llama_model_save_to_file(
    const struct llama_model * model,
    const char * path_model
);
```

```c
// Free a loaded model
void llama_model_free(struct llama_model * model);
```

### Default Parameters

```c
// Get default model loading parameters
struct llama_model_params llama_model_default_params(void);
```

Default values include `n_gpu_layers = 0` (CPU-only), `use_mmap = true`, `use_mlock = false`, `split_mode = LLAMA_SPLIT_MODE_LAYER`.

### Model Information

```c
// Training context size
int32_t llama_model_n_ctx_train(const struct llama_model * model);

// Embedding dimension
int32_t llama_model_n_embd(const struct llama_model * model);

// Input embedding dimension (may differ from n_embd for encoder-decoder models)
int32_t llama_model_n_embd_inp(const struct llama_model * model);

// Output embedding dimension
int32_t llama_model_n_embd_out(const struct llama_model * model);

// Number of layers
int32_t llama_model_n_layer(const struct llama_model * model);

// Number of attention heads
int32_t llama_model_n_head(const struct llama_model * model);

// Number of key-value attention heads
int32_t llama_model_n_head_kv(const struct llama_model * model);

// Sliding window attention size (0 = not used)
int32_t llama_model_n_swa(const struct llama_model * model);

// Model size in bytes
uint64_t llama_model_size(const struct llama_model * model);

// Number of model parameters
uint64_t llama_model_n_params(const struct llama_model * model);

// Write a human-readable model description to buf. Returns the number of chars written.
int32_t llama_model_desc(
    const struct llama_model * model,
    char * buf,
    size_t buf_size
);

// RoPE frequency scale from training
float llama_model_rope_freq_scale_train(const struct llama_model * model);

// RoPE type
enum llama_rope_type llama_model_rope_type(const struct llama_model * model);
```

### Architecture Detection

```c
// True if the model has an encoder (e.g., T5, BART)
bool llama_model_has_encoder(const struct llama_model * model);

// True if the model has a decoder
bool llama_model_has_decoder(const struct llama_model * model);

// True if the model is recurrent (e.g., Mamba, RWKV)
bool llama_model_is_recurrent(const struct llama_model * model);

// True if the model is a hybrid architecture
bool llama_model_is_hybrid(const struct llama_model * model);

// True if the model is a diffusion model
bool llama_model_is_diffusion(const struct llama_model * model);

// Get the decoder start token for encoder-decoder models
llama_token llama_model_decoder_start_token(const struct llama_model * model);
```

### Model Metadata

```c
// Get a metadata value by key. Returns the length of the value, or -1 if not found.
int32_t llama_model_meta_val_str(
    const struct llama_model * model,
    const char * key,
    char * buf,
    size_t buf_size
);

// Get the number of metadata key-value pairs
int32_t llama_model_meta_count(const struct llama_model * model);

// Get metadata key by index
int32_t llama_model_meta_key_by_index(
    const struct llama_model * model,
    int32_t i,
    char * buf,
    size_t buf_size
);

// Get metadata value string by index
int32_t llama_model_meta_val_str_by_index(
    const struct llama_model * model,
    int32_t i,
    char * buf,
    size_t buf_size
);
```

### Chat Template Access

```c
// Get the chat template string embedded in the model.
// Returns NULL if no template is found.
// name: template variant name, or NULL for the default template.
const char * llama_model_chat_template(
    const struct llama_model * model,
    const char * name
);
```

### Vocabulary Access

```c
// Get the vocabulary from a model (the vocab is owned by the model)
const struct llama_vocab * llama_model_get_vocab(const struct llama_model * model);
```

---

## 6. Context Creation

A context holds the inference state (KV cache, compute graph, thread pool) for a given model.

```c
// Create an inference context for a model
struct llama_context * llama_init_from_model(
    struct llama_model * model,
    struct llama_context_params params
);
```

```c
// Free a context (does NOT free the model)
void llama_free(struct llama_context * ctx);
```

```c
// Get default context parameters
struct llama_context_params llama_context_default_params(void);
```

### Context Query Functions

```c
// Get the actual context size (may differ from requested n_ctx)
uint32_t llama_n_ctx(const struct llama_context * ctx);

// Get the per-sequence context size
uint32_t llama_n_ctx_seq(const struct llama_context * ctx);

// Get the batch size
uint32_t llama_n_batch(const struct llama_context * ctx);

// Get the micro-batch size
uint32_t llama_n_ubatch(const struct llama_context * ctx);

// Get the max number of parallel sequences
uint32_t llama_n_seq_max(const struct llama_context * ctx);

// Get the model associated with this context
const struct llama_model * llama_get_model(const struct llama_context * ctx);

// Get the pooling type in use
enum llama_pooling_type llama_pooling_type(const struct llama_context * ctx);
```

### Context Configuration

```c
// Set the number of threads for single-token decode and batch processing
void llama_set_n_threads(
    struct llama_context * ctx,
    int32_t n_threads,
    int32_t n_threads_batch
);

// Query thread counts
int32_t llama_n_threads(struct llama_context * ctx);
int32_t llama_n_threads_batch(struct llama_context * ctx);

// Enable/disable embedding extraction mode
void llama_set_embeddings(struct llama_context * ctx, bool embeddings);

// Enable/disable causal attention mask
void llama_set_causal_attn(struct llama_context * ctx, bool causal_attn);

// Enable/disable warmup mode (for pre-filling caches)
void llama_set_warmup(struct llama_context * ctx, bool warmup);

// Set an abort callback that can cancel in-progress computation
void llama_set_abort_callback(
    struct llama_context * ctx,
    ggml_abort_callback abort_callback,
    void * abort_callback_data
);

// Wait for all pending async operations to complete
void llama_synchronize(struct llama_context * ctx);
```

---

## 7. Tokenization

### Tokenizing Text

```c
// Tokenize a string into token IDs.
//
// Two-pass pattern:
//   1. Call with tokens=NULL, n_tokens_max=0 to get the negative token count
//   2. Negate the result to get the actual count, allocate buffer, call again
//
// Parameters:
//   vocab          - The vocabulary (from llama_model_get_vocab)
//   text           - Input string
//   text_len       - Length of input string (in bytes)
//   tokens         - Output token buffer (or NULL for counting)
//   n_tokens_max   - Size of output buffer (or 0 for counting)
//   add_special    - Add BOS/EOS tokens as appropriate for the model
//   parse_special  - Parse and handle special tokens in the text
//
// Returns:
//   On success: number of tokens written
//   If buffer too small: negative number whose absolute value is the required size
int32_t llama_tokenize(
    const struct llama_vocab * vocab,
    const char * text,
    int32_t text_len,
    llama_token * tokens,
    int32_t n_tokens_max,
    bool add_special,
    bool parse_special
);
```

**Two-pass tokenization pattern:**

```c
const llama_vocab * vocab = llama_model_get_vocab(model);

// Pass 1: get token count (returns negative count)
const int n_tokens = -llama_tokenize(vocab, text, strlen(text), NULL, 0, true, true);

// Pass 2: tokenize into buffer
std::vector<llama_token> tokens(n_tokens);
if (llama_tokenize(vocab, text, strlen(text), tokens.data(), tokens.size(), true, true) < 0) {
    // handle error
}
```

### Detokenizing

```c
// Convert a single token to its text representation.
//
// Parameters:
//   vocab   - The vocabulary
//   token   - Token ID to convert
//   buf     - Output buffer
//   length  - Size of output buffer
//   lstrip  - Number of leading spaces to strip (0 = keep all)
//   special - If true, render special tokens as their text representation
//
// Returns: number of bytes written, or negative if buffer too small
int32_t llama_token_to_piece(
    const struct llama_vocab * vocab,
    llama_token token,
    char * buf,
    int32_t length,
    int32_t lstrip,
    bool special
);
```

```c
// Detokenize a sequence of tokens into a string.
//
// Parameters:
//   vocab            - The vocabulary
//   tokens           - Array of token IDs
//   n_tokens         - Number of tokens
//   text             - Output buffer
//   text_len_max     - Size of output buffer
//   remove_special   - Remove special tokens from output
//   unparse_special  - If true, render special tokens as text instead of removing
//
// Returns: number of bytes written, or negative if buffer too small
int32_t llama_detokenize(
    const struct llama_vocab * vocab,
    const llama_token * tokens,
    int32_t n_tokens,
    char * text,
    int32_t text_len_max,
    bool remove_special,
    bool unparse_special
);
```

### Special Tokens

```c
// Get special token IDs (returns LLAMA_TOKEN_NULL if not available)
llama_token llama_vocab_bos(const struct llama_vocab * vocab);  // Beginning of sequence
llama_token llama_vocab_eos(const struct llama_vocab * vocab);  // End of sequence
llama_token llama_vocab_eot(const struct llama_vocab * vocab);  // End of turn
llama_token llama_vocab_sep(const struct llama_vocab * vocab);  // Separator
llama_token llama_vocab_nl(const struct llama_vocab * vocab);   // Newline
llama_token llama_vocab_pad(const struct llama_vocab * vocab);  // Padding
llama_token llama_vocab_mask(const struct llama_vocab * vocab); // Mask token (for MLM)

// Fill-in-the-Middle (FIM) tokens
llama_token llama_vocab_fim_pre(const struct llama_vocab * vocab);  // FIM prefix
llama_token llama_vocab_fim_suf(const struct llama_vocab * vocab);  // FIM suffix
llama_token llama_vocab_fim_mid(const struct llama_vocab * vocab);  // FIM middle
llama_token llama_vocab_fim_pad(const struct llama_vocab * vocab);  // FIM padding
llama_token llama_vocab_fim_rep(const struct llama_vocab * vocab);  // FIM repo
llama_token llama_vocab_fim_sep(const struct llama_vocab * vocab);  // FIM separator
```

### Token Queries

```c
// Check if a token is an end-of-generation token (EOS, EOT, etc.)
bool llama_vocab_is_eog(const struct llama_vocab * vocab, llama_token token);

// Check if a token is a control token
bool llama_vocab_is_control(const struct llama_vocab * vocab, llama_token token);

// Get the text representation of a token
const char * llama_vocab_get_text(const struct llama_vocab * vocab, llama_token token);

// Get the score/probability of a token
float llama_vocab_get_score(const struct llama_vocab * vocab, llama_token token);

// Get token attributes (bitmask of llama_token_attr)
enum llama_token_attr llama_vocab_get_attr(const struct llama_vocab * vocab, llama_token token);

// Check whether the model wants BOS/EOS added during tokenization
bool llama_vocab_get_add_bos(const struct llama_vocab * vocab);
bool llama_vocab_get_add_eos(const struct llama_vocab * vocab);
bool llama_vocab_get_add_sep(const struct llama_vocab * vocab);
```

### Vocabulary Info

```c
// Get the vocabulary type
enum llama_vocab_type llama_vocab_type(const struct llama_vocab * vocab);

// Get the total number of tokens in the vocabulary
int32_t llama_vocab_n_tokens(const struct llama_vocab * vocab);

// Convenience (on model directly, equivalent to llama_vocab_n_tokens)
int32_t llama_n_vocab(const struct llama_vocab * vocab);
```

---

## 8. Batch and Decoding

### Creating Batches

```c
// Create a batch from a contiguous array of tokens.
// All tokens are assigned to sequence 0.
// Only the last token has logits enabled (logits[n_tokens-1] = 1).
// The returned batch does NOT own the token array -- the caller must keep it alive.
struct llama_batch llama_batch_get_one(
    llama_token * tokens,
    int32_t n_tokens
);
```

```c
// Allocate a batch with capacity for n_tokens.
// The caller must fill in the arrays (token/embd, pos, seq_id, logits).
//
// Parameters:
//   n_tokens  - Maximum number of tokens the batch can hold
//   embd      - Embedding dimension (0 for token-based batches)
//   n_seq_max - Maximum number of sequence IDs per token
//
// Must be freed with llama_batch_free().
struct llama_batch llama_batch_init(
    int32_t n_tokens,
    int32_t embd,
    int32_t n_seq_max
);
```

```c
// Free a batch allocated with llama_batch_init()
void llama_batch_free(struct llama_batch batch);
```

### Decoding (Inference)

```c
// Process a batch through the transformer model.
//
// Updates the KV cache and computes logits for tokens that have logits[i] = 1.
//
// Returns:
//    0 - Success
//    1 - Could not find a KV slot for the batch (try reducing batch size
//        or clearing/defragmenting the KV cache)
//    2 - Aborted (via abort callback)
//   -1 - Invalid arguments or other error
//
// For multi-token batches, call llama_synchronize() after llama_decode()
// before reading logits, unless using llama_batch_get_one().
int32_t llama_decode(
    struct llama_context * ctx,
    struct llama_batch batch
);
```

```c
// Process a batch through the encoder part of an encoder-decoder model.
// After encoding, use llama_decode() for the decoder.
int32_t llama_encode(
    struct llama_context * ctx,
    struct llama_batch batch
);
```

```c
// Wait for all async decode/encode operations to complete.
// Must be called before reading logits or embeddings if the batch
// was submitted asynchronously.
void llama_synchronize(struct llama_context * ctx);
```

---

## 9. Output Access

### Logits

```c
// Get the logits for the last call to llama_decode().
// Returns a pointer to an array of shape [n_outputs * n_vocab].
// n_outputs is the number of tokens that had logits[i] = 1 in the batch.
// The pointer is valid until the next llama_decode() call.
float * llama_get_logits(struct llama_context * ctx);
```

```c
// Get logits for a specific output index.
// Equivalent to llama_get_logits(ctx) + i * n_vocab.
// For llama_batch_get_one(), use i = -1 to get the last token's logits.
float * llama_get_logits_ith(struct llama_context * ctx, int32_t i);
```

### Embeddings

```c
// Get the embeddings for the last call to llama_decode()/llama_encode().
// Returns a pointer to an array of shape [n_outputs * n_embd].
// Only available when context was created with embeddings = true.
float * llama_get_embeddings(struct llama_context * ctx);
```

```c
// Get embeddings for a specific output index
float * llama_get_embeddings_ith(struct llama_context * ctx, int32_t i);
```

```c
// Get pooled embeddings for a specific sequence ID.
// Only meaningful when pooling_type != NONE.
float * llama_get_embeddings_seq(struct llama_context * ctx, llama_seq_id seq_id);
```

---

## 10. Sampling API (Chain Pattern)

The llama.cpp sampling system uses a **chain pattern**: you create a sampler chain, add individual samplers to it in order, then call `llama_sampler_sample()` to pick a token. The chain applies each sampler in sequence to the logits, then the final sampler selects a token.

### Chain Management

```c
// Create a new sampler chain
struct llama_sampler * llama_sampler_chain_init(
    struct llama_sampler_chain_params params
);
```

```c
// Get default sampler chain params
struct llama_sampler_chain_params llama_sampler_chain_default_params(void);
```

```c
// Add a sampler to the end of the chain. The chain takes ownership.
void llama_sampler_chain_add(
    struct llama_sampler * chain,
    struct llama_sampler * smpl
);
```

```c
// Get the i-th sampler from the chain (does not transfer ownership)
struct llama_sampler * llama_sampler_chain_get(
    struct llama_sampler * chain,
    int32_t i
);
```

```c
// Get the number of samplers in the chain
int llama_sampler_chain_n(const struct llama_sampler * chain);
```

```c
// Remove and return the i-th sampler from the chain (caller takes ownership)
struct llama_sampler * llama_sampler_chain_remove(
    struct llama_sampler * chain,
    int32_t i
);
```

### Sampling a Token

```c
// Sample the next token from context at the given output index.
// Applies all samplers in the chain, then returns the selected token.
//
// idx: output index in the batch (-1 for the last output, which is the common case)
//
// This function also calls llama_sampler_accept() on the chain with the result.
llama_token llama_sampler_sample(
    struct llama_sampler * smpl,
    struct llama_context * ctx,
    int32_t idx
);
```

### Sampler Lifecycle

```c
// Inform the sampler that a token was accepted (updates internal state)
void llama_sampler_accept(struct llama_sampler * smpl, llama_token token);

// Reset the sampler to its initial state
void llama_sampler_reset(struct llama_sampler * smpl);

// Deep-clone a sampler (including internal state)
struct llama_sampler * llama_sampler_clone(const struct llama_sampler * smpl);

// Free a sampler (or sampler chain, which also frees all contained samplers)
void llama_sampler_free(struct llama_sampler * smpl);

// Get the name of a sampler
const char * llama_sampler_name(const struct llama_sampler * smpl);

// Get the current RNG seed of a sampler (if applicable)
uint32_t llama_sampler_get_seed(const struct llama_sampler * smpl);
```

### Built-in Samplers

Each `llama_sampler_init_*` function returns a `struct llama_sampler *` that can be added to a chain.

#### Greedy Sampling

```c
// Always select the token with the highest logit
struct llama_sampler * llama_sampler_init_greedy(void);
```

#### Stochastic Sampling

```c
// Randomly sample from the probability distribution
// seed: RNG seed (LLAMA_DEFAULT_SEED for random)
struct llama_sampler * llama_sampler_init_dist(uint32_t seed);
```

#### Top-K Sampling

```c
// Keep only the top k tokens with highest logits
// k: number of tokens to keep (0 = disabled)
struct llama_sampler * llama_sampler_init_top_k(int32_t k);
```

#### Top-P (Nucleus) Sampling

```c
// Keep tokens whose cumulative probability exceeds p
// p: cumulative probability threshold (1.0 = disabled)
// min_keep: minimum number of tokens to keep
struct llama_sampler * llama_sampler_init_top_p(float p, size_t min_keep);
```

#### Min-P Sampling

```c
// Keep tokens whose probability is at least p times the top token's probability
// p: minimum probability ratio (0.0 = disabled)
// min_keep: minimum number of tokens to keep
struct llama_sampler * llama_sampler_init_min_p(float p, size_t min_keep);
```

#### Typical Sampling

```c
// Locally typical sampling -- keeps tokens close to the expected information content
// p: typical probability mass (1.0 = disabled)
// min_keep: minimum number of tokens to keep
struct llama_sampler * llama_sampler_init_typical(float p, size_t min_keep);
```

#### Temperature

```c
// Apply temperature scaling to logits
// t: temperature (1.0 = no effect, 0.0 = greedy, >1.0 = more random)
struct llama_sampler * llama_sampler_init_temp(float t);
```

```c
// Dynamic temperature with range
// t: base temperature
// delta: temperature range (0 = static temperature)
// exponent: controls how temperature varies with entropy
struct llama_sampler * llama_sampler_init_temp_ext(float t, float delta, float exponent);
```

#### XTC (Exclude Top Choices)

```c
// XTC sampling -- exclude top choices to increase diversity
// p: probability of applying XTC
// t: threshold for excluding top tokens
// min_keep: minimum number of tokens to keep
// seed: RNG seed
struct llama_sampler * llama_sampler_init_xtc(
    float p, float t, size_t min_keep, uint32_t seed
);
```

#### Top-N Sigma

```c
// Keep tokens within n standard deviations of the top logit
// n: number of standard deviations
struct llama_sampler * llama_sampler_init_top_n_sigma(float n);
```

#### Mirostat

```c
// Mirostat v1 -- perplexity-controlled sampling
// n_vocab: vocabulary size
// seed: RNG seed
// tau: target entropy
// eta: learning rate
// m: number of tokens to consider
struct llama_sampler * llama_sampler_init_mirostat(
    int32_t n_vocab, uint32_t seed, float tau, float eta, int32_t m
);
```

```c
// Mirostat v2 -- simplified perplexity-controlled sampling
// seed: RNG seed
// tau: target entropy
// eta: learning rate
struct llama_sampler * llama_sampler_init_mirostat_v2(
    uint32_t seed, float tau, float eta
);
```

#### Grammar-Constrained Sampling

```c
// Constrain output to a GBNF grammar
// vocab: vocabulary
// grammar_str: GBNF grammar string
// grammar_root: root rule name
struct llama_sampler * llama_sampler_init_grammar(
    const struct llama_vocab * vocab,
    const char * grammar_str,
    const char * grammar_root
);
```

```c
// Lazy grammar -- only activates when a trigger word/token is encountered
struct llama_sampler * llama_sampler_init_grammar_lazy(
    const struct llama_vocab * vocab,
    const char * grammar_str,
    const char * grammar_root,
    const char ** trigger_words,
    size_t num_trigger_words,
    const llama_token * trigger_tokens,
    size_t num_trigger_tokens
);
```

```c
// Lazy grammar with regex trigger patterns
struct llama_sampler * llama_sampler_init_grammar_lazy_patterns(
    const struct llama_vocab * vocab,
    const char * grammar_str,
    const char * grammar_root,
    const char ** trigger_patterns,
    size_t num_trigger_patterns,
    const llama_token * trigger_tokens,
    size_t num_trigger_tokens
);
```

#### Repetition Penalties

```c
// Apply repetition, frequency, and presence penalties
// penalty_last_n: number of recent tokens to consider (0 = disabled, -1 = context size)
// penalty_repeat: repetition penalty (1.0 = disabled)
// penalty_freq: frequency penalty (0.0 = disabled)
// penalty_present: presence penalty (0.0 = disabled)
struct llama_sampler * llama_sampler_init_penalties(
    int32_t penalty_last_n,
    float penalty_repeat,
    float penalty_freq,
    float penalty_present
);
```

#### DRY (Don't Repeat Yourself) Penalty

```c
// DRY repetition penalty -- penalizes repeated n-gram sequences
// vocab: vocabulary (for tokenizing sequence breakers)
// n_ctx_train: training context size of the model
// dry_multiplier: penalty multiplier (0.0 = disabled)
// dry_base: penalty base
// dry_allowed_length: maximum allowed repeated sequence length
// dry_penalty_last_n: lookback window (-1 = context size, 0 = disabled)
// seq_breakers: array of strings that break repetition sequences
// num_breakers: number of sequence breakers
struct llama_sampler * llama_sampler_init_dry(
    const struct llama_vocab * vocab,
    int32_t n_ctx_train,
    float dry_multiplier,
    float dry_base,
    int32_t dry_allowed_length,
    int32_t dry_penalty_last_n,
    const char ** seq_breakers,
    size_t num_breakers
);
```

#### Logit Bias

```c
// Add fixed biases to specific token logits
// n_vocab: vocabulary size
// n_logit_bias: number of bias entries
// logit_bias: array of llama_logit_bias structs
struct llama_sampler * llama_sampler_init_logit_bias(
    int32_t n_vocab,
    int32_t n_logit_bias,
    const llama_logit_bias * logit_bias
);
```

#### Infill Sampler

```c
// Special sampler for fill-in-the-middle (FIM) tasks
// Handles the reordering logic for prefix-suffix-middle token patterns
struct llama_sampler * llama_sampler_init_infill(
    const struct llama_vocab * vocab
);
```

#### Adaptive-P Sampling

```c
// Adaptive probability sampling
// target: target cumulative probability
// decay: decay rate
// seed: RNG seed
struct llama_sampler * llama_sampler_init_adaptive_p(
    float target, float decay, uint32_t seed
);
```

### Typical Sampler Chain Configurations

**Greedy (deterministic):**
```c
llama_sampler * smpl = llama_sampler_chain_init(llama_sampler_chain_default_params());
llama_sampler_chain_add(smpl, llama_sampler_init_greedy());
```

**Creative text generation:**
```c
llama_sampler * smpl = llama_sampler_chain_init(llama_sampler_chain_default_params());
llama_sampler_chain_add(smpl, llama_sampler_init_top_k(40));
llama_sampler_chain_add(smpl, llama_sampler_init_top_p(0.95f, 1));
llama_sampler_chain_add(smpl, llama_sampler_init_min_p(0.05f, 1));
llama_sampler_chain_add(smpl, llama_sampler_init_temp(0.8f));
llama_sampler_chain_add(smpl, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));
```

**Chat (balanced):**
```c
llama_sampler * smpl = llama_sampler_chain_init(llama_sampler_chain_default_params());
llama_sampler_chain_add(smpl, llama_sampler_init_min_p(0.05f, 1));
llama_sampler_chain_add(smpl, llama_sampler_init_temp(0.8f));
llama_sampler_chain_add(smpl, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));
```

**With repetition penalty:**
```c
llama_sampler * smpl = llama_sampler_chain_init(llama_sampler_chain_default_params());
llama_sampler_chain_add(smpl, llama_sampler_init_penalties(64, 1.1f, 0.0f, 0.0f));
llama_sampler_chain_add(smpl, llama_sampler_init_top_k(40));
llama_sampler_chain_add(smpl, llama_sampler_init_top_p(0.95f, 1));
llama_sampler_chain_add(smpl, llama_sampler_init_temp(0.8f));
llama_sampler_chain_add(smpl, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));
```

---

## 11. Chat Templates

### Applying Chat Templates

```c
// Format a conversation using a chat template (e.g., ChatML, Llama3, etc.).
//
// Uses Jinja-like template syntax. Supports incremental formatting:
// format the full conversation, then on the next turn, format again and
// take only the new portion (from prev_len to new_len).
//
// Parameters:
//   tmpl    - Template string (NULL to use a built-in default, e.g., ChatML)
//   chat    - Array of chat messages
//   n_msg   - Number of messages
//   add_ass - If true, append the assistant turn prefix (for generation)
//   buf     - Output buffer (NULL to just compute the required size)
//   length  - Size of the output buffer
//
// Returns: number of bytes written (or required if buf is NULL), -1 on error
int32_t llama_chat_apply_template(
    const char * tmpl,
    const struct llama_chat_message * chat,
    size_t n_msg,
    bool add_ass,
    char * buf,
    int32_t length
);
```

```c
// List all built-in template names
// output: array of string pointers to fill
// len: size of the output array
// Returns: number of templates available
int32_t llama_chat_builtin_templates(const char ** output, size_t len);
```

### Incremental Chat Template Pattern

The standard pattern for multi-turn chat is to format the entire conversation each turn and use string slicing to extract only the new portion (the user's message formatted with the template, plus the assistant prefix). This avoids re-processing already-decoded tokens.

```c
std::vector<llama_chat_message> messages;
std::vector<char> formatted(n_ctx);
int prev_len = 0;

// Each turn:
messages.push_back({"user", user_input});

const char * tmpl = llama_model_chat_template(model, NULL);
int new_len = llama_chat_apply_template(tmpl, messages.data(), messages.size(),
                                         true, formatted.data(), formatted.size());
if (new_len > (int)formatted.size()) {
    formatted.resize(new_len);
    new_len = llama_chat_apply_template(tmpl, messages.data(), messages.size(),
                                         true, formatted.data(), formatted.size());
}

// Extract only the new text to tokenize and decode
std::string prompt(formatted.begin() + prev_len, formatted.begin() + new_len);

// ... generate response ...

messages.push_back({"assistant", response});

// Update prev_len (without assistant prefix this time, so add_ass = false)
prev_len = llama_chat_apply_template(tmpl, messages.data(), messages.size(),
                                      false, nullptr, 0);
```

---

## 12. Memory / KV Cache Management

The KV cache is accessed via `llama_memory_t`, obtained from `llama_get_memory()`. All operations use sequence IDs (`llama_seq_id`) and position ranges.

```c
// Get the memory handle from a context
llama_memory_t llama_get_memory(const struct llama_context * ctx);
```

```c
// Clear all KV cache data
// data: if true, also clear the data buffers (not just metadata)
void llama_memory_clear(llama_memory_t mem, bool data);
```

```c
// Remove tokens in position range [p0, p1) for a sequence.
// seq_id: sequence to modify (-1 = all sequences)
// p0: start position (inclusive)
// p1: end position (exclusive, -1 = end)
// Returns false if the operation could not be completed.
bool llama_memory_seq_rm(
    llama_memory_t mem,
    llama_seq_id seq_id,
    llama_pos p0,
    llama_pos p1
);
```

```c
// Copy token data from one sequence to another in range [p0, p1).
// Creates a "fork" of the KV cache data for parallel generation.
void llama_memory_seq_cp(
    llama_memory_t mem,
    llama_seq_id seq_id_src,
    llama_seq_id seq_id_dst,
    llama_pos p0,
    llama_pos p1
);
```

```c
// Remove all token data except for the specified sequence
void llama_memory_seq_keep(llama_memory_t mem, llama_seq_id seq_id);
```

```c
// Shift token positions for a sequence in range [p0, p1) by delta.
// Used for context shifting (sliding window): shift positions left to
// make room for new tokens.
// Negative delta shifts positions toward 0.
void llama_memory_seq_add(
    llama_memory_t mem,
    llama_seq_id seq_id,
    llama_pos p0,
    llama_pos p1,
    llama_pos delta
);
```

```c
// Divide positions in [p0, p1) by d (integer division).
// Used for some context compression techniques.
void llama_memory_seq_div(
    llama_memory_t mem,
    llama_seq_id seq_id,
    llama_pos p0,
    llama_pos p1,
    int d
);
```

```c
// Get the minimum position stored for a sequence
// Returns -1 if the sequence is empty.
llama_pos llama_memory_seq_pos_min(llama_memory_t mem, llama_seq_id seq_id);
```

```c
// Get the maximum position stored for a sequence
// Returns -1 if the sequence is empty.
llama_pos llama_memory_seq_pos_max(llama_memory_t mem, llama_seq_id seq_id);
```

```c
// Check if the memory supports context shifting
bool llama_memory_can_shift(llama_memory_t mem);
```

---

## 13. State Serialization

Save and restore the complete context state (including KV cache) for session resumption.

### Full Context State

```c
// Get the size needed to store the full context state
size_t llama_state_get_size(struct llama_context * ctx);
```

```c
// Copy the context state to a buffer
// dst: destination buffer (must be at least llama_state_get_size() bytes)
// size: size of the destination buffer
// Returns: number of bytes written
size_t llama_state_get_data(
    struct llama_context * ctx,
    uint8_t * dst,
    size_t size
);
```

```c
// Restore context state from a buffer
// src: source buffer
// size: size of the source buffer
// Returns: number of bytes read
size_t llama_state_set_data(
    struct llama_context * ctx,
    const uint8_t * src,
    size_t size
);
```

### File-Based State

```c
// Save context state and token history to a file
// path_session: file path to save to
// tokens: array of token IDs representing the session history
// n_token_count: number of tokens
bool llama_state_save_file(
    struct llama_context * ctx,
    const char * path_session,
    const llama_token * tokens,
    size_t n_token_count
);
```

```c
// Load context state and token history from a file
// path_session: file path to load from
// tokens_out: buffer to receive the token history
// n_token_capacity: size of the token buffer
// n_token_count_out: receives the actual number of tokens loaded
bool llama_state_load_file(
    struct llama_context * ctx,
    const char * path_session,
    llama_token * tokens_out,
    size_t n_token_capacity,
    size_t * n_token_count_out
);
```

### Per-Sequence State

```c
// Get the size needed to store a single sequence's state
size_t llama_state_seq_get_size(struct llama_context * ctx, llama_seq_id seq_id);

// Copy a single sequence's state to a buffer
size_t llama_state_seq_get_data(
    struct llama_context * ctx,
    uint8_t * dst,
    size_t size,
    llama_seq_id seq_id
);

// Restore a single sequence's state from a buffer
size_t llama_state_seq_set_data(
    struct llama_context * ctx,
    const uint8_t * src,
    size_t size,
    llama_seq_id dest_seq_id
);

// Save a single sequence's state to a file
size_t llama_state_seq_save_file(
    struct llama_context * ctx,
    const char * filepath,
    llama_seq_id seq_id,
    const llama_token * tokens,
    size_t n_token_count
);

// Load a single sequence's state from a file
size_t llama_state_seq_load_file(
    struct llama_context * ctx,
    const char * filepath,
    llama_seq_id dest_seq_id,
    llama_token * tokens_out,
    size_t n_token_capacity,
    size_t * n_token_count_out
);
```

---

## 14. LoRA Adapters

Load and apply LoRA (Low-Rank Adaptation) adapters to a model at runtime.

```c
// Load a LoRA adapter from a file and associate it with a model.
// The model must remain loaded for the adapter's lifetime.
// Returns NULL on failure.
struct llama_adapter_lora * llama_adapter_lora_init(
    struct llama_model * model,
    const char * path_lora
);
```

```c
// Apply one or more LoRA adapters to a context with per-adapter scaling.
// adapters: array of adapter pointers
// n_adapters: number of adapters
// scales: array of scale factors (one per adapter; 1.0 = full strength)
// Returns 0 on success, negative on error.
int32_t llama_set_adapters_lora(
    struct llama_context * ctx,
    struct llama_adapter_lora ** adapters,
    size_t n_adapters,
    float * scales
);
```

```c
// Free a LoRA adapter
void llama_adapter_lora_free(struct llama_adapter_lora * adapter);
```

### LoRA Adapter Metadata

```c
// Get a metadata value from the adapter by key
int32_t llama_adapter_meta_val_str(
    const struct llama_adapter_lora * adapter,
    const char * key,
    char * buf,
    size_t buf_size
);

// Get the number of metadata entries
int32_t llama_adapter_meta_count(const struct llama_adapter_lora * adapter);

// Get metadata key by index
int32_t llama_adapter_meta_key_by_index(
    const struct llama_adapter_lora * adapter,
    int32_t i,
    char * buf,
    size_t buf_size
);

// Get metadata value string by index
int32_t llama_adapter_meta_val_str_by_index(
    const struct llama_adapter_lora * adapter,
    int32_t i,
    char * buf,
    size_t buf_size
);
```

### Control Vector

```c
// Apply a control vector to the context (for steering model behavior).
// data: control vector data
// len: length of the data
// n_embd: embedding dimension
// il_start: start layer (inclusive)
// il_end: end layer (inclusive)
// Returns 0 on success.
int32_t llama_set_adapter_cvec(
    struct llama_context * ctx,
    const float * data,
    size_t len,
    int32_t n_embd,
    int32_t il_start,
    int32_t il_end
);
```

---

## 15. Quantization

Quantize a model file to a smaller format.

```c
// Quantize a model from fname_inp and write the result to fname_out.
// Returns 0 on success, non-zero on error.
uint32_t llama_model_quantize(
    const char * fname_inp,
    const char * fname_out,
    const llama_model_quantize_params * params
);
```

```c
// Get default quantization parameters
struct llama_model_quantize_params llama_model_quantize_default_params(void);
```

**Quantization example:**

```c
llama_model_quantize_params qparams = llama_model_quantize_default_params();
qparams.nthread = 8;
qparams.ftype = LLAMA_FTYPE_MOSTLY_Q4_K_M;  // Good balance of size and quality

uint32_t result = llama_model_quantize("model-f16.gguf", "model-q4km.gguf", &qparams);
if (result != 0) {
    fprintf(stderr, "Quantization failed with code %u\n", result);
}
```

---

## 16. C++ RAII Wrappers (llama-cpp.h)

The header `llama-cpp.h` (C++ only) provides `std::unique_ptr` typedefs with custom deleters for automatic resource management.

```cpp
#pragma once

#ifndef __cplusplus
#error "This header is for C++ only"
#endif

#include <memory>
#include "llama.h"

struct llama_model_deleter {
    void operator()(llama_model * model) { llama_model_free(model); }
};

struct llama_context_deleter {
    void operator()(llama_context * context) { llama_free(context); }
};

struct llama_sampler_deleter {
    void operator()(llama_sampler * sampler) { llama_sampler_free(sampler); }
};

struct llama_adapter_lora_deleter {
    void operator()(llama_adapter_lora * adapter) { llama_adapter_lora_free(adapter); }
};

typedef std::unique_ptr<llama_model,        llama_model_deleter>        llama_model_ptr;
typedef std::unique_ptr<llama_context,       llama_context_deleter>      llama_context_ptr;
typedef std::unique_ptr<llama_sampler,       llama_sampler_deleter>      llama_sampler_ptr;
typedef std::unique_ptr<llama_adapter_lora,  llama_adapter_lora_deleter> llama_adapter_lora_ptr;
```

**Usage example:**

```cpp
#include "llama-cpp.h"

// Model and context are automatically freed when they go out of scope
llama_model_ptr model(llama_model_load_from_file("model.gguf", llama_model_default_params()));
if (!model) { /* handle error */ }

llama_context_ptr ctx(llama_init_from_model(model.get(), llama_context_default_params()));
if (!ctx) { /* handle error */ }

llama_sampler_ptr smpl(llama_sampler_chain_init(llama_sampler_chain_default_params()));
llama_sampler_chain_add(smpl.get(), llama_sampler_init_greedy());

// No need to manually call llama_model_free, llama_free, or llama_sampler_free
```

---

## 17. Complete Working Examples

### Example 1: Minimal Inference (simple.cpp pattern)

Loads a model, tokenizes a prompt, runs the decode loop, samples tokens, and prints the output.

```cpp
#include "llama.h"
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

int main(int argc, char ** argv) {
    const char * model_path = "model.gguf";
    const char * prompt = "Hello my name is";
    int n_predict = 32;
    int ngl = 99;  // GPU layers to offload

    // --- 1. Initialize backends ---
    ggml_backend_load_all();

    // --- 2. Load model ---
    llama_model_params model_params = llama_model_default_params();
    model_params.n_gpu_layers = ngl;

    llama_model * model = llama_model_load_from_file(model_path, model_params);
    if (!model) {
        fprintf(stderr, "Error: unable to load model\n");
        return 1;
    }

    const llama_vocab * vocab = llama_model_get_vocab(model);

    // --- 3. Tokenize the prompt (two-pass pattern) ---
    const int n_prompt = -llama_tokenize(vocab, prompt, strlen(prompt), NULL, 0, true, true);

    std::vector<llama_token> prompt_tokens(n_prompt);
    if (llama_tokenize(vocab, prompt, strlen(prompt),
                       prompt_tokens.data(), prompt_tokens.size(), true, true) < 0) {
        fprintf(stderr, "Error: failed to tokenize the prompt\n");
        return 1;
    }

    // --- 4. Create context ---
    llama_context_params ctx_params = llama_context_default_params();
    ctx_params.n_ctx   = n_prompt + n_predict - 1;
    ctx_params.n_batch = n_prompt;
    ctx_params.no_perf = false;

    llama_context * ctx = llama_init_from_model(model, ctx_params);
    if (!ctx) {
        fprintf(stderr, "Error: failed to create llama_context\n");
        return 1;
    }

    // --- 5. Create sampler ---
    auto sparams = llama_sampler_chain_default_params();
    sparams.no_perf = false;
    llama_sampler * smpl = llama_sampler_chain_init(sparams);
    llama_sampler_chain_add(smpl, llama_sampler_init_greedy());

    // --- 6. Print the prompt tokens ---
    for (auto id : prompt_tokens) {
        char buf[128];
        int n = llama_token_to_piece(vocab, id, buf, sizeof(buf), 0, true);
        if (n > 0) printf("%.*s", n, buf);
    }

    // --- 7. Prepare initial batch ---
    llama_batch batch = llama_batch_get_one(prompt_tokens.data(), prompt_tokens.size());

    // Handle encoder-decoder models
    if (llama_model_has_encoder(model)) {
        llama_encode(ctx, batch);
        llama_token decoder_start = llama_model_decoder_start_token(model);
        if (decoder_start == LLAMA_TOKEN_NULL) {
            decoder_start = llama_vocab_bos(vocab);
        }
        batch = llama_batch_get_one(&decoder_start, 1);
    }

    // --- 8. Decode loop ---
    int n_decode = 0;

    for (int n_pos = 0; n_pos + batch.n_tokens < n_prompt + n_predict; ) {
        if (llama_decode(ctx, batch)) {
            fprintf(stderr, "Error: llama_decode() failed\n");
            return 1;
        }
        n_pos += batch.n_tokens;

        // Sample the next token
        llama_token new_token_id = llama_sampler_sample(smpl, ctx, -1);

        // Check for end of generation
        if (llama_vocab_is_eog(vocab, new_token_id)) {
            break;
        }

        // Print the token
        char buf[128];
        int n = llama_token_to_piece(vocab, new_token_id, buf, sizeof(buf), 0, true);
        if (n > 0) {
            printf("%.*s", n, buf);
            fflush(stdout);
        }

        // Prepare next batch (single token)
        batch = llama_batch_get_one(&new_token_id, 1);
        n_decode++;
    }

    printf("\n");

    // --- 9. Print performance stats ---
    llama_perf_sampler_print(smpl);
    llama_perf_context_print(ctx);

    // --- 10. Cleanup ---
    llama_sampler_free(smpl);
    llama_free(ctx);
    llama_model_free(model);

    return 0;
}
```

### Example 2: Multi-Turn Chat Loop (simple-chat.cpp pattern)

Interactive chat with chat template formatting, multi-turn conversation history, and KV cache reuse.

```cpp
#include "llama.h"
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char ** argv) {
    const char * model_path = "model.gguf";
    int ngl   = 99;
    int n_ctx = 2048;

    // --- 1. Suppress non-error log output ---
    llama_log_set([](enum ggml_log_level level, const char * text, void *) {
        if (level >= GGML_LOG_LEVEL_ERROR) {
            fprintf(stderr, "%s", text);
        }
    }, nullptr);

    // --- 2. Initialize ---
    ggml_backend_load_all();

    llama_model_params model_params = llama_model_default_params();
    model_params.n_gpu_layers = ngl;

    llama_model * model = llama_model_load_from_file(model_path, model_params);
    if (!model) {
        fprintf(stderr, "Error: unable to load model\n");
        return 1;
    }

    const llama_vocab * vocab = llama_model_get_vocab(model);

    llama_context_params ctx_params = llama_context_default_params();
    ctx_params.n_ctx   = n_ctx;
    ctx_params.n_batch = n_ctx;

    llama_context * ctx = llama_init_from_model(model, ctx_params);
    if (!ctx) {
        fprintf(stderr, "Error: failed to create llama_context\n");
        return 1;
    }

    // --- 3. Create sampler (min_p + temperature + dist) ---
    llama_sampler * smpl = llama_sampler_chain_init(llama_sampler_chain_default_params());
    llama_sampler_chain_add(smpl, llama_sampler_init_min_p(0.05f, 1));
    llama_sampler_chain_add(smpl, llama_sampler_init_temp(0.8f));
    llama_sampler_chain_add(smpl, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));

    // --- 4. Generation helper (uses KV cache for multi-turn) ---
    auto generate = [&](const std::string & prompt) -> std::string {
        std::string response;

        // Determine if this is the first turn (empty KV cache)
        const bool is_first = llama_memory_seq_pos_max(llama_get_memory(ctx), 0) == -1;

        // Tokenize the prompt
        const int n_prompt_tokens = -llama_tokenize(vocab, prompt.c_str(), prompt.size(),
                                                     NULL, 0, is_first, true);
        std::vector<llama_token> prompt_tokens(n_prompt_tokens);
        if (llama_tokenize(vocab, prompt.c_str(), prompt.size(),
                           prompt_tokens.data(), prompt_tokens.size(),
                           is_first, true) < 0) {
            fprintf(stderr, "Error: failed to tokenize\n");
            return "";
        }

        llama_batch batch = llama_batch_get_one(prompt_tokens.data(), prompt_tokens.size());
        llama_token new_token_id;

        while (true) {
            // Check context space
            int n_ctx_used = llama_memory_seq_pos_max(llama_get_memory(ctx), 0) + 1;
            if (n_ctx_used + batch.n_tokens > (int)llama_n_ctx(ctx)) {
                fprintf(stderr, "Context size exceeded\n");
                break;
            }

            if (llama_decode(ctx, batch) != 0) {
                fprintf(stderr, "Error: llama_decode() failed\n");
                break;
            }

            new_token_id = llama_sampler_sample(smpl, ctx, -1);

            if (llama_vocab_is_eog(vocab, new_token_id)) {
                break;
            }

            char buf[256];
            int n = llama_token_to_piece(vocab, new_token_id, buf, sizeof(buf), 0, true);
            if (n > 0) {
                std::string piece(buf, n);
                printf("%s", piece.c_str());
                fflush(stdout);
                response += piece;
            }

            batch = llama_batch_get_one(&new_token_id, 1);
        }

        return response;
    };

    // --- 5. Chat loop ---
    std::vector<llama_chat_message> messages;
    std::vector<char> formatted(n_ctx);
    int prev_len = 0;

    while (true) {
        printf("\n> ");
        std::string user;
        std::getline(std::cin, user);
        if (user.empty()) break;

        // Get the chat template from the model
        const char * tmpl = llama_model_chat_template(model, nullptr);

        // Add user message and format the conversation
        messages.push_back({"user", strdup(user.c_str())});

        int new_len = llama_chat_apply_template(
            tmpl, messages.data(), messages.size(),
            true, formatted.data(), formatted.size()
        );
        if (new_len > (int)formatted.size()) {
            formatted.resize(new_len);
            new_len = llama_chat_apply_template(
                tmpl, messages.data(), messages.size(),
                true, formatted.data(), formatted.size()
            );
        }
        if (new_len < 0) {
            fprintf(stderr, "Error: failed to apply chat template\n");
            break;
        }

        // Extract only the NEW portion of the formatted text
        std::string prompt(formatted.begin() + prev_len, formatted.begin() + new_len);

        // Generate response
        std::string response = generate(prompt);
        printf("\n");

        // Add assistant response to history
        messages.push_back({"assistant", strdup(response.c_str())});

        // Update prev_len for next incremental format
        prev_len = llama_chat_apply_template(
            tmpl, messages.data(), messages.size(),
            false, nullptr, 0
        );
        if (prev_len < 0) {
            fprintf(stderr, "Error: failed to apply chat template\n");
            break;
        }
    }

    // --- 6. Cleanup ---
    for (auto & msg : messages) {
        free(const_cast<char *>(msg.content));
    }
    llama_sampler_free(smpl);
    llama_free(ctx);
    llama_model_free(model);

    return 0;
}
```

**Key differences between the two examples:**
- **Simple inference** processes a single prompt and generates a fixed number of tokens. The KV cache starts empty and grows linearly.
- **Chat loop** maintains conversation history across turns using the incremental chat template pattern. The KV cache accumulates across turns, so context space management is essential. The `is_first` flag ensures BOS is only added on the first turn.

---

## Appendix: Logging

```c
// Set a custom log callback. Pass NULL to restore the default logger.
void llama_log_set(ggml_log_callback log_callback, void * user_data);

// Get the current log callback and user data
void llama_log_get(ggml_log_callback * log_callback, void ** user_data);
```

## Appendix: Performance Monitoring

```c
// Get performance data for the context
struct llama_perf_context_data llama_perf_context(const struct llama_context * ctx);

// Print context performance stats to stderr
void llama_perf_context_print(const struct llama_context * ctx);

// Reset context performance counters
void llama_perf_context_reset(struct llama_context * ctx);

// Get performance data for a sampler chain
struct llama_perf_sampler_data llama_perf_sampler(const struct llama_sampler * chain);

// Print sampler performance stats to stderr
void llama_perf_sampler_print(const struct llama_sampler * chain);

// Reset sampler performance counters
void llama_perf_sampler_reset(struct llama_sampler * chain);

// Print memory breakdown to stderr
void llama_memory_breakdown_print(const struct llama_context * ctx);
```

## Appendix: System Info and Utility

```c
// Get current time in microseconds
int64_t llama_time_us(void);

// Get maximum number of devices supported
size_t llama_max_devices(void);

// Check backend support
bool llama_supports_mmap(void);
bool llama_supports_mlock(void);
bool llama_supports_gpu_offload(void);
bool llama_supports_rpc(void);

// Get a human-readable string describing available backends and features
const char * llama_print_system_info(void);
```

## Appendix: Model Split Utilities

```c
// Construct a split file path from a prefix, split number, and total count
int32_t llama_split_path(
    char * split_path,
    size_t maxlen,
    const char * path_prefix,
    int32_t split_no,
    int32_t split_count
);

// Extract the prefix from a split file path
int32_t llama_split_prefix(
    char * split_prefix,
    size_t maxlen,
    const char * split_path,
    int32_t split_no,
    int32_t split_count
);
```
