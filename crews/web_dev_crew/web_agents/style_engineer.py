from . import FrontendSubAgent
from utils.general_utils import Logger # CORRECTED
from utils.database import Database # CORRECTED
from utils.context_handler import ProjectContext # CORRECTED

class StyleEngineer(FrontendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(
            name="style_engineer",
            role="Style Engineer - Applies TailwindCSS or styled-components for themes, spacing, and styling of components and forms.",
            logger=logger,
            db=db,
            model_name_override=model_name_override
        )

    def run(self, project_context: ProjectContext, components_output: dict, forms_output: dict) -> dict:
        """
        Generates styles for components and forms.
        'components_output' is from ComponentGenerator.
        'forms_output' is from FormHandler.
        """
        self.logger.log(f"[{self.name}] Starting style engineering. Components keys: {components_output.keys() if components_output else 'None'}, Forms keys: {forms_output.keys() if forms_output else 'None'}", self.role)

        crew_inputs_for_prompt = {
            "components": components_output,
            "forms": forms_output
        }

        agent_result = super().run(project_context, crew_inputs=crew_inputs_for_prompt)

        self.logger.log(f"[{self.name}] Style engineering finished. Status: {agent_result['status']}", self.role)
        return agent_result
