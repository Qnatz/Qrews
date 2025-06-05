"""
agents.frontend_build_crew package initializer.
Exports all symbols from the modules in this directory,
and the FrontendSubAgent base class.
"""

# Imports for FrontendSubAgent
from agents import Agent
from utils import Logger
from database import Database
from config import ModelConfig, GeminiConfig

# Relative imports for sub-modules
from . import api_hook_writer
from . import component_generator
from . import error_boundary_writer
from . import form_handler
from . import layout_designer
from . import page_structure_designer
from . import state_manager
from . import style_engineer
from . import test_writer
from .runner import FrontendCrewRunner

# Base class for frontend sub-agents
class FrontendSubAgent(Agent):
    def __init__(self, name, role, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name, role, logger, db=db)
        if model_name_override:
            self.current_model = model_name_override
            self.logger.log(f"FrontendSubAgent {self.name} initialized. Model override: {self.current_model}", self.role)
        else:
            self.logger.log(f"FrontendSubAgent {self.name} initialized. Using default model selection. Current model: {self.current_model}", self.role)

    def run(self, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
        """
        Main execution method for a sub-agent.
        Called by FrontendCrewRunner.
        'crew_inputs' contains outputs from previous sub-agents in the crew.
        This method is expected to prepare a prompt, call the LLM (likely via super().perform_task or directly _call_model),
        and then parse the response, returning a dictionary.
        """
        self.logger.log(f"[{self.name}] Executing run method with inputs: {crew_inputs.keys() if crew_inputs else 'None'}", self.role)

        # Sub-agents will override this to use crew_inputs to build their specific prompt.
        # For the base class, we'll just log and call the original perform_task logic
        # which doesn't use 'crew_inputs'. Specific sub-agents MUST tailor this.

        # The existing Agent.perform_task generates a prompt from project_context.
        # If sub-agents need to inject 'crew_inputs' into their prompts, they'll
        # need to override 'run', prepare a custom prompt string using crew_inputs,
        # and then call self._call_model(custom_prompt_str) followed by self._parse_response().
        # Or, they could modify project_context temporarily (less ideal).

        # For this refactoring, let's assume sub-agents will override `run` and handle prompt generation.
        # If a sub-agent *doesn't* override `run`, this base implementation would just run like a normal Agent.
        # This provides backward compatibility if a sub-agent doesn't need explicit inputs.

        # This base `run` method will now directly call the LLM interaction logic.
        # It needs to construct the prompt using get_agent_prompt.
        # The Agent.perform_task() logic is being partially replicated/adapted here.

        analysis_data = project_context.analysis.model_dump() if project_context.analysis else {}
        prompt_render_context = {
            'role': self.role,
            'specialty': self.role, # Could be more specific if sub-agent has a specialty
            'project_name': project_context.project_name,
            'objective': project_context.objective or "",
            'project_type': project_context.analysis.project_type_confirmed if project_context.analysis else project_context.project_type,
            'current_dir': project_context.current_dir or "/",
            'project_summary': project_context.project_summary or "",
            'architecture': project_context.architecture or "",
            'plan': project_context.plan or "",
            'memories': project_context.project_summary or "No specific memories retrieved.",
            'tool_names': [tool['name'] for tool in self.tools],
            'tools': self.tools, # For tool usage if any
            'analysis': analysis_data,
            'current_code_snippet': project_context.current_code_snippet or "",
            'error_report': project_context.error_report or "",
            'tech_stack': project_context.tech_stack.model_dump() if project_context.tech_stack else {},
            # Add crew_inputs to the prompt context so sub-agents can use them in their prompts
            'crew_inputs': crew_inputs if crew_inputs else {},
        }

        # Allow specific sub-agents to add more to prompt_render_context
        prompt_render_context = self._enhance_prompt_context(prompt_render_context, project_context, crew_inputs)

        generated_prompt_str = get_agent_prompt(self.name, prompt_render_context) # self.name is sub-agent name

        self.logger.log(f"[{self.name}] Starting task with model {self.current_model}", self.role)

        if self.tools: # Assuming sub-agents might use tools
            response_content = self._call_model_with_tools(generated_prompt_str)
        else:
            response_content = self._call_model(generated_prompt_str)

        parsed_result = self._parse_response(response_content, project_context)
        # The 'structured_output' key is populated by _parse_response if successful.
        return parsed_result

    def _enhance_prompt_context(self, context: dict, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
        """
        Placeholder for sub-agents to add specific details to their prompt rendering context.
        This method can be overridden by each sub-agent.
        """
        # Example: a sub-agent might want to unpack crew_inputs further
        # context['specific_input_needed'] = crew_inputs.get('relevant_key_from_previous_step')
        return context

    def _parse_response(self, response_text: str, project_context: ProjectContext) -> dict:
        # This method is inherited from Agent and potentially overridden here or in specific sub-agents.
        # The base Agent._parse_response already handles basic JSON extraction.
        # FrontendSubAgent's previous override for 'structured_output' is good.
        self.logger.log(f"[{self.name}] Parsing response in FrontendSubAgent _parse_response", self.role)
        parsed_output = super()._parse_response(response_text, project_context) # Calls Agent._parse_response

        if parsed_output['status'] == 'complete':
            if 'parsed_json_content' in parsed_output:
                parsed_output['structured_output'] = parsed_output['parsed_json_content']
                self.logger.log(f"[{self.name}] JSON content set as structured_output.", self.role)
            elif 'raw_response' in parsed_output and not parsed_output.get('structured_output'): # Check if not already set
                # If no JSON, but raw_response is there, use it as structured_output
                # This helps simpler agents that just output text (e.g. a single code block)
                parsed_output['structured_output'] = parsed_output['raw_response']
                self.logger.log(f"[{self.name}] No JSON block found. Using raw response as structured_output.", self.role)

        return parsed_output

    def set_model_from_config(self, model_key: str, model_mapping: dict):
        # This method remains as previously defined.
        new_model_name = model_mapping.get(model_key)
        if new_model_name:
            self.current_model = new_model_name
            self.generation_config = GeminiConfig.get_generation_config(self.name)
            self.logger.log(f"[{self.name}] Model updated to {self.current_model} using key '{model_key}'.", self.role)
        else:
            self.logger.log(f"[{self.name}] Model key '{model_key}' not found in mapping. Retaining current model: {self.current_model}.", self.role, level="WARNING")


__all__ = [
    "api_hook_writer",
    "component_generator",
    "error_boundary_writer",
    "form_handler",
    "layout_designer",
    "page_structure_designer",
    "state_manager",
    "style_engineer",
    "test_writer",
    "FrontendSubAgent",  # Added FrontendSubAgent
    "FrontendCrewRunner",
]
