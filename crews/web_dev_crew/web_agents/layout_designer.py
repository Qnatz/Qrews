from . import FrontendSubAgent
from utils.general_utils import Logger # CORRECTED
from utils.database import Database # CORRECTED
from utils.context_handler import ProjectContext # CORRECTED

class LayoutDesigner(FrontendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(
            name="layout_designer",
            role="Layout Designer - Constructs flex/grid layouts and responsive breakpoints, using page structure and overall styles.",
            logger=logger,
            db=db,
            model_name_override=model_name_override
        )

    def run(self, project_context: ProjectContext, page_structure_data: dict, styles_output: dict) -> dict:
        """
        Designs layouts based on page structure and styles.
        'page_structure_data' is from PageStructureDesigner.
        'styles_output' is from StyleEngineer.
        """
        self.logger.log(f"[{self.name}] Starting layout design. Page_structure keys: {page_structure_data.keys() if page_structure_data else 'None'}, Styles keys: {styles_output.keys() if styles_output else 'None'}", self.role)

        crew_inputs_for_prompt = {
            "page_structure": page_structure_data,
            "styles": styles_output
        }

        agent_result = super().run(project_context, crew_inputs=crew_inputs_for_prompt)

        self.logger.log(f"[{self.name}] Layout design finished. Status: {agent_result['status']}", self.role)
        return agent_result
