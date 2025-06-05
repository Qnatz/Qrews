from typing import Optional, Dict, Any, List
import os
import json # For potential debug logging of context

try:
    from .models import EndpointList # Relative import for package structure
    from utils.api_crew_utils import SubAgentWrapper, LoggerPlaceholder # CORRECTED
except ImportError:
    # Fallback for direct script execution or testing if . Linter might complain.
    from crews.api_designer_crew.api_agents.models import EndpointList # CORRECTED Fallback
    from utils.api_crew_utils import SubAgentWrapper, LoggerPlaceholder # CORRECTED Fallback


class EndpointPlannerAgent:
    def __init__(self, logger: Optional[LoggerPlaceholder] = None):
        self.agent_name = "endpoint_planner"
        self.logger = logger or LoggerPlaceholder()
        # The SubAgentWrapper is initialized to expect an EndpointList Pydantic model
        self.wrapper = SubAgentWrapper(
            sub_agent_name=self.agent_name,
            output_model=EndpointList,
            logger=self.logger
        )
        self.logger.log(f"{self.agent_name.capitalize()} initialized.", role=self.agent_name)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identifies and plans RESTful endpoints based on context.
        The context dictionary is expected to contain keys like:
        'project_name', 'project_objective',
        'feature_objectives' (Optional[List[str]]),
        'planner_milestones' (Optional[List[Dict[str, Any]]]).
        Returns a dictionary (JSON-serializable) of the planned endpoints
        or an error dictionary.
        """
        project_name = context.get("project_name", "Unknown Project")
        self.logger.log(f"Starting endpoint planning for project: {project_name}", role=self.agent_name)

        # Extract necessary information from the context
        project_objective = context.get("project_objective", "No objective provided.")
        feature_objectives = context.get("feature_objectives")
        planner_milestones = context.get("planner_milestones")

        context_for_prompt = {
            "project_name": project_name,
            "objective": project_objective,
            "feature_objectives": feature_objectives or "No specific feature objectives provided.",
            "planner_milestones": planner_milestones or "No planner milestones provided.",
        }

        self.logger.log(f"Context for {self.agent_name} prompt (first 300 chars): {str(context_for_prompt)[:300]}", role=self.agent_name, level="DEBUG")

        endpoint_list_model: Optional[EndpointList] = self.wrapper.execute(context_for_prompt)

        if endpoint_list_model and isinstance(endpoint_list_model, EndpointList):
            self.logger.log(f"Successfully planned {len(endpoint_list_model.endpoints)} endpoints.", role=self.agent_name)
            if endpoint_list_model.summary:
                 self.logger.log(f"Endpoint planning summary: {endpoint_list_model.summary}", role=self.agent_name)
            return endpoint_list_model.model_dump(by_alias=True)
        else:
            error_msg = "Endpoint planning failed or returned no valid output from LLM wrapper."
            self.logger.log(error_msg, role=self.agent_name, level="ERROR")
            return {"error": error_msg, "agent_name": self.agent_name, "details": "LLM wrapper returned None or invalid type."}

if __name__ == '__main__':
    logger = LoggerPlaceholder()
    logger.log("Testing EndpointPlannerAgent standalone...")
    planner_agent = EndpointPlannerAgent(logger=logger)
    sample_run_context = {
        "project_name": "SmartHome API (Standalone Test)",
        "project_objective": "To create a comprehensive API for managing smart home devices.",
        "feature_objectives": [
            "User authentication and authorization.",
            "Device registration and management.",
            "Control specific device features.",
            "Scene creation and management."
        ],
        "planner_milestones": [
            {"name": "M1: Core Auth & Device Registration"},
            {"name": "M2: Basic Device Control"}
        ]
    }

    if not os.environ.get("GEMINI_API_KEY"):
        logger.log("GEMINI_API_KEY not set. Skipping live LLM call test for EndpointPlannerAgent in __main__.", level="WARNING")
        from unittest.mock import MagicMock # Keep this import local to __main__ if only used here
        mock_output_data = {
            "endpoints": [{'method': 'get', 'path': '/devices', 'description': 'List all devices', 'operationId': 'listDevices'}],
            "summary": "Mocked summary for offline test"
        }
        # Try to use the real EndpointList for the mock's return value if available
        RealEndpointList = None
        try:
            from crews.api_designer_crew.api_agents.models import EndpointList as RealEndpointList # CORRECTED
        except ImportError:
            logger.log("Real EndpointList model not found for __main__ test, using dict for mock wrapper.", level="DEBUG")

        if RealEndpointList and RealEndpointList.__name__ != 'MockBaseModel': # Check it's not already a mock
            planner_agent.wrapper.execute = MagicMock(return_value=RealEndpointList(**mock_output_data))
        else:
            class TempMockEpList: # Fallback mock that has model_dump
                def __init__(self, data):
                    self.endpoints = data.get("endpoints", [])
                    self.summary = data.get("summary", None)
                def model_dump(self, **kwargs):
                    return {"endpoints": self.endpoints, "summary": self.summary}
            planner_agent.wrapper.execute = MagicMock(return_value=TempMockEpList(mock_output_data))


        logger.log("Running EndpointPlannerAgent with MOCKED LLM call.", role="TestMain")
        result_dict = planner_agent.run(sample_run_context)
    else:
        logger.log("GEMINI_API_KEY found. Proceeding with LIVE LLM call test for EndpointPlannerAgent in __main__.")
        result_dict = planner_agent.run(sample_run_context)

    logger.log(f"Result from EndpointPlannerAgent run:\n{json.dumps(result_dict, indent=2)}")

    if "error" not in result_dict and "endpoints" in result_dict:
        logger.log("EndpointPlannerAgent __main__ test deemed successful (produced endpoints).")
    else:
        logger.log("EndpointPlannerAgent __main__ test deemed failed (error or no endpoints).", level="ERROR")
