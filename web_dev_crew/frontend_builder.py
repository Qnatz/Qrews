import json
from agents import Agent # Base Agent class
from .frontend_crew.runner import FrontendCrewRunner # Import the new runner
from utils import Logger
from database import Database
from context_handler import ProjectContext

# Path to the model mapping configuration
MODEL_MAPPING_JSON_PATH = "config/frontend_model_mapping.json"

class FrontendBuilder(Agent):
    def __init__(self, logger: Logger, db: Database = None, sub_agent_model_config_override: dict = None):
        """
        Initializes the FrontendBuilder.
        'sub_agent_model_config_override' can be used to directly pass model configs,
        otherwise they are loaded from MODEL_MAPPING_JSON_PATH.
        """
        super().__init__(
            name='frontend_builder',
            role='Frontend Developer - Orchestrates the frontend_crew to build the application frontend.',
            logger=logger,
            db=db
        )

        loaded_model_config = {}
        if sub_agent_model_config_override is not None:
            loaded_model_config = sub_agent_model_config_override
            self.logger.log(f"[{self.name}] Using provided model config override for sub-agents.", self.role)
        else:
            try:
                with open(MODEL_MAPPING_JSON_PATH, "r") as f:
                    raw_config_from_file = json.load(f)
                # Process to extract just {agent_key: model_name}
                for agent_key, config_details in raw_config_from_file.items():
                    if isinstance(config_details, dict) and "model_name" in config_details:
                        loaded_model_config[agent_key] = config_details["model_name"]
                    else:
                        self.logger.log(f"Warning: Model config for '{{agent_key}}' in '{MODEL_MAPPING_JSON_PATH}' is missing 'model_name' or has unexpected structure. It will use its default model.", self.role, level="WARNING")
                self.logger.log(f"[{self.name}] Successfully loaded and processed model mapping from {MODEL_MAPPING_JSON_PATH}", self.role)
            except FileNotFoundError:
                self.logger.log(f"[{self.name}] Model mapping file {MODEL_MAPPING_JSON_PATH} not found. Sub-agents will use their default models.", self.role, level="WARNING")
            except json.JSONDecodeError as e:
                self.logger.log(f"[{self.name}] Error decoding JSON from {MODEL_MAPPING_JSON_PATH}: {{e}}. Sub-agents will use their default models.", self.role, level="ERROR")

        # Instantiate the FrontendCrewRunner, passing logger, db, and the effective model config
        self.crew_runner = FrontendCrewRunner(
            logger=self.logger, # Pass down the logger instance
            db=self.db,         # Pass down the db instance
            sub_agent_model_config=loaded_model_config
        )
        self.logger.log(f"[{self.name}] FrontendCrewRunner initialized.", self.role)

    def perform_task(self, project_context: ProjectContext) -> dict:
        """
        Orchestrates the frontend construction by delegating to FrontendCrewRunner.
        Adapts the runner's output to the standard Agent output format.
        """
        self.logger.log(f"[{self.name}] Delegating frontend construction to FrontendCrewRunner.", self.role)

        crew_result = self.crew_runner.execute(project_context)

        # crew_result is expected to be:
        # { "status": overall_status, "errors": [], "warnings": [], "frontend_artifacts": {} }

        final_status = crew_result.get("status", "error")
        final_errors = crew_result.get("errors", ["FrontendCrewRunner did not return errors." if final_status == "error" else "Unknown error in runner."])
        final_warnings = crew_result.get("warnings", [])
        frontend_artifacts = crew_result.get("frontend_artifacts", {})

        # Assemble a "raw_response" for the FrontendBuilder from the artifacts for logging/context.
        # This is a simplified representation; in reality, files would be written to disk.
        raw_response_parts = [f"// --- FrontendBuilder Result: Status {final_status} ---"]
        for key, artifact_data in frontend_artifacts.items():
            raw_response_parts.append(f"// Artifact: {key}")
            if isinstance(artifact_data, str):
                raw_response_parts.append(artifact_data)
            elif isinstance(artifact_data, (dict, list)):
                try:
                    raw_response_parts.append(json.dumps(artifact_data, indent=2))
                except TypeError:
                    raw_response_parts.append(f"/* Could not serialize artifact {key} to JSON */")
            elif artifact_data is None:
                 raw_response_parts.append(f"// No output for {key}")
            else:
                raw_response_parts.append(f"// Artifact {key} is of type {type(artifact_data).__name__}")

        final_raw_response = "\n\n".join(raw_response_parts)

        # Update project_context.current_code_snippet with the main assembled output if applicable
        # For now, we'll use the full raw_response. A more specific assembled output might be chosen.
        project_context.current_code_snippet = final_raw_response
        # Or, more selectively:
        # project_context.current_code_snippet = frontend_artifacts.get("assembled_app_code", final_raw_response)

        self.logger.log(f"[{self.name}] FrontendBuilder task finished. Overall status: {final_status}", self.role)

        return {
            "status": final_status,
            "errors": final_errors,
            "warnings": final_warnings,
            "raw_response": final_raw_response, # This is the combined output
            "structured_output": frontend_artifacts, # Keep the detailed artifacts
            "agent_name": self.name,
            "agent_role": self.role,
            "model_used": self.current_model # Model of FrontendBuilder itself (N/A if it makes no LLM calls)
        }

    def _parse_response(self, response_text: str, project_context: ProjectContext) -> dict:
        # This method is part of the Agent base class.
        # For FrontendBuilder, which now delegates and assembles, this specific parsing
        # of a single LLM response is less relevant for its main perform_task output.
        # The result is constructed in perform_task from crew_runner's output.
        self.logger.log(f"[{self.name}] _parse_response called. For FrontendBuilder, output is assembled by perform_task.", self.role, level="DEBUG")
        return {
            "status": "complete", # Default, actual status comes from perform_task
            "errors": [],
            "warnings": [],
            "raw_response": response_text,
            "structured_output": None, # Or could be response_text if it's directly usable.
                                     # For FrontendBuilder, structured_output is frontend_artifacts.
            "agent_name": self.name,
            "agent_role": self.role,
            "model_used": self.current_model
        }
