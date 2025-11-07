"""
Cake Executor - Safely executes Cake scripts within Poetry-managed environments
"""
import subprocess
import os
from typing import Dict, Any, List
from pathlib import Path
import json
import time


class CakeExecutor:
    """Executes Cake build scripts safely within isolated Poetry environments"""
    
    def __init__(self, poetry_manager, config: Dict[str, Any]):
        self.poetry_manager = poetry_manager
        self.config = config
        self.execution_log = []
        
    def execute_script(self, script_path: str, env_path: str, 
                      args: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a Cake script within a Poetry environment
        """
        script_path_obj = Path(script_path)
        
        if not script_path_obj.exists():
            return {
                "success": False,
                "error": f"Script not found: {script_path}",
                "output": "",
                "execution_time": 0
            }
        
        # Build Cake command
        cake_command = self._build_cake_command(script_path, args)
        
        # Get isolation config
        isolation_config = self._get_isolation_config(env_path)
        timeout = isolation_config.get("resource_limits", {}).get("timeout", 30)
        
        # Execute within Poetry environment
        start_time = time.time()
        
        try:
            result = self._execute_in_poetry_env(env_path, cake_command, timeout)
            execution_time = time.time() - start_time
            
            # Log execution
            log_entry = {
                "timestamp": time.time(),
                "script": str(script_path),
                "env_path": env_path,
                "args": args,
                "success": result["success"],
                "execution_time": execution_time
            }
            self.execution_log.append(log_entry)
            
            result["execution_time"] = execution_time
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "execution_time": execution_time
            }
    
    def _build_cake_command(self, script_path: str, args: Dict[str, Any] = None) -> List[str]:
        """Build the Cake execution command"""
        # Check if dotnet-cake is available, otherwise use dotnet cake
        command = ["dotnet", "cake", script_path]
        
        # Add arguments
        if args:
            for key, value in args.items():
                command.append(f"--{key}={value}")
        
        return command
    
    def _execute_in_poetry_env(self, env_path: str, command: List[str], 
                               timeout: int) -> Dict[str, Any]:
        """Execute command in Poetry environment"""
        return self.poetry_manager.execute_in_environment(env_path, command, timeout)
    
    def _get_isolation_config(self, env_path: str) -> Dict[str, Any]:
        """Get isolation configuration for environment"""
        config_path = Path(env_path) / ".isolation_config.json"
        
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        
        return {}
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get execution log"""
        return self.execution_log
    
    def clear_execution_log(self):
        """Clear execution log"""
        self.execution_log = []
