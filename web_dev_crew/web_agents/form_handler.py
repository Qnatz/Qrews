from . import FrontendSubAgent
from utils import Logger
from database import Database
from context_handler import ProjectContext

class FormHandler(FrontendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(
            name="form_handler",
            role="Form Handler - Handles forms, state bindings, validation logic, based on generated components.",
            logger=logger,
            db=db,
            model_name_override=model_name_override
        )

    def run(self, project_context: ProjectContext, components_output: dict) -> dict:
        """
        Generates form handling logic for the provided components.
        'components_output' is the output from ComponentGenerator.
        """
        self.logger.log(f"[{self.name}] Starting form handling. Received components_output with keys: {components_output.keys() if components_output else 'None'}", self.role)

        crew_inputs_for_prompt = {
            "components": components_output
        }

        agent_result = super().run(project_context, crew_inputs=crew_inputs_for_prompt)

        self.logger.log(f"[{self.name}] Form handling finished. Status: {agent_result['status']}", self.role)
        return agent_result
