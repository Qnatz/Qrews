from typing import Optional, Dict, Any, List
import json
import os

try:
    from .models import AuthDefinition, EndpointList # Relative imports
    from .utils import SubAgentWrapper, LoggerPlaceholder
except ImportError:
    from models import AuthDefinition, EndpointList # Fallback
    from utils import SubAgentWrapper, LoggerPlaceholder

class AuthDesignerAgent:
    def __init__(self, logger: Optional[LoggerPlaceholder] = None):
        self.agent_name = "auth_designer"
        self.logger = logger or LoggerPlaceholder()
        self.wrapper = SubAgentWrapper(
            sub_agent_name=self.agent_name,
            output_model=AuthDefinition,
            logger=self.logger
        )
        self.logger.log(f"{self.agent_name.capitalize()} initialized.", role=self.agent_name)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Designs OpenAPI security schemes and global security requirements based on context.
        Context keys: 'project_name', 'project_objective',
                      'security_requirements' (Optional[List[str]]),
                      'planned_endpoints_output' (Optional[Dict[str,Any]] from EndpointPlannerAgent).
        Returns a dictionary (JSON-serializable) of the auth definitions
        or an error dictionary.
        """
        project_name = context.get("project_name", "Unknown Project")
        self.logger.log(f"Starting auth design for project: {project_name}", role=self.agent_name)

        project_objective = context.get("project_objective", "No objective provided.")
        security_requirements = context.get("security_requirements")

        planned_endpoints_output = context.get("planned_endpoints_output", {})
        planned_endpoints_summary = "No endpoint summary provided for context." # Default
        if isinstance(planned_endpoints_output, dict):
            planned_endpoints_summary = planned_endpoints_output.get("summary", planned_endpoints_summary)
            # If no summary, try to create a basic one from endpoint count
            if planned_endpoints_summary == "No endpoint summary provided for context." and isinstance(planned_endpoints_output.get("endpoints"), list):
                num_eps = len(planned_endpoints_output["endpoints"])
                planned_endpoints_summary = f"{num_eps} endpoint(s) planned. (Details not summarized for auth context)."

        context_for_prompt = {
            "project_name": project_name,
            "objective": project_objective,
            "security_requirements": security_requirements or "No specific security requirements. Consider standard token auth.",
            "planned_endpoints_summary": planned_endpoints_summary,
        }
        self.logger.log(f"Context for {self.agent_name} prompt (first 300 chars): {str(context_for_prompt)[:300]}", role=self.agent_name, level="DEBUG")

        auth_definition_model: Optional[AuthDefinition] = self.wrapper.execute(context_for_prompt)

        if auth_definition_model and isinstance(auth_definition_model, AuthDefinition):
            num_schemes = len(auth_definition_model.security_schemes) if hasattr(auth_definition_model, 'security_schemes') and auth_definition_model.security_schemes else 0
            self.logger.log(f"Successfully designed {num_schemes} security scheme(s).", role=self.agent_name)
            return auth_definition_model.model_dump(by_alias=True)
        else:
            error_msg = "Auth design failed or returned no valid output from LLM wrapper."
            self.logger.log(error_msg, role=self.agent_name, level="ERROR")
            return {"error": error_msg, "agent_name": self.agent_name, "details": "LLM wrapper returned None or invalid type."}

if __name__ == '__main__':
    logger = LoggerPlaceholder()
    logger.log("Testing AuthDesignerAgent standalone...")
    designer_agent = AuthDesignerAgent(logger=logger)
    sample_run_context = {
        "project_name": "Secure IoT Platform (Auth Test)",
        "project_objective": "API for secure IoT communication.",
        "security_requirements": [
            "All endpoints protected.",
            "Support client credentials flow.",
            "JWT tokens."
        ],
        "planned_endpoints_output": {
            "endpoints": [
                {"method": "get", "path": "/devices", "description": "List devices", "operationId": "listDevices"},
                {"method": "post", "path": "/devices", "description": "Add device", "operationId": "addDevice"}
            ],
            "summary": "Device management and telemetry endpoints."
        }
    }
    if not os.environ.get("GEMINI_API_KEY"):
        logger.log("GEMINI_API_KEY not set. Skipping live LLM call for AuthDesignerAgent in __main__.", level="WARNING")
        from unittest.mock import MagicMock
        mock_output_data = {
            "securitySchemes": {"ClientCredOAuth": {"type": "oauth2", "flows": {"clientCredentials": {"tokenUrl": "https://example.com/token", "scopes": {"read": "read data"}}}}},
            "security": [{"ClientCredOAuth": ["read"]}]
        }
        RealAuthDefinition = None
        try: from models import AuthDefinition as RealAuthDefinition
        except: pass
        if RealAuthDefinition and RealAuthDefinition.__name__ != "MockBaseModel":
            designer_agent.wrapper.execute = MagicMock(return_value=RealAuthDefinition(**mock_output_data))
        else:
            class TempMockAuthDef:
                def __init__(self, data):
                    # Pydantic aliases: security_schemes maps to securitySchemes in dict
                    self.security_schemes = data.get("securitySchemes", {})
                    self.global_security = data.get("security", []) # global_security maps to security
                def model_dump(self, **kwargs):
                    return {"securitySchemes": self.security_schemes, "security": self.global_security} if kwargs.get('by_alias') else {"security_schemes": self.security_schemes, "global_security": self.global_security}

            designer_agent.wrapper.execute = MagicMock(return_value=TempMockAuthDef(mock_output_data))
        logger.log("Running AuthDesignerAgent with MOCKED LLM call.", role="TestMain")
        result_dict = designer_agent.run(sample_run_context)
    else:
        logger.log("GEMINI_API_KEY found. Proceeding with LIVE LLM call for AuthDesignerAgent in __main__.")
        result_dict = designer_agent.run(sample_run_context)
    logger.log(f"Result from AuthDesignerAgent run:\n{json.dumps(result_dict, indent=2)}")
    if "error" not in result_dict and "securitySchemes" in result_dict:
        logger.log("AuthDesignerAgent __main__ test deemed successful.")
    else:
        logger.log("AuthDesignerAgent __main__ test deemed failed.", level="ERROR")
