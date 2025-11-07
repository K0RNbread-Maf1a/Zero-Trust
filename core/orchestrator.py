"""
Orchestrator - Main coordination system for zero-trust AI defense
"""
import yaml
import json
from typing import Dict, Any
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.detector import PatternDetector, RequestMetadata
from core.risk_scorer import RiskScorer, RiskLevel
from core.query_analyzer import QueryAnalyzer
from environments.poetry_manager import PoetryEnvironmentManager
from cake.generator import CakeScriptGenerator
from cake.executor import CakeExecutor


class DefenseOrchestrator:
    """
    Main orchestrator that coordinates all defense components
    """
    
    def __init__(self, config_dir: str, base_dir: str):
        self.base_dir = Path(base_dir)
        self.config_dir = Path(config_dir)
        
        # Load configurations
        self.rules_config = self._load_config("rules.yaml")
        self.policies_config = self._load_config("policies.yaml")
        
        # Initialize components
        self.detector = PatternDetector(self.rules_config)
        self.risk_scorer = RiskScorer(self.rules_config)
        self.query_analyzer = QueryAnalyzer(self.rules_config)
        
        # Initialize Poetry manager
        self.poetry_manager = PoetryEnvironmentManager(
            self.policies_config, 
            str(self.base_dir)
        )
        
        # Initialize Cake components
        templates_dir = self.base_dir / "cake" / "templates"
        self.cake_generator = CakeScriptGenerator(
            str(templates_dir),
            self.policies_config
        )
        self.cake_executor = CakeExecutor(self.poetry_manager, self.policies_config)
        
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        config_path = self.config_dir / filename
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming request through the defense pipeline
        """
        # Create request metadata
        request = RequestMetadata(
            timestamp=request_data.get("timestamp", 0),
            source_ip=request_data.get("ip", ""),
            user_agent=request_data.get("user_agent", ""),
            endpoint=request_data.get("endpoint", ""),
            query_params=request_data.get("params", {}),
            headers=request_data.get("headers", {}),
            content=request_data.get("content", ""),
            session_id=request_data.get("session_id", "")
        )
        
        # Stage 1: Safety check
        query = request_data.get("content", "")
        metadata = {
            "ip": request.source_ip,
            "user_agent": request.user_agent,
            "params": request.query_params,
            "headers": request.headers,
            "session_id": request.session_id
        }
        
        is_safe, safety_analysis = self.query_analyzer.analyze_query(query, metadata)
        
        if is_safe:
            return {
                "action": "allow",
                "reason": "Passed safety verification",
                "details": safety_analysis
            }
        
        # Stage 2: Pattern detection
        detection_result = self.detector.analyze_request(request)
        
        if not detection_result.is_suspicious:
            return {
                "action": "allow",
                "reason": "No suspicious patterns detected",
                "risk_score": detection_result.risk_score
            }
        
        # Stage 3: Risk assessment
        risk_assessment = self.risk_scorer.assess_risk(
            detection_result.risk_score,
            detection_result.detected_patterns,
            detection_result.evidence
        )
        
        # Stage 4: Deploy countermeasures if needed
        response = {
            "action": "countermeasures",
            "risk_level": risk_assessment.risk_level.value,
            "risk_score": risk_assessment.risk_score,
            "threat_category": risk_assessment.threat_category,
            "recommended_actions": risk_assessment.recommended_actions,
            "confidence": risk_assessment.confidence
        }
        
        if self.risk_scorer.should_deploy_countermeasures(risk_assessment):
            countermeasures_result = self.deploy_countermeasures(
                risk_assessment,
                request_data
            )
            response["countermeasures"] = countermeasures_result
        
        return response
    
    def deploy_countermeasures(self, risk_assessment, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy active countermeasures based on risk assessment
        """
        # Determine scenario
        scenario_name = self.risk_scorer.get_scenario_for_threat(
            risk_assessment.threat_category
        )
        
        # Determine intensity based on risk level
        intensity_map = {
            RiskLevel.LOW: "low",
            RiskLevel.MEDIUM: "medium",
            RiskLevel.HIGH: "high",
            RiskLevel.CRITICAL: "high"
        }
        intensity = intensity_map.get(risk_assessment.risk_level, "medium")
        
        # Prepare attack details
        attack_details = {
            "ip": request_data.get("ip", "unknown"),
            "endpoint": request_data.get("endpoint", ""),
            "attack_type": risk_assessment.threat_category,
            "risk_score": risk_assessment.risk_score,
            "patterns": risk_assessment.evidence_summary.get("patterns_detected", [])
        }
        
        try:
            # Create scenario-based environment
            env_path = self.poetry_manager.create_scenario_environment(
                scenario_name,
                attack_details
            )
            
            # Generate Cake script
            script_content = self.cake_generator.generate_script(
                scenario_name,
                attack_details,
                intensity
            )
            
            # Save script
            script_path = self.cake_generator.save_script(
                script_content,
                scenario_name,
                env_path
            )
            
            # Execute Cake script
            execution_result = self.cake_executor.execute_script(
                script_path,
                env_path
            )
            
            return {
                "success": execution_result["success"],
                "scenario": scenario_name,
                "intensity": intensity,
                "environment": env_path,
                "script": script_path,
                "execution_time": execution_result.get("execution_time", 0),
                "output": execution_result.get("stdout", ""),
                "error": execution_result.get("stderr", "")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "scenario": scenario_name
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        active_envs = self.poetry_manager.list_active_environments()
        execution_log = self.cake_executor.get_execution_log()
        
        return {
            "active_environments": len(active_envs),
            "total_executions": len(execution_log),
            "recent_executions": execution_log[-10:] if execution_log else []
        }
    
    def cleanup(self):
        """Cleanup resources"""
        # Clean up old environments
        envs = self.poetry_manager.list_active_environments()
        for env in envs:
            try:
                self.poetry_manager.cleanup_environment(env["path"])
            except:
                pass
