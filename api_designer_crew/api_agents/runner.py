from typing import Optional, Dict, Any
import json # For logging and preparing context strings
import os # For __main__ test

# Attempt to import real classes; define mocks if import fails
RUNNER_IMPORTS_OK = False
try:
    from .models import EndpointList, SchemaComponents, RequestResponseMap, AuthDefinition, ErrorSchemaDefinition
    from .endpoint_planner import EndpointPlannerAgent
    from .schema_designer import SchemaDesignerAgent
    from .request_response_designer import RequestResponseDesignerAgent
    from .auth_designer import AuthDesignerAgent
    from .error_designer import ErrorDesignerAgent
    from .utils import LoggerPlaceholder
    RUNNER_IMPORTS_OK = True
except ImportError as e:
    # This block is for when the script is run directly and relative imports fail.
    # The actual application should have these paths resolved correctly.
    print(f"APIDesignCrewRunner: Info: One or more imports failed: {e}. This is okay if running __main__ for basic tests with mocks.")
    class LoggerPlaceholder:
        def log(self, msg, role="Runner", level="INFO"): print(f"[{level}][{role}] {msg}")
    class MockAgentPlaceholder:
        def __init__(self, logger=None):
            self.logger = logger or LoggerPlaceholder()
            self.agent_name = self.__class__.__name__.replace('Agent','').lower()
        def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
            self.logger.log(f"Mock {self.agent_name} run called", role=self.agent_name)
            # Provide a more structured mock output matching what real agents might return
            if self.agent_name == "endpoint_planner": return {"endpoints": [], "summary":"Mocked EPs"}
            if self.agent_name == "schema_designer": return {"schemas": {}}
            if self.agent_name == "request_response_designer": return {"paths": {}}
            if self.agent_name == "auth_designer": return {"securitySchemes": {}}
            if self.agent_name == "error_designer": return {"errorSchemas": {}}
            return {"mock_output": f"from {self.agent_name}", "error": None}

    EndpointPlannerAgent = type("EndpointPlannerAgent", (MockAgentPlaceholder,), {})
    SchemaDesignerAgent = type("SchemaDesignerAgent", (MockAgentPlaceholder,), {})
    RequestResponseDesignerAgent = type("RequestResponseDesignerAgent", (MockAgentPlaceholder,), {})
    AuthDesignerAgent = type("AuthDesignerAgent", (MockAgentPlaceholder,), {})
    ErrorDesignerAgent = type("ErrorDesignerAgent", (MockAgentPlaceholder,), {})
    # These Pydantic models are just for type hints in this file if imports succeed
    EndpointList, SchemaComponents, RequestResponseMap, AuthDefinition, ErrorSchemaDefinition = (dict, dict, dict, dict, dict)


class APIDesignCrewRunner:
    def __init__(self, master_context: Dict[str, Any], logger: Optional[LoggerPlaceholder] = None):
        self.master_context = master_context
        self.logger = logger or LoggerPlaceholder()
        self.logger.log("APIDesignCrewRunner initialized.", role="CrewRunner")

        if not RUNNER_IMPORTS_OK: # This flag is set at import time
            self.logger.log("APIDesignCrewRunner is using MOCKED agent classes due to initial import errors.", role="CrewRunner", level="WARNING")

        self.endpoint_planner = EndpointPlannerAgent(logger=self.logger)
        self.schema_designer = SchemaDesignerAgent(logger=self.logger)
        self.request_response_designer = RequestResponseDesignerAgent(logger=self.logger)
        self.auth_designer = AuthDesignerAgent(logger=self.logger)
        self.error_designer = ErrorDesignerAgent(logger=self.logger)

        self.crew_outputs: Dict[str, Any] = {}

    def _extract_agent_context(self, agent_name_str: str) -> Dict[str, Any]:
        agent_context = {
            "project_name": self.master_context.get("project_name", "Unknown Project"),
            "project_objective": self.master_context.get("project_objective", "No objective specified."),
            "analysis": self.master_context.get("analysis", {}), # Pass full dicts
            "plan": self.master_context.get("plan", {}),
            "architecture": self.master_context.get("architecture", {}),
        }
        # Specific context additions based on agent needs from master context or previous outputs
        if agent_name_str == "endpoint_planner":
            plan_data = self.master_context.get("plan", {})
            agent_context["feature_objectives"] = plan_data.get("feature_objectives_text")
            agent_context["planner_milestones"] = plan_data.get("milestones")
        elif agent_name_str == "schema_designer":
            analysis_data = self.master_context.get("analysis", {})
            agent_context["domain_models"] = analysis_data.get("domain_models_text")
            agent_context["key_data_requirements"] = analysis_data.get("key_requirements")
            agent_context["planned_endpoints_output"] = self.crew_outputs.get("endpoint_planner_output", {})
        elif agent_name_str == "request_response_designer":
            agent_context["planned_endpoints_output"] = self.crew_outputs.get("endpoint_planner_output", {})
            agent_context["available_schemas_output"] = self.crew_outputs.get("schema_designer_output", {})
        elif agent_name_str == "auth_designer":
            arch_data = self.master_context.get("architecture", {})
            agent_context["security_requirements"] = arch_data.get("security_requirements_text")
            agent_context["planned_endpoints_output"] = self.crew_outputs.get("endpoint_planner_output", {}) # For summary
        elif agent_name_str == "error_designer":
            analysis_data = self.master_context.get("analysis", {})
            arch_data = self.master_context.get("architecture", {})
            agent_context["common_error_scenarios"] = analysis_data.get("common_error_scenarios")
            agent_context["error_style_guide"] = arch_data.get("error_style_guide_text")
        return agent_context

    def _run_single_agent(self, agent_instance, agent_name_str: str, output_key: str) -> bool:
        self.logger.log(f"Running {agent_name_str}...", role="CrewRunner")
        context_for_agent = self._extract_agent_context(agent_name_str)

        output_dict = agent_instance.run(context_for_agent)
        self.crew_outputs[output_key] = output_dict

        if isinstance(output_dict, dict) and output_dict.get("error"):
            self.logger.log(f"{agent_name_str} failed: {output_dict.get('error')} - Details: {output_dict.get('details')}", level="ERROR", role="CrewRunner")
            return False
        self.logger.log(f"{agent_name_str} completed successfully.", role="CrewRunner")
        return True

    def run(self) -> Dict[str, Any]:
        self.logger.log("APIDesignCrewRunner: Starting generation pipeline...", role="CrewRunner")
        self.crew_outputs = {}

        pipeline = [
            (self.endpoint_planner, "endpoint_planner", "endpoint_planner_output"),
            (self.schema_designer, "schema_designer", "schema_designer_output"),
            (self.request_response_designer, "request_response_designer", "request_response_designer_output"),
            (self.auth_designer, "auth_designer", "auth_designer_output"),
            (self.error_designer, "error_designer", "error_designer_output"),
        ]

        for agent_instance, agent_name_str, output_key in pipeline:
            if not self._run_single_agent(agent_instance, agent_name_str, output_key):
                self.logger.log(f"Pipeline halted due to error in {agent_name_str}.", level="ERROR", role="CrewRunner")
                return self.crew_outputs # Return partial outputs with error indication

        self.logger.log("APIDesignCrewRunner: All generation agents completed successfully.", role="CrewRunner")
        return self.crew_outputs

