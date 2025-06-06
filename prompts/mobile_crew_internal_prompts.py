# prompts/mobile_crew_internal_prompts.py
"""
Internal prompts for the Mobile Development Crew sub-agents.
These prompts are designed to be used by the MobileSubAgent class and expect
a context dictionary populated by the _enhance_prompt_context method.
"""

from prompts.general_prompts import (
    AGENT_ROLE_TEMPLATE,
    COMMON_CONTEXT_TEMPLATE,
    RESPONSE_FORMAT_TEMPLATE,
    TOOL_PROMPT_SECTION,
    NAVIGATION_TIPS
)

# --- Generalized Placeholders for Mobile Prompts (examples, expand as needed) ---
# {TECH_STACK_MOBILE} - e.g., "React Native", "Flutter", "SwiftUI"
# {PROJECT_DETAILS} - General description of the app.
# {USER_REQUIREMENTS} - Key features or user stories.
# {MAIN_ENTITY_SINGULAR_NAME} - e.g., "Recipe", "Product", "Task"
# {MAIN_ENTITY_PLURAL_NAME} - e.g., "Recipes", "Products", "Tasks"
# {AUTH_SCREEN_NAME} - e.g., "LoginScreen", "AuthenticationScreen"
# {GENERIC_LIST_SCREEN_NAME} - e.g., "ItemListScreen", "DashboardScreen"
# {GENERIC_DETAIL_SCREEN_NAME} - e.g., "ItemDetailScreen"
# {GENERIC_FORM_NAME} - e.g., "CreateItemForm", "SettingsForm"
# {GENERIC_COMPONENT_NAME} - e.g., "PrimaryButton", "ListItemCard"
# {DATA_SERVICE_NAME} - e.g., "RecipeService", "ApiService"
# {STATE_STORE_NAME} - e.g., "UserStore", "SettingsContext"
# {API_SPECIFICATIONS} - OpenAPI spec or similar.
# {UI_STRUCTURE_JSON} - JSON output from UIStructureDesigner.
# {COMPONENT_DESIGNS} - JSON/text output from ComponentDesigner.
# {COMPONENT_DESIGNS_WITH_FORMS} - Specifically for FormValidator.

UI_STRUCTURE_DESIGNER_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role.
{SPECIALTY} – Your specialization for UI structure design.
{PROJECT_NAME} – Name of the current project.
{OBJECTIVE} – Overall objective of the project.
{TECH_STACK_MOBILE} – The mobile framework/technology being used (e.g., "React Native", "Flutter", "SwiftUI").
{PROJECT_DETAILS} – A brief overview of the project and its goals.
{USER_REQUIREMENTS} – Key user stories, features, or functional requirements for the application.
{MAIN_ENTITY_PLURAL_NAME} – Plural name of the primary data entity the app revolves around (e.g., "Recipes", "Tasks", "Products").
{MAIN_ENTITY_SINGULAR_NAME} – Singular name of the primary data entity.
{AUTH_SCREEN_NAME} – Generic name for authentication screens (e.g., "AuthScreen", "LoginSignupScreen").
{GENERIC_LIST_SCREEN_NAME} – Generic name for screens displaying a list of main entities (e.g., "{MAIN_ENTITY_PLURAL_NAME}ListScreen").
{GENERIC_DETAIL_SCREEN_NAME} – Generic name for screens displaying details of a single main entity (e.g., "{MAIN_ENTITY_SINGULAR_NAME}DetailScreen").
{SETTINGS_SCREEN_NAME} – Generic name for a settings or profile screen (e.g., "SettingsScreen", "UserProfileScreen").
{COMMON_CONTEXT} – Common contextual information about the project.
{TOOL_NAMES} – List of available tools.

Your task: MUST design the screen hierarchy, navigation graph, and key UI flows for the mobile application "{PROJECT_NAME}" using {TECH_STACK_MOBILE}.
Project Details: {PROJECT_DETAILS}
User Requirements: {USER_REQUIREMENTS}

