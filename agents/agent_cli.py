"""CLI interface for the Defense Agent."""

import sys
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.defense_agent import DefenseAgent
from agents.agent_config import ANTHROPIC_API_KEY
from core.orchestrator import DefenseOrchestrator


def main():
    """Run the Defense Agent in interactive mode."""
    console = Console()
    
    # Check for API key
    if not ANTHROPIC_API_KEY:
        console.print("[red]Error: ANTHROPIC_API_KEY not found in environment.[/red]")
        console.print("Please set your API key:")
        console.print("  $env:ANTHROPIC_API_KEY='your_key_here'")
        console.print("Or create a .env file in the project root.")
        sys.exit(1)
    
    # Initialize defense system
    console.print("[yellow]Initializing Zero-Trust AI Defense System...[/yellow]")
    try:
        base_dir = Path(__file__).parent.parent
        config_dir = base_dir / "config"
        orchestrator = DefenseOrchestrator(str(config_dir), str(base_dir))
        console.print("[green]✓ Defense system initialized[/green]")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not initialize defense system: {e}[/yellow]")
        console.print("[yellow]Agent will run without defense integration[/yellow]")
        orchestrator = None
    
    # Initialize agent
    agent = DefenseAgent(defense_orchestrator=orchestrator)
    
    console.print(Panel.fit(
        "[bold cyan]Defense Agent[/bold cyan]\n"
        "AI agent integrated with Zero-Trust AI Defense system.\n\n"
        "[dim]Special commands:[/dim]\n"
        "  [cyan]/status[/cyan]  - Show defense system status\n"
        "  [cyan]/help[/cyan]    - Show available tools\n"
        "  [cyan]/reset[/cyan]   - Clear conversation history\n"
        "  [cyan]/quit[/cyan]    - Exit the agent\n\n"
        "[dim]Type your request to begin...[/dim]",
        border_style="cyan"
    ))
    
    while True:
        try:
            # Get user input
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            
            if not user_input.strip():
                continue
            
            # Handle special commands
            if user_input.lower() in ['/quit', '/exit', '/q']:
                console.print("[cyan]Goodbye![/cyan]")
                break
            
            if user_input.lower() == '/reset':
                agent.reset()
                console.print("[cyan]Conversation history cleared.[/cyan]")
                continue
            
            if user_input.lower() == '/status':
                status = agent.get_defense_status()
                console.print("[bold]Defense System Status:[/bold]")
                console.print(status)
                continue
            
            if user_input.lower() == '/help':
                console.print("[bold]Available Tools:[/bold]")
                console.print("• File operations: read_file, create_file, edit_file")
                console.print("• Shell commands: run_command, aish")
                console.print("• Code search: search_files, grep")
                console.print("• Defense system: defense_status, analyze_threat, list_scenarios, view_defense_logs")
                console.print("• Task management: create_todo_list, read_todos, mark_todo_done")
                continue
            
            # Get agent response
            console.print("\n[bold blue]Agent[/bold blue]:")
            try:
                response = agent.run(user_input)
                # Display response as markdown
                console.print(Markdown(response))
            except Exception as e:
                console.print(f"[red]Error during execution: {e}[/red]")
                console.print("[yellow]The agent encountered an error. Try rephrasing your request.[/yellow]")
            
        except KeyboardInterrupt:
            console.print("\n[cyan]Interrupted. Type /quit to exit or press Enter to continue.[/cyan]")
            continue
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")


if __name__ == "__main__":
    main()
