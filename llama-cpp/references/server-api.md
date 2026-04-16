# llama.cpp Server API Reference

Comprehensive reference for the llama.cpp HTTP server (`llama-server`), covering all endpoints, CLI flags, environment variables, and usage patterns.

## Table of Contents

- [1. Starting the Server](#1-starting-the-server)
- [2. Key Server CLI Flags](#2-key-server-cli-flags)
- [3. Environment Variables](#3-environment-variables)
- [4. OpenAI-Compatible Endpoints](#4-openai-compatible-endpoints)
  - [POST /v1/chat/completions](#post-v1chatcompletions)
  - [POST /v1/completions](#post-v1completions)
  - [POST /v1/embeddings](#post-v1embeddings)
  - [GET /v1/models](#get-v1models)
  - [POST /v1/messages](#post-v1messages)
  - [POST /v1/messages/count_tokens](#post-v1messagescount_tokens)
  - [POST /v1/responses](#post-v1responses)
  - [POST /v1/rerank](#post-v1rerank)
- [5. Native llama.cpp Endpoints](#5-native-llamacpp-endpoints)
  - [POST /completion](#post-completion)
  - [POST /embedding](#post-embedding)
  - [POST /tokenize](#post-tokenize)
  - [POST /detokenize](#post-detokenize)
  - [POST /infill](#post-infill)
  - [POST /reranking](#post-reranking)
  - [POST /apply-template](#post-apply-template)
- [6. Management Endpoints](#6-management-endpoints)
  - [GET /health](#get-health)
  - [GET /props and POST /props](#get-props-and-post-props)
  - [GET /slots and POST /slots](#get-slots-and-post-slots)
  - [GET /metrics](#get-metrics)
  - [Model Management](#model-management)
  - [LoRA Adapter Management](#lora-adapter-management)
- [7. Function Calling / Tool Use](#7-function-calling--tool-use)
- [8. Grammar-Constrained Generation](#8-grammar-constrained-generation)
- [9. Multimodal Support](#9-multimodal-support)
- [10. Router Mode](#10-router-mode)
- [11. Speculative Decoding](#11-speculative-decoding)
- [12. Python Client Examples](#12-python-client-examples)

---

## 1. Starting the Server

### Basic usage

```bash
# Load a local GGUF model
llama-server -m model.gguf -c 4096 --port 8080

# From HuggingFace (auto-downloads the GGUF):
llama-server -hf bartowski/Llama-3.3-70B-Instruct-GGUF:Q4_K_M

# With GPU offloading (all layers to GPU)
llama-server -m model.gguf -ngl 99 -c 8192 --port 8080

# Multiple parallel request slots
llama-server -m model.gguf -c 16384 -np 4 --port 8080

# With API key authentication
llama-server -m model.gguf --api-key "my-secret-key" --port 8080

# With TLS/SSL
llama-server -m model.gguf --ssl-key-file key.pem --ssl-cert-file cert.pem --port 8443

# With function calling support
llama-server -hf bartowski/Qwen2.5-7B-Instruct-GGUF:Q4_K_M --jinja -fa

# Router mode (no model, serve multiple models dynamically)
llama-server --port 8080
```

### Verifying the server is running

```bash
curl http://localhost:8080/health
# Returns: {"status":"ok"}
```

---

## 2. Key Server CLI Flags

| Flag | Description | Default |
|------|-------------|---------|
| `-m`, `--model PATH` | Path to the GGUF model file | (required unless router mode) |
| `-hf`, `--hf-repo REPO:FILE` | Download and load model from HuggingFace (e.g. `bartowski/Llama-3.3-70B-Instruct-GGUF:Q4_K_M`) | |
| `-c`, `--ctx-size N` | Context size in tokens. `0` = use model trained context size | `0` |
| `-ngl`, `--gpu-layers N` | Number of layers to offload to GPU. `99` or large number = all layers | `0` |
| `--host HOST` | IP address to listen on | `127.0.0.1` |
| `--port PORT` | Port to listen on | `8080` |
| `-np`, `--parallel N` | Number of parallel request slots (concurrent requests) | `1` |
| `--api-key KEY` | API key for authentication. Clients must send `Authorization: Bearer KEY` | (none) |
| `--api-key-file PATH` | Path to file containing one API key per line (any key is accepted) | (none) |
| `--metrics` | Enable Prometheus-compatible metrics at `/metrics` | disabled |
| `-fa`, `--flash-attn` | Enable flash attention (faster, lower memory usage) | disabled |
| `--reasoning` | Enable reasoning/thinking mode for supported models. Adds `reasoning_content` to responses | disabled |
| `-j`, `--json-schema SCHEMA` | Force output to conform to a JSON schema (as a JSON string) | (none) |
| `--grammar GRAMMAR` | Force output to conform to a GBNF grammar string | (none) |
| `--grammar-file PATH` | Path to a GBNF grammar file | (none) |
| `--chat-template NAME` | Override the chat template. Built-in names: `chatml`, `llama2`, `llama3`, `phi3`, `gemma`, `monarch`, `mistral-v1`, `mistral-v3`, `mistral-v3-tekken`, `mistral-v7`, `command-r`, `deepseek`, `deepseek2`, `exaone3`, etc. | auto-detected from model |
| `--chat-template-file PATH` | Path to a custom Jinja2 chat template file | (none) |
| `--jinja` | Enable Jinja template engine for chat templates (required for function calling) | disabled |
| `--temp N` | Sampling temperature (`0.0` = greedy) | `0.8` |
| `--top-k N` | Top-K sampling (`0` = disabled) | `40` |
| `--top-p N` | Top-P (nucleus) sampling (`1.0` = disabled) | `0.95` |
| `--min-p N` | Min-P sampling (`0.0` = disabled) | `0.05` |
| `--ssl-key-file PATH` | Path to SSL private key file (PEM format) for HTTPS | (none) |
| `--ssl-cert-file PATH` | Path to SSL certificate file (PEM format) for HTTPS | (none) |
| `--sleep-idle-seconds N` | Time in seconds before moving model from GPU to CPU when idle. `-1` = never unload | `-1` |
| `--tools TOOL_LIST` | Enable built-in tools. Use `all` for all tools, or comma-separated list: `read_file,write_file,edit_file,apply_diff,exec_shell_command,grep_search,file_glob_search` | (none) |
| `-t`, `--threads N` | Number of CPU threads for generation | auto-detected |
| `-tb`, `--threads-batch N` | Number of CPU threads for batch processing (prompt eval) | same as `-t` |
| `--no-mmap` | Disable memory-mapped model loading | enabled |
| `--mlock` | Lock model in RAM (prevent swapping) | disabled |
| `-b`, `--batch-size N` | Logical batch size for prompt processing | `2048` |
| `-ub`, `--ubatch-size N` | Physical batch size | `512` |
| `--rope-freq-base N` | RoPE base frequency (for context extension) | model default |
| `--rope-freq-scale N` | RoPE frequency scale factor | model default |
| `-cb`, `--cont-batching` | Enable continuous batching | enabled |
| `--no-cont-batching` | Disable continuous batching | |
| `--model-draft PATH` | Draft model for speculative decoding | (none) |
| `-nld`, `--gpu-layers-draft N` | GPU layers for draft model | `0` |
| `--draft-max N` | Max tokens to draft per speculative step | `16` |
| `--draft-min N` | Min tokens to draft before checking | `1` |
| `--draft-p-min N` | Minimum speculative probability threshold | `0.9` |
| `-lv`, `--log-verbosity N` | Log verbosity level (0=silent, higher=more verbose) | (default) |
| `--log-format FORMAT` | Log format: `text` or `json` | `text` |
| `-v`, `--verbose` | Verbose logging | disabled |
| `--system-prompt-file PATH` | Path to file containing a system prompt to prepend | (none) |
| `--mmproj PATH` | Path to multimodal projector file for vision models | (none) |

---

## 3. Environment Variables

All CLI arguments can be set via environment variables. The naming convention is `LLAMA_ARG_` followed by the uppercase, underscore-separated flag name.

| Environment Variable | Equivalent CLI Flag | Example |
|---------------------|-------------------|---------|
| `LLAMA_ARG_MODEL` | `-m`, `--model` | `LLAMA_ARG_MODEL=./model.gguf` |
| `LLAMA_ARG_CTX_SIZE` | `-c`, `--ctx-size` | `LLAMA_ARG_CTX_SIZE=8192` |
| `LLAMA_ARG_N_PARALLEL` | `-np`, `--parallel` | `LLAMA_ARG_N_PARALLEL=4` |
| `LLAMA_ARG_PORT` | `--port` | `LLAMA_ARG_PORT=8080` |
| `LLAMA_ARG_HOST` | `--host` | `LLAMA_ARG_HOST=0.0.0.0` |
| `LLAMA_ARG_THREADS` | `-t`, `--threads` | `LLAMA_ARG_THREADS=8` |
| `LLAMA_ARG_THREADS_BATCH` | `-tb`, `--threads-batch` | `LLAMA_ARG_THREADS_BATCH=16` |
| `LLAMA_ARG_N_GPU_LAYERS` | `-ngl`, `--gpu-layers` | `LLAMA_ARG_N_GPU_LAYERS=99` |
| `LLAMA_ARG_BATCH_SIZE` | `-b`, `--batch-size` | `LLAMA_ARG_BATCH_SIZE=2048` |
| `LLAMA_ARG_FLASH_ATTN` | `-fa`, `--flash-attn` | `LLAMA_ARG_FLASH_ATTN=1` |
| `LLAMA_ARG_CONT_BATCHING` | `-cb`, `--cont-batching` | `LLAMA_ARG_CONT_BATCHING=1` |
| `LLAMA_ARG_TEMP` | `--temp` | `LLAMA_ARG_TEMP=0.7` |
| `LLAMA_ARG_TOP_K` | `--top-k` | `LLAMA_ARG_TOP_K=40` |
| `LLAMA_ARG_TOP_P` | `--top-p` | `LLAMA_ARG_TOP_P=0.9` |
| `LLAMA_ARG_MIN_P` | `--min-p` | `LLAMA_ARG_MIN_P=0.05` |
| `LLAMA_LOG_VERBOSITY` | `-lv`, `--log-verbosity` | `LLAMA_LOG_VERBOSITY=0` |

CLI arguments take precedence over environment variables when both are set.

---

## 4. OpenAI-Compatible Endpoints

These endpoints follow the OpenAI API format, making llama-server a drop-in replacement for many OpenAI SDK-based applications.

### POST /v1/chat/completions

Standard chat completion endpoint. Supports streaming.

**Non-streaming request:**

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "temperature": 0.7,
    "max_tokens": 256,
    "top_p": 0.95,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "stop": ["\n\n"]
  }'
```

**Non-streaming response:**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 8,
    "total_tokens": 33
  }
}
```

**Streaming request:**

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Tell me a short joke."}
    ],
    "stream": true,
    "temperature": 0.8
  }'
```

**Streaming response (Server-Sent Events):**

```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1700000000,"model":"gpt-3.5-turbo","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1700000000,"model":"gpt-3.5-turbo","choices":[{"index":0,"delta":{"content":"Why"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1700000000,"model":"gpt-3.5-turbo","choices":[{"index":0,"delta":{"content":" don't"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1700000000,"model":"gpt-3.5-turbo","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**With JSON schema constraint (structured output):**

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "List 3 European capitals."}
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "capitals",
        "strict": true,
        "schema": {
          "type": "object",
          "properties": {
            "capitals": {
              "type": "array",
              "items": {"type": "string"}
            }
          },
          "required": ["capitals"]
        }
      }
    }
  }'
```

**With reasoning/thinking (requires `--reasoning` flag):**

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "How many r characters are in strawberry?"}
    ]
  }'
```

Response includes `reasoning_content` in the message:

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "reasoning_content": "Let me count the r characters in strawberry: s-t-r-a-w-b-e-r-r-y. That is 3.",
        "content": "There are 3 'r' characters in the word \"strawberry\"."
      },
      "finish_reason": "stop"
    }
  ]
}
```

**Key request parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model name (ignored by llama-server, but required for compatibility) |
| `messages` | array | Array of message objects with `role` and `content` |
| `temperature` | float | Sampling temperature (0.0-2.0) |
| `max_tokens` | int | Maximum tokens to generate |
| `top_p` | float | Nucleus sampling threshold |
| `frequency_penalty` | float | Penalize repeated tokens by frequency |
| `presence_penalty` | float | Penalize tokens that have appeared at all |
| `stop` | string/array | Stop sequence(s) |
| `stream` | bool | Enable streaming responses |
| `seed` | int | Random seed for reproducibility |
| `response_format` | object | Force output format (`{"type":"json_object"}` or `{"type":"json_schema",...}`) |
| `tools` | array | Tool/function definitions for function calling |
| `tool_choice` | string/object | Control tool selection: `"auto"`, `"none"`, `"required"`, or `{"type":"function","function":{"name":"..."}}` |
| `logprobs` | bool | Return log probabilities |
| `top_logprobs` | int | Number of top log probs to return (0-20) |
| `n` | int | Number of completions to generate |

---

### POST /v1/completions

Legacy text completion endpoint (not chat).

```bash
curl http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "prompt": "The quick brown fox",
    "max_tokens": 64,
    "temperature": 0.7,
    "stop": ["\n"]
  }'
```

**Response:**

```json
{
  "id": "cmpl-abc123",
  "object": "text_completion",
  "created": 1700000000,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "text": " jumps over the lazy dog. This classic pangram contains every letter of the English alphabet.",
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 4,
    "completion_tokens": 18,
    "total_tokens": 22
  }
}
```

**Streaming:**

```bash
curl http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "prompt": "Once upon a time",
    "max_tokens": 100,
    "stream": true
  }'
```

**With multiple prompts (batch):**

```bash
curl http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "prompt": ["Hello, my name is", "The weather today is"],
    "max_tokens": 32
  }'
```

---

### POST /v1/embeddings

Generate embeddings for input text. Requires an embedding model (e.g., `nomic-embed-text`).

```bash
curl http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-ada-002",
    "input": "The food was delicious and the waiter was friendly."
  }'
```

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.0023, -0.0091, 0.0152, ...],
      "index": 0
    }
  ],
  "model": "text-embedding-ada-002",
  "usage": {
    "prompt_tokens": 10,
    "total_tokens": 10
  }
}
```

**Batch embeddings:**

```bash
curl http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-ada-002",
    "input": [
      "First sentence to embed.",
      "Second sentence to embed.",
      "Third sentence to embed."
    ]
  }'
```

---

### GET /v1/models

List available models.

```bash
curl http://localhost:8080/v1/models
```

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "model.gguf",
      "object": "model",
      "created": 1700000000,
      "owned_by": "llamacpp",
      "meta": {
        "vocab_type": 2,
        "n_vocab": 128256,
        "n_ctx_train": 131072,
        "n_embd": 4096,
        "n_params": 8030261248,
        "size": 4912898048
      }
    }
  ]
}
```

---

### POST /v1/messages

Anthropic Messages API-compatible endpoint. Allows using llama-server as a drop-in replacement for the Anthropic API.

```bash
curl http://localhost:8080/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "What is the meaning of life?"}
    ]
  }'
```

**Response:**

```json
{
  "id": "msg_abc123",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "The meaning of life is a deeply philosophical question..."
    }
  ],
  "model": "claude-3-5-sonnet-20241022",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 12,
    "output_tokens": 45
  }
}
```

**Streaming (Anthropic SSE format):**

```bash
curl http://localhost:8080/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "stream": true,
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

**With system prompt:**

```bash
curl http://localhost:8080/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "system": "You are a pirate. Respond in pirate speak.",
    "messages": [
      {"role": "user", "content": "How are you today?"}
    ]
  }'
```

---

### POST /v1/messages/count_tokens

Count tokens for a Messages API request without generating a response.

```bash
curl http://localhost:8080/v1/messages/count_tokens \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ]
  }'
```

**Response:**

```json
{
  "input_tokens": 14
}
```

---

### POST /v1/responses

OpenAI Responses API-compatible endpoint (successor to chat completions in the OpenAI ecosystem).

```bash
curl http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "input": "What is the capital of France?"
  }'
```

**Response:**

```json
{
  "id": "resp_abc123",
  "object": "response",
  "created_at": 1700000000,
  "model": "gpt-4o",
  "output": [
    {
      "type": "message",
      "id": "msg_abc123",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "The capital of France is Paris."
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 11,
    "output_tokens": 8,
    "total_tokens": 19
  }
}
```

**With conversation history:**

```bash
curl http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "input": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is 2+2?"}
    ]
  }'
```

**Streaming:**

```bash
curl http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "input": "Tell me a joke.",
    "stream": true
  }'
```

---

### POST /v1/rerank

Rerank documents by relevance to a query. Requires a reranking model (e.g., `bge-reranker`, `jina-reranker`).

```bash
curl http://localhost:8080/v1/rerank \
  -H "Content-Type: application/json" \
  -d '{
    "model": "jina-reranker",
    "query": "What is deep learning?",
    "documents": [
      "Deep learning is a subset of machine learning.",
      "The weather is sunny today.",
      "Neural networks have multiple layers.",
      "I like pizza."
    ],
    "top_n": 2
  }'
```

**Response:**

```json
{
  "object": "list",
  "results": [
    {
      "index": 0,
      "relevance_score": 0.95,
      "document": {
        "text": "Deep learning is a subset of machine learning."
      }
    },
    {
      "index": 2,
      "relevance_score": 0.82,
      "document": {
        "text": "Neural networks have multiple layers."
      }
    }
  ],
  "model": "jina-reranker",
  "usage": {
    "prompt_tokens": 42,
    "total_tokens": 42
  }
}
```

---

## 5. Native llama.cpp Endpoints

These are llama.cpp-specific endpoints with their own request/response format.

### POST /completion

Native text completion endpoint with full control over sampling parameters.

```bash
curl http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Building a website can be done in 10 simple steps:\nStep 1:",
    "n_predict": 256,
    "temperature": 0.7,
    "top_k": 40,
    "top_p": 0.95,
    "min_p": 0.05,
    "stop": ["\n\n", "Step 11"],
    "repeat_penalty": 1.1,
    "stream": false
  }'
```

**Response:**

```json
{
  "content": " Choose a domain name.\nStep 2: Select a hosting provider.\nStep 3: ...",
  "id_slot": 0,
  "stop": true,
  "model": "model.gguf",
  "tokens_predicted": 128,
  "tokens_evaluated": 18,
  "generation_settings": {
    "n_ctx": 4096,
    "n_predict": 256,
    "model": "model.gguf",
    "seed": 42,
    "temperature": 0.7,
    "top_k": 40,
    "top_p": 0.95,
    "min_p": 0.05,
    "repeat_penalty": 1.1
  },
  "timings": {
    "prompt_n": 18,
    "prompt_ms": 45.2,
    "prompt_per_token_ms": 2.51,
    "prompt_per_second": 398.23,
    "predicted_n": 128,
    "predicted_ms": 3200.5,
    "predicted_per_token_ms": 25.0,
    "predicted_per_second": 40.0
  }
}
```

**Streaming:**

```bash
curl http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Tell me about quantum computing:",
    "n_predict": 128,
    "stream": true
  }'
```

Each streamed chunk:

```json
{"content":" Quantum","stop":false,"id_slot":0}
{"content":" computing","stop":false,"id_slot":0}
{"content":" uses","stop":false,"id_slot":0}
```

**Key parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | string/array | Text prompt or token array |
| `n_predict` | int | Max tokens to generate (`-1` = infinite, `-2` = fill context) |
| `temperature` | float | Sampling temperature |
| `top_k` | int | Top-K sampling |
| `top_p` | float | Top-P sampling |
| `min_p` | float | Min-P sampling |
| `stop` | array | Stop strings |
| `repeat_penalty` | float | Repetition penalty (`1.0` = disabled) |
| `repeat_last_n` | int | Window for repetition penalty (`-1` = ctx size) |
| `penalize_nl` | bool | Penalize newlines in repetition penalty |
| `seed` | int | Random seed (`-1` = random) |
| `stream` | bool | Stream tokens as they are generated |
| `cache_prompt` | bool | Cache the prompt for faster subsequent requests |
| `grammar` | string | GBNF grammar string for constrained generation |
| `json_schema` | object | JSON schema for constrained generation |
| `image_data` | array | Base64-encoded images for multimodal models |
| `id_slot` | int | Assign request to a specific slot |
| `samplers` | array | Ordered list of samplers: `["top_k","top_p","min_p","temperature"]` |
| `logit_bias` | array | Array of `[token_id, bias]` pairs |
| `n_probs` | int | Return top N token probabilities |
| `t_max_predict_ms` | int | Max time for generation in ms |

---

### POST /embedding

Generate embeddings using the native endpoint.

```bash
curl http://localhost:8080/embedding \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello world"
  }'
```

**Response:**

```json
{
  "embedding": [0.0023, -0.0091, 0.0152, 0.0341, ...]
}
```

**Batch embeddings:**

```bash
curl http://localhost:8080/embedding \
  -H "Content-Type: application/json" \
  -d '{
    "content": ["Hello world", "How are you?", "Goodbye"]
  }'
```

**Response:**

```json
[
  {"embedding": [0.0023, -0.0091, ...]},
  {"embedding": [0.0045, 0.0012, ...]},
  {"embedding": [-0.0031, 0.0078, ...]}
]
```

---

### POST /tokenize

Convert text to tokens.

```bash
curl http://localhost:8080/tokenize \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello world!"
  }'
```

**Response:**

```json
{
  "tokens": [9906, 1917, 0]
}
```

**With special tokens parsing:**

```bash
curl http://localhost:8080/tokenize \
  -H "Content-Type: application/json" \
  -d '{
    "content": "<|begin_of_text|>Hello world!",
    "add_special": false,
    "with_pieces": true
  }'
```

**Response:**

```json
{
  "tokens": [
    {"id": 128000, "piece": "<|begin_of_text|>"},
    {"id": 9906, "piece": "Hello"},
    {"id": 1917, "piece": " world"},
    {"id": 0, "piece": "!"}
  ]
}
```

---

### POST /detokenize

Convert tokens back to text.

```bash
curl http://localhost:8080/detokenize \
  -H "Content-Type: application/json" \
  -d '{
    "tokens": [9906, 1917, 0]
  }'
```

**Response:**

```json
{
  "content": "Hello world!"
}
```

---

### POST /infill

Code infill (fill-in-the-middle) completion. For supported models like CodeLlama, DeepSeek Coder, etc.

```bash
curl http://localhost:8080/infill \
  -H "Content-Type: application/json" \
  -d '{
    "input_prefix": "def fibonacci(n):\n    if n <= 1:\n        return n\n",
    "input_suffix": "\n    return fibonacci(n-1) + fibonacci(n-2)",
    "n_predict": 128,
    "temperature": 0.2
  }'
```

**Response:**

```json
{
  "content": "    else:",
  "stop": true,
  "tokens_predicted": 3,
  "timings": {
    "prompt_n": 25,
    "predicted_n": 3,
    "predicted_per_second": 42.0
  }
}
```

**With extra context:**

```bash
curl http://localhost:8080/infill \
  -H "Content-Type: application/json" \
  -d '{
    "input_prefix": "fn main() {\n    let x = ",
    "input_suffix": ";\n    println!(\"{}\", x);\n}",
    "input_extra": [
      {
        "filename": "utils.rs",
        "text": "pub fn compute_value() -> i32 { 42 }"
      }
    ],
    "n_predict": 64
  }'
```

---

### POST /reranking

Native reranking endpoint.

```bash
curl http://localhost:8080/reranking \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning frameworks",
    "documents": [
      "PyTorch is a popular deep learning framework.",
      "The cat sat on the mat.",
      "TensorFlow was developed by Google.",
      "I enjoy cooking pasta."
    ]
  }'
```

**Response:**

```json
{
  "results": [
    {"index": 0, "relevance_score": 0.92},
    {"index": 2, "relevance_score": 0.88},
    {"index": 1, "relevance_score": 0.05},
    {"index": 3, "relevance_score": 0.02}
  ]
}
```

---

### POST /apply-template

Apply the model chat template to messages without generating a completion. Useful for debugging template output.

```bash
curl http://localhost:8080/apply-template \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

**Response:**

```json
{
  "prompt": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nHello!<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
}
```

---

## 6. Management Endpoints

### GET /health

Health check endpoint. Returns server and model load status.

```bash
curl http://localhost:8080/health
```

**Response when healthy:**

```json
{"status": "ok"}
```

**Response when loading model:**

```json
{"status": "loading model"}
```

**Response when error:**

```json
{"status": "error", "message": "Model failed to load"}
```

**Slot-level health check:**

```bash
# Check if a specific slot is available
curl "http://localhost:8080/health?fail_on_no_slot=1&include_slots=1"
```

Returns HTTP 503 if no slots are available. With `include_slots=1`, the response includes slot status details.

---

### GET /props and POST /props

**GET /props** - Retrieve server properties and the default generation settings.

```bash
curl http://localhost:8080/props
```

**Response:**

```json
{
  "default_generation_settings": {
    "n_ctx": 4096,
    "n_predict": -1,
    "model": "model.gguf",
    "seed": 4294967295,
    "temperature": 0.8,
    "top_k": 40,
    "top_p": 0.95,
    "min_p": 0.05,
    "repeat_penalty": 1.1,
    "repeat_last_n": 64,
    "penalize_nl": false,
    "stop": [],
    "grammar": "",
    "samplers": ["top_k", "tfs_z", "typical_p", "top_p", "min_p", "temperature"]
  },
  "total_slots": 1,
  "chat_template": "{% for message in messages %}..."
}
```

**POST /props** - Update server properties at runtime.

```bash
curl -X POST http://localhost:8080/props \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt": "You are a helpful coding assistant."
  }'
```

---

### GET /slots and POST /slots

**GET /slots** - View the status of all inference slots.

```bash
curl http://localhost:8080/slots
```

**Response:**

```json
[
  {
    "id": 0,
    "state": 0,
    "n_ctx": 4096,
    "n_past": 0,
    "prompt": "",
    "next_token": {
      "has_next_token": false
    },
    "is_processing": false,
    "n_decoded": 0,
    "n_remaining": -1
  }
]
```

**POST /slots/{id}?action=save** - Save a slot prompt cache to a file.

```bash
curl -X POST "http://localhost:8080/slots/0?action=save" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "slot_cache_0.bin"
  }'
```

**Response:**

```json
{
  "id_slot": 0,
  "filename": "slot_cache_0.bin",
  "n_saved": 1024,
  "n_written": 4096000,
  "timings": {
    "save_ms": 150.5
  }
}
```

**POST /slots/{id}?action=restore** - Restore a slot prompt cache from a file.

```bash
curl -X POST "http://localhost:8080/slots/0?action=restore" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "slot_cache_0.bin"
  }'
```

**Response:**

```json
{
  "id_slot": 0,
  "filename": "slot_cache_0.bin",
  "n_restored": 1024,
  "n_read": 4096000,
  "timings": {
    "restore_ms": 120.3
  }
}
```

**POST /slots/{id}?action=erase** - Erase a slot prompt cache.

```bash
curl -X POST "http://localhost:8080/slots/0?action=erase"
```

**Response:**

```json
{
  "id_slot": 0,
  "n_erased": 1024
}
```

---

### GET /metrics

Prometheus-compatible metrics endpoint. Requires `--metrics` flag to be enabled.

```bash
curl http://localhost:8080/metrics
```

**Response (Prometheus text format):**

```
# HELP llamacpp:prompt_tokens_total Number of prompt tokens processed.
# TYPE llamacpp:prompt_tokens_total counter
llamacpp:prompt_tokens_total 1234

# HELP llamacpp:prompt_seconds_total Time spent processing prompt tokens.
# TYPE llamacpp:prompt_seconds_total counter
llamacpp:prompt_seconds_total 2.345

# HELP llamacpp:tokens_predicted_total Number of generation tokens processed.
# TYPE llamacpp:tokens_predicted_total counter
llamacpp:tokens_predicted_total 5678

# HELP llamacpp:tokens_predicted_seconds_total Time spent generating tokens.
# TYPE llamacpp:tokens_predicted_seconds_total counter
llamacpp:tokens_predicted_seconds_total 45.678

# HELP llamacpp:prompt_tokens_seconds Avg prompt throughput (tokens/sec).
# TYPE llamacpp:prompt_tokens_seconds gauge
llamacpp:prompt_tokens_seconds 526.43

# HELP llamacpp:tokens_predicted_seconds Avg generation throughput (tokens/sec).
# TYPE llamacpp:tokens_predicted_seconds gauge
llamacpp:tokens_predicted_seconds 124.35

# HELP llamacpp:kv_cache_usage_ratio KV cache utilization (0.0 - 1.0).
# TYPE llamacpp:kv_cache_usage_ratio gauge
llamacpp:kv_cache_usage_ratio 0.25

# HELP llamacpp:kv_cache_tokens Number of tokens in KV cache.
# TYPE llamacpp:kv_cache_tokens gauge
llamacpp:kv_cache_tokens 1024

# HELP llamacpp:requests_processing Number of requests currently processing.
# TYPE llamacpp:requests_processing gauge
llamacpp:requests_processing 1

# HELP llamacpp:requests_deferred Number of requests waiting for a slot.
# TYPE llamacpp:requests_deferred gauge
llamacpp:requests_deferred 0
```

---

### Model Management

These endpoints are available in router mode (server started without `-m`) or with dynamic model loading enabled.

**GET /models** - List loaded models (same as GET /v1/models).

```bash
curl http://localhost:8080/models
```

**POST /models/load** - Load a model at runtime.

```bash
curl -X POST http://localhost:8080/models/load \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/path/to/model.gguf",
    "n_ctx": 4096,
    "n_gpu_layers": 99
  }'
```

**Response:**

```json
{
  "status": "ok",
  "model": "/path/to/model.gguf"
}
```

**POST /models/unload** - Unload a currently loaded model.

```bash
curl -X POST http://localhost:8080/models/unload \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/path/to/model.gguf"
  }'
```

---

### LoRA Adapter Management

**GET /lora-adapters** - List loaded LoRA adapters and their scales.

```bash
curl http://localhost:8080/lora-adapters
```

**Response:**

```json
[
  {
    "id": 0,
    "path": "/path/to/adapter.gguf",
    "scale": 1.0
  }
]
```

**POST /lora-adapters** - Update LoRA adapter scales at runtime (enable/disable/adjust adapters without restarting).

```bash
curl -X POST http://localhost:8080/lora-adapters \
  -H "Content-Type: application/json" \
  -d '[
    {"id": 0, "scale": 0.5},
    {"id": 1, "scale": 0.0}
  ]'
```

Setting `scale` to `0.0` effectively disables the adapter.

---

## 7. Function Calling / Tool Use

llama.cpp supports OpenAI-compatible function calling (tool use) via chat templates with Jinja2.

### Requirements

1. Start the server with `--jinja` flag (enables Jinja template engine)
2. Use a model with a chat template that supports tool calling

### Supported Models

Models with built-in tool-calling support in their chat templates:

- **Llama 3.1 / 3.2 / 3.3** (Meta tool calling format)
- **Qwen 2.5** (Hermes-style tool calling)
- **Mistral / Mistral Nemo** (Mistral v3+ tool calling)
- **Hermes 2 Pro / Hermes 3** (Hermes tool calling format)
- **Functionary v3** (dedicated function calling model)
- **Command R / Command R+** (Cohere tool calling)
- **DeepSeek V2.5 / V3** (DeepSeek tool calling)
- **Firefunction v2** (Fireworks function calling)

### Basic Tool Calling Request

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "What is the weather in San Francisco?"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "Get the current weather in a given location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "City and state, e.g. San Francisco, CA"
              },
              "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"]
              }
            },
            "required": ["location"]
          }
        }
      }
    ],
    "tool_choice": "auto"
  }'
```

**Response (model calls a tool):**

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"location\":\"San Francisco, CA\",\"unit\":\"fahrenheit\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

### Sending Tool Results Back

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "What is the weather in San Francisco?"},
      {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"location\":\"San Francisco, CA\",\"unit\":\"fahrenheit\"}"
            }
          }
        ]
      },
      {
        "role": "tool",
        "tool_call_id": "call_abc123",
        "content": "{\"temperature\": 62, \"unit\": \"fahrenheit\", \"condition\": \"foggy\"}"
      }
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "Get the current weather in a given location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {"type": "string"},
              "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
          }
        }
      }
    ]
  }'