Based on the above, you MUST provide the screen-to-screen structure strictly in JSON format.
The JSON output MUST include:
1.  A list of screens, each with a unique `name`, a list of key `elements` (as strings describing functionality, e.g., "{MAIN_ENTITY_SINGULAR_NAME}_title", "save_button"), and a `navigation` object.
2.  The `navigation` object for each screen should detail possible navigation targets based on user actions (e.g., `"onSelect{MAIN_ENTITY_SINGULAR_NAME}": "{GENERIC_DETAIL_SCREEN_NAME}"`).
3.  An `entry_point` field specifying the name of the initial screen.
4.  Screens should include at least: `{AUTH_SCREEN_NAME}`, `{GENERIC_LIST_SCREEN_NAME}` for `{MAIN_ENTITY_PLURAL_NAME}`, `{GENERIC_DETAIL_SCREEN_NAME}` for a `{MAIN_ENTITY_SINGULAR_NAME}`, and a `{SETTINGS_SCREEN_NAME}`.

Example JSON Structure:
```json
{{
  "screens": [
    {{
      "name": "{AUTH_SCREEN_NAME}",
      "elements": ["email_input_field", "password_input_field", "login_action_button", "signup_navigation_link"],
      "navigation": {{
        "onLoginSuccess": "{GENERIC_LIST_SCREEN_NAME}",
        "onSignupLink": "{AUTH_SCREEN_NAME}Signup"
      }}
    }},
    {{
      "name": "{GENERIC_LIST_SCREEN_NAME}",
      "elements": ["{MAIN_ENTITY_PLURAL_NAME}_list_view", "{SETTINGS_SCREEN_NAME}_navigation_button", "add_{MAIN_ENTITY_SINGULAR_NAME}_button"],
      "navigation": {{
        "onNavigateToSettings": "{SETTINGS_SCREEN_NAME}",
        "onSelectItem": "{GENERIC_DETAIL_SCREEN_NAME}",
        "onAddItem": "{MAIN_ENTITY_SINGULAR_NAME}CreateScreen"
      }}
    }},
    {{
      "name": "{GENERIC_DETAIL_SCREEN_NAME}",
      "elements": ["{MAIN_ENTITY_SINGULAR_NAME}_details_view", "edit_{MAIN_ENTITY_SINGULAR_NAME}_button"],
      "navigation": {{
        "onEdit": "{MAIN_ENTITY_SINGULAR_NAME}EditScreen"
      }}
    }},
    {{
      "name": "{SETTINGS_SCREEN_NAME}",
      "elements": ["theme_toggle_switch", "logout_button"],
      "navigation": {{
        "onLogout": "{AUTH_SCREEN_NAME}"
      }}
    }}
  ],
  "entry_point": "{AUTH_SCREEN_NAME}"
}}
```
Ensure all screen names and element descriptions are clear and purposeful.
""" + RESPONSE_FORMAT_TEMPLATE

COMPONENT_DESIGNER_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role.
{SPECIALTY} – Your specialization for component design.
{PROJECT_NAME} – Name of the current project.
{TECH_STACK_MOBILE} – The mobile framework being used.
{UI_STRUCTURE_JSON} – JSON string describing the screen hierarchy and elements, from UIStructureDesigner.
{GENERIC_BUTTON_NAME} – Generic name for button components (e.g., "AppButton", "ActionTrigger").
{GENERIC_INPUT_FIELD_NAME} – Generic name for input field components (e.g., "AppTextInput", "DataEntryField").
{GENERIC_LIST_ITEM_NAME} – Generic name for list item components (e.g., "SummaryCard", "EntityRow").
{GENERIC_CONTAINER_NAME} – Generic name for container components (e.g., "ScreenWrapper", "InfoPanel").
{COMMON_CONTEXT} – Common contextual information about the project.
{TOOL_NAMES} – List of available tools.

Your task: MUST break down the screens (defined in `{UI_STRUCTURE_JSON}`) into reusable UI components for the mobile application "{PROJECT_NAME}", tailored for {TECH_STACK_MOBILE}.

Based on the UI structure, you MUST identify and specify reusable components.
For each identified component, provide:
1.  `component_name`: A descriptive name (e.g., "`{GENERIC_BUTTON_NAME}`", "`{GENERIC_INPUT_FIELD_NAME}`").
2.  `description`: Brief purpose of the component.
3.  `framework_equivalent`: The closest native or common library component in {TECH_STACK_MOBILE} (e.g., "Button (React Native Paper)", "TextField (Flutter Material)").
4.  `properties`: Key properties/props it should accept (e.g., "title: string", "onPress: function", "value: string", "onValueChanged: function").
5.  `usage_screens`: A list of screen names from `{UI_STRUCTURE_JSON}` where this component would likely be used.

Output MUST be a JSON object where keys are component names and values are their specifications as described above.

Example JSON Output:
```json
{{
  "{GENERIC_BUTTON_NAME}": {{
    "component_name": "{GENERIC_BUTTON_NAME}",
    "description": "A standard pressable button for actions.",
    "framework_equivalent": "Button (React Native Paper) or ElevatedButton (Flutter)",
    "properties": ["label: string", "onPress: function", "style: object", "isDisabled: boolean"],
    "usage_screens": ["AuthScreen", "SettingsScreen"]
  }},
  "{GENERIC_INPUT_FIELD_NAME}": {{
    "component_name": "{GENERIC_INPUT_FIELD_NAME}",
    "description": "A text input field for user data entry.",
    "framework_equivalent": "TextInput (React Native) or TextField (Flutter)",
    "properties": ["placeholder: string", "value: string", "onChangeText: function", "isSecure: boolean"],
    "usage_screens": ["AuthScreen", "ProfileEditScreen"]
  }},
  "{GENERIC_LIST_ITEM_NAME}": {{
    "component_name": "{GENERIC_LIST_ITEM_NAME}",
    "description": "Displays a summary of an item in a list.",
    "framework_equivalent": "Card (React Native Paper) or ListTile (Flutter)",
    "properties": ["itemData: object", "onPress: function"],
    "usage_screens": ["ItemListScreen"]
  }}
}}
```
Focus on reusability and adherence to {TECH_STACK_MOBILE} best practices.
""" + RESPONSE_FORMAT_TEMPLATE

