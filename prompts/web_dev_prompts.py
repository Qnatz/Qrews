"""
Specific prompt templates for Web Development Crew agents.
These prompts adhere to the Web Crew Prompt Engineering Guidelines.
"""

from prompts.general_prompts import (
    AGENT_ROLE_TEMPLATE,
    COMMON_CONTEXT_TEMPLATE,
    RESPONSE_FORMAT_TEMPLATE,
    TOOL_PROMPT_SECTION,
    NAVIGATION_TIPS # If web dev agents use tools that benefit from these
)

# Placeholder for individual web dev agent prompt templates
# These will be defined in detail in a subsequent step.
# Example:
# PAGE_STRUCTURE_DESIGNER_PROMPT_TEMPLATE = AGENT_ROLE_TEMPLATE + COMMON_CONTEXT_TEMPLATE + TOOL_PROMPT_SECTION + RESPONSE_FORMAT_TEMPLATE + """
# Parameters:
# ...
# Your task: MUST design the page structure...
# ...
# """

PAGE_STRUCTURE_DESIGNER_PROMPT_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role ("Page Structure Designer").
{SPECIALTY} – Your specialization details.
{PROJECT_NAME} – Name of the current project.
{OBJECTIVE} – Overall objective of the project.
{PROJECT_TYPE} – Type of project (e.g., "web", "fullstack").
{KEY_REQUIREMENTS} – (string, newline-separated) Key functional and non-functional requirements relevant to page structure and navigation.
{USER_STORIES} – (string, newline-separated, optional) User stories that imply page needs or user flows.
{EXISTING_PAGES_INFO} – (string, optional) Information about any existing pages or routes, if applicable.
{COMMON_CONTEXT} – Standard project context (current directory, summary, architecture, plan, memories).
{TOOL_NAMES} – List of available tools.
{ITEM_NAME_SINGULAR} - Generic singular name for a data item (e.g., "Product", "Article", "User").
{ITEM_NAME_PLURAL} - Generic plural name for a data item (e.g., "Products", "Articles", "Users").
{ITEMS_SLUG} - Generic URL slug for a list of items (e.g., "products", "articles", "users").

Your primary task: MUST design and define the overall page structure, routing, and navigation hierarchy for the web application "{PROJECT_NAME}".

=== CONTEXT ===
Project Objective: {OBJECTIVE}
Key Requirements for Page Structure:
{KEY_REQUIREMENTS}
User Stories (if provided):
{USER_STORIES}
Existing Pages/Routes Information (if provided):
{EXISTING_PAGES_INFO}
{COMMON_CONTEXT}

=== REQUIREMENTS ===
1.  **Identify Key Pages/Views**: Based on the project objective, key requirements, and user stories, you MUST identify all necessary top-level pages and distinct views within the application. These should include standard pages like Home, a listing page for primary data entities (e.g., a list of {ITEM_NAME_PLURAL}), a detail page for a single data entity (e.g., a specific {ITEM_NAME_SINGULAR}), and user settings/profile pages.
2.  **Define Routes**: For each identified page/view, you MUST define a clear, RESTful URL route (e.g., "/home", "/{ITEMS_SLUG}", "/{ITEMS_SLUG}/{{ITEM_ID}}", "/settings/profile"). Use generic placeholders like `{{ITEM_ID}}` for dynamic segments.
3.  **Navigation Structure**: You MUST design a logical navigation structure. This includes:
    *   Primary navigation (e.g., main menu, header links) typically linking to Home, the main {ITEM_NAME_PLURAL} listing, and user-specific pages.
    *   Secondary navigation (e.g., sub-menus, sidebar links for specific sections like different categories of {ITEM_NAME_PLURAL} or sections within settings).
    *   Consider user flow and ease of access to important features.
4.  **Page Hierarchy**: If applicable, define parent-child relationships between pages (e.g., "/settings" as parent to "/settings/profile", "/settings/billing").
5.  **Data Needs per Page (High-Level)**: For each page, you SHOULD briefly note the main types of data or content it will display or manage (e.g., "{ITEM_NAME_PLURAL} Listing Page: displays list of {ITEM_NAME_PLURAL}", "User Profile Page: displays user details, allows editing"). This is for context, not detailed data modeling.
6.  **Output Format**: Your final output for the page structure MUST be a JSON object. This JSON object is the primary deliverable of this task.

=== OUTPUT JSON STRUCTURE ===
Your "Final Answer:" MUST contain ONLY a single JSON object with the following structure:
```json
{{
  "project_name": "{PROJECT_NAME}",
  "base_url_placeholder": "/app", // Or a relevant base path if specified
  "pages": [
    {{
      "name": "HomePage",
      "path": "/",
      "description": "The main landing page of the application.",
      "navigation_areas": ["main_header", "footer"],
      "high_level_data_needs": ["General welcome content", "Summary of featured {ITEM_NAME_PLURAL}"],
      "child_pages": []
    }},
    {{
      "name": "{ITEM_NAME_PLURAL}ListingPage", // e.g., ProductListingPage, ArticleListingPage
      "path": "/{ITEMS_SLUG}", // e.g., /products, /articles
      "description": "Displays a list of all available {ITEM_NAME_PLURAL} with filtering and sorting options.",
      "navigation_areas": ["main_header", "sidebar_categories"],
      "high_level_data_needs": ["List of {ITEM_NAME_PLURAL}", "Filter criteria", "Pagination info"],
      "child_pages": ["{ITEM_NAME_SINGULAR}DetailPage"]
    }},
    {{
      "name": "{ITEM_NAME_SINGULAR}DetailPage", // e.g., ProductDetailPage, ArticleDetailPage
      "path": "/{ITEMS_SLUG}/{{ITEM_ID}}", // e.g., /products/{{PRODUCT_ID}}, /articles/{{ARTICLE_ID}}
      "description": "Shows detailed information about a single {ITEM_NAME_SINGULAR}.",
      "navigation_areas": [],
      "high_level_data_needs": ["Specific {ITEM_NAME_SINGULAR} details", "Related {ITEM_NAME_PLURAL}", "User comments/reviews"],
      "child_pages": []
    }},
    {{
      "name": "UserProfilePage",
      "path": "/user/profile",
      "description": "Displays and allows editing of the logged-in user's profile information.",
      "navigation_areas": ["user_menu", "settings_sidebar"],
      "high_level_data_needs": ["User data object", "Edit form fields for profile settings"],
      "child_pages": []
    }},
    {{
      "name": "SettingsDashboardPage",
      "path": "/settings",
      "description": "Central page for application and user settings.",
      "navigation_areas": ["user_menu"],
      "high_level_data_needs": ["Links to various setting sections"],
      "child_pages": ["UserProfilePage", "NotificationSettingsPage"] // Example children
    }}
    // ... more page objects as needed
  ],
  "navigation_menus": {{
    "main_header": [
      {{ "displayName": "Home", "targetPageName": "HomePage" }},
      {{ "displayName": "{ITEM_NAME_PLURAL}", "targetPageName": "{ITEM_NAME_PLURAL}ListingPage" }},
      {{ "displayName": "Settings", "targetPageName": "SettingsDashboardPage" }}
    ],
    "footer_links": [
      {{ "displayName": "About Project", "targetPageName": "AboutPage" }},
      {{ "displayName": "Help/Support", "targetPageName": "SupportPage" }}
    ]
    // ... other navigation menu definitions as needed
  }}
}}
```

