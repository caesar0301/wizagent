# WizAgent Development Guide

## Project Overview

WizAgent is a sophisticated web automation and intelligent agent framework with advanced memory capabilities and multi-LLM support.

### Key Modules
- `wizagent.bu` - Browser automation and web interaction capabilities (includes LLM integrations)
- `wizagent.memu` - Advanced memory management system for AI agents
- `wizagent.prompt` - Prompt management and templating system
- `wizagent.web_surfer` - Web surfing and data extraction capabilities

### LLM Providers
Supported providers in `wizagent.bu.llm`:
- `openai` - OpenAI API compatible services
- `anthropic` - Claude models via Anthropic API
- `google` - Gemini models via Google AI API
- `aws` - AWS Bedrock models (Claude, etc.)
- `azure` - Azure OpenAI services
- `groq` - Groq inference API
- `deepseek` - DeepSeek models
- `ollama` - Local Ollama instances
- `openrouter` - OpenRouter API for multiple providers

## Project Structure

```
wizagent/
├── wizagent/              # Core functionality
│   ├── bu/               # Browser automation (BU - Browser Use)
│   │   ├── agent/        # Agent management and messaging
│   │   │   ├── message_manager/  # Message handling utilities
│   │   │   ├── service.py        # Agent service
│   │   │   ├── prompts.py        # Agent prompts
│   │   │   └── views.py          # Agent views
│   │   ├── browser/      # Browser control and watchdogs  
│   │   │   ├── watchdogs/        # Browser monitoring watchdogs
│   │   │   ├── session.py        # Browser session management
│   │   │   └── views.py          # Browser views
│   │   ├── dom/          # DOM manipulation and serialization
│   │   │   ├── serializer/       # DOM serialization
│   │   │   ├── playground/       # DOM experimentation
│   │   │   └── enhanced_snapshot.py  # Enhanced DOM snapshots
│   │   ├── llm/          # LLM integrations for browser use
│   │   │   ├── openai/           # OpenAI integration
│   │   │   ├── anthropic/        # Anthropic integration
│   │   │   ├── google/           # Google/Gemini integration
│   │   │   ├── aws/              # AWS Bedrock integration
│   │   │   ├── azure/            # Azure OpenAI integration
│   │   │   ├── groq/             # Groq integration
│   │   │   ├── deepseek/         # DeepSeek integration
│   │   │   ├── ollama/           # Ollama integration
│   │   │   └── openrouter/       # OpenRouter integration
│   │   ├── tools/        # Tool registry and management
│   │   │   └── registry/         # Tool registry implementation
│   │   ├── screenshots/  # Screenshot capture utilities
│   │   ├── filesystem/   # File system integration for browser
│   │   ├── integrations/ # External integrations
│   │   │   └── gmail/            # Gmail integration
│   │   ├── mcp/          # Model Context Protocol support
│   │   └── tokens/       # Token management and cost tracking
│   ├── memu/             # Advanced memory management system
│   │   ├── config/       # Memory configuration and prompts
│   │   │   ├── activity/         # Activity memory config
│   │   │   ├── event/            # Event memory config
│   │   │   └── profile/          # Profile memory config
│   │   └── memory/       # Memory agent and file management
│   │       ├── actions/          # Memory operation actions
│   │       ├── memory_agent.py   # Main memory agent
│   │       ├── file_manager.py   # File-based storage
│   │       ├── embeddings.py     # Embedding utilities
│   │       └── recall_agent.py   # Memory retrieval agent
│   ├── prompt/           # Prompt management system
│   │   ├── prompt.py             # Prompt templates
│   │   └── message.py            # Message formatting
│   ├── prompt_template/  # Prompt template files
│   ├── llm_adapter.py    # LLM client adapter for cogents-core
│   └── web_surfer.py     # Web surfing capabilities
├── examples/             # Usage examples and demonstrations
│   ├── bu_examples/      # Browser automation examples
│   │   ├── getting_started/      # Basic tutorials
│   │   ├── features/             # Feature demonstrations
│   │   ├── custom-functions/     # Custom function examples
│   │   ├── integrations/         # Integration examples
│   │   ├── models/               # LLM model examples
│   │   ├── use-cases/            # Real-world use cases
│   │   └── ui/                   # UI examples (Gradio, Streamlit)
│   ├── memory_agent/     # Memory system examples
│   └── prompt_manager/   # Prompt management examples
├── tests/               # Test suite
│   └── test_web_surfer.py
└── wiz-memory-store/    # Memory storage location
```

