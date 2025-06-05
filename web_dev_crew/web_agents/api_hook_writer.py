from . import FrontendSubAgent
from utils import Logger
from database import Database
from context_handler import ProjectContext

class APIHookWriter(FrontendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(
            name="api_hook_writer",
            role="API Hook Writer - Creates Axios or Fetch hooks for CRUD with backend, guided by page structure and API specs from project_context.",
            logger=logger,
            db=db,
            model_name_override=model_name_override
        )

    def run(self, project_context: ProjectContext, page_structure_data: dict) -> dict:
        """
        Generates API client hooks.
        'page_structure_data' is from PageStructureDesigner.
        API specifications are expected to be in project_context.api_specs.
        """
        self.logger.log(f"[{self.name}] Starting API hook writing. Page_structure keys: {page_structure_data.keys() if page_structure_data else 'None'}", self.role)
        self.logger.log(f"[{self.name}] API specs from project_context (first 100 chars): {project_context.api_specs[:100] if project_context.api_specs else 'None'}", self.role)

        crew_inputs_for_prompt = {
            "page_structure": page_structure_data
            # The prompt for this agent will also need to reference project_context.api_specs
            # which is available in the standard prompt_render_context in FrontendSubAgent.run()
        }

        agent_result = super().run(project_context, crew_inputs=crew_inputs_for_prompt)

        self.logger.log(f"[{self.name}] API hook writing finished. Status: {agent_result['status']}", self.role)
        return agent_result