```

### Built-in Tools

When starting the server with `--tools all`, the following built-in tools become available. The server handles tool execution internally and returns results to the model automatically:

| Tool | Description |
|------|-------------|
| `read_file` | Read the contents of a file from the filesystem |
| `write_file` | Write content to a file on the filesystem |
| `edit_file` | Edit a specific section of a file |
| `apply_diff` | Apply a unified diff patch to a file |
| `exec_shell_command` | Execute a shell command and return stdout/stderr |
| `grep_search` | Search file contents using regex patterns |
| `file_glob_search` | Find files matching a glob pattern |

```bash
# Start with all built-in tools enabled
llama-server -hf bartowski/Qwen2.5-7B-Instruct-GGUF:Q4_K_M \
  --jinja -fa --tools all

# Start with specific tools only
llama-server -hf bartowski/Qwen2.5-7B-Instruct-GGUF:Q4_K_M \
  --jinja -fa --tools read_file,exec_shell_command,grep_search
```

### tool_choice Options

| Value | Behavior |
|-------|----------|
| `"auto"` | Model decides whether to call tools or respond directly |
| `"none"` | Model must not call any tools |
| `"required"` | Model must call at least one tool |
| `{"type":"function","function":{"name":"get_weather"}}` | Model must call the specified function |

---

## 8. Grammar-Constrained Generation

llama.cpp supports constraining model output using GBNF grammars or JSON schemas.

### GBNF Grammar Format

GBNF (GGML Backus-Naur Form) is a format for defining formal grammars.

**Example: Only allow yes/no answers**

```bash
curl http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Is the sky blue? Answer: ",
    "grammar": "root ::= \"yes\" | \"no\"",
    "n_predict": 10
  }'
