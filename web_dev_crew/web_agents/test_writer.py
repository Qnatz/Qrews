from . import FrontendSubAgent
from utils import Logger
from database import Database
from context_handler import ProjectContext

class TestWriter(FrontendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(
            name="test_writer",
            role="Test Writer - Generates unit/integration/UI tests (Jest + RTL or Cypress) for all generated frontend artifacts.",
            logger=logger,
            db=db,
            model_name_override=model_name_override
        )

    def run(self, project_context: ProjectContext,
            page_structure_data: dict,
            components_output: dict,
            forms_output: dict,
            state_output: dict,
            styles_output: dict, # Though styles might be tested implicitly via component/UI tests
            layout_output: dict, # Similar to styles
            api_hooks_output: dict,
            error_boundaries_output: dict) -> dict:
        """
        Generates test code based on all previously generated frontend artifacts.
        """
        self.logger.log(f"[{self.name}] Starting test writing. Receiving all prior artifacts.", self.role)

        crew_inputs_for_prompt = {
            "page_structure": page_structure_data,
            "components": components_output,
            "forms": forms_output,
            "state_management": state_output,
            "styles": styles_output,
            "layout": layout_output,
            "api_hooks": api_hooks_output,
            "error_boundaries": error_boundaries_output
            # The prompt for 'test_writer' should be designed to comprehensively
            # use these inputs to generate relevant tests.
        }

        agent_result = super().run(project_context, crew_inputs=crew_inputs_for_prompt)

        self.logger.log(f"[{self.name}] Test writing finished. Status: {agent_result['status']}", self.role)
        return agent_result