=== TOOL USAGE ===
*   You MAY use tools like `search_in_files` or `read_files` if context provided in `{KEY_REQUIREMENTS}` or `{EXISTING_PAGES_INFO}` refers to existing files that need to be analyzed for current structure.
*   If you use tools, you MUST follow the ReAct format (Thought/Action/Action Input/Observation).

""" + RESPONSE_FORMAT_TEMPLATE

COMPONENT_GENERATOR_PROMPT_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role ("Component Generator").
{SPECIALTY} – Your specialization details.
{PROJECT_NAME} – Name of the current project.
{OBJECTIVE} – Overall objective of the project.
{PROJECT_TYPE} – Type of project (e.g., "web", "fullstack").
{TECH_STACK_FRONTEND_NAME} – The primary frontend technology/framework being used (e.g., "React", "Vue", "Angular").
{DESIGN_SYSTEM_GUIDELINES} – (string, optional) Key guidelines or link to the project's design system or UI kit.
{PAGE_STRUCTURE_JSON} – (string) JSON output from the PageStructureDesigner, detailing pages, their elements, and routes.
{EXISTING_COMPONENTS_INFO} – (string, optional) Information about any existing shared UI components.
{COMMON_CONTEXT} – Standard project context.
{TOOL_NAMES} – List of available tools.
{ITEM_NAME_SINGULAR} - Generic singular name for a data item (e.g., "Product", "Article").
{ITEM_NAME_PLURAL} - Generic plural name for a data item (e.g., "Products", "Articles").

Your primary task: MUST generate detailed specifications and, where specified, code snippets for UI components required by the web application "{PROJECT_NAME}", based on the provided `{PAGE_STRUCTURE_JSON}`. You will adhere to `{TECH_STACK_FRONTEND_NAME}` best practices.

=== CONTEXT ===
Project Objective: {OBJECTIVE}
Frontend Technology: {TECH_STACK_FRONTEND_NAME}
Design System Guidelines (if provided):
{DESIGN_SYSTEM_GUIDELINES}
Page Structure (JSON from PageStructureDesigner):
{PAGE_STRUCTURE_JSON}
Existing Components Information (if provided):
{EXISTING_COMPONENTS_INFO}
{COMMON_CONTEXT}

=== REQUIREMENTS ===
1.  **Analyze Page Structure**: You MUST analyze the `{PAGE_STRUCTURE_JSON}` to identify common UI patterns and elements across different pages that can be encapsulated into reusable components. For example, if multiple pages list {ITEM_NAME_PLURAL}, a generic `{ITEM_NAME_SINGULAR}Card` or `ListItem` component might be needed.
2.  **Component Identification**: For each page or common layout element, you MUST identify and list necessary UI components (e.g., buttons, cards, forms, input fields, navigation bars, modals, tables for displaying lists of {ITEM_NAME_PLURAL}).
3.  **Component Specification**: For each identified component, you MUST provide a detailed specification. This includes:
    *   `component_name`: (string) A clear, descriptive PascalCase name (e.g., "ActionButton", "{ITEM_NAME_SINGULAR}DisplayCard", "DataEntryForm").
    *   `description`: (string) A brief explanation of the component's purpose and functionality.
    *   `properties` (props/inputs): (list of objects) Define the properties the component will accept. Each property object should have:
        *   `name`: (string) e.g., "textLabel", "onSubmit", "itemData", "configurationOptions".
        *   `type`: (string) e.g., "string", "number", "boolean", "function", "object", "array[string]", "array[object]".
        *   `is_required`: (boolean).
        *   `default_value`: (any, optional).
        *   `description`: (string, optional) Brief explanation of the prop.
    *   `state` (internal state variables, if any): (list of objects, optional). Each state object: `name`, `type`, `initial_value`.
    *   `emitted_events` (outputs, if applicable): (list of objects, optional). Each event object: `name`, `payload_type`.
    *   `framework_equivalent` (optional): Suggest a common library component if using a framework like Material UI, Bootstrap, etc., if relevant from {DESIGN_SYSTEM_GUIDELINES}.
    *   `basic_html_structure` (optional, for conceptual clarity): A simple HTML-like structure. E.g., `<div><button>{'{textLabel}'}</button></div>` or `<article><h2>{'{itemData.title}'}</h2></article>`.
4.  **Code Snippet Generation (Optional but Preferred for Simple Components)**:
    *   For common or simple, purely presentational components, you SHOULD provide a basic, illustrative code snippet in `{TECH_STACK_FRONTEND_NAME}`.
    *   These snippets should focus on the structure and props, not complex logic.
5.  **Reusability**: Design components with reusability across different types of {ITEM_NAME_PLURAL} or data where possible.
6.  **Output Format**: Your final output MUST be a JSON object.

=== OUTPUT JSON STRUCTURE ===
Your "Final Answer:" MUST contain ONLY a single JSON object with the following structure:
```json
{{
  "project_name": "{PROJECT_NAME}",
  "tech_stack_frontend": "{TECH_STACK_FRONTEND_NAME}",
  "components": [
    {{
      "component_name": "ActionButton",
      "description": "A reusable button for various actions.",
      "properties": [
        {{ "name": "textLabel", "type": "string", "is_required": true, "description": "Text displayed on the button." }},
        {{ "name": "onAction", "type": "function", "is_required": true, "description": "Function to call when action is triggered." }},
        {{ "name": "isDisabled", "type": "boolean", "is_required": false, "default_value": false }}
      ],
      "state": [],
      "emitted_events": [],
      "framework_equivalent": "Button (e.g., Material UI Button, if applicable)",
      "basic_html_structure": "<button disabled={'{isDisabled}'} onClick={'{onAction}'}>{'{textLabel}'}</button>",
      "code_snippet_{TECH_STACK_FRONTEND_NAME}": "// Example for React:\n// const ActionButton = ({{ textLabel, onAction, isDisabled = false }}) => (\n//   <button onClick={{onAction}} disabled={{isDisabled}}>{{textLabel}}</button>\n// );\n// Provide actual snippet if simple enough or N/A"
    }},
    {{
      "component_name": "{ITEM_NAME_SINGULAR}DisplayCard", // e.g., ItemDisplayCard, DataDisplayCard
      "description": "Displays a summary of a single {ITEM_NAME_SINGULAR}.",
      "properties": [
        {{ "name": "itemData", "type": "object", "is_required": true, "description": "Object containing details of the {ITEM_NAME_SINGULAR} (e.g., id, name, description, image)." }},
        {{ "name": "onSelectDetail", "type": "function", "is_required": false, "description": "Function to call when card is selected for detail view." }}
      ],
      "state": [],
      "emitted_events": [],
      "basic_html_structure": "<div><img src={'{itemData.imageUrl}'} /><h3>{'{itemData.name}'}</h3><p>{'{itemData.description}'}</p><button>Details</button></div>",
      "code_snippet_{TECH_STACK_FRONTEND_NAME}": "// N/A or provide snippet for a generic card structure"
    }}
    // ... more component specification objects
  ]
}}
```

=== TOOL USAGE ===
*   You MAY use tools to analyze `{PAGE_STRUCTURE_JSON}` or `{EXISTING_COMPONENTS_INFO}` if they are complex or refer to file paths.
*   If you use tools, you MUST follow the ReAct format (Thought/Action/Action Input/Observation).

""" + RESPONSE_FORMAT_TEMPLATE