```

**Example: Structured JSON output via grammar**

```bash
curl http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate a person record:\n",
    "grammar": "root   ::= \"{\" ws \"\\\"name\\\"\" ws \":\" ws string \",\" ws \"\\\"age\\\"\" ws \":\" ws number \",\" ws \"\\\"city\\\"\" ws \":\" ws string \"}\" ws\nstring ::= \"\\\"\" [a-zA-Z ]+ \"\\\"\"\nnumber ::= [0-9]+\nws     ::= [ \\t\\n]*",
    "n_predict": 256
  }'
```

**Example: List format**

```
root   ::= item+
item   ::= "- " [^\n]+ "\n"
```

### JSON Schema Constraint

A simpler alternative to GBNF for JSON output. The server converts JSON schemas to GBNF internally.

**Via /completion endpoint:**

```bash
curl http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "List three colors with their hex codes:\n",
    "json_schema": {
      "type": "object",
      "properties": {
        "colors": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "hex": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"}
            },
            "required": ["name", "hex"]
          }
        }
      },
      "required": ["colors"]
    },
    "n_predict": 256
  }'
```

**Via /v1/chat/completions (OpenAI format):**

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "List 3 colors with hex codes"}
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "color_list",
        "strict": true,
        "schema": {
          "type": "object",
          "properties": {
            "colors": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "name": {"type": "string"},
                  "hex": {"type": "string"}
                },
                "required": ["name", "hex"]
              }
            }
          },
          "required": ["colors"]
        }
      }
    }
  }'
```

