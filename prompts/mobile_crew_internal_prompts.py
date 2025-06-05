# mobile_developer_crew/crew_internal_prompts.py

# Prompts for individual sub-agents.
# These prompts should only expect keys that are directly passed into their
# sub-agent's `run` method and then into `prompt_input_data` by that `run` method.
# Common key expected in all prompt_input_data: `tech_stack_mobile`.

UI_STRUCTURE_DESIGNER_TEMPLATE = """
You are a UI Structure Designer.
Your task is to design the screen hierarchy, navigation graph, and UI flows for a mobile application.
Mobile Framework: {tech_stack_mobile}
Project Details: {project_details}
User Requirements: {user_requirements}

Based on the above, provide the screen-to-screen structure strictly in JSON format.
Include details about navigation paths and key UI elements on each screen.
Example:
{
  "screens": [
    {
      "name": "LoginScreen",
      "elements": ["email_field", "password_field", "login_button"],
      "navigation": { "onLoginSuccess": "HomeScreen" }
    },
    {
      "name": "HomeScreen",
      "elements": ["item_list", "profile_button"],
      "navigation": { "onProfileButton": "ProfileScreen" }
    }
  ],
  "entry_point": "LoginScreen"
}
"""

COMPONENT_DESIGNER_TEMPLATE = """
You are a Component Designer.
Your task is to break down screens (provided as UI structure JSON) into reusable UI components for a mobile application.
Mobile Framework: {tech_stack_mobile}
UI Structure (JSON): {ui_structure_json}

Output detailed specifications or code templates for components like buttons, cards, forms, lists that align with the UI structure and mobile framework.
Organize output by screen if appropriate.
Provide output strictly in JSON or structured text format.
Example for a component:
{
  "component_name": "PrimaryButton",
  "framework_equivalent": "Button (React Native Paper) or ElevatedButton (Flutter)",
  "properties": ["title (string)", "onPress (function)", "style (object)"],
  "usage_screens": ["LoginScreen", "SettingsScreen"]
}
"""

API_BINDER_TEMPLATE = """
You are an API Binder.
Your task is to define how frontend screens/components connect to API endpoints for a mobile application.
Mobile Framework: {tech_stack_mobile}
Component Designs/Needs: {component_designs} # Describes what data components need
API Specifications (OpenAPI JSON): {api_specifications}

Generate service classes, hooks, or data fetching logic (e.g., using Axios for React Native, or http/dio for Flutter) to connect the UI components to the provided API endpoints.
Focus on creating reusable data service layers.
Output the code for these services/hooks.
Example for a user service:
// Assuming {tech_stack_mobile} is React Native
import axios from 'axios';
const API_BASE_URL = 'https://api.example.com/v1'; // From api_specifications.servers[0].url

export const UserService = {
  getUser: async (userId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/users/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching user:', error);
      throw error;
    }
  }
};
"""

STATE_MANAGER_TEMPLATE = """
You are a State Manager.
Your task is to implement local state handling for screens/components of a mobile application.
Mobile Framework: {tech_stack_mobile}
Component Designs: {component_designs}
UI Structure (JSON): {ui_structure_json} # Optional, for context

Define state containers, stores, or providers (e.g., using React Context/Redux, Riverpod/Provider for Flutter) for managing UI state, user input, and data fetched from APIs.
Specify state shape and actions for each relevant component or screen.
Output code snippets or configuration for the state management setup.
Example for a settings screen state using React Context:
// Assuming {tech_stack_mobile} is React Native
import React, { createContext, useState, useContext } from 'react';

const SettingsContext = createContext();

export const SettingsProvider = ({ children }) => {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  // ... other settings ...
  return (
    <SettingsContext.Provider value={{ notificationsEnabled, setNotificationsEnabled }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => useContext(SettingsContext);
"""

FORM_VALIDATOR_TEMPLATE = """
You are a Form Validator.
Your task is to generate schema-based form validators for a mobile application.
Mobile Framework: {tech_stack_mobile}
Component Designs (specifically forms, with field names and types): {component_designs_with_forms}

For each form identified, generate validation logic or schemas (e.g., using Yup, Zod, or framework-specific validation methods).
Validators should cover common cases like required fields, data types (string, number, boolean), formats (email, phone), and custom rules if specified.
Output validation code or schemas.
Example for a login form schema using Yup:
// Assuming {tech_stack_mobile} is React Native and component_designs_with_forms describes a login form
import * as yup from 'yup';

export const loginValidationSchema = yup.object().shape({
  email: yup.string().email('Must be a valid email').required('Email is required'),
  password: yup.string().min(6, 'Password must be at least 6 characters').required('Password is required'),
});
"""