### Core Module Details

**Memory Management (`wizagent.memu`)**
- `memory/` - Advanced memory agent with function calling architecture
- `config/` - Memory category configuration and prompt templates
- `actions/` - Individual memory operation modules (add, link, cluster, etc.)
- `file_manager.py` - File-based memory storage in markdown format
- `embeddings.py` - Embedding client for semantic memory search

**Browser Use (`wizagent.bu`)**
- `agent/` - Agent service and message management for browser automation
- `browser/` - Browser control, profiles, and watchdog systems for monitoring
- `dom/` - DOM manipulation, enhanced snapshots, and element serialization
- `llm/` - Multi-provider LLM integrations optimized for browser use
  - `openai/` - OpenAI API integration with function calling support
  - `anthropic/` - Claude models via Anthropic API
  - `google/` - Gemini models with vision capabilities
  - `aws/` - AWS Bedrock integration for Claude and other models
  - `azure/` - Azure OpenAI services integration
  - `groq/` - Groq inference API for fast model responses
  - `deepseek/` - DeepSeek model integration
  - `ollama/` - Local Ollama model support
  - `openrouter/` - Multi-provider access through OpenRouter
- `tools/` - Tool registry and management for browser actions
- `screenshots/` - Screenshot capture and management utilities
- `filesystem/` - File system integration for browser file operations

**Prompt Management (`wizagent.prompt`)**
- `prompt.py` - Advanced prompt template system with variable substitution
- `message.py` - Message formatting and conversation management
- Template support for different agent types and use cases

### Additional Components

**Web Surfing (`wizagent.web_surfer`)**
- Intelligent web browsing and data extraction
- Integration with search engines and web APIs
- Content analysis and structured data extraction

**LLM Adapter (`wizagent.llm_adapter`)**
- Unified interface for cogents-core LLM clients
- Browser-use compatibility layer
- Automatic provider configuration from environment variables

## Development Workflow

### After Each Implementation
1. **Run unit tests**: `make test-unit` to ensure tests pass
2. **Format code**: `make format` to apply consistent formatting
3. **Check quality**: `make quality` for comprehensive code quality checks

### Quick Development Checks
- `make dev-check` - Quality + unit tests (fast feedback)
- `make full-check` - All checks + tests + build (comprehensive)
- `make ci-test` - CI test suite
- `make ci-quality` - CI quality checks

### Python Command Execution

- **Always use `poetry run` for Python commands in development**
  - Use `poetry run python script.py` instead of `python script.py`
  - Use `poetry run pytest` instead of `pytest`
  - Use `poetry run python -m module` instead of `python -m module`
  - This ensures proper dependency management and virtual environment isolation

## Examples

```bash
# ✅ Correct
poetry run python examples/base/llamacpp_demo.py
poetry run python examples/goalith/goalith_decomposer_example.py
poetry run pytest tests/
poetry run python -m cogents_core.example

# ❌ Incorrect
python examples/base/llamacpp_demo.py
pytest tests/
python -m cogents_core.example
```

## Usage Examples

### Basic Imports

```python
# LLM clients
from wizagent.llm_adapter import get_llm_client

# Memory management
from wizagent.memu import MemoryAgent, get_default_embedding_client

# Prompt management
from wizagent.prompt import Prompt, Message

# Web surfing
from wizagent.web_surfer import WebSurfer
```

### LLM Usage Examples

```python
from wizagent.llm_adapter import get_llm_client

# Environment variable configuration (recommended)
# Set these environment variables:
# WIZAGENT_LLM_PROVIDER=openai
# WIZAGENT_LLM_API_KEY=your-api-key
# WIZAGENT_LLM_CHAT_MODEL=gpt-4
# WIZAGENT_LLM_BASE_URL=custom-endpoint (optional)

# Get LLM client (automatically configured from environment)
client = get_llm_client(instructor=True)

# Basic chat completion
response = client.chat_completion([
    {"role": "user", "content": "Hello, how are you?"}
])

# Memory Agent usage
from wizagent.memu import MemoryAgent

memory_agent = MemoryAgent(
    agent_id="my_agent",
    user_id="user_123",
    memory_dir="./memory_storage"
)
memory_agent.memory_core.llm_client = client

# Process conversation with automated memory management
results = memory_agent.run(
    conversation=[
        {"role": "user", "content": "Hi, I'm Alice"},
        {"role": "assistant", "content": "Nice to meet you Alice!"}
    ],
    character_name="Alice",
    max_iterations=10
)
```

