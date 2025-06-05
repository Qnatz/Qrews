from . import FrontendSubAgent
from utils.general_utils import Logger # CORRECTED
from utils.database import Database # CORRECTED
from utils.context_handler import ProjectContext # CORRECTED

class ErrorBoundaryWriter(FrontendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(
            name="error_boundary_writer",
            role="Error Boundary Writer - Generates fallback UI, suspense components, error handlers, potentially informed by page structure.",
            logger=logger,
            db=db,
            model_name_override=model_name_override
        )

    def run(self, project_context: ProjectContext, page_structure_data: dict) -> dict:
        """
        Generates error boundary components and suspense/loading UI.
        'page_structure_data' (from PageStructureDesigner) can provide context for placement or types of boundaries.
        """
        self.logger.log(f"[{self.name}] Starting error boundary writing. Page_structure keys: {page_structure_data.keys() if page_structure_data else 'None'}", self.role)

        crew_inputs_for_prompt = {
            "page_structure": page_structure_data
        }

        agent_result = super().run(project_context, crew_inputs=crew_inputs_for_prompt)

        self.logger.log(f"[{self.name}] Error boundary writing finished. Status: {agent_result['status']}", self.role)
        return agent_result
