from . import FrontendSubAgent
from utils import Logger
from database import Database
from context_handler import ProjectContext

class StateManager(FrontendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(
            name="state_manager",
            role="State Manager - Defines state structure and flows (e.g., useState, useReducer, Redux/MobX) based on page structure and components.",
            logger=logger,
            db=db,
            model_name_override=model_name_override
        )

    def run(self, project_context: ProjectContext, page_structure_data: dict, components_output: dict) -> dict:
        """
        Defines state management logic based on page structure and components.
        'page_structure_data' is from PageStructureDesigner.
        'components_output' is from ComponentGenerator.
        """
        self.logger.log(f"[{self.name}] Starting state management design. Page_structure keys: {page_structure_data.keys() if page_structure_data else 'None'}, Components keys: {components_output.keys() if components_output else 'None'}", self.role)

        crew_inputs_for_prompt = {
            "page_structure": page_structure_data,
            "components": components_output
        }

        agent_result = super().run(project_context, crew_inputs=crew_inputs_for_prompt)

        self.logger.log(f"[{self.name}] State management design finished. Status: {agent_result['status']}", self.role)
        return agent_result