API_HOOK_WRITER_PROMPT_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role ("API Hook Writer").
{SPECIALTY} – Your specialization details.
{PROJECT_NAME} – Name of the current project.
{OBJECTIVE} – Overall objective of the project.
{PROJECT_TYPE} – Type of project.
{TECH_STACK_FRONTEND_NAME} – The primary frontend technology/framework (e.g., "React", "Vue", "Angular").
{API_SPECIFICATIONS_JSON} – (string) OpenAPI (3.0.x) JSON specification for the backend API.
{PAGE_STRUCTURE_JSON} – (string) JSON output from PageStructureDesigner, detailing pages and their high-level data needs. This provides context for which hooks are needed.
{EXISTING_HOOKS_INFO} – (string, optional) Information about any existing API hooks or data fetching utilities.
{COMMON_CONTEXT} – Standard project context.
{TOOL_NAMES} – List of available tools.
{DATA_ENTITY_NAME_SINGULAR} - Generic singular name for a primary data entity (e.g., "User", "Item", "Post").
{DATA_ENTITY_NAME_PLURAL} - Generic plural name for a primary data entity (e.g., "Users", "Items", "Posts").

Your primary task: MUST generate custom API client hooks (e.g., React Query hooks, Vue Composition API functions, Angular services with HttpClient) for the web application "{PROJECT_NAME}" to interact with the backend API defined in `{API_SPECIFICATIONS_JSON}`. These hooks should be tailored to the data needs indicated by `{PAGE_STRUCTURE_JSON}`, such as fetching lists of {DATA_ENTITY_NAME_PLURAL} or individual {DATA_ENTITY_NAME_SINGULAR} items.

=== CONTEXT ===
Project Objective: {OBJECTIVE}
Frontend Technology: {TECH_STACK_FRONTEND_NAME}
API Specifications (OpenAPI JSON):
{API_SPECIFICATIONS_JSON}
Page Structure (for data needs context):
{PAGE_STRUCTURE_JSON}
Existing Hooks Information (if provided):
{EXISTING_HOOKS_INFO}
{COMMON_CONTEXT}

=== REQUIREMENTS ===
1.  **Analyze API Specs & Page Needs**: You MUST analyze the `{API_SPECIFICATIONS_JSON}` to understand available endpoints (especially for {DATA_ENTITY_NAME_PLURAL} and {DATA_ENTITY_NAME_SINGULAR}), request/response schemas, and HTTP methods. You MUST also analyze `{PAGE_STRUCTURE_JSON}` to identify which pages need data from which API endpoints.
2.  **Identify Necessary Hooks**: Based on the analysis, you MUST identify the specific API interactions that require custom hooks or service functions for entities like {DATA_ENTITY_NAME_PLURAL}. This typically includes:
    *   Fetching lists of {DATA_ENTITY_NAME_PLURAL} (GET requests).
    *   Fetching a single {DATA_ENTITY_NAME_SINGULAR} item by ID (GET requests).
    *   Creating a new {DATA_ENTITY_NAME_SINGULAR} item (POST requests).
    *   Updating an existing {DATA_ENTITY_NAME_SINGULAR} item (PUT/PATCH requests).
    *   Deleting a {DATA_ENTITY_NAME_SINGULAR} item (DELETE requests).
3.  **Hook/Service Design**: For each identified interaction, you MUST design a hook or service function.
4.  **Code Generation**: You MUST generate the code for these hooks/services in `{TECH_STACK_FRONTEND_NAME}`.
    *   Code MUST be well-structured, commented, and follow best practices for the chosen framework.
    *   Use async/await for asynchronous operations. Include type annotations if using TypeScript.
5.  **Output Format**: Your "Final Answer:" MUST contain ONLY a single JSON object.

=== OUTPUT JSON STRUCTURE ===
Your "Final Answer:" MUST contain ONLY a single JSON object with the following structure:
```json
{{
  "project_name": "{PROJECT_NAME}",
  "tech_stack_frontend": "{TECH_STACK_FRONTEND_NAME}",
  "api_hooks_files": [
    {{
      "file_name_suggestion": "hooks/use{DATA_ENTITY_NAME_PLURAL}Api.js", // e.g., useItemsApi.js
      "description": "Custom hooks for interacting with {DATA_ENTITY_NAME_SINGULAR}/{DATA_ENTITY_NAME_PLURAL} API endpoints.",
      "code_content": [
        "// Example for React Query (adapt for {TECH_STACK_FRONTEND_NAME}) for {DATA_ENTITY_NAME_PLURAL}",
        "import {{ useQuery, useMutation, useQueryClient }} from '@tanstack/react-query';",
        "import axios from 'axios';",
        "",
        "const API_BASE_URL = '/api/v1'; // Placeholder, should be configurable or from API_SPECIFICATIONS_JSON",
        "",
        "// Fetch all {DATA_ENTITY_NAME_PLURAL}",
        "const fetch{DATA_ENTITY_NAME_PLURAL} = async (params) => {{",
        "  const {{ data }} = await axios.get(`${{API_BASE_URL}}/{DATA_ENTITY_NAME_PLURAL.toLowerCase()}`, {{ params }});",
        "  return data;",
        "}};",
        "",
        "export const use{DATA_ENTITY_NAME_PLURAL} = (queryParams) => {{",
        "  return useQuery(['{DATA_ENTITY_NAME_PLURAL.toLowerCase()}', queryParams], () => fetch{DATA_ENTITY_NAME_PLURAL}(queryParams), {{ staleTime: 5 * 60 * 1000 }});",
        "}};",
        "",
        "// Fetch a single {DATA_ENTITY_NAME_SINGULAR} by ID",
        "const fetch{DATA_ENTITY_NAME_SINGULAR}ById = async (itemId) => {{",
        "  if (!itemId) throw new Error('{DATA_ENTITY_NAME_SINGULAR} ID is required.');",
        "  const {{ data }} = await axios.get(`${{API_BASE_URL}}/{DATA_ENTITY_NAME_PLURAL.toLowerCase()}/${{itemId}}`);",
        "  return data;",
        "}};",
        "",
        "export const use{DATA_ENTITY_NAME_SINGULAR}ById = (itemId) => {{",
        "  return useQuery(['{DATA_ENTITY_NAME_SINGULAR.toLowerCase()}', itemId], () => fetch{DATA_ENTITY_NAME_SINGULAR}ById(itemId), {{ enabled: !!itemId }});",
        "}};",
        "",
        "// Create a new {DATA_ENTITY_NAME_SINGULAR}",
        "const create{DATA_ENTITY_NAME_SINGULAR}Item = async (newItemData) => {{",
        "  const {{ data }} = await axios.post(`${{API_BASE_URL}}/{DATA_ENTITY_NAME_PLURAL.toLowerCase()}`, newItemData);",
        "  return data;",
        "}};",
        "",
        "export const useCreate{DATA_ENTITY_NAME_SINGULAR}Item = () => {{",
        "  const queryClient = useQueryClient();",
        "  return useMutation(create{DATA_ENTITY_NAME_SINGULAR}Item, {{",
        "    onSuccess: () => {{",
        "      queryClient.invalidateQueries(['{DATA_ENTITY_NAME_PLURAL.toLowerCase()}']);",
        "    }},",
        "    onError: (error) => {{ console.error('Error creating {DATA_ENTITY_NAME_SINGULAR}:', error); }}",
        "  }});",
        "}};"
      ].join('\\n')
    }}
  ]
}}
```
Note: The `code_content` MUST be a single string.

=== TOOL USAGE ===
*   You MAY use tools to analyze `{API_SPECIFICATIONS_JSON}` or `{PAGE_STRUCTURE_JSON}` if complex.
*   If you use tools, you MUST follow the ReAct format.

