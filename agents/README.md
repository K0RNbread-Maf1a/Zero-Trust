# Defense Agent

An AI agent integrated with the Zero-Trust AI Defense system, providing autonomous task execution, defense system interaction, and AI-powered shell assistance.

## Overview

The Defense Agent is a Warp-style AI agent that can:
- Execute development tasks autonomously
- Interact with the Zero-Trust AI Defense system
- Analyze threats and review defense logs
- Use AI-powered shell assistance (via aishell integration)
- Manage complex tasks with TODO lists

## Setup

### 1. Install Dependencies

```powershell
poetry install
```

This will install the required packages:
- `anthropic` - Claude API client
- `rich` - Rich terminal UI
- All defense system dependencies

### 2. Configure API Key

Set your Anthropic API key as an environment variable:

```powershell
$env:ANTHROPIC_API_KEY="your_api_key_here"
```

Or create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Run the Agent

```powershell
poetry run defense-agent
```

Or directly:

```powershell
poetry run python agents/agent_cli.py
```

## Features

### Standard Tools

- **File Operations**: Read, create, and edit files
- **Shell Commands**: Execute PowerShell/cmd commands
- **Code Search**: Find files and search for text patterns
- **Task Management**: Automatic TODO lists for complex operations

### Defense System Integration

- **defense_status**: Get current defense system status
- **analyze_threat**: Simulate a request through the detection pipeline
- **list_scenarios**: View available attack scenarios
- **view_defense_logs**: Inspect environment and counter-action logs

### AI-Powered Shell (aish)

The agent includes an `aish` tool that:
- Attempts to use system aish if installed (Microsoft AI Shell)
- Falls back to built-in command suggestions if aish is unavailable
- Provides PowerShell command suggestions based on natural language queries

## Usage Examples

### Development Tasks

```
You: find all Python files in the core directory
Agent: [uses search_files tool]

You: read the detector.py file
Agent: [displays file contents with line numbers]

You: add a comment explaining the risk scoring algorithm
Agent: [edits the file]
```

### Defense System Operations

```
You: check the defense system status
Agent: [uses defense_status tool]

You: show me the available attack scenarios
Agent: [uses list_scenarios tool]

You: analyze this SQL injection: {"ip": "203.0.113.42", "content": "SELECT * FROM users WHERE id='1' OR '1'='1'"}
Agent: [uses analyze_threat tool, shows risk assessment]
```

### Shell Assistance

```
You: use aish to suggest a command for finding large files
Agent: [calls aish tool with query]

You: run the suggested command
Agent: [executes via run_command]
```

### Complex Tasks

```
You: refactor the query_analyzer.py to improve performance
Agent: [creates TODO list, reads file, analyzes code, makes changes, runs tests]
```

## Special Commands

When running the agent CLI:

- `/status` - Show defense system status
- `/help` - Show available tools
- `/reset` - Clear conversation history
- `/quit` - Exit the agent

## Architecture

### Components

- **defense_agent.py**: Main agent with agentic loop
- **agent_config.py**: Configuration and system prompt
- **agent_tools.py**: Tool definitions and implementations
- **agent_cli.py**: Rich CLI interface

### Tool Execution Flow

```
User Request → Claude API → Tool Selection → Tool Execution → Result → Response
                    ↑                                                      ↓
                    └──────────── Agentic Loop (continues) ───────────────┘
```

### Defense Integration

The agent can optionally be initialized with a `DefenseOrchestrator` instance:

```python
from agents import DefenseAgent
from core.orchestrator import DefenseOrchestrator

orchestrator = DefenseOrchestrator("config", ".")
agent = DefenseAgent(defense_orchestrator=orchestrator)
```

This enables defense-specific tools like `analyze_threat` and `defense_status`.

## aish Integration

The agent's `aish` tool provides two modes:

### System aish Mode
If aish is installed (Microsoft AI Shell via `winget install Microsoft.AIShell`):
- Calls the system aish command
- Returns actual AI-powered suggestions

### Fallback Mode
If aish is not available:
- Uses built-in pattern matching
- Provides suggestions for common PowerShell commands
- Covers: file operations, git commands, poetry, cake, process management

To use system aish specifically:
```python
# Agent will automatically detect and use if available
"use aish to find files modified in the last day"
```

## Security Considerations

- **API Key**: Never commit your ANTHROPIC_API_KEY
- **Shell Execution**: Commands run with full shell access - be cautious
- **Defense System**: Agent can analyze threats but not modify active defenses without explicit action
- **Logs**: All tool executions are visible in the conversation

## Programmatic Usage

You can use the agent programmatically:

```python
from agents import DefenseAgent
from core.orchestrator import DefenseOrchestrator

# Initialize with defense system
orchestrator = DefenseOrchestrator("config", ".")
agent = DefenseAgent(defense_orchestrator=orchestrator)

# Run a task
response = agent.run("analyze the recent defense logs")
print(response)

# Check defense status
status = agent.get_defense_status()
print(status)

# Process a threat
threat_data = {
    "ip": "203.0.113.42",
    "user_agent": "bot",
    "endpoint": "/api/users",
    "content": "malicious content"
}
result = agent.process_defense_request(threat_data)
print(result)
```

## Troubleshooting

### API Key Not Found
```
Error: ANTHROPIC_API_KEY not found in environment.
```
Set the environment variable or create a .env file.

### Defense System Initialization Failed
```
Warning: Could not initialize defense system
```
The agent will continue without defense integration. Check that config files exist.

### aish Not Found
The agent will fall back to built-in suggestions. To use system aish:
```powershell
winget install Microsoft.AIShell
```

### Import Errors
```powershell
poetry install  # Ensure all dependencies are installed
```

## Future Enhancements

- Streaming responses for better UX
- Vector database for semantic code search
- Multi-agent collaboration
- Persistent memory between sessions
- Git operation integration
- Enhanced aish integration with conversation context
