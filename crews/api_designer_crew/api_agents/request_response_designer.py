from typing import Optional, Dict, Any, List
import json
import os

try:
    from .models import RequestResponseMap, EndpointList, SchemaComponents # Relative imports
    from utils.api_crew_utils import SubAgentWrapper, LoggerPlaceholder # CORRECTED
except ImportError:
    # Fallback to absolute paths for robustness
    from crews.api_designer_crew.api_agents.models import RequestResponseMap, EndpointList, SchemaComponents # CORRECTED Fallback
    from utils.api_crew_utils import SubAgentWrapper, LoggerPlaceholder # CORRECTED Fallback

class RequestResponseDesignerAgent:
    def __init__(self, logger: Optional[LoggerPlaceholder] = None):
        self.agent_name = "request_response_designer"
        self.logger = logger or LoggerPlaceholder()
        self.wrapper = SubAgentWrapper(
            sub_agent_name=self.agent_name,
            output_model=RequestResponseMap,
            logger=self.logger
        )
        self.logger.log(f"{self.agent_name.capitalize()} initialized.", role=self.agent_name)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Defines request bodies and response formats for API endpoints based on context.
        Context keys: 'project_name', 'project_objective',
                      'planned_endpoints_output' (Dict from EndpointPlannerAgent),
                      'available_schemas_output' (Dict from SchemaDesignerAgent).
        Returns a dictionary (JSON-serializable) of the request/response map
        or an error dictionary.
        """
        project_name = context.get("project_name", "Unknown Project")
        self.logger.log(f"Starting request/response design for project: {project_name}", role=self.agent_name)

        project_objective = context.get("project_objective", "No objective provided.")

        planned_endpoints_output = context.get("planned_endpoints_output", {})
        # Ensure endpoints_for_prompt_list is a list of dicts, not Pydantic models
        endpoints_for_prompt_list_raw = planned_endpoints_output.get("endpoints", [])
        endpoints_for_prompt_list = []
        if isinstance(endpoints_for_prompt_list_raw, list):
            for ep_item in endpoints_for_prompt_list_raw:
                if hasattr(ep_item, 'model_dump'): # If it's a Pydantic model from a previous step's mock
                    endpoints_for_prompt_list.append(ep_item.model_dump(by_alias=True))
                elif isinstance(ep_item, dict):
                    endpoints_for_prompt_list.append(ep_item)
                # else, skip or log warning if item is not a dict or Pydantic model

        available_schemas_output = context.get("available_schemas_output", {})
        schemas_dict_for_prompt = available_schemas_output.get("schemas", {})

        schemas_summary_for_prompt = "No component schemas provided."
        if schemas_dict_for_prompt and isinstance(schemas_dict_for_prompt, dict):
            schemas_summary_for_prompt = f"Available component schema names: {list(schemas_dict_for_prompt.keys())}. "
            schemas_summary_for_prompt += "Refer to these using '#/components/schemas/SchemaName'."

        context_for_prompt = {
            "project_name": project_name,
            "objective": project_objective,
            "planned_endpoints_json_list": json.dumps(endpoints_for_prompt_list, indent=2),
            "available_schemas_summary": schemas_summary_for_prompt,
        }
        self.logger.log(f"Context for {self.agent_name} prompt (first 300 chars): {str(context_for_prompt)[:300]}", role=self.agent_name, level="DEBUG")

        request_response_map_model: Optional[RequestResponseMap] = self.wrapper.execute(context_for_prompt)

        if request_response_map_model and isinstance(request_response_map_model, RequestResponseMap):
            num_paths = len(request_response_map_model.paths) if hasattr(request_response_map_model, 'paths') and request_response_map_model.paths else 0
            self.logger.log(f"Successfully designed request/response definitions for {num_paths} paths.", role=self.agent_name)
            return request_response_map_model.model_dump(by_alias=True)
        else:
            error_msg = "Request/response design failed or returned no valid output from LLM wrapper."
            self.logger.log(error_msg, role=self.agent_name, level="ERROR")
            return {"error": error_msg, "agent_name": self.agent_name, "details": "LLM wrapper returned None or invalid type."}

if __name__ == '__main__':
    logger = LoggerPlaceholder()
    logger.log("Testing RequestResponseDesignerAgent standalone...")
    designer_agent = RequestResponseDesignerAgent(logger=logger)
    sample_run_context = {
        "project_name": "ECommerce API (ReqResp Test)",
        "project_objective": "Design request and response bodies for product and order endpoints.",
        "planned_endpoints_output": {
            "endpoints": [
                {"method": "get", "path": "/products", "description": "List products", "operationId": "listProducts"},
                {"method": "post", "path": "/orders", "description": "Create an order", "operationId": "createOrder"}
            ],
            "summary": "Product and order endpoints."
        },
        "available_schemas_output": {
            "schemas": {
                "Product": {"type": "object", "properties": {"id": {"type": "string"}, "name": {"type": "string"}}},
                "Order": {"type": "object", "properties": {"orderId": {"type": "string"}, "items": {"type": "array"}}},
                "NewOrder": {"type": "object", "properties": {"items": {"type": "array"}, "userId": {"type": "string"}}}
            }
        }
    }
    if not os.environ.get("GEMINI_API_KEY"):
        logger.log("GEMINI_API_KEY not set. Skipping live LLM call for ReqRespDesignerAgent in __main__.", level="WARNING")
        from unittest.mock import MagicMock
        mock_output_data = {"paths": {"/products": { "get": { "summary": "List all products (mocked)", "responses": { "200": { "description": "Mocked list of products" }}}}}}
        RealRequestResponseMap = None
        try:
            from crews.api_designer_crew.api_agents.models import RequestResponseMap as RealRequestResponseMap # CORRECTED
        except: pass
        if RealRequestResponseMap and RealRequestResponseMap.__name__ != "MockBaseModel":
            designer_agent.wrapper.execute = MagicMock(return_value=RealRequestResponseMap(**mock_output_data))
        else:
            class TempMockMap:
                def __init__(self, data):
                    self.paths = data.get("paths", {}) # Ensure paths attribute exists
                def model_dump(self, **kwargs): return {"paths": self.paths}
            designer_agent.wrapper.execute = MagicMock(return_value=TempMockMap(mock_output_data))
        logger.log("Running RequestResponseDesignerAgent with MOCKED LLM call.", role="TestMain")
        result_dict = designer_agent.run(sample_run_context)
    else:
        logger.log("GEMINI_API_KEY found. Proceeding with LIVE LLM call for ReqRespDesignerAgent in __main__.")
        result_dict = designer_agent.run(sample_run_context)
    logger.log(f"Result from RequestResponseDesignerAgent run:\n{json.dumps(result_dict, indent=2)}")
    if "error" not in result_dict and "paths" in result_dict:
        logger.log("RequestResponseDesignerAgent __main__ test deemed successful.")
    else:
        logger.log("RequestResponseDesignerAgent __main__ test deemed failed.", level="ERROR")