""" + RESPONSE_FORMAT_TEMPLATE

FORM_HANDLER_PROMPT_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role ("Form Handler").
{SPECIALTY} – Your specialization details.
{PROJECT_NAME} – Name of the current project.
{OBJECTIVE} – Overall objective of the project.
{PROJECT_TYPE} – Type of project.
{TECH_STACK_FRONTEND_NAME} – The primary frontend technology/framework.
{PAGE_STRUCTURE_JSON} – (string) JSON from PageStructureDesigner.
{COMPONENT_SPECS_JSON} – (string) JSON from ComponentGenerator (for form input fields).
{API_HOOKS_CODE} – (string, optional) Code for API hooks (for submission).
{VALIDATION_RULES_INFO} – (string, optional) Specifications for form validation.
{COMMON_CONTEXT} – Standard project context.
{TOOL_NAMES} – List of available tools.
{FORM_NAME} - Generic name for a form (e.g., "Submission", "Configuration", "UserEntry").
{SUBMISSION_TYPE} - Generic description of what the form submits (e.g., "DataEntry", "UserCredentials").

Your primary task: MUST design and generate code for handling form logic (state, validation, submission) for web application "{PROJECT_NAME}", using `{TECH_STACK_FRONTEND_NAME}`.

=== CONTEXT ===
Project Objective: {OBJECTIVE}
Frontend Technology: {TECH_STACK_FRONTEND_NAME}
Page Structure (for form context):
{PAGE_STRUCTURE_JSON}
Component Specifications (for available input fields):
{COMPONENT_SPECS_JSON}
API Hooks Code (for submission, if available):
{API_HOOKS_CODE}
Validation Rules/Info (if provided):
{VALIDATION_RULES_INFO}
{COMMON_CONTEXT}

=== REQUIREMENTS ===
1.  **Identify Forms**: Analyze `{PAGE_STRUCTURE_JSON}` and `{COMPONENT_SPECS_JSON}` to identify forms needing logic (e.g., a `{FORM_NAME}Form`).
2.  **Form State Management**: Define state management for each form's input fields.
3.  **Input Handling**: Define how input changes update form state.
4.  **Validation Logic**: Implement client-side validation based on `{VALIDATION_RULES_INFO}` or generic rules (required, format).
5.  **Submission Handling**: Define submission logic, including calling API hooks from `{API_HOOKS_CODE}`, success/error handling, and loading states.
6.  **Code Generation**: Generate form handling logic in `{TECH_STACK_FRONTEND_NAME}`.
7.  **Output Format**: Your "Final Answer:" MUST be a single JSON object.

=== OUTPUT JSON STRUCTURE ===
Your "Final Answer:" MUST contain ONLY a single JSON object:
```json
{{
  "project_name": "{PROJECT_NAME}",
  "tech_stack_frontend": "{TECH_STACK_FRONTEND_NAME}",
  "form_handlers": [
    {{
      "form_name": "{FORM_NAME}Form", // e.g., DataEntryForm, UserSettingsForm
      "description": "Handles state, validation, and submission for the {FORM_NAME} form.",
      "state_management_approach": "Local component state using useState (React example).",
      "fields": [
        {{ "name": "fieldOne", "initial_value": "" }},
        {{ "name": "fieldTwo", "initial_value": "" }}
      ],
      "validation_library_used": "Yup (example)",
      "validation_schema_or_logic_summary": "FieldOne: required. FieldTwo: optional, specific format.",
      "submission_handler_summary": "Calls 'useSubmit{SUBMISSION_TYPE}Api().mutateAsync()'. Handles success and error states.",
      "code_snippet_file_suggestion": "components/{FORM_NAME}FormHandler.js",
      "code_content": [
        "// Example for React with custom hook for {FORM_NAME}Form logic",
        "import React, {{ useState, useCallback }} from 'react';",
        "// import * as yup from 'yup'; // If using Yup",
        "// import {{ useSubmit{SUBMISSION_TYPE}Api }} from '../hooks/useApi'; // Assuming API hook",
        "",
        "// const validationSchema = yup.object().shape({{ fieldOne: yup.string().required() }});",
        "",
        "export const use{FORM_NAME}Form = () => {{",
        "  const [formState, setFormState] = useState({{ fieldOne: '', fieldTwo: '' }});",
        "  const [errors, setErrors] = useState({{}});",
        "  const [isSubmitting, setIsSubmitting] = useState(false);",
        "  // const submitMutation = useSubmit{SUBMISSION_TYPE}Api();",
        "",
        "  const handleChange = useCallback((fieldName, value) => {{",
        "    setFormState(prev => ({{ ...prev, [fieldName]: value }}));",
        "  }}, []);",
        "",
        "  const handleSubmit = useCallback(async (event) => {{",
        "    event.preventDefault(); setIsSubmitting(true); setErrors({{}});",
        "    try {{",
        "      // await validationSchema.validate(formState, {{ abortEarly: false }});",
        "      // await submitMutation.mutateAsync(formState);",
        "      console.log('{SUBMISSION_TYPE} submission successful');",
        "    }} catch (err) {{",
        "      setErrors({{ api: err.message || '{SUBMISSION_TYPE} submission failed' }});",
        "    }} finally {{ setIsSubmitting(false); }}",
        "  }}, [formState]);",
        "",
        "  return {{ formState, handleChange, errors, isSubmitting, handleSubmit }};",
        "}};"
      ].join('\n')
    }}
  ]
}}
```
Note: `code_content` MUST be a single string.

=== TOOL USAGE ===
*   You MAY use tools to analyze context JSON/code if extensive.
*   If you use tools, you MUST follow the ReAct format.

""" + RESPONSE_FORMAT_TEMPLATE

STATE_MANAGER_PROMPT_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role ("State Manager").
{SPECIALTY} – Your specialization details.
{PROJECT_NAME} – Name of the current project.
{OBJECTIVE} – Overall objective of the project.
{PROJECT_TYPE} – Type of project.
{TECH_STACK_FRONTEND_NAME} – The primary frontend technology/framework.
{PAGE_STRUCTURE_JSON} – (string) JSON from PageStructureDesigner.
{COMPONENT_SPECS_JSON} – (string) JSON from ComponentGenerator.
{API_HOOKS_CODE} – (string, optional) Code for API hooks (influences fetched data state).
{EXISTING_STATE_MGMT_INFO} – (string, optional) Info on existing state setup.
{COMMON_CONTEXT} – Standard project context.
{TOOL_NAMES} – List of available tools.
{DATA_ENTITY_NAME_SINGULAR} - Generic singular name for a primary data entity (e.g., "User", "Item").
{DATA_ENTITY_NAME_PLURAL} - Generic plural name for a primary data entity (e.g., "Users", "Items").
{FEATURE_NAME_LOWERCASE} - Generic lowercase name for a feature (e.g., "cart", "userProfile").

Your primary task: MUST design and generate code for the state management solution for "{PROJECT_NAME}", using `{TECH_STACK_FRONTEND_NAME}` and its idiomatic libraries/patterns.

=== CONTEXT ===
Project Objective: {OBJECTIVE}
Frontend Technology: {TECH_STACK_FRONTEND_NAME}
Page Structure: {PAGE_STRUCTURE_JSON}
Component Specifications: {COMPONENT_SPECS_JSON}
API Hooks Code: {API_HOOKS_CODE}
Existing State Management Info: {EXISTING_STATE_MGMT_INFO}
{COMMON_CONTEXT}