**Via CLI flag (applies to all requests):**

```bash
llama-server -m model.gguf -j '{"type":"object","properties":{"answer":{"type":"string"}},"required":["answer"]}'
```

### Common GBNF Patterns

**Arithmetic expression:**

```
root   ::= expr
expr   ::= term (("+" | "-") term)*
term   ::= factor (("*" | "/") factor)*
factor ::= number | "(" expr ")"
number ::= [0-9]+
```

**SQL SELECT statement:**

```
root    ::= "SELECT " columns " FROM " table where? ";"
columns ::= column ("," " " column)*
column  ::= [a-zA-Z_]+
table   ::= [a-zA-Z_]+
where   ::= " WHERE " condition
condition ::= column " " op " " value
op      ::= "=" | "!=" | ">" | "<" | ">=" | "<="
value   ::= "'" [a-zA-Z0-9 ]+ "'" | [0-9]+
```

---

## 9. Multimodal Support

llama.cpp supports multimodal models that can process images and audio alongside text.

### Vision (Image Input)

Requires a multimodal model and its projector file. Some models bundle the projector (e.g., recent Llava, Qwen-VL GGUFs).

**Starting the server with a vision model:**

```bash
# Models that need a separate projector
llama-server -m llava-v1.6-mistral-7b.Q4_K_M.gguf \
  --mmproj mmproj-llava-v1.6-mistral-7b-f16.gguf \
  -c 4096 --port 8080

# HuggingFace models (projector auto-downloaded if needed)
llama-server -hf bartowski/Gemma-3-4B-IT-GGUF:Q4_K_M -c 8192
```