### Environment Variables

For WizAgent configuration, you can set:
- `WIZAGENT_LLM_PROVIDER` - LLM provider (openai, anthropic, azure, etc.)
- `WIZAGENT_LLM_API_KEY` - API key for the chosen provider
- `WIZAGENT_LLM_CHAT_MODEL` - Model name (gpt-4, claude-3-sonnet, etc.)
- `WIZAGENT_LLM_BASE_URL` - Custom base URL for provider (optional)

## Testing

- Integration tests are marked as `pytest.mark.integration`
- Use `make test-unit` to run unit tests
- Use `make test-integration` to run integration tests
- Use `make test` to run all tests
- Use `poetry run pytest tests/` to run all tests (manual)
- Use `poetry run pytest -m integration` for integration tests only (manual)
- Use `poetry run pytest -m "not slow"` to skip slow tests (manual)

### Test Classification Rules

**Integration Tests**: Mark tests with `@pytest.mark.integration` if they:
- Depend on external API services (OpenAI, OpenRouter, Gemini, etc.)
- Require network connectivity to third-party services
- Need API keys or authentication tokens
- Make actual HTTP requests to external services

**Unit Tests**: Tests that can run locally without external dependencies:
- Use mocked external services
- Test local functionality only (file operations, data processing, etc.)
- Don't require network connectivity
- Can run in isolated environments

**Examples:**
```python
# Integration test - requires OpenAI API
@pytest.mark.integration
async def test_analyze_image_with_openai(self, image_toolkit):
    result = await image_toolkit.analyze_image("image.jpg", "Describe this")
    assert "description" in result

# Unit test - uses mocks, runs locally
async def test_get_image_info_success(self, image_toolkit):
    with patch.object(image_toolkit, "_load_image") as mock_load:
        mock_image = MagicMock()
        mock_image.size = (800, 600)
        mock_load.return_value = mock_image

        result = await image_toolkit.get_image_info("image.jpg")
        assert result["width"] == 800
```

## Code Quality

- Use `make format` to format code (black, isort, autoflake)
- Use `make format-check` to check formatting without changes
- Use `make lint` to run linting (flake8, mypy)
- Use `make quality` to run all quality checks
- Use `make autofix` to auto-fix code quality issues
- Keep the first-level folder stuctures of `cogents`, `examples`, and `tests` as the same.

## Development Environment Tips

- Use `poetry install` to install dependencies
- Use `poetry shell` to activate the virtual environment
- Use `poetry add <package>` to add new dependencies
- Use `poetry update` to update existing dependencies

## PR Guidelines

- Title format: `[<module_name>] <Description>`
- Always run `make quality` and `make test` before committing
- Ensure all tests pass before submitting PRs
- Update documentation for any new features or breaking changes
- Follow the existing code style and patterns

## Environment Variables Documentation

### Rule: Production-Only Environment Variables
When creating or updating `env.example` files, **ONLY include environment variables that are actually used in production code**.

**What to include:**
- Environment variables used in `cogents/core/**/*.py` files
- Variables that control runtime behavior of the application
- Configuration variables that users need to set for production deployment

**What to exclude:**
- Environment variables only used in `examples/**/*.py` files
- Variables only used in `tests/**/*.py` files
- Variables only used in `thirdparty/**/*.py` files
- Test-specific configuration variables
- Example-specific configuration variables

**How to verify:**
1. Search for `os.getenv` and `os.environ` usage in production code
2. Use pattern: `cogents/core/**/*.py` (exclude examples, tests, thirdparty)
3. Only document variables that appear in production code search results

**Example:**
```bash
# ✅ Include - used in production code
grep_search query="os\.getenv|os\.environ" include_pattern="cogents/core/**/*.py" exclude_pattern="**/tests/**|**/examples/**|**/thirdparty/**"

# ❌ Don't include - only used in examples/tests
grep_search query="os\.getenv|os\.environ" include_pattern="examples/**/*.py"
```

This ensures that `env.example` files are accurate and only show variables that users actually need to configure in production environments.

## Rationale

Using `poetry run` ensures:
- Consistent dependency versions across development environments
- Proper virtual environment activation
- Access to all project dependencies
- Isolation from system Python packages
