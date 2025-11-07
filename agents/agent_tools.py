"""Tool definitions and execution logic for Defense Agent."""

import os
import subprocess
import glob
from typing import Any, Dict, List
import uuid
import json
import sys
from pathlib import Path
import shutil

# Add parent directory for defense system imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Tool definitions in Claude's format
TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file from the filesystem. Returns the file content with line numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The absolute or relative path to the file to read"
                },
                "start_line": {
                    "type": "integer",
                    "description": "Optional starting line number (1-indexed). If not provided, reads from beginning."
                },
                "end_line": {
                    "type": "integer",
                    "description": "Optional ending line number (1-indexed). If not provided, reads to end."
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "create_file",
        "description": "Create a new file with the specified content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path where the file should be created"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "Edit a file by replacing a specific section of text. The search text must match exactly.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit"
                },
                "search": {
                    "type": "string",
                    "description": "The exact text to search for (must match exactly including whitespace)"
                },
                "replace": {
                    "type": "string",
                    "description": "The text to replace it with. Use empty string to delete."
                }
            },
            "required": ["path", "search", "replace"]
        }
    },
    {
        "name": "run_command",
        "description": "Execute a shell command and return the output. Use this to run tests, build, lint, git commands, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                },
                "cwd": {
                    "type": "string",
                    "description": "Optional working directory for the command"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "aish",
        "description": "Get AI-powered shell command suggestions using Microsoft AI Shell (aish). Use this when you need help constructing complex shell commands. If aish is not installed, provides simulated AI suggestions based on the query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language description of what you want to do in the shell"
                },
                "use_system_aish": {
                    "type": "boolean",
                    "description": "If true, attempts to use system aish command if available. If false or unavailable, uses built-in suggestions."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for files matching a pattern using glob syntax (e.g., '**/*.py' for all Python files).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match files (e.g., '*.py', 'src/**/*.js')"
                },
                "root_dir": {
                    "type": "string",
                    "description": "Directory to start search from. Defaults to current directory."
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "grep",
        "description": "Search for text patterns in files. Returns matching lines with file paths and line numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The text pattern to search for"
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Optional file pattern to limit search (e.g., '*.py')"
                }
            },
            "required": ["pattern", "path"]
        }
    },
    {
        "name": "defense_status",
        "description": "Get the current status of the Zero-Trust AI Defense system, including active environments, execution counts, and system health.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "view_defense_logs",
        "description": "View defense system logs including environment creation and counter-action logs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "log_type": {
                    "type": "string",
                    "description": "Type of log to view: 'environment' or 'counter_actions'",
                    "enum": ["environment", "counter_actions", "all"]
                },
                "lines": {
                    "type": "integer",
                    "description": "Number of recent lines to show. Default is 50."
                }
            },
            "required": ["log_type"]
        }
    },
    {
        "name": "analyze_threat",
        "description": "Analyze a potential threat by simulating it through the defense system detection pipeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "request_data": {
                    "type": "object",
                    "description": "Request data to analyze (must include: ip, user_agent, endpoint, content)"
                }
            },
            "required": ["request_data"]
        }
    },
    {
        "name": "list_scenarios",
        "description": "List all available attack scenarios and their configurations from the defense system.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "create_todo_list",
        "description": "Create a TODO list for complex tasks with 3+ steps. Replaces any existing TODO list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Short summary of the task"
                            },
                            "details": {
                                "type": "string",
                                "description": "Additional context about the task"
                            }
                        },
                        "required": ["title", "details"]
                    }
                }
            },
            "required": ["todos"]
        }
    },
    {
        "name": "read_todos",
        "description": "Read the current TODO list to check progress.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "mark_todo_done",
        "description": "Mark one or more TODO items as completed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "todo_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of TODO IDs to mark as done"
                }
            },
            "required": ["todo_ids"]
        }
    }
]