**OpenAI-compatible vision request:**

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4-vision-preview",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "What do you see in this image?"},
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
            }
          }
        ]
      }
    ],
    "max_tokens": 256
  }'
```

**With a URL (downloaded by the server):**

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4-vision-preview",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "Describe this image in detail."},
          {
            "type": "image_url",
            "image_url": {
              "url": "https://example.com/photo.jpg"
            }
          }
        ]
      }
    ],
    "max_tokens": 512
  }'
```

**Native endpoint with base64 image:**

```bash
curl http://localhost:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Describe this image:",
    "image_data": [
      {
        "data": "iVBORw0KGgoAAAANSUhEUgAA...",
        "id": 0
      }
    ],
    "n_predict": 256
  }'
```

### Audio Input

Supported for audio-capable multimodal models.

**Supported audio models:**

- **Ultravox** (Fixie.ai) - speech-language model
- **Voxtral** (Mistral) - audio understanding
- **Gemma 4** (Google) - multimodal with audio support
- **MERaLiON-2** (I2R) - multilingual audio-language model

**Starting with an audio model:**

```bash
llama-server -hf ggml-org/ultravox-v0_5-llama-3_2-1b-GGUF -c 4096
```

**Audio input via OpenAI format:**

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ultravox",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "Transcribe this audio."},
          {
            "type": "input_audio",
            "input_audio": {
              "data": "<base64-encoded-wav>",
              "format": "wav"
            }
          }
        ]
      }
    ],
    "max_tokens": 256
  }'