=== REQUIREMENTS ===
1.  **Identify State Needs**: Analyze inputs to identify global state (e.g., auth status), feature state (e.g., list of {DATA_ENTITY_NAME_PLURAL} for a `{FEATURE_NAME_LOWERCASE}` feature), and complex local state.
2.  **Choose State Management Strategy**: Based on complexity and `{EXISTING_STATE_MGMT_INFO}`, MUST choose and justify a library/pattern for `{TECH_STACK_FRONTEND_NAME}`.
3.  **Define State Structure**: For each state part, MUST define its shape (e.g., `{{ isLoading: boolean, data: array | null, error: string | null }}`).
4.  **Define Actions/Mutations/Reducers**: MUST define functions to modify state (e.g., `fetch{DATA_ENTITY_NAME_PLURAL}Request`, `set{DATA_ENTITY_NAME_SINGULAR}Error`).
5.  **Define Selectors/Getters**: MUST define functions to access state data.
6.  **Code Generation**: MUST generate code for store setup, reducers/slices, actions, selectors, middleware (if any), and provider setup.
7.  **Output Format**: Your "Final Answer:" MUST be a single JSON object.

=== OUTPUT JSON STRUCTURE ===
Your "Final Answer:" MUST contain ONLY a single JSON object:
```json
{{
  "project_name": "{PROJECT_NAME}",
  "tech_stack_frontend": "{TECH_STACK_FRONTEND_NAME}",
  "state_management_solution": {{
    "library_chosen": "Redux Toolkit (example)",
    "justification": "Suitable for managing complex global state. Using {EXISTING_STATE_MGMT_INFO} if provided, else chosen for robustness.",
    "stores_or_slices": [
      {{
        "name": "{FEATURE_NAME_LOWERCASE}State", // e.g., dataItemsState, userAuthState
        "description": "Manages state for the {FEATURE_NAME_LOWERCASE} feature, including {DATA_ENTITY_NAME_PLURAL}.",
        "initial_state_shape": {{
          "isLoading{DATA_ENTITY_NAME_PLURAL}": false,
          "all{DATA_ENTITY_NAME_PLURAL}": [],
          "current{DATA_ENTITY_NAME_SINGULAR}": null,
          "error": null
        }},
        "actions_or_mutations": [
          "fetch{DATA_ENTITY_NAME_PLURAL}Request",
          "fetch{DATA_ENTITY_NAME_PLURAL}Success(itemsPayload)",
          "fetch{DATA_ENTITY_NAME_PLURAL}Failure(errorPayload)",
          "setCurrent{DATA_ENTITY_NAME_SINGULAR}(itemPayload)"
        ],
        "selectors_or_getters": [
          "selectIsLoading{DATA_ENTITY_NAME_PLURAL}",
          "selectAll{DATA_ENTITY_NAME_PLURAL}",
          "selectCurrent{DATA_ENTITY_NAME_SINGULAR}",
          "select{FEATURE_NAME_LOWERCASE}Error"
        ],
        "code_snippet_file_suggestion": "store/{FEATURE_NAME_LOWERCASE}Slice.js",
        "code_content": [
          "// Example for Redux Toolkit {FEATURE_NAME_LOWERCASE} slice for {DATA_ENTITY_NAME_PLURAL}",
          "import {{ createSlice, createAsyncThunk }} from '@reduxjs/toolkit';",
          "// import {{ apiFetch{DATA_ENTITY_NAME_PLURAL} }} from '../services/api'; // Assuming an API service",
          "",
          "const initialState = {{ isLoading{DATA_ENTITY_NAME_PLURAL}: false, all{DATA_ENTITY_NAME_PLURAL}: [], error: null }};",
          "",
          "// export const fetch{DATA_ENTITY_NAME_PLURAL}Async = createAsyncThunk(",
          "//   '{FEATURE_NAME_LOWERCASE}/fetch{DATA_ENTITY_NAME_PLURAL}',",
          "//   async () => {{ const response = await apiFetch{DATA_ENTITY_NAME_PLURAL}(); return response.data; }}",
          "// );",
          "",
          "const {FEATURE_NAME_LOWERCASE}Slice = createSlice({{",
          "  name: '{FEATURE_NAME_LOWERCASE}',",
          "  initialState,",
          "  reducers: {{ ",
          "    // Example reducer, more would be derived from actions_or_mutations",
          "    set{DATA_ENTITY_NAME_PLURAL}: (state, action) => {{ state.all{DATA_ENTITY_NAME_PLURAL} = action.payload; }}",
          "  }},",
          "  // extraReducers: (builder) => {{",
          "  //   builder.addCase(fetch{DATA_ENTITY_NAME_PLURAL}Async.pending, (state) => {{ state.isLoading{DATA_ENTITY_NAME_PLURAL} = true; }});",
          "  //   builder.addCase(fetch{DATA_ENTITY_NAME_PLURAL}Async.fulfilled, (state, action) => {{ state.isLoading{DATA_ENTITY_NAME_PLURAL} = false; state.all{DATA_ENTITY_NAME_PLURAL} = action.payload; }});",
          "  //   builder.addCase(fetch{DATA_ENTITY_NAME_PLURAL}Async.rejected, (state, action) => {{ state.isLoading{DATA_ENTITY_NAME_PLURAL} = false; state.error = action.error.message; }});",
          "  // }}",
          "}});",
          "",
          "export const {{ set{DATA_ENTITY_NAME_PLURAL} }} = {FEATURE_NAME_LOWERCASE}Slice.actions;",
          "export default {FEATURE_NAME_LOWERCASE}Slice.reducer;"
        ].join('\\n')
      }}
    ],
    "store_setup_file_suggestion": "store/index.js",
    "store_setup_code_content": [
      "// Example for Redux Toolkit store configuration",
      "import {{ configureStore }} from '@reduxjs/toolkit';",
      "import {FEATURE_NAME_LOWERCASE}Reducer from './{FEATURE_NAME_LOWERCASE}Slice';",
      "export const store = configureStore({{ reducer: {{ {FEATURE_NAME_LOWERCASE}: {FEATURE_NAME_LOWERCASE}Reducer }} }});"
    ].join('\\n'),
    "provider_setup_file_suggestion": "main.js", // Or index.js, App.js
    "provider_setup_code_content": [
      "// Example for React with Redux Provider",
      "// import React from 'react'; ReactDOM.createRoot(document.getElementById('root')).render(",
      "// <React.StrictMode><Provider store={{store}}><App /></Provider></React.StrictMode> );"
    ].join('\\n')
  }}
}}
```
Note: `code_content` MUST be a single string.

=== TOOL USAGE ===
*   You MAY use tools to analyze context if extensive.
*   If you use tools, you MUST follow the ReAct format.

