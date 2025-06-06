# crews/mobile_dev_crew/mobile_agents/__init__.py
"""
Mobile Development Sub-Agents package.
"""
import json
from agents.base_agent import Agent
from utils.general_utils import Logger
from utils.database import Database
from prompts.general_prompts import get_agent_prompt
from utils.context_handler import ProjectContext

class MobileSubAgent(Agent):
    def __init__(self, name, role, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name, role, logger, db=db)
        if model_name_override:
            self.current_model = model_name_override
            if hasattr(self, 'gemini_config'):
                self.generation_config = self.gemini_config.get_generation_config(self.name)
            self.logger.log(f"MobileSubAgent {self.name} initialized. Model override: {self.current_model}", self.role)
        else:
            self.logger.log(f"MobileSubAgent {self.name} initialized. Using default model selection. Current model: {self.current_model}", self.role)

    def run(self, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
        self.logger.log(f"[{self.name}] Executing MobileSubAgent run method with crew_inputs: {list(crew_inputs.keys()) if crew_inputs else 'None'}", self.role)
        analysis_data = project_context.analysis.model_dump() if project_context.analysis else {}
        prompt_render_context = {
            'ROLE': self.role, 'SPECIALTY': self.role,
            'PROJECT_NAME': project_context.project_name,
            'OBJECTIVE': project_context.objective or "",
            'PROJECT_TYPE': project_context.analysis.project_type_confirmed if project_context.analysis else project_context.project_type,
            'CURRENT_DIR': project_context.current_dir or "/",
            'PROJECT_SUMMARY': project_context.project_summary or "",
            'ARCHITECTURE': project_context.architecture or "",
            'PLAN': project_context.plan or "",
            'MEMORIES': project_context.project_summary or "No specific memories.",
            'TOOL_NAMES': [tool['name'] for tool in self.tools if 'name' in tool],
            'TOOLS': self.tools,
            'ANALYSIS': analysis_data,
            'TECH_STACK': project_context.tech_stack.model_dump() if project_context.tech_stack else {},
            'crew_inputs': crew_inputs if crew_inputs else {},
        }

        prompt_render_context = self._enhance_prompt_context(prompt_render_context, project_context, crew_inputs)

        # For MobileSubAgents, we will use get_crew_internal_prompt from mobile_crew_internal_prompts.py
        # This is because their prompts are currently defined there and are not yet integrated into the main AGENT_PROMPTS.
        # This will be reconciled later.
        from prompts.mobile_crew_internal_prompts import get_crew_internal_prompt as get_mobile_prompt
        generated_prompt_str = get_mobile_prompt(self.name, prompt_render_context)

        response_content = self._call_model(generated_prompt_str) if not self.tools else self._call_model_with_tools(generated_prompt_str)
        return self._parse_response(response_content, project_context)

    def _enhance_prompt_context(self, context: dict, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
        if crew_inputs is None: crew_inputs = {}

        # --- Populate standard mobile placeholders ---
        context['TECH_STACK_MOBILE'] = str(project_context.tech_stack.frontend if project_context.tech_stack and project_context.tech_stack.frontend else "Not Specified")
        context['PROJECT_DETAILS'] = str(crew_inputs.get('project_details', getattr(project_context, 'project_summary', 'No project details provided.')))

        user_req_source = crew_inputs.get('user_requirements', getattr(project_context.analysis, 'key_requirements_str', 'No user requirements specified.'))
        context['USER_REQUIREMENTS'] = str(user_req_source) if user_req_source else 'No user requirements specified.'

        # Placeholders for data passed between agents via `artifacts` in the runner
        context['UI_STRUCTURE_JSON'] = json.dumps(crew_inputs.get('ui_structure_output', crew_inputs.get('ui_structure_json', {})), default=str)
        context['COMPONENT_DESIGNS'] = json.dumps(crew_inputs.get('component_specs_output', crew_inputs.get('component_designs', {})), default=str)
        context['API_SPECIFICATIONS'] = json.dumps(getattr(project_context, 'api_specs', crew_inputs.get('api_specifications', {})), default=str)
        context['COMPONENT_DESIGNS_WITH_FORMS'] = json.dumps(crew_inputs.get('component_specs_output', crew_inputs.get('component_designs_with_forms', {})), default=str) # Often same as COMPONENT_DESIGNS

        # --- Populate new generic placeholders ---
        # Sourced from crew_inputs (runner), then project_context (lead/taskmaster), then defaults
        context['MAIN_ENTITY_SINGULAR_NAME'] = str(crew_inputs.get('main_entity_singular_name', getattr(project_context, 'main_entity_singular_name', "Item")))
        context['MAIN_ENTITY_PLURAL_NAME'] = str(crew_inputs.get('main_entity_plural_name', getattr(project_context, 'main_entity_plural_name', "Items")))
        context['AUTH_SCREEN_NAME'] = str(crew_inputs.get('auth_screen_name', getattr(project_context, 'auth_screen_name', "AuthScreen")))
        context['GENERIC_LIST_SCREEN_NAME'] = str(crew_inputs.get('generic_list_screen_name', getattr(project_context, 'generic_list_screen_name', f"{context['MAIN_ENTITY_PLURAL_NAME']}ListScreen")))
        context['GENERIC_DETAIL_SCREEN_NAME'] = str(crew_inputs.get('generic_detail_screen_name', getattr(project_context, 'generic_detail_screen_name', f"{context['MAIN_ENTITY_SINGULAR_NAME']}DetailScreen")))
        context['SETTINGS_SCREEN_NAME'] = str(crew_inputs.get('settings_screen_name', getattr(project_context, 'settings_screen_name', "SettingsScreen")))

        context['GENERIC_COMPONENT_NAME'] = str(crew_inputs.get('generic_component_name', getattr(project_context, 'generic_component_name', "AppButton")))
        context['GENERIC_BUTTON_NAME'] = str(crew_inputs.get('generic_button_name', getattr(project_context, 'generic_button_name', "SubmitButton")))
        context['GENERIC_INPUT_FIELD_NAME'] = str(crew_inputs.get('generic_input_field_name', getattr(project_context, 'generic_input_field_name', "CustomInput")))
        context['GENERIC_LIST_ITEM_NAME'] = str(crew_inputs.get('generic_list_item_name', getattr(project_context, 'generic_list_item_name', "EntityListItem")))
        context['GENERIC_CONTAINER_NAME'] = str(crew_inputs.get('generic_container_name', getattr(project_context, 'generic_container_name', "MainContainer")))

        context['DATA_ITEM_CARD_NAME'] = str(crew_inputs.get('data_item_card_name', getattr(project_context, 'data_item_card_name', f"{context['MAIN_ENTITY_SINGULAR_NAME']}Card")))
        context['DATA_ENTITY_NAME_SINGULAR'] = str(crew_inputs.get('data_entity_name_singular', getattr(project_context, 'data_entity_name_singular', context['MAIN_ENTITY_SINGULAR_NAME']))) # Default to main entity
        context['DATA_ENTITY_NAME_PLURAL'] = str(crew_inputs.get('data_entity_name_plural', getattr(project_context, 'data_entity_name_plural', context['MAIN_ENTITY_PLURAL_NAME']))) # Default to main entity

        context['FORM_NAME'] = str(crew_inputs.get('form_name', getattr(project_context, 'form_name', f"{context['DATA_ENTITY_NAME_SINGULAR']}Form")))
        context['FEATURE_NAME'] = str(crew_inputs.get('feature_name', getattr(project_context, 'feature_name', f"{context['DATA_ENTITY_NAME_SINGULAR']}Feature")))
        context['FEATURE_NAME_LOWERCASE'] = context['FEATURE_NAME'].lower()

        context['DATA_SERVICE_NAME'] = str(crew_inputs.get('data_service_name', getattr(project_context, 'data_service_name', "ApiService")))
        context['STATE_STORE_NAME'] = str(crew_inputs.get('state_store_name', getattr(project_context, 'state_store_name', "RootStore")))
        context['STATE_MANAGEMENT_LIBRARY'] = str(crew_inputs.get('state_management_library', getattr(project_context.tech_stack, 'state_management_library', "NotSpecifiedLib")))
        context['HTTP_CLIENT_LIBRARY'] = str(crew_inputs.get('http_client_library', getattr(project_context.tech_stack, 'http_client_library', "axios/fetch")))
        context['VALIDATION_LIBRARY'] = str(crew_inputs.get('validation_library', getattr(project_context.tech_stack, 'validation_library', "yup/zod")))
        context['TESTING_FRAMEWORK'] = str(crew_inputs.get('testing_framework', getattr(project_context.tech_stack, 'testing_framework', "jest")))
        context['USER_FLOW_NAME'] = str(crew_inputs.get('user_flow_name', "UserAuthenticationFlow"))


        # Ensure all context values are strings before returning, excluding TOOLS
        for key, value in context.items():
            if key == 'TOOLS': # Skip TOOLS as it's a list of dicts for the model
                continue
            if isinstance(value, (dict, list)):
                try:
                    context[key] = json.dumps(value, default=str)
                except TypeError:
                    context[key] = str(value) # Fallback for truly problematic types
            elif not isinstance(value, str):
                context[key] = str(value)

        self.logger.log(f"[{self.name}] Enhanced prompt context for mobile agent. Keys: {list(context.keys())}", self.role)
        return context

    def _parse_response(self, response_text: str, project_context: ProjectContext) -> dict:
        parsed_output = super()._parse_response(response_text, project_context)
        if parsed_output['status'] == 'complete' and 'parsed_json_content' in parsed_output:
            parsed_output['structured_output'] = parsed_output['parsed_json_content']
        elif parsed_output['status'] == 'complete' and 'raw_response' in parsed_output and not parsed_output.get('structured_output'):
            # Specific mobile agents known to output raw code strings
            if self.name in ["api_binder", "state_manager", "form_validator", "test_designer"]:
                parsed_output['structured_output'] = parsed_output['raw_response']
            else: # Others are expected to be JSON
                self.logger.log(f"[{self.name}] WARNING: No JSON block found where one was expected for agent '{self.name}'. Using raw response.", self.role, level="WARNING")
                parsed_output['structured_output'] = parsed_output['raw_response'] # Fallback
        return parsed_output

# Import existing mobile agents
from .ui_structure_designer import UIStructureDesigner
from .component_designer import ComponentDesigner
from .api_binder import APIBinder
from .state_manager import StateManager
from .form_validator import FormValidator
from .test_designer import TestDesigner
# from .mobile_merger import MobileMerger # Assuming this is not an LLM agent
from .runner import MobileCrewRunner

__all__ = [
    "MobileSubAgent",
    "UIStructureDesigner", "ComponentDesigner", "APIBinder",
    "StateManager", "FormValidator", "TestDesigner",
    # "MobileMerger",
    "MobileCrewRunner",
]