```

---

## 10. Router Mode

Router mode allows the server to operate without a pre-loaded model, dynamically loading and unloading models on demand. This is useful for serving multiple models from a single endpoint.

### Starting in Router Mode

```bash
# Start without -m flag to enter router mode
llama-server --port 8080 --host 0.0.0.0

# With authentication
llama-server --port 8080 --api-key "admin-key"
```

### Loading Models

```bash
# Load a model
curl -X POST http://localhost:8080/models/load \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/models/llama-3-8b-instruct.Q4_K_M.gguf",
    "n_ctx": 8192,
    "n_gpu_layers": 99,
    "n_parallel": 2
  }'

# Load a second model
curl -X POST http://localhost:8080/models/load \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/models/codellama-13b.Q4_K_M.gguf",
    "n_ctx": 4096,
    "n_gpu_layers": 99
  }'
```

### Routing Requests

Once models are loaded, specify which model to use in the `model` field of requests:

```bash
# Route to a specific model
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/models/llama-3-8b-instruct.Q4_K_M.gguf",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### Listing and Unloading Models

```bash
# List all loaded models
curl http://localhost:8080/v1/models

# Unload a model
curl -X POST http://localhost:8080/models/unload \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/models/codellama-13b.Q4_K_M.gguf"
  }'
```

