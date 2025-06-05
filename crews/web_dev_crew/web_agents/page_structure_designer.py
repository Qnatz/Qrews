from . import FrontendSubAgent
from utils.general_utils import Logger # CORRECTED
from utils.database import Database # CORRECTED
from utils.context_handler import ProjectContext # CORRECTED

class PageStructureDesigner(FrontendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(
            name="page_structure_designer",
            role="Page Structure Designer - Builds route structure, pages, nested layout flows (React Router, Next.js AppDir, etc.).",
            logger=logger,
            db=db,
            model_name_override=model_name_override
        )

    def run(self, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
        """
        Generates the page and routing structure for the frontend application.
        'crew_inputs' is not typically used by this first agent in the sequence for inputs from other crew members.
        """
        self.logger.log(f"[{self.name}] Starting page structure design. Received crew_inputs keys: {crew_inputs.keys() if crew_inputs else 'None'}", self.role)

        # This agent uses the base FrontendSubAgent's run logic, which prepares a prompt
        # using project_context and potentially generic crew_inputs (though PSD won't use specific keys from it).
        # If PSD needed to customize prompt context beyond what base 'run' and '_enhance_prompt_context' do,
        # it would prepare prompt_render_context and call self._call_model here.

        # For now, rely on the base run method to handle LLM interaction
        agent_result = super().run(project_context, crew_inputs) # Pass crew_inputs along

        # Specific parsing for PageStructureDesigner output could be done here if needed,
        # for example, validating the structure of routes or page components.
        # The base _parse_response already populates 'structured_output'.

        # Example validation (conceptual):
        # if agent_result["status"] == "complete" and agent_result.get("structured_output"):
        #     if not isinstance(agent_result["structured_output"], dict) or "routes" not in agent_result["structured_output"]:
        #         agent_result["status"] = "error"
        #         agent_result["errors"].append("PageStructureDesigner output missing 'routes' key or is not a dict.")
        #         agent_result["structured_output"] = None # Clear invalid output

        self.logger.log(f"[{self.name}] Page structure design finished. Status: {agent_result['status']}", self.role)
        return agent_result

    # _enhance_prompt_context can be overridden here if PSD needs to add specific things
    # to the prompt context beyond what's in project_context or generic crew_inputs.
    # def _enhance_prompt_context(self, context: dict, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
    #     context = super()._enhance_prompt_context(context, project_context, crew_inputs)
    #     # Add PSD-specific items to context for prompt rendering if needed
    #     # context['my_custom_psd_detail'] = "some_value"
    #     return context
