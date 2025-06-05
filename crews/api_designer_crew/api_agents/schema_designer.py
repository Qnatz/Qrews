from typing import Optional, Dict, Any, List
import os
import json # For logging and __main__ example

try:
    from .models import SchemaComponents, EndpointList # Relative imports
    from utils.api_crew_utils import SubAgentWrapper, LoggerPlaceholder # CORRECTED
except ImportError:
    # Fallback for direct script execution or testing if . Linter might complain.
    from crews.api_designer_crew.api_agents.models import SchemaComponents, EndpointList # CORRECTED Fallback
    from utils.api_crew_utils import SubAgentWrapper, LoggerPlaceholder # CORRECTED Fallback


class SchemaDesignerAgent:
    def __init__(self, logger: Optional[LoggerPlaceholder] = None):
        self.agent_name = "schema_designer"
        self.logger = logger or LoggerPlaceholder()
        self.wrapper = SubAgentWrapper(
            sub_agent_name=self.agent_name,
            output_model=SchemaComponents,
            logger=self.logger
        )
        self.logger.log(f"{self.agent_name.capitalize()} initialized.", role=self.agent_name)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Designs OpenAPI component schemas based on context.
        Context keys: 'project_name', 'project_objective',
                      'domain_models' (Optional[str]),
                      'key_data_requirements' (Optional[List[str]]),
                      'planned_endpoints_output' (Optional[Dict[str,Any]] from EndpointPlannerAgent output).
        Returns a dictionary (JSON-serializable) of the designed schemas
        or an error dictionary.
        """
        project_name = context.get("project_name", "Unknown Project")
        self.logger.log(f"Starting schema design for project: {project_name}", role=self.agent_name)

        project_objective = context.get("project_objective", "No objective provided.")
        domain_models = context.get("domain_models")
        key_data_requirements = context.get("key_data_requirements")

        planned_endpoints_output_dict = context.get("planned_endpoints_output")
        planned_endpoints_context_str = "No planned endpoints provided for context."
        if planned_endpoints_output_dict and isinstance(planned_endpoints_output_dict.get("endpoints"), list):
            try:
                ep_list_model = None
                # Check if EndpointList is the real Pydantic model or a mock, then try to instantiate
                if EndpointList.__name__ != 'MockBaseModel' and callable(getattr(EndpointList, 'model_validate', None)): # Pydantic v2
                    ep_list_model = EndpointList.model_validate(planned_endpoints_output_dict)
                elif EndpointList.__name__ != 'MockBaseModel': # Pydantic v1 or other
                     ep_list_model = EndpointList(**planned_endpoints_output_dict)


                if ep_list_model and hasattr(ep_list_model, 'endpoints') and ep_list_model.endpoints:
                    endpoint_summary_list = [
                        f"{ep.method.upper() if hasattr(ep,'method') else ep.get('method','N/A').upper()} {ep.path if hasattr(ep,'path') else ep.get('path','N/A')} ({str(ep.description if hasattr(ep,'description') else ep.get('description','N/A'))[:50]}...)"
                        for ep in ep_list_model.endpoints
                    ]
                    planned_endpoints_context_str = "Planned Endpoints for context:\n" + "\n".join(endpoint_summary_list)
                    if hasattr(ep_list_model, 'summary') and ep_list_model.summary:
                        planned_endpoints_context_str += f"\nOverall Summary: {ep_list_model.summary}"
                elif isinstance(planned_endpoints_output_dict.get("endpoints"), list): # Fallback to dict iteration
                    endpoint_summary_list = [
                        f"{ep.get('method','N/A').upper()} {ep.get('path','N/A')} ({str(ep.get('description','N/A'))[:50]}...)"
                        for ep in planned_endpoints_output_dict["endpoints"]
                    ]
                    planned_endpoints_context_str = "Planned Endpoints for context (from dict):\n" + "\n".join(endpoint_summary_list)
                    if planned_endpoints_output_dict.get("summary"):
                         planned_endpoints_context_str += f"\nOverall Summary: {planned_endpoints_output_dict.get('summary')}"
            except Exception as e:
                self.logger.log(f"Could not parse 'planned_endpoints_output' for context string: {e}", role=self.agent_name, level="WARNING")
                if isinstance(planned_endpoints_output_dict, dict):
                    planned_endpoints_context_str = f"Planned Endpoints (raw dict for context): {json.dumps(planned_endpoints_output_dict)}"
                else:
                    planned_endpoints_context_str = "Error processing planned_endpoints_output for context."

        context_for_prompt = {
            "project_name": project_name,
            "objective": project_objective,
            "domain_models": domain_models or "No specific domain models described.",
            "key_data_requirements": key_data_requirements or "No specific data requirements listed.",
            "planned_endpoints": planned_endpoints_context_str,
        }
        self.logger.log(f"Context for {self.agent_name} prompt (first 300 chars): {str(context_for_prompt)[:300]}", role=self.agent_name, level="DEBUG")

        schema_components_model: Optional[SchemaComponents] = self.wrapper.execute(context_for_prompt)

        if schema_components_model and isinstance(schema_components_model, SchemaComponents):
            self.logger.log(f"Successfully designed {len(schema_components_model.schemas) if hasattr(schema_components_model, 'schemas') and schema_components_model.schemas else 0} component schemas.", role=self.agent_name)
            return schema_components_model.model_dump(by_alias=True)
        else:
            error_msg = "Schema design failed or returned no valid output from LLM wrapper."
            self.logger.log(error_msg, role=self.agent_name, level="ERROR")
            return {"error": error_msg, "agent_name": self.agent_name, "details": "LLM wrapper returned None or invalid type."}

if __name__ == '__main__':
    logger = LoggerPlaceholder()
    logger.log("Testing SchemaDesignerAgent standalone...")
    designer_agent = SchemaDesignerAgent(logger=logger)
    sample_context_for_run = {
        "project_name": "SmartHome API (Standalone Schema Test)",
        "project_objective": "To create schemas for smart home devices.",
        "domain_models": "Device (id, name, type, status), Room (id, name)",
        "key_data_requirements": ["Device status must be an enum (on, off, standby)."],
        "planned_endpoints_output": {
            "endpoints": [
                {"method": "get", "path": "/devices", "description": "List all devices", "operation_id": "listDevices"},
                {"method": "post", "path": "/devices", "description": "Add new device", "operation_id": "addDevice"}
            ],
            "summary": "Endpoints for device management."
        }
    }
    if not os.environ.get("GEMINI_API_KEY"):
        logger.log("GEMINI_API_KEY not set. Skipping live LLM call for SchemaDesignerAgent in __main__.", level="WARNING")
        from unittest.mock import MagicMock
        mock_output_data = {"schemas": {"Device": {"type": "object", "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}}}
        RealSchemaComponents = None
        try:
            from crews.api_designer_crew.api_agents.models import SchemaComponents as RealSchemaComponents # CORRECTED
        except: pass
        if RealSchemaComponents and RealSchemaComponents.__name__ != "MockBaseModel": # Check if it's the real Pydantic model
            designer_agent.wrapper.execute = MagicMock(return_value=RealSchemaComponents(**mock_output_data))
        else: # Fallback for mock
            class TempMockSchemaComp:
                def __init__(self, data):
                    self.schemas = data.get("schemas", {}) # Ensure schemas attribute exists
                def model_dump(self, **kwargs): return {"schemas": self.schemas}
            designer_agent.wrapper.execute = MagicMock(return_value=TempMockSchemaComp(mock_output_data))
        logger.log("Running SchemaDesignerAgent with MOCKED LLM call.", role="TestMain")
        result_dict = designer_agent.run(sample_context_for_run)
    else:
        logger.log("GEMINI_API_KEY found. Proceeding with LIVE LLM call for SchemaDesignerAgent in __main__.")
        result_dict = designer_agent.run(sample_context_for_run)
    logger.log(f"Result from SchemaDesignerAgent run:\n{json.dumps(result_dict, indent=2)}")
    if "error" not in result_dict and "schemas" in result_dict:
        logger.log("SchemaDesignerAgent __main__ test deemed successful.")
    else:
        logger.log("SchemaDesignerAgent __main__ test deemed failed.", level="ERROR")
