# Using Ollama as the Default Model in AutoGen

This guide explains how to use Ollama as the default model in AutoGen and AutoGen Studio.

## Overview

Starting with this version, **Ollama is the default model provider** for AutoGen Studio. This change makes it easier to get started with AutoGen without requiring API keys from commercial LLM providers.

## Why Ollama?

- **No API keys required**: Run models locally without external dependencies
- **Privacy**: Your data stays on your machine
- **Cost-effective**: No per-token charges
- **Fast**: Low latency for local inference
- **Flexible**: Support for many open-source models

## Prerequisites

### 1. Install Ollama

Download and install Ollama from [https://ollama.ai](https://ollama.ai)

```bash
# On macOS/Linux
curl https://ollama.ai/install.sh | sh

# On Windows
# Download from https://ollama.ai/download
```

### 2. Pull Required Models

The default configuration uses `qwen3:0.6b`, a lightweight but capable model:

```bash
ollama pull qwen3:0.6b
```

For better performance, you can also use:

```bash
# Recommended for tool calling and general tasks
ollama pull llama3.2:1b

# For more advanced use cases
ollama pull llama3.2:3b
```

### 3. Verify Ollama is Running

Check that Ollama is running on the default port:

```bash
curl http://localhost:11434/api/tags
```

You should see a JSON response with available models.

## Default Configuration

AutoGen Studio now uses the following default settings:

```python
from autogen_ext.models.ollama import OllamaChatCompletionClient

# Default model client
model_client = OllamaChatCompletionClient(
    model="qwen3:0.6b",
    host="http://localhost:11434"
)
```

## Supported Features

The Ollama integration supports all major AutoGen features:

### ✅ Basic Chat Completion
```python
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_core.models import UserMessage

client = OllamaChatCompletionClient(model="qwen3:0.6b")
result = await client.create([
    UserMessage(content="Hello, how are you?", source="user")
])
print(result.content)
```

### ✅ Streaming
```python
async for chunk in client.create_stream([
    UserMessage(content="Count from 1 to 5", source="user")
]):
    if isinstance(chunk, str):
        print(chunk, end="", flush=True)
```

### ✅ Function/Tool Calling
```python
from autogen_core.tools import FunctionTool

def add(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

tool = FunctionTool(add, description="Add two numbers")

result = await client.create(
    messages=[UserMessage(content="What is 5 + 7?", source="user")],
    tools=[tool]
)
```

### ✅ Structured Output
```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    city: str

result = await client.create(
    messages=[UserMessage(content="Generate person info", source="user")],
    json_output=Person
)
person = Person.model_validate_json(result.content)
```

### ✅ Multi-Agent Teams
All team types work with Ollama:
- RoundRobinGroupChat
- SelectorGroupChat
- Swarm

## Changing the Default Model

You can change the default model in several ways:

### 1. Environment Variable (Recommended)
Set the `OLLAMA_MODEL` environment variable:

```bash
export OLLAMA_MODEL=llama3.2:3b
```

### 2. Configuration File
Update `~/.autogenstudio/config.json`:

```json
{
  "default_model_client": {
    "provider": "OllamaChatCompletionClient",
    "config": {
      "model": "llama3.2:3b",
      "host": "http://localhost:11434"
    }
  }
}
```

### 3. Programmatically
```python
from autogen_ext.models.ollama import OllamaChatCompletionClient

client = OllamaChatCompletionClient(
    model="llama3.2:3b",
    host="http://localhost:11434"
)
```

## Recommended Models

Different models for different use cases:

| Model | Size | Best For | Tool Calling |
|-------|------|----------|--------------|
| qwen3:0.6b | 0.6B | Quick responses, low resource usage | ✅ |
| llama3.2:1b | 1B | Balanced performance and speed | ✅ |
| llama3.2:3b | 3B | Better reasoning, more accurate | ✅ |
| qwen2.5:0.5b | 0.5B | Very fast, minimal resources | ✅ |

### For Tool Calling
Models that support function calling:
- qwen3 (all sizes)
- llama3.2 (all sizes)
- qwen2.5 (all sizes)
- mistral
- mixtral

### For Vision Tasks
- llama3.2-vision
- llava

## Remote Ollama Instance

If you're running Ollama on a different machine or port:

```python
client = OllamaChatCompletionClient(
    model="qwen3:0.6b",
    host="http://192.168.1.100:11434"  # Your Ollama server
)
```

## Performance Tips

1. **Use smaller models for development**: Start with 0.5B-1B models for faster iteration
2. **Use appropriate context windows**: Smaller models = smaller context
3. **Enable GPU acceleration**: Ollama automatically uses GPU if available
4. **Keep Ollama updated**: `ollama update`

## Troubleshooting

### Ollama Not Found
```
ConnectionError: [Errno 111] Connection refused
```
**Solution**: Make sure Ollama is running:
```bash
ollama serve
```

### Model Not Found
```
Model 'qwen3:0.6b' not found
```
**Solution**: Pull the model first:
```bash
ollama pull qwen3:0.6b
```

### Out of Memory
```
Error: failed to allocate memory
```
**Solution**: Use a smaller model or increase available RAM:
```bash
# Use a smaller model
ollama pull qwen3:0.6b

# Or set memory limit
export OLLAMA_MAX_LOADED_MODELS=1
```

### Tool Calling Not Working
**Solution**: Make sure you're using a model that supports tool calling (see table above)

## Switching Back to OpenAI

If you prefer to use OpenAI instead:

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key="your-api-key"
)
```

Or set in the configuration:
```bash
export OPENAI_API_KEY=your-api-key
```

## Testing Your Setup

Run the reliability tests to verify everything works:

```bash
cd python
source .venv/bin/activate
pytest packages/autogen-ext/tests/models/test_ollama_reliability.py -v
```

Note: These tests require Ollama to be running with the models pulled.

## Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama/tree/main/docs)
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [Model Library](https://ollama.ai/library)
- [AutoGen Studio Guide](https://microsoft.github.io/autogen/docs/autogen-studio/)

## Support

If you encounter issues:
1. Check Ollama is running: `curl http://localhost:11434/api/tags`
2. Verify models are available: `ollama list`
3. Check logs: `journalctl -u ollama -f` (Linux) or Console.app (macOS)
4. Report issues: [AutoGen GitHub Issues](https://github.com/microsoft/autogen/issues)
