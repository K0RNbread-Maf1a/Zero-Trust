"""
Cake Script Generator - Generates targeted Cake build scripts based on attacker patterns
"""
from typing import Dict, Any
from pathlib import Path
from jinja2 import Template
import json


class CakeScriptGenerator:
    """Generates Cake build scripts dynamically based on attack analysis"""
    
    def __init__(self, templates_dir: str, config: Dict[str, Any]):
        self.templates_dir = Path(templates_dir)
        self.config = config
        self.scenarios = config.get("scenarios", {})
        self.counter_strategies = config.get("counter_strategies", {})
        
    def generate_script(self, scenario_name: str, attack_details: Dict[str, Any],
                       intensity: str = "medium") -> str:
        """
        Generate a Cake script for the given scenario
        """
        scenario_config = self.scenarios.get(scenario_name, {})
        
        if not scenario_config:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        template_name = scenario_config.get("cake_template", "default.cake")
        template_path = self.templates_dir / template_name
        
        if not template_path.exists():
            # Use default template
            template_path = self.templates_dir / "default.cake"
        
        # Load template
        with open(template_path) as f:
            template_content = f.read()
        
        template = Template(template_content)
        
        # Prepare context for template
        context = self._prepare_context(scenario_name, scenario_config, 
                                       attack_details, intensity)
        
        # Render template
        script_content = template.render(**context)
        
        return script_content
    
    def _prepare_context(self, scenario_name: str, scenario_config: Dict[str, Any],
                        attack_details: Dict[str, Any], intensity: str) -> Dict[str, Any]:
        """Prepare context data for template rendering"""
        
        counter_strategy_name = scenario_config.get("counter_strategy", "")
        counter_strategy = self.counter_strategies.get(counter_strategy_name, {})
        
        tactics = counter_strategy.get("tactics", [])
        intensity_levels = counter_strategy.get("intensity_levels", {})
        intensity_value = intensity_levels.get(intensity, 10)
        
        attacker_ip = attack_details.get("ip", "unknown")
        attacker_endpoint = attack_details.get("endpoint", "")
        attack_type = attack_details.get("attack_type", "unknown")
        
        context = {
            "scenario_name": scenario_name,
            "counter_strategy": counter_strategy_name,
            "tactics": tactics,
            "intensity": intensity_value,
            "attacker_ip": attacker_ip,
            "attacker_endpoint": attacker_endpoint,
            "attack_type": attack_type,
            "attack_details": json.dumps(attack_details, indent=2),
            "tracking_token": self._generate_tracking_token(attack_details)
        }
        
        return context
    
    def _generate_tracking_token(self, attack_details: Dict[str, Any]) -> str:
        """Generate unique tracking token for this attack"""
        import hashlib
        import time
        
        data = f"{json.dumps(attack_details, sort_keys=True)}{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def save_script(self, script_content: str, scenario_name: str, env_path: str) -> str:
        """Save generated script to environment directory"""
        env_path_obj = Path(env_path)
        script_path = env_path_obj / f"{scenario_name}_counter.cake"
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        return str(script_path)