API_BINDER_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role.
{SPECIALTY} – Your specialization for API binding.
{PROJECT_NAME} – Name of the current project.
{TECH_STACK_MOBILE} – The mobile framework being used.
{COMPONENT_DESIGNS} – JSON string describing UI components and their data needs.
{API_SPECIFICATIONS} – JSON string (e.g., OpenAPI format) describing the backend API endpoints.
{DATA_SERVICE_NAME} – Generic name for the API service module (e.g., "ApiService", "BackendClient").
{DATA_ENTITY_NAME_SINGULAR} – Generic singular name for a data entity (e.g., "User", "Item").
{DATA_ENTITY_NAME_PLURAL} – Generic plural name for data entities (e.g., "Users", "Items").
{HTTP_CLIENT_LIBRARY} – Name of the HTTP client library to be used (e.g., "axios", "fetch", "dio", "http").
{COMMON_CONTEXT} – Common contextual information about the project.
{TOOL_NAMES} – List of available tools.

Your task: MUST generate data service code for the mobile application "{PROJECT_NAME}" to connect UI components (described in `{COMPONENT_DESIGNS}`) to backend APIs (defined in `{API_SPECIFICATIONS}`). The code MUST be suitable for {TECH_STACK_MOBILE}.

You MUST:
1.  Identify data fetching requirements from `{COMPONENT_DESIGNS}`.
2.  Map these requirements to specific endpoints in `{API_SPECIFICATIONS}`.
3.  Generate a data service module (e.g., named `{DATA_SERVICE_NAME}.{FILE_EXTENSION_FROM_TECH_STACK}`).
4.  This module MUST contain functions for each required API interaction (e.g., `get{DATA_ENTITY_NAME_PLURAL}()`, `create{DATA_ENTITY_NAME_SINGULAR}(data)`).
5.  Use the `{HTTP_CLIENT_LIBRARY}` for making HTTP requests. Base URL should be extracted from `{API_SPECIFICATIONS}`.
6.  Functions MUST handle request parameters, request body, and parse responses.
7.  Implement basic error handling (e.g., log errors, throw exceptions).

Output the generated code for the data service module(s) as a raw string.