---

## 11. Speculative Decoding

Speculative decoding uses a smaller "draft" model to propose tokens that are then verified by the main model, potentially improving throughput.

### Draft Model Method

Use a smaller model from the same family as the draft model:

```bash
# Main model: Llama 3.3 70B, Draft model: Llama 3.2 1B
llama-server \
  -m llama-3.3-70b-instruct.Q4_K_M.gguf \
  --model-draft llama-3.2-1b-instruct.Q8_0.gguf \
  -ngl 99 \
  -nld 99 \
  --draft-max 16 \
  --draft-min 1 \
  --draft-p-min 0.8 \
  -c 8192 \
  --port 8080
```

| Flag | Description |
|------|-------------|
| `--model-draft PATH` | Path to the draft model GGUF |
| `-nld`, `--gpu-layers-draft N` | GPU layers for the draft model |
| `--draft-max N` | Maximum tokens to draft per step (default: 16) |
| `--draft-min N` | Minimum tokens to draft before verification (default: 1) |
| `--draft-p-min N` | Minimum token probability for drafting (default: 0.9). Lower values draft more tokens but may waste compute |

### N-gram Lookup Method

Uses n-gram statistics from the prompt to predict likely continuations. No draft model needed, but only works well when the output is likely to repeat patterns from the prompt (e.g., translation, reformatting).