def execute_tool(tool_name: str, parameters: Dict[str, Any], agent_state: Any) -> Any:
    """Execute a tool and return its result."""
    
    tool_map = {
        "read_file": tool_read_file,
        "create_file": tool_create_file,
        "edit_file": tool_edit_file,
        "run_command": tool_run_command,
        "aish": tool_aish,
        "search_files": tool_search_files,
        "grep": tool_grep,
        "defense_status": lambda p: tool_defense_status(agent_state),
        "view_defense_logs": tool_view_defense_logs,
        "analyze_threat": lambda p: tool_analyze_threat(p, agent_state),
        "list_scenarios": tool_list_scenarios,
        "create_todo_list": lambda p: tool_create_todo_list(p, agent_state),
        "read_todos": lambda p: tool_read_todos(agent_state),
        "mark_todo_done": lambda p: tool_mark_todo_done(p, agent_state)
    }
    
    tool_func = tool_map.get(tool_name)
    if tool_func:
        # Check if function needs only agent_state or both params and agent_state
        if tool_name in ["defense_status", "read_todos"]:
            return tool_func()
        elif tool_name in ["analyze_threat", "create_todo_list", "mark_todo_done"]:
            return tool_func(parameters)
        else:
            return tool_func(parameters)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def tool_read_file(params: Dict[str, Any]) -> Dict[str, Any]:
    """Read file contents with optional line range."""
    try:
        path = params["path"]
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start = params.get("start_line", 1) - 1  # Convert to 0-indexed
        end = params.get("end_line", len(lines))
        
        selected_lines = lines[start:end]
        content = "".join([f"{i+start+1}|{line}" for i, line in enumerate(selected_lines)])
        
        return {
            "path": path,
            "content": content,
            "total_lines": len(lines)
        }
    except Exception as e:
        return {"error": str(e)}