if __name__ == '__main__':
    logger = LoggerPlaceholder() # Defined in ImportError block or from utils
    logger.log("--- Testing APIDesignCrewRunner Standalone ---", role="TestMain")
    sample_master_context = {
        "project_name": "E-commerce Platform Runner Test",
        "project_objective": "To test the APIDesignCrewRunner.",
        "api_version": "1.1.0",
        "analysis": {"key_requirements": ["Auth"], "domain_models_text": "User", "common_error_scenarios": ["404"]},
        "plan": {"feature_objectives_text": ["Login"], "milestones": [{"name": "M1"}]},
        "architecture": {"security_requirements_text": ["OAuth2"], "error_style_guide_text": "JSON errors"}
    }

    # Check if GEMINI_API_KEY is set to decide if we expect real or mock agents
    use_real_agents = RUNNER_IMPORTS_OK and os.environ.get("GEMINI_API_KEY")

    if use_real_agents:
        logger.log("GEMINI_API_KEY is set and imports were okay. Runner will use real agents.", role="TestMain")
    else:
        logger.log("RUNNER_IMPORTS_OK is False or GEMINI_API_KEY not set. Runner will use MOCKED agents for test.", level="WARNING", role="TestMain")
        # If imports failed, agent classes are already MockAgentPlaceholder.
        # If imports succeeded but no API key, we still want to mock the 'run' methods for __main__ test.
        if RUNNER_IMPORTS_OK: # Imports were fine, but no API key, so mock the real agent's run method
            from unittest.mock import MagicMock
            EndpointPlannerAgent.run = MagicMock(return_value={"endpoints": [{"path":"/mock_ep"}], "summary":"mocked_eps"})
            SchemaDesignerAgent.run = MagicMock(return_value={"schemas": {"MockSchema": {"type":"object"}}})
            RequestResponseDesignerAgent.run = MagicMock(return_value={"paths": {"/mock_ep": {"get": {"summary":"mock"}}}})
            AuthDesignerAgent.run = MagicMock(return_value={"securitySchemes": {"mockAuth": {"type":"apiKey"}}})
            ErrorDesignerAgent.run = MagicMock(return_value={"errorSchemas": {"MockError": {"type":"object"}}})

    runner = APIDesignCrewRunner(master_context=sample_master_context, logger=logger)
    final_crew_outputs = runner.run()

    logger.log(f"--- APIDesignCrewRunner Test Output ({'REAL' if use_real_agents else 'MOCKED'} Agents) ---", role="TestMain")
    logger.log(json.dumps(final_crew_outputs, indent=2), role="TestMain")
    expected_keys = ["endpoint_planner_output", "schema_designer_output", "request_response_designer_output", "auth_designer_output", "error_designer_output"]
    success = all(key in final_crew_outputs and not final_crew_outputs[key].get("error") for key in expected_keys)

    if success:
        logger.log("APIDesignCrewRunner __main__ test deemed successful.", role="TestMain")
    else:
        logger.log("APIDesignCrewRunner __main__ test deemed failed (missing keys or errors in outputs).", level="ERROR", role="TestMain")
