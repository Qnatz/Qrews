# crews/backend_dev_crew/lead.py
from agents.base_agent import Agent
from utils.general_utils import Logger
from utils.database import Database
from utils.context_handler import ProjectContext # Ensure this is imported
from .backend_agents.runner import BackendCrewRunner

class BackendLeadAgent(Agent):
    def __init__(self, logger: Logger, db: Database = None, sub_agent_model_config: dict = None): # Added sub_agent_model_config
        super().__init__(
            name="backend_lead_agent",
            role="Backend Lead Agent - Orchestrates the backend development crew.",
            logger=logger,
            db=db
        )
        # Pass sub_agent_model_config to the runner
        self.runner = BackendCrewRunner(logger=self.logger, db=self.db, sub_agent_model_config=sub_agent_model_config)
        self.logger.log(f"[{self.name}] BackendCrewRunner initialized.", self.role)

    def run_crew(self, project_context: ProjectContext) -> dict:
        self.logger.log(f"[{self.name}] Starting backend crew run for project: {project_context.project_name}", self.role)

        # Potentially load/prepare parts of project_context specific for this crew run
        # For example, if backend_agents_config.json needs to be loaded into sub_agent_model_config
        # and wasn't passed in __init__. For now, assume sub_agent_model_config is handled at instantiation.

        results = self.runner.execute(project_context)

        self.logger.log(f"[{self.name}] Backend crew run finished. Overall status: {results.get('status')}", self.role)
        if results.get('errors'):
            # Ensure errors are logged appropriately, check if it's a list
            errors_to_log = results['errors']
            if isinstance(errors_to_log, list) and not errors_to_log: # Empty list
                pass # Do not log if list is empty
            elif isinstance(errors_to_log, list):
                self.logger.log(f"[{self.name}] Errors encountered: {'; '.join(map(str, errors_to_log))}", self.role, level="ERROR")
            else: # Single error string or other format
                self.logger.log(f"[{self.name}] Errors encountered: {str(errors_to_log)}", self.role, level="ERROR")

        if results.get('warnings'):
            # Ensure warnings are logged appropriately, check if it's a list
            warnings_to_log = results['warnings']
            if isinstance(warnings_to_log, list) and not warnings_to_log: # Empty list
                pass # Do not log if list is empty
            elif isinstance(warnings_to_log, list):
                self.logger.log(f"[{self.name}] Warnings generated: {'; '.join(map(str, warnings_to_log))}", self.role, level="WARNING")
            else: # Single warning string or other format
                self.logger.log(f"[{self.name}] Warnings generated: {str(warnings_to_log)}", self.role, level="WARNING")

        return results