def tool_create_file(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new file."""
    try:
        path = params["path"]
        content = params["content"]
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {"success": True, "path": path}
    except Exception as e:
        return {"error": str(e)}


def tool_edit_file(params: Dict[str, Any]) -> Dict[str, Any]:
    """Edit a file using search and replace."""
    try:
        path = params["path"]
        search = params["search"]
        replace = params["replace"]
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if search not in content:
            return {"error": f"Search text not found in {path}"}
        
        new_content = content.replace(search, replace, 1)  # Replace first occurrence
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {"success": True, "path": path}
    except Exception as e:
        return {"error": str(e)}


def tool_run_command(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a shell command."""
    try:
        command = params["command"]
        cwd = params.get("cwd", None)
        
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 30 seconds"}
    except Exception as e:
        return {"error": str(e)}


def tool_aish(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get AI-powered shell command suggestions using Microsoft AI Shell (aish).
    Attempts to use system aish if available, otherwise provides simulated suggestions.
    """
    query = params["query"]
    use_system = params.get("use_system_aish", True)
    
    # Check if aish is available on the system
    aish_available = shutil.which("aish") is not None
    
    if use_system and aish_available:
        try:
            result = subprocess.run(
                ["aish", query],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                "source": "system_aish",
                "suggestion": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {"error": f"Failed to run system aish: {str(e)}"}
    else:
        # Provide built-in AI suggestions based on common patterns
        suggestions = _get_builtin_shell_suggestions(query)
        return {
            "source": "builtin_suggestions",
            "suggestion": suggestions,
            "note": "System aish not available. Using built-in suggestions."
        }


def _get_builtin_shell_suggestions(query: str) -> str:
    """Provide built-in shell command suggestions based on query patterns."""
    query_lower = query.lower()
    
    # Common patterns
    patterns = {
        "find files": "Get-ChildItem -Path . -Recurse -Filter '*.ext'",
        "search text": "Select-String -Path '*.ext' -Pattern 'text'",
        "list directory": "Get-ChildItem -Path .",
        "run tests": "poetry run pytest",
        "git status": "git status",
        "git commit": "git commit -m 'message'",
        "poetry install": "poetry install",
        "poetry run": "poetry run python script.py",
        "cake": "dotnet cake script.cake",
        "check port": "netstat -ano | findstr :PORT",
        "process list": "Get-Process | Where-Object {$_.Name -like '*name*'}",
        "kill process": "Stop-Process -Name process_name -Force",
        "environment variable": "$env:VAR_NAME",
        "start server": "poetry run python server/protected_server.py"
    }
    
    for pattern, suggestion in patterns.items():
        if pattern in query_lower:
            return f"Suggested command: {suggestion}\n\nAdjust as needed for your specific use case."
    
    return f"For query '{query}', consider breaking it down into specific PowerShell or Python commands. Use 'Get-Help command' for PowerShell help."


def tool_search_files(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search for files matching a pattern."""
    try:
        pattern = params["pattern"]
        root_dir = params.get("root_dir", ".")
        
        # Use glob to find matching files
        matches = glob.glob(os.path.join(root_dir, pattern), recursive=True)
        
        # Filter out directories
        files = [f for f in matches if os.path.isfile(f)]
        
        return {
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        return {"error": str(e)}


def tool_grep(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search for text in files."""
    try:
        pattern = params["pattern"]
        path = params["path"]
        file_pattern = params.get("file_pattern", "*")
        
        results = []
        
        if os.path.isfile(path):
            files = [path]
        else:
            files = glob.glob(os.path.join(path, "**", file_pattern), recursive=True)
            files = [f for f in files if os.path.isfile(f)]
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.lower() in line.lower():
                            results.append({
                                "file": file_path,
                                "line": line_num,
                                "text": line.strip()
                            })
            except:
                continue  # Skip files that can't be read
        
        return {
            "matches": results,
            "count": len(results)
        }
    except Exception as e:
        return {"error": str(e)}


def tool_defense_status(agent_state: Any) -> Dict[str, Any]:
    """Get defense system status."""
    return agent_state.get_defense_status()


def tool_view_defense_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    """View defense system logs."""
    try:
        log_type = params["log_type"]
        lines = params.get("lines", 50)
        
        logs_dir = Path("logs")
        result = {}
        
        if log_type in ["environment", "all"]:
            env_log = logs_dir / "environment_creation.log"
            if env_log.exists():
                with open(env_log, 'r') as f:
                    all_lines = f.readlines()
                    result["environment_logs"] = all_lines[-lines:]
            else:
                result["environment_logs"] = ["No environment logs found"]
        
        if log_type in ["counter_actions", "all"]:
            # Counter actions are typically in Cake output
            result["counter_actions"] = ["Counter action logs are stored with Cake execution output"]
        
        return result
    except Exception as e:
        return {"error": str(e)}


def tool_analyze_threat(params: Dict[str, Any], agent_state: Any) -> Dict[str, Any]:
    """Analyze a threat through the defense system."""
    try:
        import time
        request_data = params["request_data"]
        
        # Ensure required fields
        if "timestamp" not in request_data:
            request_data["timestamp"] = time.time()
        
        # Process through defense system
        return agent_state.process_defense_request(request_data)
    except Exception as e:
        return {"error": str(e)}


def tool_list_scenarios() -> Dict[str, Any]:
    """List available attack scenarios."""
    try:
        import yaml
        config_path = Path("config/policies.yaml")
        
        if not config_path.exists():
            return {"error": "policies.yaml not found"}
        
        with open(config_path, 'r') as f:
            policies = yaml.safe_load(f)
        
        scenarios = policies.get("scenarios", {})
        
        return {
            "scenarios": {
                name: {
                    "description": config.get("description"),
                    "isolation_level": config.get("isolation_level"),
                    "counter_strategy": config.get("counter_strategy")
                }
                for name, config in scenarios.items()
            },
            "count": len(scenarios)
        }
    except Exception as e:
        return {"error": str(e)}


def tool_create_todo_list(params: Dict[str, Any], agent_state: Any) -> Dict[str, Any]:
    """Create a new TODO list."""
    todos = params["todos"]
    agent_state.todos = []
    agent_state.todo_id_counter = 0
    
    for todo in todos:
        todo_id = str(uuid.uuid4())
        agent_state.todos.append({
            "id": todo_id,
            "title": todo["title"],
            "details": todo["details"],
            "done": False
        })
    
    return {"success": True, "count": len(agent_state.todos)}


def tool_read_todos(agent_state: Any) -> Dict[str, Any]:
    """Read current TODO list."""
    pending = [t for t in agent_state.todos if not t["done"]]
    completed = [t for t in agent_state.todos if t["done"]]
    
    return {
        "pending": pending,
        "completed": completed
    }


def tool_mark_todo_done(params: Dict[str, Any], agent_state: Any) -> Dict[str, Any]:
    """Mark TODOs as complete."""
    todo_ids = params["todo_ids"]
    
    for todo in agent_state.todos:
        if todo["id"] in todo_ids:
            todo["done"] = True
    
    return {"success": True}
