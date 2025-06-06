# crews/mobile_dev_crew/mobile_agents/runner.py
from utils.general_utils import Logger
from utils.database import Database
from utils.context_handler import ProjectContext

# Imports for all 6 mobile sub-agents
from .ui_structure_designer import UIStructureDesigner
from .component_designer import ComponentDesigner
from .api_binder import APIBinder
from .state_manager import StateManager
from .form_validator import FormValidator
from .test_designer import TestDesigner

class MobileCrewRunner:
    def __init__(self, logger: Logger, db: Database = None, sub_agent_model_config: dict = None):
        self.logger = logger
        self.db = db
        self.model_config = sub_agent_model_config if sub_agent_model_config else {}
        self.logger.log(f"[MobileCrewRunner] Initializing with model config keys: {list(self.model_config.keys())}", "MobileCrewRunner")

        # Instantiate all 6 mobile sub-agents
        self.ui_structure_designer = UIStructureDesigner(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("ui_structure_designer")
        )
        self.component_designer = ComponentDesigner(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("component_designer")
        )
        self.api_binder = APIBinder(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("api_binder")
        )
        self.state_manager = StateManager(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("state_manager")
        )
        self.form_validator = FormValidator(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("form_validator")
        )
        self.test_designer = TestDesigner(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("test_designer")
        )
        self.logger.log(f"[MobileCrewRunner] All 6 mobile sub-agents initialized.", "MobileCrewRunner")

    def execute(self, project_context: ProjectContext) -> dict:
        self.logger.log(f"[MobileCrewRunner] Starting execution for mobile project: {project_context.project_name}", "MobileCrewRunner")

        artifacts = {}
        overall_status = "complete"
        accumulated_errors = []
        accumulated_warnings = []

        def _process_agent_result(agent_name: str, result: dict, artifact_key: str, critical_step: bool = False) -> bool:
            nonlocal overall_status # Allow modification of the outer scope variable

            if result is None: # Handle case where agent might unexpectedly return None
                self.logger.log(f"[{agent_name}] returned None. Treating as error.", "ERROR", "MobileCrewRunner")
                error_message = f"{agent_name} returned None result."
                accumulated_errors.append(error_message)
                overall_status = "error"
                if critical_step:
                    self.logger.log(f"[MobileCrewRunner] Critical step {agent_name} failed. Halting execution.", "ERROR", "MobileCrewRunner")
                    return False
                return True # Allow continuation if not critical

            structured_output = result.get("structured_output")
            artifacts[artifact_key] = structured_output

            warnings = result.get("warnings")
            if warnings and isinstance(warnings, list):
                accumulated_warnings.extend(warnings)
                for warning in warnings:
                    self.logger.log(f"[{agent_name}] Warning: {warning}", "WARNING", "MobileCrewRunner")
            elif warnings: # If warnings is not a list but a single string
                 accumulated_warnings.append(str(warnings))
                 self.logger.log(f"[{agent_name}] Warning: {warnings}", "WARNING", "MobileCrewRunner")

            agent_status = result.get("status", "unknown")
            if agent_status != "complete":
                error_message = result.get("error") or result.get("message", f"{agent_name} failed with unknown error.")
                if not isinstance(error_message, str): error_message = str(error_message)
                accumulated_errors.append(f"{agent_name}: {error_message}")
                self.logger.log(f"[{agent_name}] Failed. Error: {error_message}", "ERROR", "MobileCrewRunner")
                overall_status = "error"
                if critical_step:
                    self.logger.log(f"[MobileCrewRunner] Critical step {agent_name} failed. Halting execution.", "ERROR", "MobileCrewRunner")
                    return False

            output_type_msg = type(structured_output).__name__ if structured_output is not None else "None"
            self.logger.log(f"[{agent_name}] completed with status: {agent_status}. Output type: {output_type_msg}", "MobileCrewRunner")
            return True

        # --- Agent Execution Sequence ---

        # 1. UIStructureDesigner
        self.logger.log(f"[MobileCrewRunner] Running UIStructureDesigner...", "MobileCrewRunner")
        ui_structure_inputs = {
            # project_details, user_requirements, tech_stack_mobile are expected to be in project_context
            # and handled by MobileSubAgent._enhance_prompt_context
        }
        ui_structure_result = self.ui_structure_designer.run(project_context, crew_inputs=ui_structure_inputs)
        if not _process_agent_result("UIStructureDesigner", ui_structure_result, "ui_structure_output", critical_step=True):
            return {"status": "error", "errors": accumulated_errors, "warnings": accumulated_warnings, "mobile_artifacts": artifacts}

        # 2. ComponentDesigner
        self.logger.log(f"[MobileCrewRunner] Running ComponentDesigner...", "MobileCrewRunner")
        component_designer_inputs = {
            "ui_structure_json": artifacts.get("ui_structure_output")
            # tech_stack_mobile from project_context
        }
        component_designer_result = self.component_designer.run(project_context, crew_inputs=component_designer_inputs)
        if not _process_agent_result("ComponentDesigner", component_designer_result, "component_specs_output", critical_step=True):
            return {"status": "error", "errors": accumulated_errors, "warnings": accumulated_warnings, "mobile_artifacts": artifacts}

        # 3. APIBinder
        self.logger.log(f"[MobileCrewRunner] Running APIBinder...", "MobileCrewRunner")
        api_binder_inputs = {
            "component_designs": artifacts.get("component_specs_output"),
            "api_specifications": getattr(project_context, 'api_specs', None) # Assuming api_specs is on project_context
            # tech_stack_mobile from project_context
        }
        api_binder_result = self.api_binder.run(project_context, crew_inputs=api_binder_inputs)
        if not _process_agent_result("APIBinder", api_binder_result, "api_binder_output", critical_step=False): # Not always critical
            pass

        # 4. StateManager
        self.logger.log(f"[MobileCrewRunner] Running StateManager...", "MobileCrewRunner")
        state_manager_inputs = {
            "component_designs": artifacts.get("component_specs_output"),
            "ui_structure_json": artifacts.get("ui_structure_output")
            # tech_stack_mobile from project_context
        }
        state_manager_result = self.state_manager.run(project_context, crew_inputs=state_manager_inputs)
        if not _process_agent_result("StateManager", state_manager_result, "state_manager_output", critical_step=False):
            pass

        # 5. FormValidator
        self.logger.log(f"[MobileCrewRunner] Running FormValidator...", "MobileCrewRunner")
        form_validator_inputs = {
            "component_designs_with_forms": artifacts.get("component_specs_output")
            # tech_stack_mobile from project_context
        }
        form_validator_result = self.form_validator.run(project_context, crew_inputs=form_validator_inputs)
        if not _process_agent_result("FormValidator", form_validator_result, "form_validator_output", critical_step=False):
            pass

        # 6. TestDesigner
        self.logger.log(f"[MobileCrewRunner] Running TestDesigner...", "MobileCrewRunner")
        test_designer_inputs = {
            "ui_structure_json": artifacts.get("ui_structure_output"),
            "component_designs": artifacts.get("component_specs_output"),
            "api_specifications": getattr(project_context, 'api_specs', None)
            # tech_stack_mobile from project_context
        }
        test_designer_result = self.test_designer.run(project_context, crew_inputs=test_designer_inputs)
        if not _process_agent_result("TestDesigner", test_designer_result, "test_designer_output", critical_step=False):
            pass

        self.logger.log(f"[MobileCrewRunner] Completed all mobile agent executions. Overall status: {overall_status}", "MobileCrewRunner")
        return {
            "status": overall_status,
            "errors": accumulated_errors,
            "warnings": accumulated_warnings,
            "mobile_artifacts": artifacts
        }
