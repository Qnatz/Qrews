# crews/mobile_dev_crew/lead.py
from agents.base_agent import Agent
from utils.general_utils import Logger
from utils.database import Database
from utils.context_handler import ProjectContext
from .mobile_agents.runner import MobileCrewRunner

class MobileLeadAgent(Agent):
    def __init__(self, logger: Logger, db: Database = None, sub_agent_model_config: dict = None):
        super().__init__(
            name="mobile_lead_agent",
            role="Mobile Lead Agent - Orchestrates the mobile development sub-agents.",
            logger=logger,
            db=db
        )
        self.sub_agent_model_config = sub_agent_model_config if sub_agent_model_config else {}
        self.runner = MobileCrewRunner(
            logger=self.logger,
            db=self.db,
            sub_agent_model_config=self.sub_agent_model_config
        )
        self.logger.log(f"[{self.name}] MobileCrewRunner initialized.", self.role)

    def run_crew(self, project_context: ProjectContext) -> dict:
        self.logger.log(f"[{self.name}] Starting mobile crew run for project: {project_context.project_name}", self.role)

        results = self.runner.execute(project_context)

        self.logger.log(f"[{self.name}] Mobile crew run finished. Overall status: {results.get('status')}", self.role)

        errors_to_log = results.get('errors')
        if errors_to_log: # Check if there are any errors
            if isinstance(errors_to_log, list) and not errors_to_log: pass # Empty list
            elif isinstance(errors_to_log, list):
                self.logger.log(f"[{self.name}] Errors encountered: {'; '.join(map(str, errors_to_log))}", self.role, level="ERROR")
            else:
                self.logger.log(f"[{self.name}] Errors encountered: {str(errors_to_log)}", self.role, level="ERROR")

        warnings_to_log = results.get('warnings')
        if warnings_to_log: # Check if there are any warnings
            if isinstance(warnings_to_log, list) and not warnings_to_log: pass # Empty list
            elif isinstance(warnings_to_log, list):
                self.logger.log(f"[{self.name}] Warnings generated: {'; '.join(map(str, warnings_to_log))}", self.role, level="WARNING")
            else:
                self.logger.log(f"[{self.name}] Warnings generated: {str(warnings_to_log)}", self.role, level="WARNING")

        return results