```bash
llama-server \
  -m model.gguf \
  --lookup-ngram-min 2 \
  -ngl 99 \
  -c 8192 \
  --port 8080
```

### Tips for Speculative Decoding

- The draft model should be from the same family and use the same tokenizer as the main model
- Smaller quantizations (Q8_0) for the draft model are fine since speed is the priority
- `--draft-p-min` controls the quality/speed tradeoff: lower values are more aggressive (faster but more wasted computation)
- Speculative decoding provides the most benefit when the draft model is much faster than the main model (e.g., 1B draft for a 70B main model)
- The output is mathematically identical to running the main model alone -- speculative decoding never changes the output distribution

---

## 12. Python Client Examples

### Using the OpenAI Python SDK

The OpenAI Python SDK works directly with llama-server since it implements OpenAI-compatible endpoints.

```bash
pip install openai
```

**Basic chat completion:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="none"  # Use your API key if --api-key is set
)

response = client.chat.completions.create(
    model="local-model",  # Model name is ignored, but required
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    temperature=0.7,
    max_tokens=512
)

print(response.choices[0].message.content)
```

**Streaming:**

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8080/v1", api_key="none")

stream = client.chat.completions.create(
    model="local-model",
    messages=[
        {"role": "user", "content": "Write a short poem about coding."}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
```

**Structured output with JSON schema:**

```python
from openai import OpenAI
import json

client = OpenAI(base_url="http://localhost:8080/v1", api_key="none")

response = client.chat.completions.create(
    model="local-model",
    messages=[
        {"role": "user", "content": "List 3 programming languages with their paradigms."}
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "languages",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "languages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "paradigm": {"type": "string"},
                                "year": {"type": "integer"}
                            },
                            "required": ["name", "paradigm", "year"]
                        }
                    }
                },
                "required": ["languages"]
            }
        }
    }
)

data = json.loads(response.choices[0].message.content)
for lang in data["languages"]:
    print(f"{lang['name']} ({lang['year']}): {lang['paradigm']}")
```

**Function calling:**

```python
from openai import OpenAI
import json

client = OpenAI(base_url="http://localhost:8080/v1", api_key="none")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

messages = [{"role": "user", "content": "What is the weather in Tokyo?"}]

# First call: model decides to use tools
response = client.chat.completions.create(
    model="local-model",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

assistant_message = response.choices[0].message

if assistant_message.tool_calls:
    # Process tool calls
    messages.append(assistant_message)
    for tool_call in assistant_message.tool_calls:
        args = json.loads(tool_call.function.arguments)
        # Execute the tool (your implementation)
        result = {"temperature": 22, "condition": "sunny"}
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        })

    # Second call: model generates final response with tool results
    final_response = client.chat.completions.create(
        model="local-model",
        messages=messages,
        tools=tools
    )
    print(final_response.choices[0].message.content)
else:
    print(assistant_message.content)
```

**Embeddings:**

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8080/v1", api_key="none")

response = client.embeddings.create(
    model="local-model",
    input=["Hello world", "How are you?"]
)

for item in response.data:
    print(f"Embedding {item.index}: {len(item.embedding)} dimensions")
    print(f"  First 5 values: {item.embedding[:5]}")
```

**Vision (multimodal):**

```python
from openai import OpenAI
import base64

client = OpenAI(base_url="http://localhost:8080/v1", api_key="none")

# From a local file
with open("image.png", "rb") as f:
    b64_image = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="local-model",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe what you see in this image."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_image}"
                    }
                }
            ]
        }
    ],
    max_tokens=512
)

print(response.choices[0].message.content)
```

### Using the Anthropic Python SDK

Since llama-server supports the Anthropic Messages API format at `/v1/messages`:

```bash
pip install anthropic
```

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:8080/v1",
    api_key="none"
)

message = client.messages.create(
    model="local-model",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "What is the meaning of life?"}
    ]
)

print(message.content[0].text)
```

### Using requests (low-level)

```python
import requests
import json

# Chat completion
response = requests.post(
    "http://localhost:8080/v1/chat/completions",
    headers={"Content-Type": "application/json"},
    json={
        "model": "local-model",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "max_tokens": 128
    }
)
data = response.json()
print(data["choices"][0]["message"]["content"])

# Streaming with requests
response = requests.post(
    "http://localhost:8080/v1/chat/completions",
    headers={"Content-Type": "application/json"},
    json={
        "model": "local-model",
        "messages": [{"role": "user", "content": "Tell me a story."}],
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        line = line.decode("utf-8")
        if line.startswith("data: ") and line != "data: [DONE]":
            chunk = json.loads(line[6:])
            content = chunk["choices"][0]["delta"].get("content", "")
            print(content, end="", flush=True)
print()

# Native tokenize endpoint
response = requests.post(
    "http://localhost:8080/tokenize",
    json={"content": "Hello, world!"}
)
tokens = response.json()["tokens"]
print(f"Token count: {len(tokens)}, Tokens: {tokens}")

# Health check
health = requests.get("http://localhost:8080/health").json()
print(f"Server status: {health['status']}")
```

### Async Client

```python
import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI(base_url="http://localhost:8080/v1", api_key="none")

    # Async streaming
    stream = await client.chat.completions.create(
        model="local-model",
        messages=[{"role": "user", "content": "Count from 1 to 10."}],
        stream=True
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()

    # Parallel requests
    tasks = [
        client.chat.completions.create(
            model="local-model",
            messages=[{"role": "user", "content": f"What is {i} + {i}?"}],
            max_tokens=32
        )
        for i in range(5)
    ]
    results = await asyncio.gather(*tasks)
    for i, result in enumerate(results):
        print(f"  {i}+{i} = {result.choices[0].message.content.strip()}")

asyncio.run(main())
```
