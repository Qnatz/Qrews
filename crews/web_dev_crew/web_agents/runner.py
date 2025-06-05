import json # For logging
from utils.general_utils import Logger # CORRECTED
from utils.database import Database # CORRECTED
from utils.context_handler import ProjectContext # CORRECTED

# Import all sub-agent classes
from .page_structure_designer import PageStructureDesigner
from .component_generator import ComponentGenerator
from .api_hook_writer import APIHookWriter
from .form_handler import FormHandler
from .state_manager import StateManager
from .style_engineer import StyleEngineer
from .layout_designer import LayoutDesigner
from .error_boundary_writer import ErrorBoundaryWriter
from .test_writer import TestWriter

class FrontendCrewRunner:
    def __init__(self, logger: Logger, db: Database = None, sub_agent_model_config: dict = None):
        """
        Initializes the FrontendCrewRunner and all its sub-agents.
        sub_agent_model_config is a dictionary like:
        { "page_structure_designer": "model_name_for_psd", ... }
        """
        self.logger = logger
        self.db = db
        self.model_config = sub_agent_model_config if sub_agent_model_config else {}

        self.logger.log(f"[FrontendCrewRunner] Initializing with model config: {json.dumps(self.model_config)}", "FrontendCrewRunner")

        # Instantiate all sub-agents, passing logger, db, and specific model overrides
        self.page_structure_designer = PageStructureDesigner(logger, db, model_name_override=self.model_config.get("page_structure_designer"))
        self.component_generator = ComponentGenerator(logger, db, model_name_override=self.model_config.get("component_generator"))
        self.api_hook_writer = APIHookWriter(logger, db, model_name_override=self.model_config.get("api_hook_writer"))
        self.form_handler = FormHandler(logger, db, model_name_override=self.model_config.get("form_handler"))
        self.state_manager = StateManager(logger, db, model_name_override=self.model_config.get("state_manager"))
        self.style_engineer = StyleEngineer(logger, db, model_name_override=self.model_config.get("style_engineer"))
        self.layout_designer = LayoutDesigner(logger, db, model_name_override=self.model_config.get("layout_designer"))
        self.error_boundary_writer = ErrorBoundaryWriter(logger, db, model_name_override=self.model_config.get("error_boundary_writer"))
        self.test_writer = TestWriter(logger, db, model_name_override=self.model_config.get("test_writer"))

        self.logger.log("[FrontendCrewRunner] All sub-agents initialized.", "FrontendCrewRunner")

    def execute(self, project_context: ProjectContext) -> dict:
        """
        Executes the frontend construction crew sequentially, passing outputs explicitly.
        Returns a dictionary with status, errors, warnings, and aggregated artifacts.
        """
        self.logger.log(f"[FrontendCrewRunner] Starting execution for project: {project_context.project_name}", "FrontendCrewRunner")

        artifacts = {}
        overall_status = "complete"
        accumulated_errors = []
        accumulated_warnings = []

        # Helper to process sub-agent result
        def _process_agent_result(agent_name: str, result: dict, artifact_key: str):
            nonlocal overall_status # Allow modification of outer scope variable
            artifacts[artifact_key] = result.get("structured_output")

            if result.get("warnings"):
                accumulated_warnings.extend(result["warnings"])
                for warning in result["warnings"]:
                    self.logger.log(f"Warning from {agent_name}: {warning}", "FrontendCrewRunner", level="WARNING")

            if result.get("status") != "complete":
                if result.get("errors"):
                    accumulated_errors.extend(result["errors"])
                    for error in result["errors"]:
                        self.logger.log(f"Error from {agent_name}: {error}", "FrontendCrewRunner", level="ERROR")
                else: # Should ideally always have an error message if status is not complete
                    generic_error = f"{agent_name} failed with status '{result.get('status')}' but provided no specific errors."
                    accumulated_errors.append(generic_error)
                    self.logger.log(generic_error, "FrontendCrewRunner", level="ERROR")

                # If any agent fails, the overall status is marked as error.
                # Specific handling for critical failures can be added here.
                if overall_status != "error": # Avoid demoting from "error" to "partial_error" if already an error
                    overall_status = "error"

            self.logger.log(f"[FrontendCrewRunner] {agent_name} finished. Status: {result.get('status')}. Output keys: {artifacts[artifact_key].keys() if isinstance(artifacts[artifact_key], dict) else type(artifacts[artifact_key]).__name__ if artifacts[artifact_key] is not None else 'None'}", "FrontendCrewRunner")


        # --- Sub-Agent Execution Flow ---
        # Each agent's 'run' method returns a dict: {"status": ..., "structured_output": ..., "errors": ..., "warnings": ...}

        # 1. Page Structure Designer
        psd_result = self.page_structure_designer.run(project_context)
        _process_agent_result("PageStructureDesigner", psd_result, "page_structure")
        if psd_result.get("status") != "complete": # Critical first step
            self.logger.log("Halting crew execution: PageStructureDesigner failed.", "FrontendCrewRunner", level="ERROR")
            return {"status": "error", "errors": accumulated_errors, "warnings": accumulated_warnings, "frontend_artifacts": artifacts}
        page_structure_data = psd_result.get("structured_output")

        # 2. Component Generator
        cg_result = self.component_generator.run(project_context, page_structure_data=page_structure_data)
        _process_agent_result("ComponentGenerator", cg_result, "components")
        components_data = cg_result.get("structured_output")
        # Allow continuing even if some components fail, to gather more results/errors

        # 3. Form Handler
        fh_result = self.form_handler.run(project_context, components_output=components_data)
        _process_agent_result("FormHandler", fh_result, "forms")
        forms_data = fh_result.get("structured_output")

        # 4. State Manager
        sm_result = self.state_manager.run(project_context, page_structure_data=page_structure_data, components_output=components_data)
        _process_agent_result("StateManager", sm_result, "state_management")
        state_data = sm_result.get("structured_output")

        # 5. Style Engineer
        se_result = self.style_engineer.run(project_context, components_output=components_data, forms_output=forms_data)
        _process_agent_result("StyleEngineer", se_result, "styles")
        styles_data = se_result.get("structured_output")

        # 6. Layout Designer
        ld_result = self.layout_designer.run(project_context, page_structure_data=page_structure_data, styles_output=styles_data)
        _process_agent_result("LayoutDesigner", ld_result, "layout")
        layout_data = ld_result.get("structured_output")

        # 7. API Hook Writer
        ahw_result = self.api_hook_writer.run(project_context, page_structure_data=page_structure_data)
        _process_agent_result("APIHookWriter", ahw_result, "api_hooks")
        api_hooks_data = ahw_result.get("structured_output")

        # 8. Error Boundary Writer
        ebw_result = self.error_boundary_writer.run(project_context, page_structure_data=page_structure_data)
        _process_agent_result("ErrorBoundaryWriter", ebw_result, "error_boundaries")
        error_boundaries_data = ebw_result.get("structured_output")

        # 9. Test Writer (depends on all previous artifacts)
        # Ensure all data passed is what TestWriter expects (or None if a step failed to produce output)
        tw_result = self.test_writer.run(
            project_context,
            page_structure_data=page_structure_data if page_structure_data else {},
            components_output=components_data if components_data else {},
            forms_output=forms_data if forms_data else {},
            state_output=state_data if state_data else {},
            styles_output=styles_data if styles_data else {},
            layout_output=layout_data if layout_data else {},
            api_hooks_output=api_hooks_data if api_hooks_data else {},
            error_boundaries_output=error_boundaries_data if error_boundaries_data else {}
        )
        _process_agent_result("TestWriter", tw_result, "tests")

        self.logger.log(f"[FrontendCrewRunner] Execution finished. Overall status: {overall_status}", "FrontendCrewRunner")
        return {
            "status": overall_status,
            "errors": accumulated_errors,
            "warnings": accumulated_warnings,
            "frontend_artifacts": artifacts
        }
