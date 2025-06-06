"""
agents.frontend_build_crew package initializer.
Exports all symbols from the modules in this directory,
and the FrontendSubAgent base class.
"""
import json

# Imports for FrontendSubAgent
from agents.base_agent import Agent
from utils.general_utils import Logger
from utils.database import Database
from configs.global_config import ModelConfig, GeminiConfig
from prompts.general_prompts import get_agent_prompt
from utils.context_handler import ProjectContext

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

        prompt_render_context = {
            'ROLE': self.role,
            'SPECIALTY': self.role,
            'PROJECT_NAME': project_context.project_name,
            'OBJECTIVE': project_context.objective or "",
            'PROJECT_TYPE': project_context.analysis.project_type_confirmed if project_context.analysis else project_context.project_type,
            'CURRENT_DIR': project_context.current_dir or "/",
            'PROJECT_SUMMARY': project_context.project_summary or "",
            'ARCHITECTURE': project_context.architecture or "",
            'PLAN': project_context.plan or "",
            'MEMORIES': project_context.project_summary or "No specific memories retrieved.",
            'TOOL_NAMES': [tool['name'] for tool in self.tools],
            'TOOLS': self.tools,
            'ANALYSIS': analysis_data,
            'CURRENT_CODE_SNIPPET': project_context.current_code_snippet or "",
            'ERROR_REPORT': project_context.error_report or "",
            'TECH_STACK': project_context.tech_stack.model_dump() if project_context.tech_stack else {},
        }

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
        page_structure = crew_inputs.get('page_structure')
        context['PAGE_STRUCTURE_JSON'] = json.dumps(page_structure) if isinstance(page_structure, (dict, list)) else str(page_structure or '{}')

        components_output = crew_inputs.get('components_output')
        context['COMPONENT_SPECS_JSON'] = json.dumps(components_output) if isinstance(components_output, (dict, list)) else str(components_output or '{}')

        api_hooks = crew_inputs.get('api_hooks')
        context['API_HOOKS_CODE'] = json.dumps(api_hooks) if isinstance(api_hooks, (dict, list)) else str(api_hooks or 'N/A')

        forms = crew_inputs.get('forms')
        context['FORM_HANDLER_LOGIC_JSON'] = json.dumps(forms) if isinstance(forms, (dict, list)) else str(forms or '{}')

        state_management = crew_inputs.get('state_management')
        context['STATE_MANAGEMENT_SETUP_JSON'] = json.dumps(state_management) if isinstance(state_management, (dict, list)) else str(state_management or '{}')

        styling_output = crew_inputs.get('styling_output')
        # Try to get detailed style guide summary from styling_output first, then from project_context
        style_guide_from_crew = styling_output.get('styling_strategy', {}).get('justification') if isinstance(styling_output, dict) else None
        context['STYLE_GUIDE_SUMMARY'] = str(style_guide_from_crew or project_context.style_guide_summary or "General responsive design principles apply.")

        layout_output = crew_inputs.get('layout_output')
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

        # Specific context for PageStructureDesigner
        key_requirements_list = project_context.analysis.key_requirements if project_context.analysis and project_context.analysis.key_requirements else []
        context['KEY_REQUIREMENTS'] = "\n".join(key_requirements_list) if key_requirements_list else "No specific key requirements provided for page structure."
        context['USER_STORIES'] = str(project_context.user_stories or "No user stories provided.")
        context['EXISTING_PAGES_INFO'] = str(project_context.existing_pages_info or "No existing pages information provided.")

        # New generic placeholders (sourced from crew_inputs, then project_context, then default)
        context['ITEM_NAME_SINGULAR'] = str(crew_inputs.get('item_name_singular', getattr(project_context, 'generic_item_name_singular', "Item")))
        context['ITEM_NAME_PLURAL'] = str(crew_inputs.get('item_name_plural', getattr(project_context, 'generic_item_name_plural', "Items")))
        context['DATA_ENTITY_NAME_SINGULAR'] = str(crew_inputs.get('data_entity_name_singular', getattr(project_context, 'generic_data_entity_singular', "Entry")))
        context['DATA_ENTITY_NAME_PLURAL'] = str(crew_inputs.get('data_entity_name_plural', getattr(project_context, 'generic_data_entity_plural', "Entries")))
        context['ITEMS_SLUG'] = str(crew_inputs.get('items_slug', getattr(project_context, 'generic_items_slug', "items")))
        context['FORM_NAME'] = str(crew_inputs.get('form_name', getattr(project_context, 'generic_form_name', "DetailForm")))
        context['SUBMISSION_TYPE'] = str(crew_inputs.get('submission_type', getattr(project_context, 'generic_submission_type', "DataSubmission")))
        context['PRIMARY_ACTION_DESCRIPTION'] = str(crew_inputs.get('primary_action_description', getattr(project_context, 'generic_primary_action_desc', "Submit Data")))
        context['FEATURE_NAME_GENERIC'] = str(crew_inputs.get('feature_name_generic', getattr(project_context, 'generic_feature_name', "MainFeature")))
        context['FEATURE_NAME_LOWERCASE'] = str(crew_inputs.get('feature_name_lowercase', getattr(project_context, 'generic_feature_name_lc', "mainfeature")))
        context['MODULE_NAME_GENERIC'] = str(crew_inputs.get('module_name_generic', getattr(project_context, 'generic_module_name', "CoreModule")))
        context['COMPONENT_NAME_GENERIC'] = str(crew_inputs.get('component_name_generic', getattr(project_context, 'generic_component_name', "DisplayComponent")))
        context['PAGE_NAME_GENERIC'] = str(crew_inputs.get('page_name_generic', getattr(project_context, 'generic_page_name', "StandardPage")))
        context['CRITICAL_COMPONENT_EXAMPLE_NAME'] = str(crew_inputs.get('critical_component_example_name', getattr(project_context, 'generic_critical_component_name', "CriticalWidget")))

        context['ROLE'] = self.role

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
                if self.name in ["api_hook_writer", "state_manager", "style_engineer"]:
                    self.logger.log(f"[{self.name}] WARNING: No JSON block found. Agent is expected to output JSON. Using raw response. This might cause issues.", self.role, level="WARNING")
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
