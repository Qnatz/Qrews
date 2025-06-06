"""
agents.frontend_build_crew package initializer.
Exports all symbols from the modules in this directory,
and the FrontendSubAgent base class.
"""
import json # ADDED for json.dumps

# Imports for FrontendSubAgent
from agents.base_agent import Agent # CORRECTED
from utils.general_utils import Logger # CORRECTED
from utils.database import Database # CORRECTED
from configs.global_config import ModelConfig, GeminiConfig # CORRECTED
from prompts.general_prompts import get_agent_prompt # ADDED
from utils.context_handler import ProjectContext # ADDED

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
        """
        self.logger.log(f"[{self.name}] Executing run method with crew_inputs keys: {list(crew_inputs.keys()) if crew_inputs else 'None'}", self.role)

        analysis_data = project_context.analysis.model_dump() if project_context.analysis else {}

        # Initial prompt_render_context setup (mostly from general_prompts needs)
        # Ensures basic placeholders for AGENT_ROLE_TEMPLATE, COMMON_CONTEXT_TEMPLATE etc. are present.
        # _enhance_prompt_context will add/override with web-dev specific keys in UPPER_SNAKE_CASE.
        prompt_render_context = {
            'ROLE': self.role, # Will be overridden by specific agent role from its config
            'SPECIALTY': self.role,
            'PROJECT_NAME': project_context.project_name,
            'OBJECTIVE': project_context.objective or "",
            'PROJECT_TYPE': project_context.analysis.project_type_confirmed if project_context.analysis else project_context.project_type,
            'CURRENT_DIR': project_context.current_dir or "/", # Used by TOOL_PROMPT_SECTION
            'PROJECT_SUMMARY': project_context.project_summary or "",
            'ARCHITECTURE': project_context.architecture or "", # Could be dict or string
            'PLAN': project_context.plan or "", # Could be dict or string
            'MEMORIES': project_context.project_summary or "No specific memories retrieved.",
            'TOOL_NAMES': [tool['name'] for tool in self.tools], # List of strings
            'TOOLS': self.tools, # List of tool dicts for TOOL_PROMPT_SECTION
            'ANALYSIS': analysis_data, # Dict
            'CURRENT_CODE_SNIPPET': project_context.current_code_snippet or "",
            'ERROR_REPORT': project_context.error_report or "",
            'TECH_STACK': project_context.tech_stack.model_dump() if project_context.tech_stack else {}, # Dict
            # crew_inputs itself is not directly used by prompts, its contents are mapped below
        }

        # Enhance context with web-dev specific keys and ensure proper formatting
        prompt_render_context = self._enhance_prompt_context(prompt_render_context, project_context, crew_inputs)

        generated_prompt_str = get_agent_prompt(self.name, prompt_render_context)

        self.logger.log(f"[{self.name}] Starting task with model {self.current_model}", self.role)

        if self.tools:
            response_content = self._call_model_with_tools(generated_prompt_str)
        else:
            response_content = self._call_model(generated_prompt_str)

        parsed_result = self._parse_response(response_content, project_context)
        return parsed_result

    def _enhance_prompt_context(self, context: dict, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
        """
        Enhances the prompt context with specific details required by Web Development agent prompts,
        ensuring keys are in UPPER_SNAKE_CASE and values are appropriately formatted (JSON strings for complex types).
        """
        if crew_inputs is None:
            crew_inputs = {}

        # Map from crew_inputs (outputs of previous agents)
        # Ensure values are JSON strings if they are dicts/lists
        page_structure = crew_inputs.get('page_structure')
        context['PAGE_STRUCTURE_JSON'] = json.dumps(page_structure) if isinstance(page_structure, (dict, list)) else str(page_structure or '{}')

        components_output = crew_inputs.get('components_output')
        context['COMPONENT_SPECS_JSON'] = json.dumps(components_output) if isinstance(components_output, (dict, list)) else str(components_output or '{}')

        api_hooks = crew_inputs.get('api_hooks') # Expected to be a dict with 'api_hooks_files' containing code strings
        context['API_HOOKS_CODE'] = json.dumps(api_hooks) if isinstance(api_hooks, (dict, list)) else str(api_hooks or 'N/A')

        forms = crew_inputs.get('forms') # Expected to be a dict with 'form_handlers'
        context['FORM_HANDLER_LOGIC_JSON'] = json.dumps(forms) if isinstance(forms, (dict, list)) else str(forms or '{}')

        state_management = crew_inputs.get('state_management') # Expected to be a dict with 'state_management_solution'
        context['STATE_MANAGEMENT_SETUP_JSON'] = json.dumps(state_management) if isinstance(state_management, (dict, list)) else str(state_management or '{}')

        # Styling information might come from crew_inputs if a style engineer runs first, or project_context
        styling_output = crew_inputs.get('styling_output') # Expected from StyleEngineer
        context['STYLE_GUIDE_SUMMARY'] = json.dumps(styling_output) if isinstance(styling_output, (dict, list)) else str(styling_output or project_context.style_guide_summary or "General responsive design principles apply.")

        layout_output = crew_inputs.get('layout_output') # Expected from LayoutDesigner
        context['LAYOUT_INFO_JSON'] = json.dumps(layout_output) if isinstance(layout_output, (dict, list)) else str(layout_output or '{}')


        # Populate from project_context (these are generally initial project settings or broader contexts)
        context['TECH_STACK_FRONTEND_NAME'] = project_context.tech_stack.frontend if project_context.tech_stack and project_context.tech_stack.frontend else "Not Specified"

        context['DESIGN_SYSTEM_GUIDELINES'] = str(project_context.design_system_guidelines or "Standard design principles and common sense apply.")
        context['EXISTING_COMPONENTS_INFO'] = str(project_context.existing_components_info or "No existing components listed.")

        api_specs_data = project_context.api_specs
        context['API_SPECIFICATIONS_JSON'] = json.dumps(api_specs_data) if isinstance(api_specs_data, (dict, list)) else str(api_specs_data or '{}')

        context['EXISTING_HOOKS_INFO'] = str(project_context.existing_hooks_info or "No existing API hooks listed.")
        context['VALIDATION_RULES_INFO'] = str(project_context.validation_rules_info or "Standard validation rules apply (e.g., required fields, email format).")
        context['EXISTING_STATE_MGMT_INFO'] = str(project_context.existing_state_mgmt_info or "No existing state management info; choose based on framework and complexity.")
        context['EXISTING_STYLING_INFO'] = str(project_context.existing_styling_info or "No existing styling setup; choose based on framework and design system.")
        context['LOGGING_SERVICE_INFO'] = str(project_context.logging_service_info or "Log errors to console by default.")
        context['EXISTING_TESTS_INFO'] = str(project_context.existing_tests_info or f"Use Jest and React Testing Library (or equivalent for {context['TECH_STACK_FRONTEND_NAME']}) by default.")

        # Specific context for PageStructureDesigner (typically runs first in web dev crew)
        key_requirements_list = project_context.analysis.key_requirements if project_context.analysis and project_context.analysis.key_requirements else []
        context['KEY_REQUIREMENTS'] = "\n".join(key_requirements_list) if key_requirements_list else "No specific key requirements provided for page structure."
        context['USER_STORIES'] = str(project_context.user_stories or "No user stories provided.")
        context['EXISTING_PAGES_INFO'] = str(project_context.existing_pages_info or "No existing pages information provided.")

        # Override general role/specialty if specific agent has different ones
        # This is usually handled by agent config, but ensure context has final say if needed
        context['ROLE'] = self.role # The sub-agent's specific role
        # 'SPECIALTY' can remain the role or be more specific if defined for the sub-agent

        self.logger.log(f"[{self.name}] Enhanced prompt context. Keys: {list(context.keys())}", self.role)
        return context

    def _parse_response(self, response_text: str, project_context: ProjectContext) -> dict:
        self.logger.log(f"[{self.name}] Parsing response in FrontendSubAgent _parse_response", self.role)
        parsed_output = super()._parse_response(response_text, project_context)

        if parsed_output['status'] == 'complete':
            if 'parsed_json_content' in parsed_output:
                parsed_output['structured_output'] = parsed_output['parsed_json_content']
                self.logger.log(f"[{self.name}] JSON content set as structured_output.", self.role)
            elif 'raw_response' in parsed_output and not parsed_output.get('structured_output'):
                # If no JSON, but raw_response is there, use it as structured_output
                # This helps simpler agents that just output text (e.g. a single code block for API_HOOK_WRITER)
                # Check if the agent is one that is expected to output non-JSON code directly
                if self.name in ["api_hook_writer", "state_manager", "style_engineer"]: # Add other direct code output agents
                    # For these agents, the raw_response might be the code itself if not wrapped in JSON by the LLM
                    # The prompt asks for JSON, but this is a fallback.
                    # A more robust solution would be for the LLM to *always* return JSON as requested.
                    # For now, we assume if parsed_json_content is missing, raw_response is the intended output for these.
                    if isinstance(parsed_output['raw_response'], str):
                        # The prompts for these agents ask for a JSON structure that *contains* the code.
                        # If the LLM failed to produce that JSON, this fallback might be incorrect.
                        # The primary expectation is that `parsed_json_content` is populated.
                        # This fallback is a safety net, but might lead to downstream issues if the runner expects JSON.
                        self.logger.log(f"[{self.name}] WARNING: No JSON block found. Agent is expected to output JSON. Using raw response. This might cause issues.", self.role, level="WARNING")
                        # The agent's prompt asks for a JSON structure, so this raw output might not match.
                        # For example, api_hook_writer should return: {"project_name": "...", "api_hooks_files": [...]}
                        # If it returns raw code, it's not adhering to its own output format.
                        # This fallback should be critically reviewed. For now, let's keep it to see behavior.
                        parsed_output['structured_output'] = parsed_output['raw_response']


        return parsed_output

    def set_model_from_config(self, model_key: str, model_mapping: dict):
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
    "FrontendSubAgent",
    "FrontendCrewRunner",
]

[end of crews/web_dev_crew/web_agents/__init__.py]