Example for a `{DATA_SERVICE_NAME}` in JavaScript (if {TECH_STACK_MOBILE} is React Native):
```javascript
// {DATA_SERVICE_NAME}.js
import axios from 'axios'; // Assuming {HTTP_CLIENT_LIBRARY} is axios

// Assuming API_BASE_URL is derived from {API_SPECIFICATIONS}.servers[0].url
const API_BASE_URL = 'https://your.api.domain/api/v1';

export const {DATA_SERVICE_NAME} = {{
  async get{DATA_ENTITY_NAME_PLURAL}(params) {{
    try {{
      const response = await axios.get(`${{API_BASE_URL}}/{DATA_ENTITY_NAME_PLURAL.toLowerCase()}`, {{ params }});
      return response.data;
    }} catch (error) {{
      console.error('Error fetching {DATA_ENTITY_NAME_PLURAL.toLowerCase()}:', error);
      throw error;
    }}
  }},

  async get{DATA_ENTITY_NAME_SINGULAR}ById(id) {{
    try {{
      const response = await axios.get(`${{API_BASE_URL}}/{DATA_ENTITY_NAME_PLURAL.toLowerCase()}/${{id}}`);
      return response.data;
    }} catch (error) {{
      console.error(`Error fetching {DATA_ENTITY_NAME_SINGULAR.toLowerCase()} with id ${{id}}:`, error);
      throw error;
    }}
  }},

  async create{DATA_ENTITY_NAME_SINGULAR}(data) {{
    try {{
      const response = await axios.post(`${{API_BASE_URL}}/{DATA_ENTITY_NAME_PLURAL.toLowerCase()}`, data);
      return response.data;
    }} catch (error) {{
      console.error('Error creating {DATA_ENTITY_NAME_SINGULAR.toLowerCase()}:', error);
      throw error;
    }}
  }}
  // Add update and delete methods as needed
}};
```
Ensure the generated code is well-structured and aligns with {TECH_STACK_MOBILE} conventions.
""" + RESPONSE_FORMAT_TEMPLATE

STATE_MANAGER_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role.
{SPECIALTY} – Your specialization for state management.
{PROJECT_NAME} – Name of the current project.
{TECH_STACK_MOBILE} – The mobile framework being used.
{COMPONENT_DESIGNS} – JSON string describing UI components and their state needs.
{UI_STRUCTURE_JSON} – JSON string describing screen hierarchy (for context).
{STATE_MANAGEMENT_LIBRARY} – Name of the state management library to be used (e.g., "Redux Toolkit", "Zustand", "Riverpod", "Provider", "SwiftUI @State/@EnvironmentObject").
{STATE_STORE_NAME_PRIMARY} – Generic name for the primary state store or context (e.g., "AppStore", "PrimaryContext").
{FEATURE_STATE_NAME} – Generic name for a feature-specific state slice or provider (e.g., "UserProfileState", "ItemListState").
{COMMON_CONTEXT} – Common contextual information about the project.
{TOOL_NAMES} – List of available tools.

Your task: MUST define and generate setup code for state management in the mobile application "{PROJECT_NAME}", using `{STATE_MANAGEMENT_LIBRARY}` for {TECH_STACK_MOBILE}.

You MUST:
1.  Analyze `{COMPONENT_DESIGNS}` and `{UI_STRUCTURE_JSON}` to identify shared state and local component state requirements.
2.  Define the structure (shape) of the global application state if using a centralized store (e.g., for `{STATE_STORE_NAME_PRIMARY}`).
3.  Generate code for state slices, reducers/mutations, actions/events, and selectors/getters for key features like user authentication, `{FEATURE_STATE_NAME}`.
4.  Show how to provide and consume state in UI components, following `{STATE_MANAGEMENT_LIBRARY}` patterns.
5.  Output the necessary code files for setting up the state management solution.

Example for a feature state using `{STATE_MANAGEMENT_LIBRARY}` (illustrative, adapt to actual library):
```javascript
// Example for Redux Toolkit if {TECH_STACK_MOBILE} is React Native
// features/{FEATURE_STATE_NAME}Slice.js

import {{ createSlice }} from '@reduxjs/toolkit';

const initialState = {{
  items: [],
  isLoading: false,
  error: null,
}};

const {FEATURE_STATE_NAME}Slice = createSlice({{
  name: '{FEATURE_STATE_NAME.toLowerCase()}',
  initialState,
  reducers: {{
    fetchItemsStart(state) {{
      state.isLoading = true;
    }},
    fetchItemsSuccess(state, action) {{
      state.items = action.payload;
      state.isLoading = false;
      state.error = null;
    }},
    fetchItemsFailure(state, action) {{
      state.isLoading = false;
      state.error = action.payload;
    }},
  }},
}});

export const {{ fetchItemsStart, fetchItemsSuccess, fetchItemsFailure }} = {FEATURE_STATE_NAME}Slice.actions;
export default {FEATURE_STATE_NAME}Slice.reducer;

// Example for store configuration:
// app/store.js
// import {{ configureStore }} from '@reduxjs/toolkit';
// import {FEATURE_STATE_NAME}Reducer from './features/{FEATURE_STATE_NAME}Slice';
//
// export const store = configureStore({{
//   reducer: {{
//     {FEATURE_STATE_NAME.toLowerCase()}: {FEATURE_STATE_NAME}Reducer,
//     // other reducers...
//   }},
// }});
```
The output should be raw code string(s) for the state management files.
""" + RESPONSE_FORMAT_TEMPLATE

