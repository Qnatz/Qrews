from . import FrontendSubAgent
from utils.general_utils import Logger # CORRECTED
from utils.database import Database # CORRECTED
from utils.context_handler import ProjectContext # CORRECTED

class ComponentGenerator(FrontendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(
            name="component_generator",
            role="Component Generator - Generates visual widgets: cards, buttons, tables, modals, etc., from screen descriptions and page structure.",
            logger=logger,
            db=db,
            model_name_override=model_name_override
        )

    def run(self, project_context: ProjectContext, page_structure_data: dict) -> dict:
        """
        Generates UI components based on the provided page structure.
        'page_structure_data' is the output from PageStructureDesigner.
        """
        self.logger.log(f"[{self.name}] Starting component generation. Received page_structure_data with keys: {page_structure_data.keys() if page_structure_data else 'None'}", self.role)

        # We'll pass page_structure_data as part of crew_inputs to the base 'run' method.
        # The prompt for 'component_generator' should be designed to use 'crew_inputs.page_structure'.
        crew_inputs_for_prompt = {
            "page_structure": page_structure_data
        }

        agent_result = super().run(project_context, crew_inputs=crew_inputs_for_prompt)

        # Example validation (conceptual):
        # if agent_result["status"] == "complete" and agent_result.get("structured_output"):
        #     if not isinstance(agent_result["structured_output"], dict): # Expecting a dict of components
        #         agent_result["status"] = "error"
        #         agent_result["errors"].append("ComponentGenerator output is not a dict of components.")
        #         agent_result["structured_output"] = None

        self.logger.log(f"[{self.name}] Component generation finished. Status: {agent_result['status']}", self.role)
        return agent_result

    # Override _enhance_prompt_context if more specific prompt detailing is needed
    # based on page_structure_data, beyond just including it in crew_inputs.
    # def _enhance_prompt_context(self, context: dict, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
    #     context = super()._enhance_prompt_context(context, project_context, crew_inputs)
    #     if crew_inputs and "page_structure" in crew_inputs:
    #         # Example: You might want to summarize or extract specific parts of the page_structure
    #         # for the prompt, if the full structure is too verbose or complex.
    #         context['page_routes_for_prompt'] = crew_inputs['page_structure'].get('routes', [])
    #         context['number_of_pages_for_prompt'] = len(crew_inputs['page_structure'].get('routes', []))
    #     self.logger.log(f"[{self.name}] Enhanced prompt context with page_structure details.", self.role)
    #     return context