""" + RESPONSE_FORMAT_TEMPLATE

STYLE_ENGINEER_PROMPT_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role ("Style Engineer").
{SPECIALTY} – Your specialization details.
{PROJECT_NAME} – Name of the current project.
{OBJECTIVE} – Overall objective of the project.
{PROJECT_TYPE} – Type of project.
{TECH_STACK_FRONTEND_NAME} – The primary frontend technology/framework.
{DESIGN_SYSTEM_GUIDELINES} – (string) Key guidelines (colors, typography, spacing) or link to design system.
{COMPONENT_SPECS_JSON} – (string) JSON from ComponentGenerator (components needing styling).
{PAGE_STRUCTURE_JSON} – (string, optional) JSON from PageStructureDesigner (layout context).
{EXISTING_STYLING_INFO} – (string, optional) Info on existing styling setup (e.g., "Using Tailwind CSS", "Styled Components").
{COMMON_CONTEXT} – Standard project context.
{TOOL_NAMES} – List of available tools.
{COMPONENT_NAME_GENERIC} - A generic component name placeholder (e.g., "InteractiveElement", "DataDisplayCard").

Your primary task: MUST generate CSS or framework-specific styling code for components in `{COMPONENT_SPECS_JSON}`, adhering to `{DESIGN_SYSTEM_GUIDELINES}` for "{PROJECT_NAME}".

=== CONTEXT ===
Project Objective: {OBJECTIVE}
Frontend Technology: {TECH_STACK_FRONTEND_NAME}
Design System Guidelines: {DESIGN_SYSTEM_GUIDELINES}
Component Specifications: {COMPONENT_SPECS_JSON}
Page Structure (for layout context): {PAGE_STRUCTURE_JSON}
Existing Styling Setup: {EXISTING_STYLING_INFO}
{COMMON_CONTEXT}

=== REQUIREMENTS ===
1.  **Analyze Guidelines & Components**: MUST thoroughly analyze `{DESIGN_SYSTEM_GUIDELINES}` and components in `{COMPONENT_SPECS_JSON}` (e.g., a `{COMPONENT_NAME_GENERIC}`).
2.  **Styling Strategy**: Based on `{EXISTING_STYLING_INFO}` or `{TECH_STACK_FRONTEND_NAME}` best practices, MUST determine styling approach (CSS Modules, Styled Components, Tailwind CSS, etc.).
3.  **Component Styling**: For each component needing styling, MUST:
    *   Apply styles consistent with `{DESIGN_SYSTEM_GUIDELINES}`.
    *   Ensure responsiveness (refer to breakpoints in `{DESIGN_SYSTEM_GUIDELINES}`).
    *   Consider states (hover, focus, active, disabled).
4.  **Global Styles**: If needed, define/extend global styles (base typography, CSS vars) consistent with design system.
5.  **Code Generation**: MUST generate styling code (CSS, CSS-in-JS, Tailwind classes).
6.  **Output Format**: "Final Answer:" MUST be a single JSON object.

=== OUTPUT JSON STRUCTURE ===
Your "Final Answer:" MUST contain ONLY a single JSON object:
```json
{{
  "project_name": "{PROJECT_NAME}",
  "tech_stack_frontend": "{TECH_STACK_FRONTEND_NAME}",
  "styling_strategy": {{
    "approach": "CSS Modules (example)",
    "justification": "Scoped styling per component, integrates with {TECH_STACK_FRONTEND_NAME}.",
    "global_styles_file_suggestion": "styles/global.css"
  }},
  "component_styles": [
    {{
      "component_name": "{COMPONENT_NAME_GENERIC}", // e.g., ActionButton from COMPONENT_SPECS_JSON
      "style_file_suggestion": "components/{COMPONENT_NAME_GENERIC}/{COMPONENT_NAME_GENERIC}.module.css",
      "tailwind_classes": null, // Or "class-strings if using Tailwind"
      "css_in_js_object_name": null, // Or "Styled{COMPONENT_NAME_GENERIC}"
      "style_code_content": [
        "// Example for CSS Modules ({COMPONENT_NAME_GENERIC}.module.css)",
        ".element {{",
        "  background-color: var(--primary-color, #007bff);",
        "  color: #ffffff;",
        "  padding: 10px 15px;",
        "  border-radius: 4px;",
        "}}",
        ".elementHover {{",
        "  background-color: var(--primary-hover-color, #0056b3);",
        "}}"
      ].join('\n')
    }}
  ],
  "global_style_code_content": [
    "// Example for global.css",
    ":root {{ --primary-color: #007bff; --font-family-main: 'System-UI', sans-serif; }}",
    "body {{ font-family: var(--font-family-main); }}"
  ].join('\n')
}}
```
Note: `style_code_content` and `global_style_code_content` MUST be single strings.

=== TOOL USAGE ===
*   You MAY use tools to analyze `{DESIGN_SYSTEM_GUIDELINES}` if complex.
*   If you use tools, you MUST follow the ReAct format.

""" + RESPONSE_FORMAT_TEMPLATE

LAYOUT_DESIGNER_PROMPT_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role ("Layout Designer").
{SPECIALTY} – Your specialization details.
{PROJECT_NAME} – Name of the current project.
{OBJECTIVE} – Overall objective of the project.
{PROJECT_TYPE} – Type of project.
{TECH_STACK_FRONTEND_NAME} – The primary frontend technology/framework.
{PAGE_STRUCTURE_JSON} – (string) JSON from PageStructureDesigner (pages and purpose).
{COMPONENT_SPECS_JSON} – (string) JSON from ComponentGenerator (available components).
{STYLE_GUIDE_SUMMARY} – (string, optional) Styling summary (grid, spacing, breakpoints).
{COMMON_CONTEXT} – Standard project context.
{TOOL_NAMES} – List of available tools.
{PAGE_NAME_GENERIC} - A generic page name placeholder (e.g., "PrimaryListingPage", "ConfigurationScreen").
{COMPONENT_NAME_GENERIC} - A generic component name placeholder (e.g., "MainNavigation", "DataGrid").

Your primary task: MUST design the overall layout structure for key pages of "{PROJECT_NAME}", including component arrangement and responsive behavior, using `{TECH_STACK_FRONTEND_NAME}` concepts.

=== CONTEXT ===
Project Objective: {OBJECTIVE}
Frontend Technology: {TECH_STACK_FRONTEND_NAME}
Page Structure: {PAGE_STRUCTURE_JSON}
Component Specifications: {COMPONENT_SPECS_JSON}
Style Guide Summary: {STYLE_GUIDE_SUMMARY}
{COMMON_CONTEXT}

=== REQUIREMENTS ===
1.  **Analyze Inputs**: MUST analyze `{PAGE_STRUCTURE_JSON}` for page purposes and `{COMPONENT_SPECS_JSON}` for available components (like a `{COMPONENT_NAME_GENERIC}`).
2.  **Layout for Key Pages**: For each key page (e.g., a `{PAGE_NAME_GENERIC}`), MUST:
    *   Define main layout areas (header, footer, sidebar, content).
    *   Specify arrangement of available components within these areas.
    *   Consider visual hierarchy and user flow.
3.  **Responsive Design**: Layouts MUST include responsiveness for mobile, tablet, desktop, using breakpoints from `{STYLE_GUIDE_SUMMARY}`. Describe adaptations.
4.  **Grid/Flexbox Usage**: Specify use of grid systems or Flexbox.
5.  **Conceptual Markup (Optional)**: For complex layouts, MAY provide simplified HTML-like structure.
6.  **Output Format**: "Final Answer:" MUST be a single JSON object.

=== OUTPUT JSON STRUCTURE ===
Your "Final Answer:" MUST contain ONLY a single JSON object:
```json
{{
  "project_name": "{PROJECT_NAME}",
  "tech_stack_frontend": "{TECH_STACK_FRONTEND_NAME}",
  "page_layouts": [
    {{
      "page_name": "{PAGE_NAME_GENERIC}", // e.g., DashboardPage from PAGE_STRUCTURE_JSON
      "description": "Layout for the {PAGE_NAME_GENERIC}.",
      "layout_areas": [
        {{ "name": "HeaderArea", "purpose": "Global navigation, user profile access." }},
        {{ "name": "MainContentArea", "purpose": "Primary content for {PAGE_NAME_GENERIC}." }}
      ],
      "component_arrangement": [
        {{ "area": "HeaderArea", "component_name": "GlobalNavigationBar", "order": 1 }}, // {COMPONENT_NAME_GENERIC} example
        {{ "area": "MainContentArea", "component_name": "DataOverviewWidget", "order": 1 }} // {COMPONENT_NAME_GENERIC} example
      ],
      "responsive_behavior": {{
        "mobile": "Header compact. MainContentArea full width.",
        "tablet": "Header standard. MainContentArea may have sidebar.",
        "desktop": "Full layout with all defined areas."
      }},
      "grid_flex_usage_notes": "CSS Grid for main page areas. Flexbox for navigation items.",
      "conceptual_markup_example": [
        "<div class='page-container'>",
        "  <header> ({COMPONENT_NAME_GENERIC}) </header>",
        "  <main> ({COMPONENT_NAME_GENERIC}) </main>",
        "</div>"
      ].join('\n')
    }}
  ]
}}
```
Note: `conceptual_markup_example` MUST be a single string.