FORM_VALIDATOR_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role.
{SPECIALTY} – Your specialization for form validation.
{PROJECT_NAME} – Name of the current project.
{TECH_STACK_MOBILE} – The mobile framework being used.
{COMPONENT_DESIGNS_WITH_FORMS} – JSON string describing UI components that include forms, detailing field names and expected input types.
{VALIDATION_LIBRARY} – Name of the validation library to be used (e.g., "Yup", "Zod", "Flutter FormBuilder validators", "SwiftUI built-in validation").
{GENERIC_FORM_NAME} – Generic name for a form (e.g., "AuthForm", "ProfileSettingsForm").
{COMMON_CONTEXT} – Common contextual information about the project.
{TOOL_NAMES} – List of available tools.

Your task: MUST generate validation schemas or logic for forms identified in `{COMPONENT_DESIGNS_WITH_FORMS}` for the mobile application "{PROJECT_NAME}". Use `{VALIDATION_LIBRARY}` for {TECH_STACK_MOBILE}.

For each form (e.g., `{GENERIC_FORM_NAME}`) described in `{COMPONENT_DESIGNS_WITH_FORMS}`:
1.  Identify form fields and their expected data types (string, number, email, password, etc.).
2.  Generate a validation schema or a set of validation functions.
3.  Schemas/logic MUST include common validation rules:
    *   Required fields.
    *   Minimum/maximum length for strings.
    *   Specific formats (e.g., email regex, numeric checks).
    *   Password complexity rules (if applicable, e.g., minimum length, character types).
4.  Output the generated code for these validation schemas/functions as a raw string.