TEST_DESIGNER_TEMPLATE = """
You are a Test Designer.
Your task is to write test cases for UI and integration aspects of a mobile application.
Mobile Framework: {tech_stack_mobile}
UI Structure (JSON): {ui_structure_json}
Component Designs: {component_designs}
API Specifications (OpenAPI JSON): {api_specifications} # Optional, for integration tests

Write unit tests for components and integration tests for UI flows and API interactions (e.g., using Jest/React Testing Library, Flutter's widgetTest/integration_test).
Focus on key user paths and critical functionalities.
Output test case descriptions or actual test code.
Example for a component test:
// Assuming {tech_stack_mobile} is React Native and using Jest & React Testing Library
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
// import MyButton from '../components/MyButton'; // Assuming MyButton is a component from component_designs

describe('MyButton', () => {
  it('calls onPress when clicked', () => {
    const onPressMock = jest.fn();
    // const { getByText } = render(<MyButton title="Click Me" onPress={onPressMock} />);
    // fireEvent.press(getByText('Click Me'));
    // expect(onPressMock).toHaveBeenCalledTimes(1);
    expect(true).toBe(true); // Placeholder if MyButton is not actually available
  });
});
"""

# Note: mobile_merger is a system task, so it might not use an LLM prompt via invoker.
# If it did, its template would be here. For now, invoker.py handles it specially.


PROMPT_TEMPLATES = {
    "ui_structure_designer": UI_STRUCTURE_DESIGNER_TEMPLATE,
    "component_designer": COMPONENT_DESIGNER_TEMPLATE,
    "api_binder": API_BINDER_TEMPLATE,
    "state_manager": STATE_MANAGER_TEMPLATE,
    "form_validator": FORM_VALIDATOR_TEMPLATE,
    "test_designer": TEST_DESIGNER_TEMPLATE,
    # "mobile_merger": MOBILE_MERGER_TEMPLATE, # If it were LLM-based
}

def get_crew_internal_prompt(agent_name: str, prompt_input_data: dict) -> str:
    """
    Retrieves and formats the prompt for a given crew sub-agent.
    Args:
        agent_name (str): The name of the sub-agent.
        prompt_input_data (dict): Data to format the prompt with.
                                  Expected to contain keys like 'tech_stack_mobile'
                                  and other agent-specific keys.
    Returns:
        str: The formatted prompt.
    Raises:
        ValueError: If no template is found for the agent_name.
    """
    template = PROMPT_TEMPLATES.get(agent_name)
    if not template:
        # This case should ideally not be hit if agent_name is always valid
        raise ValueError(f"No internal prompt template found for crew agent: {agent_name}")

    try:
        return template.format(**prompt_input_data)
    except KeyError as e:
        # This error means the prompt_input_data was missing a key expected by the template
        raise ValueError(f"Missing key '{str(e)}' in prompt_input_data for agent '{agent_name}'. Provided data: {prompt_input_data.keys()}")
    except Exception as e_format:
        raise ValueError(f"Error formatting prompt for agent '{agent_name}': {str(e_format)}")


if __name__ == '__main__':
    # Example Usage
    print("--- Testing crew_internal_prompts.py ---")

    # UI Structure Designer Example
    ui_designer_input = {
        "tech_stack_mobile": "Flutter",
        "project_details": "A recipe sharing app.",
        "user_requirements": "Users can browse, search, and save recipes. They can also upload their own."
    }
    try:
        ui_prompt = get_crew_internal_prompt("ui_structure_designer", ui_designer_input)
        print("\n--- UI Structure Designer Prompt Example ---")
        # print(ui_prompt) # Can be very long
        print(f"Prompt for ui_structure_designer generated successfully. Starts with: '{ui_prompt[:100]}...'")
    except ValueError as e:
        print(f"Error generating UI designer prompt: {e}")

    # Component Designer Example
    cd_input = {
        "tech_stack_mobile": "SwiftUI",
        "ui_structure_json": "{ \"screen_name\": \"RecipeDetail\", \"elements\": [\"recipe_image\", \"ingredients_list\"] }"
    }
    try:
        cd_prompt = get_crew_internal_prompt("component_designer", cd_input)
        print("\n--- Component Designer Prompt Example ---")
        print(f"Prompt for component_designer generated successfully. Starts with: '{cd_prompt[:100]}...'")
    except ValueError as e:
        print(f"Error generating component designer prompt: {e}")

    # Test missing key
    broken_input = {
        "tech_stack_mobile": "React Native"
        # Missing "project_details" and "user_requirements" for ui_structure_designer
    }
    try:
        get_crew_internal_prompt("ui_structure_designer", broken_input)
    except ValueError as e:
        print(f"\nSuccessfully caught missing key error: {e}")

    # Test invalid agent name
    try:
        get_crew_internal_prompt("non_existent_agent", {})
    except ValueError as e:
        print(f"\nSuccessfully caught invalid agent name error: {e}")