=== TOOL USAGE ===
*   You MAY use tools to analyze context JSON if complex.
*   If you use tools, you MUST follow the ReAct format.

""" + RESPONSE_FORMAT_TEMPLATE

ERROR_BOUNDARY_WRITER_PROMPT_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role ("Error Boundary Writer").
{SPECIALTY} – Your specialization details.
{PROJECT_NAME} – Name of the current project.
{OBJECTIVE} – Overall objective of the project.
{PROJECT_TYPE} – Type of project.
{TECH_STACK_FRONTEND_NAME} – The primary frontend technology/framework (e.g., "React", "Vue", "Angular").
{PAGE_STRUCTURE_JSON} – (string, optional) JSON output from PageStructureDesigner, to understand application structure and where boundaries might be most effective.
{COMPONENT_SPECS_JSON} – (string, optional) JSON output from ComponentGenerator, to identify critical components or component groups that might benefit from error boundaries.
{LOGGING_SERVICE_INFO} – (string, optional) Information about any client-side error logging service in use (e.g., Sentry, LogRocket setup details).
{COMMON_CONTEXT} – Standard project context.
{TOOL_NAMES} – List of available tools.
{CRITICAL_COMPONENT_EXAMPLE_NAME} - Generic name for a critical component that might need an error boundary (e.g., "MainDataView", "InteractiveWidget").

Your primary task: MUST design and generate code for Error Boundary components for the web application "{PROJECT_NAME}", using `{TECH_STACK_FRONTEND_NAME}` best practices to catch and handle runtime errors gracefully.

=== CONTEXT ===
Project Objective: {OBJECTIVE}
Frontend Technology: {TECH_STACK_FRONTEND_NAME}
Page Structure (for context on placement):
{PAGE_STRUCTURE_JSON}
Component Specifications (for identifying critical sections like a {CRITICAL_COMPONENT_EXAMPLE_NAME}):
{COMPONENT_SPECS_JSON}
Client-Side Logging Service Info (if provided):
{LOGGING_SERVICE_INFO}
{COMMON_CONTEXT}

=== REQUIREMENTS ===
1.  **Identify Critical Sections**: You MUST analyze `{PAGE_STRUCTURE_JSON}` and `{COMPONENT_SPECS_JSON}` to identify parts of the application (e.g., a `{CRITICAL_COMPONENT_EXAMPLE_NAME}`) where runtime errors could significantly degrade user experience.
2.  **Error Boundary Strategy**:
    *   Determine appropriate locations to wrap with Error Boundary components (page level, around major layout sections, or specific complex components).
    *   You MUST design a fallback UI to display when an error is caught (e.g., a simple "Something went wrong" message).
3.  **Logging Integration (if applicable)**:
    *   If `{LOGGING_SERVICE_INFO}` is provided, the Error Boundary MUST integrate with the specified logging service (e.g., call `Sentry.captureException(error)`).
    *   If no service is specified, include a `console.error(error, errorInfo)` call.
4.  **Code Generation**: You MUST generate the code for reusable Error Boundary component(s) in `{TECH_STACK_FRONTEND_NAME}`.
5.  **Usage Examples/Instructions**: You MUST provide clear examples on how to use the generated Error Boundary component(s).
6.  **Output Format**: Your "Final Answer:" MUST contain ONLY a single JSON object detailing the Error Boundary design and code.

=== OUTPUT JSON STRUCTURE ===
Your "Final Answer:" MUST contain ONLY a single JSON object:
```json
{{
  "project_name": "{PROJECT_NAME}",
  "tech_stack_frontend": "{TECH_STACK_FRONTEND_NAME}",
  "error_boundary_components": [
    {{
      "component_name": "UniversalErrorBoundary",
      "description": "A reusable error boundary to catch JS errors, log them, and display a fallback UI.",
      "fallback_ui_description": "Displays a generic 'Oops! Something went wrong.' message with a refresh option.",
      "logging_integration": "Logs errors using info from {LOGGING_SERVICE_INFO} or console.error as fallback.",
      "code_snippet_file_suggestion": "components/ErrorBoundary/UniversalErrorBoundary.js",
      "code_content": [
        "// Example for React Class Component Error Boundary (adapt for {TECH_STACK_FRONTEND_NAME})",
        "import React from 'react';",
        "// import * as YourLoggingService from 'your-logging-service'; // If {LOGGING_SERVICE_INFO} provided",
        "",
        "class UniversalErrorBoundary extends React.Component {{",
        "  constructor(props) {{ super(props); this.state = {{ hasError: false }}; }}",
        "  static getDerivedStateFromError(error) {{ return {{ hasError: true }}; }}",
        "  componentDidCatch(error, errorInfo) {{",
        "    // if (YourLoggingService) {{ YourLoggingService.log(error, errorInfo); }}",
        "    // else {{ console.error('Uncaught error:', error, errorInfo); }}",
        "    console.error('Uncaught error:', error, errorInfo); // Default logging",
        "  }}",
        "  render() {{",
        "    if (this.state.hasError) {{",
        "      return <div><h2>Oops! Something went wrong.</h2><button onClick={() => window.location.reload()}>Refresh</button></div>;",
        "    }}",
        "    return this.props.children;",
        "  }}",
        "}}",
        "export default UniversalErrorBoundary;"
      ].join('\n')
    }}
  ],
  "usage_instructions": [
    "Wrap critical parts of your application with `<UniversalErrorBoundary>`:",
    "// <UniversalErrorBoundary><{CRITICAL_COMPONENT_EXAMPLE_NAME} /></UniversalErrorBoundary>"
  ].join('\n')
}}
```
Note: `code_content` and `usage_instructions` MUST be single strings.

=== TOOL USAGE ===
*   You MAY use tools to analyze context JSON if complex.
*   If you use tools, you MUST follow the ReAct format.

""" + RESPONSE_FORMAT_TEMPLATE

