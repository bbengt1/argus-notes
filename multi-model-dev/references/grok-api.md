# Grok API Integration

Documentation for xAI's Grok API integration in the multi-model orchestrator.

## Setup

### API Key

Get your API key from [xAI Console](https://console.x.ai/).

```bash
export GROK_API_KEY="xai-..."
```

### Dependencies

```bash
pip install requests
```

## Available Models

| Model | Description | Best For |
|-------|-------------|----------|
| `grok-2` | Full model, most capable | Complex tasks, architecture |
| `grok-2-mini` | Faster, cheaper | Quick tasks, iterations |
| `grok-beta` | Latest features | Experimental |

## API Endpoints

### Chat Completions

```
POST https://api.x.ai/v1/chat/completions
```

**Headers:**
```
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request Body:**
```json
{
  "model": "grok-2",
  "messages": [
    {"role": "system", "content": "System prompt"},
    {"role": "user", "content": "User message"}
  ],
  "temperature": 0.7,
  "max_tokens": 4096
}
```

**Response:**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "model": "grok-2",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Response text"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 150,
    "total_tokens": 200
  }
}
```

## Client Usage

### Basic Chat

```python
from grok_client import GrokClient

client = GrokClient()
response = client.chat("Explain quantum computing")
print(response.content)
```

### Code Generation

```python
response = client.code_task(
    "Write a Python function to merge two sorted lists",
    language="python"
)
print(response.first_code_block)  # Extracted code
```

### With System Prompt

```python
response = client.chat(
    prompt="Design a REST API for a todo app",
    system_prompt="You are a senior API architect",
    temperature=0.5
)
```

### Multi-turn Conversation

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language..."},
    {"role": "user", "content": "Show me a hello world example"}
]
response = client.chat_messages(messages)
```

## Error Handling

```python
from grok_client import GrokClient, GrokError, GrokRateLimitError, GrokAuthError

try:
    client = GrokClient()
    response = client.chat("Hello")
except GrokAuthError:
    print("Check your API key")
except GrokRateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except GrokError as e:
    print(f"API error: {e}")
```

## Rate Limiting

The client handles rate limiting automatically:

1. Detects 429 responses
2. Reads `Retry-After` header if present
3. Uses exponential backoff (1s, 2s, 4s...)
4. Retries up to `max_retries` times (default: 3)

Configure retry behavior:

```python
client = GrokClient(
    max_retries=5,
    retry_delay=2.0,  # Initial delay
    timeout=120       # Request timeout
)
```

## CLI Usage

```bash
# Simple query
python grok_client.py "What is the capital of France?"

# Code generation
python grok_client.py -c "Write a binary search function"

# With language hint
python grok_client.py -c -l rust "Implement a linked list"

# Interactive mode
python grok_client.py
```

## Orchestrator Integration

Grok is automatically used for:
- System architecture tasks
- DevOps & infrastructure
- Security design
- Scalability challenges
- Novel/edge case solutions

Task routing example:
```python
from orchestrate import MultiModelOrchestrator

orch = MultiModelOrchestrator()
result = orch.orchestrate("Design a microservices architecture for an e-commerce platform")
# Grok will be selected as a primary model for architecture tasks
```

## Best Practices

1. **Temperature**: Use lower (0.3) for code, higher (0.7-1.0) for creative tasks
2. **System prompts**: Be specific about output format and constraints
3. **Max tokens**: Set appropriately to avoid truncation
4. **Retries**: Let the client handle transient errors automatically
5. **Code extraction**: Use `response.first_code_block` for clean code output

## Troubleshooting

### "GROK_API_KEY not set"
```bash
export GROK_API_KEY="your-key-here"
```

### Rate limit errors
- Reduce request frequency
- Use `grok-2-mini` for less critical tasks
- Implement request queuing

### Timeout errors
- Increase `timeout` parameter
- Reduce `max_tokens` for faster responses
- Check network connectivity