Example for a `{GENERIC_FORM_NAME}` validation schema using Zod (if {TECH_STACK_MOBILE} is React Native/TS):
```typescript
// validationSchemas.ts
import {{ z }} from 'zod';

export const {GENERIC_FORM_NAME}Schema = z.object({{
  email: z.string().email({{ message: "Invalid email address" }}).min(1, {{ message: "Email is required" }}),
  password: z.string().min(8, {{ message: "Password must be at least 8 characters long" }}).min(1, {{ message: "Password is required" }}),
  confirmPassword: z.string().min(1, {{ message: "Confirm password is required" }})
}}).refine((data) => data.password === data.confirmPassword, {{
  message: "Passwords don't match",
  path: ["confirmPassword"], // Path of error
}});

// Example for another form
export const ProfileUpdateSchema = z.object({{
  username: z.string().min(3, "Username must be at least 3 characters"),
  bio: z.string().max(150, "Bio cannot exceed 150 characters").optional(),
}});
```
Ensure the generated code is idiomatic for `{VALIDATION_LIBRARY}` and {TECH_STACK_MOBILE}.
""" + RESPONSE_FORMAT_TEMPLATE

TEST_DESIGNER_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role.
{SPECIALTY} – Your specialization for test design.
{PROJECT_NAME} – Name of the current project.
{TECH_STACK_MOBILE} – The mobile framework being used.
{UI_STRUCTURE_JSON} – JSON string describing screen hierarchy.
{COMPONENT_DESIGNS} – JSON string describing UI components.
{API_SPECIFICATIONS} – JSON string (OpenAPI) of backend APIs (optional, for integration tests).
{TESTING_FRAMEWORK} – Testing framework to be used (e.g., "Jest", "React Testing Library", "Flutter Widget Tests", "XCTest").
{GENERIC_COMPONENT_NAME} – A generic name for a component being tested (e.g., "UserLogin").
{USER_FLOW_NAME} – A generic name for a user flow being tested (e.g., "CompletePurchase").
{COMMON_CONTEXT} – Common contextual information about the project.
{TOOL_NAMES} – List of available tools.

Your task: MUST design and write test cases for UI components and key user flows in the mobile application "{PROJECT_NAME}", using `{TESTING_FRAMEWORK}` for {TECH_STACK_MOBILE}.

You MUST:
1.  **Component Tests**: For major components identified in `{COMPONENT_DESIGNS}` (e.g., "`{GENERIC_COMPONENT_NAME}`"):
    *   Write unit tests to verify rendering based on props.
    *   Test event handling and user interactions (e.g., button presses, input changes).
    *   Mock dependencies (functions, modules) as needed.
2.  **User Flow/Integration Tests**: For critical user flows derived from `{UI_STRUCTURE_JSON}` and `{USER_REQUIREMENTS}` (e.g., "`{USER_FLOW_NAME}` flow"):
    *   Write integration tests covering navigation between screens.
    *   Test interaction with state management.
    *   If `{API_SPECIFICATIONS}` are provided, test interactions with mocked API services.
3.  Output test case descriptions or, preferably, actual test code as a raw string.
4.  Organize tests logically (e.g., by component or feature).

Example for a component test using Jest and React Testing Library (if {TECH_STACK_MOBILE} is React Native):
```javascript
// __tests__/{GENERIC_COMPONENT_NAME}.test.js
import React from 'react';
import {{ render, fireEvent }} from '@testing-library/react-native';
// import {GENERIC_COMPONENT_NAME} from '../path/to/{GENERIC_COMPONENT_NAME}'; // Actual import

// Mock dependencies if any
// jest.mock('../path/to/someModule');

describe('{GENERIC_COMPONENT_NAME}', () => {
  const mockOnPress = jest.fn();
  const defaultProps = {{
    title: "Submit",
    onPress: mockOnPress,
    // other necessary props
  }};

  // Test case 1: Renders correctly with given props
  it('renders correctly with default props', () => {
    // const {{ getByText }} = render(<{GENERIC_COMPONENT_NAME} {{...defaultProps}} />);
    // expect(getByText('Submit')).toBeTruthy();
    expect(true).toBe(true); // Placeholder if component not available
  });

  // Test case 2: Handles press event
  it('calls onPress prop when pressed', () => {
    // const {{ getByText }} = render(<{GENERIC_COMPONENT_NAME} {{...defaultProps}} />);
    // fireEvent.press(getByText('Submit'));
    // expect(mockOnPress).toHaveBeenCalledTimes(1);
    expect(true).toBe(true); // Placeholder
  });

  // Add more test cases for different states and props
});
```
Ensure tests are clear, maintainable, and follow `{TESTING_FRAMEWORK}` best practices.
""" + RESPONSE_FORMAT_TEMPLATE

PROMPT_TEMPLATES = {
    "ui_structure_designer": UI_STRUCTURE_DESIGNER_TEMPLATE,
    "component_designer": COMPONENT_DESIGNER_TEMPLATE,
    "api_binder": API_BINDER_TEMPLATE,
    "state_manager": STATE_MANAGER_TEMPLATE,
    "form_validator": FORM_VALIDATOR_TEMPLATE,
    "test_designer": TEST_DESIGNER_TEMPLATE,
}

def get_crew_internal_prompt(agent_name: str, prompt_input_data: dict) -> str:
    """
    Retrieves and formats the prompt for a given crew sub-agent.
    Args:
        agent_name (str): The name of the sub-agent.
        prompt_input_data (dict): Data to format the prompt with.
                                  Expected to contain UPPER_SNAKE_CASE keys like 'TECH_STACK_MOBILE'
                                  and other agent-specific keys.
    Returns:
        str: The formatted prompt.
    Raises:
        ValueError: If no template is found for the agent_name or if a key is missing.
    """
    template = PROMPT_TEMPLATES.get(agent_name)
    if not template:
        raise ValueError(f"No internal prompt template found for crew agent: {agent_name}")

    try:
        # Ensure all keys in prompt_input_data are strings, as expected by format()
        # This step might be redundant if the caller ensures this, but good for safety.
        # Stringified_prompt_input_data = {k: str(v) for k, v in prompt_input_data.items()}
        # However, direct formatting is usually fine if types are basic.
        # The main thing is that the _enhance_prompt_context should have made all values strings.
        return template.format(**prompt_input_data)
    except KeyError as e:
        raise ValueError(f"Missing key '{{str(e)}}' (expected in UPPER_SNAKE_CASE) in prompt_input_data for agent '{{agent_name}}'. Provided data keys: {{list(prompt_input_data.keys())}}")
    except Exception as e_format:
        raise ValueError(f"Error formatting prompt for agent '{agent_name}': {str(e_format)}")