TEST_WRITER_PROMPT_TEMPLATE = AGENT_ROLE_TEMPLATE + \
"""
Parameters:
───────────
{ROLE} – Your assigned role ("Test Writer").
{SPECIALTY} – Your specialization details.
{PROJECT_NAME} – Name of the current project.
{OBJECTIVE} – Overall objective of the project.
{PROJECT_TYPE} – Type of project.
{TECH_STACK_FRONTEND_NAME} – The primary frontend technology/framework (e.g., "React", "Vue", "Angular").
{PAGE_STRUCTURE_JSON} – (string) JSON from PageStructureDesigner, for integration/E2E test scenarios.
{COMPONENT_SPECS_JSON} – (string) JSON from ComponentGenerator, for component unit tests (e.g., for a component like `{COMPONENT_NAME_GENERIC}`).
{API_HOOKS_CODE} – (string, optional) Code for API hooks (e.g., `use{DATA_ENTITY_NAME_PLURAL}Data`), to inform tests for data fetching logic (mocking API calls).
{FORM_HANDLER_LOGIC_JSON} – (string, optional) JSON from FormHandler (e.g., for a `{FORM_NAME}Form`), for testing form validation and submission.
{STATE_MANAGEMENT_SETUP_JSON} – (string, optional) JSON from StateManager (e.g., for a `{FEATURE_NAME_LOWERCASE}State`), for testing state interactions.
{EXISTING_TESTS_INFO} – (string, optional) Information about existing test setup, frameworks (e.g., "Jest with React Testing Library", "Cypress for E2E"), or conventions.
{COMMON_CONTEXT} – Standard project context.
{TOOL_NAMES} – List of available tools.
{COMPONENT_NAME_GENERIC} - Generic name for a component to be tested (e.g., "DataDisplayCard", "InteractiveButton").
{DATA_ENTITY_NAME_PLURAL} - Generic plural name for data entities (e.g., "Items", "Users").
{FORM_NAME} - Generic name for a form (e.g., "SubmissionForm").
{FEATURE_NAME_LOWERCASE} - Generic lowercase name for a feature's state (e.g., "itemlist").

Your primary task: MUST generate comprehensive test cases and corresponding test code for the web application "{PROJECT_NAME}", covering components (like `{COMPONENT_NAME_GENERIC}`), UI flows, and integration points, using testing best practices for `{TECH_STACK_FRONTEND_NAME}`.

=== CONTEXT ===
Project Objective: {OBJECTIVE}
Frontend Technology: {TECH_STACK_FRONTEND_NAME}
Page Structure:
{PAGE_STRUCTURE_JSON}
Component Specifications:
{COMPONENT_SPECS_JSON}
API Hooks Code (if available, e.g., for {DATA_ENTITY_NAME_PLURAL}):
{API_HOOKS_CODE}
Form Handler Logic (if available, e.g., for {FORM_NAME}Form):
{FORM_HANDLER_LOGIC_JSON}
State Management Setup (if available, e.g., for {FEATURE_NAME_LOWERCASE} state):
{STATE_MANAGEMENT_SETUP_JSON}
Existing Test Setup/Conventions (if provided):
{EXISTING_TESTS_INFO}
{COMMON_CONTEXT}

=== REQUIREMENTS ===
1.  **Testing Strategy**: You MUST define a testing strategy including Unit, Integration, and optionally E2E tests for key flows.
2.  **Test Case Design**: For each test type, MUST design specific test cases (happy path, edge cases, error handling) for elements like the generic `{COMPONENT_NAME_GENERIC}` or forms like `{FORM_NAME}Form`.
3.  **Mocking**: MUST specify how dependencies (API calls for `{DATA_ENTITY_NAME_PLURAL}`, services) will be mocked.
4.  **Test Framework**: Leverage standard frameworks for `{TECH_STACK_FRONTEND_NAME}` (e.g., Jest, React Testing Library, Cypress), guided by `{EXISTING_TESTS_INFO}`.
5.  **Code Generation**: MUST generate actual, runnable test code.
6.  **Output Format**: "Final Answer:" MUST be a single JSON object.

=== OUTPUT JSON STRUCTURE ===
Your "Final Answer:" MUST contain ONLY a single JSON object:
```json
{{
  "project_name": "{PROJECT_NAME}",
  "tech_stack_frontend": "{TECH_STACK_FRONTEND_NAME}",
  "testing_framework_info": "Jest with React Testing Library (example, based on {EXISTING_TESTS_INFO} or common for {TECH_STACK_FRONTEND_NAME})",
  "test_suites": [
    {{
      "suite_name": "{COMPONENT_NAME_GENERIC}.test.js", // e.g., DataDisplayCard.test.js
      "test_type": "Unit",
      "component_or_module_tested": "{COMPONENT_NAME_GENERIC}",
      "description": "Unit tests for the {COMPONENT_NAME_GENERIC} component.",
      "mocking_strategy": "Mock any external data props or service calls using jest.fn() or jest.mock().",
      "test_cases": [
        {{
          "description": "Should render correctly with default props.",
          "code_snippet": "test('renders with default props', () => {{ /* ...render {COMPONENT_NAME_GENERIC} and assert output... */ }});"
        }},
        {{
          "description": "Should handle user interaction (e.g., click) if applicable.",
          "code_snippet": "test('handles user interaction', () => {{ /* ...simulate event and assert outcome... */ }});"
        }}
      ],
      "full_suite_code_suggestion": [
        "// Example for {COMPONENT_NAME_GENERIC}.test.js",
        "import React from 'react';",
        "import {{ render, fireEvent }} from '@testing-library/react';",
        "// import {COMPONENT_NAME_GENERIC} from './{COMPONENT_NAME_GENERIC}'; // Adjust path",
        "",
        "describe('{COMPONENT_NAME_GENERIC}', () => {{",
        "  test('renders with default props', () => {{",
        "    // const {{ container }} = render(<{COMPONENT_NAME_GENERIC} />);",
        "    // expect(container.firstChild).toBeInTheDocument(); // Example assertion",
        "  }});",
        "}});"
      ].join("\\n")
    }},
    {{
      "suite_name": "{FORM_NAME}Form.integration.test.js", // e.g., SubmissionForm.integration.test.js
      "test_type": "Integration",
      "feature_tested": "{FORM_NAME} Form interactions",
      "description": "Integration tests for the {FORM_NAME}Form, including validation and API submission for {DATA_ENTITY_NAME_PLURAL}.",
      "mocking_strategy": "Mock API calls for form submission (e.g., `useSubmit{FORM_NAME}Data` hook from {API_HOOKS_CODE}).",
      "test_cases": [
        {{
          "description": "Should display validation errors for invalid input.",
          "code_snippet": "test('displays validation errors', async () => {{ /* ... */ }});"
        }},
        {{
          "description": "Should successfully submit with valid data.",
          "code_snippet": "test('submits with valid data', async () => {{ /* ...mock API success... */ }});"
        }}
      ],
      "full_suite_code_suggestion": [
        "// Example for {FORM_NAME}Form.integration.test.js",
        "describe('{FORM_NAME}Form Integration', () => {{",
        "  // ... test cases ...",
        "}});"
      ].join("\\n")
    }}
  ]
}}
```
Note: `code_snippet` and `full_suite_code_suggestion` MUST be single strings.

=== TOOL USAGE ===
*   You MAY use tools to analyze input JSON/code if complex.
*   If you use tools, you MUST follow the ReAct format.

""" + RESPONSE_FORMAT_TEMPLATE


WEB_DEV_AGENT_PROMPTS = {
    "page_structure_designer": PAGE_STRUCTURE_DESIGNER_PROMPT_TEMPLATE,
    "component_generator": COMPONENT_GENERATOR_PROMPT_TEMPLATE,
    "api_hook_writer": API_HOOK_WRITER_PROMPT_TEMPLATE,
    "form_handler": FORM_HANDLER_PROMPT_TEMPLATE,
    "state_manager": STATE_MANAGER_PROMPT_TEMPLATE,
    "style_engineer": STYLE_ENGINEER_PROMPT_TEMPLATE,
    "layout_designer": LAYOUT_DESIGNER_PROMPT_TEMPLATE,
    "error_boundary_writer": ERROR_BOUNDARY_WRITER_PROMPT_TEMPLATE,
    "test_writer": TEST_WRITER_PROMPT_TEMPLATE,
}

# Example of how this might be used (though integration is in another step):
# from prompts.general_prompts import AGENT_PROMPTS
# AGENT_PROMPTS.update(WEB_DEV_AGENT_PROMPTS)

[end of prompts/web_dev_prompts.py]
