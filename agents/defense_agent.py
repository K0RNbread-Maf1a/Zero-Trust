"""Defense Agent - Warp-style AI agent integrated with Zero-Trust AI Defense system."""

import anthropic
from typing import Any, Dict, List
import json
import sys
from pathlib import Path

# Add parent directory to path for defense system imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .agent_config import ANTHROPIC_API_KEY, MODEL, MAX_TOKENS, TEMPERATURE, SYSTEM_PROMPT
from .agent_tools import TOOLS, execute_tool


class DefenseAgent:
    """
    Main agent class that handles conversation, tool execution, 
    and integration with the Zero-Trust AI Defense system.
    """
    
    def __init__(self, defense_orchestrator=None):
        """
        Initialize the Defense Agent.
        
        Args:
            defense_orchestrator: Optional DefenseOrchestrator instance for defense integration
        """
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.conversation_history: List[Dict[str, Any]] = []
        self.todos: List[Dict[str, Any]] = []
        self.todo_id_counter = 0
        self.defense_orchestrator = defense_orchestrator
        
    def run(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.
        Handles the agentic loop with tool calls.
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        response_text = ""
        
        # Agentic loop: keep calling the model until no more tool calls
        while True:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                system=SYSTEM_PROMPT,
                messages=self.conversation_history,
                tools=TOOLS
            )
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })
            
            # Extract text from response
            for block in response.content:
                if block.type == "text":
                    response_text = block.text
            
            # Check if we're done (no tool calls)
            if response.stop_reason == "end_turn":
                break
            
            # Execute tool calls
            if response.stop_reason == "tool_use":
                tool_results = []
                
                for block in response.content:
                    if block.type == "tool_use":
                        result = execute_tool(
                            block.name,
                            block.input,
                            agent_state=self
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result) if isinstance(result, dict) else str(result)
                        })
                
                # Add tool results to conversation
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
            else:
                # Unexpected stop reason
                break
        
        return response_text
    
    def reset(self):
        """Clear conversation history."""
        self.conversation_history = []
        self.todos = []
        
    def get_defense_status(self) -> Dict[str, Any]:
        """Get status of the defense system if orchestrator is available."""
        if self.defense_orchestrator:
            return self.defense_orchestrator.get_status()
        return {"error": "Defense orchestrator not initialized"}
    
    def process_defense_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request through the defense system.
        
        Args:
            request_data: Request data dictionary containing timestamp, ip, user_agent, etc.
            
        Returns:
            Defense response with action and countermeasures
        """
        if self.defense_orchestrator:
            return self.defense_orchestrator.process_request(request_data)
        return {"error": "Defense orchestrator not initialized"}