if __name__ == '__main__':
    print("--- Testing prompts/mobile_crew_internal_prompts.py ---")

    ui_designer_input = {
        "ROLE": "UI Structure Designer", # From AGENT_ROLE_TEMPLATE
        "SPECIALTY": "UI Structure Designer for Mobile Applications", # From AGENT_ROLE_TEMPLATE
        "PROJECT_NAME": "RecipeApp",
        "OBJECTIVE": "Create a recipe sharing app.",
        "PROJECT_TYPE": "Mobile Application",
        "TECH_STACK_MOBILE": "Flutter",
        "PROJECT_DETAILS": "A recipe sharing app for users to browse, search, save, and upload recipes.",
        "USER_REQUIREMENTS": "Users can browse recipes. Users can search recipes. Users can save recipes. Users can upload recipes.",
        "MAIN_ENTITY_PLURAL_NAME": "Recipes",
        "MAIN_ENTITY_SINGULAR_NAME": "Recipe",
        "AUTH_SCREEN_NAME": "AuthScreen",
        "GENERIC_LIST_SCREEN_NAME": "RecipeListScreen",
        "GENERIC_DETAIL_SCREEN_NAME": "RecipeDetailScreen",
        "SETTINGS_SCREEN_NAME": "SettingsScreen",
        "COMMON_CONTEXT": "This is a common context string.",
        "TOOL_NAMES": "tool1, tool2",
        "RESPONSE_FORMAT_EXPECTATION": "Your response MUST be in JSON format, detailing the screen structure." # From RESPONSE_FORMAT_TEMPLATE
    }
    try:
        ui_prompt = get_crew_internal_prompt("ui_structure_designer", ui_designer_input)
        print("\n--- UI Structure Designer Prompt Example ---")
        print(f"Prompt for ui_structure_designer generated successfully. Starts with: '{ui_prompt[:150]}...'")
    except ValueError as e:
        print(f"Error generating UI designer prompt: {e}")

    cd_input = {
        "ROLE": "Component Designer",
        "SPECIALTY": "Designs individual UI components.",
        "PROJECT_NAME": "RecipeApp",
        "TECH_STACK_MOBILE": "SwiftUI",
        "UI_STRUCTURE_JSON": "{ \"screens\": [{\"name\": \"RecipeListScreen\", \"elements\": [\"recipe_card_list\"]}] }",
        "GENERIC_BUTTON_NAME": "AppButton",
        "GENERIC_INPUT_FIELD_NAME": "AppTextField",
        "GENERIC_LIST_ITEM_NAME": "RecipeCard",
        "GENERIC_CONTAINER_NAME": "ScreenView",
        "COMMON_CONTEXT": "Shared project info.",
        "TOOL_NAMES": "none",
        "RESPONSE_FORMAT_EXPECTATION": "Output detailed specifications in JSON format."
    }
    try:
        cd_prompt = get_crew_internal_prompt("component_designer", cd_input)
        print("\n--- Component Designer Prompt Example ---")
        print(f"Prompt for component_designer generated successfully. Starts with: '{cd_prompt[:150]}...'")
    except ValueError as e:
        print(f"Error generating component designer prompt: {e}")

    broken_input = {
        "TECH_STACK_MOBILE": "React Native"
        # Missing other required placeholders for ui_structure_designer
    }
    try:
        get_crew_internal_prompt("ui_structure_designer", broken_input)
    except ValueError as e:
        print(f"\nSuccessfully caught missing key error: {e}")
        assert "Missing key" in str(e) # Check that it's a KeyError related message

    try:
        get_crew_internal_prompt("non_existent_agent", {})
    except ValueError as e:
        print(f"\nSuccessfully caught invalid agent name error: {e}")
        assert "No internal prompt template found" in str(e)
