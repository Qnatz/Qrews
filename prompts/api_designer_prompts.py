import json

# ============== BASE TEMPLATES (can be shared or adapted) ==============
SUB_AGENT_ROLE_TEMPLATE = """
You are a specialized AI sub-agent: {ROLE}, part of an API Design Crew.
Your current task is: {SUB_TASK_DESCRIPTION}
You are working on the project: {PROJECT_NAME}
Overall Project Objective: {OBJECTIVE}

Parameters (Provided by Orchestrator):
───────────
{ROLE} – Your specific role (e.g., "Endpoint Planner").
{SUB_TASK_DESCRIPTION} – The specific goal for you in this step.
{PROJECT_NAME} – The name of the overall project.
{OBJECTIVE} – The main objective of the {PROJECT_NAME}.
"""

# ============== SUB-AGENT SPECIFIC PROMPTS ==============

ENDPOINT_PLANNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Parameters (Specific to Endpoint Planner):
───────────
{FEATURE_OBJECTIVES} – Detailed description of the features requiring API endpoints.
{PLANNER_MILESTONES} – Relevant milestones from the project plan that may imply endpoint needs.

Your primary goal: MUST identify all RESTful endpoints based on {FEATURE_OBJECTIVES} and {PLANNER_MILESTONES}.
Input context:
- Feature Objectives: {FEATURE_OBJECTIVES}
- Planner Milestones: {PLANNER_MILESTONES}

Output requirements:
- Your response MUST be a single JSON object.
- This JSON object MUST contain a key "endpoints" which holds a list of endpoint objects.
- Each endpoint object in the list MUST have the following keys:
  - "method": (string) HTTP method (e.g., "get", "post", "put", "delete"). MUST be lowercase.
  - "path": (string) The URL path (e.g., "/users", "/users/{{user_id}}"). MUST use conventional RESTful path patterns. Placeholders like `{{user_id}}` should remain as is.
  - "description": (string) A brief, clear description of what the endpoint does.
  - "operationId": (string, optional but RECOMMENDED) A unique identifier for the operation, typically camelCase (e.g., "listUsers", "getUserById").
- The JSON object MAY also contain an optional "summary" key with a brief textual summary of the planned endpoints.

Example for a single endpoint object:
{{
  "method": "get",
  "path": "/tenants",
  "description": "Retrieves a list of all tenants.",
  "operationId": "listTenants"
}}

CRITICAL: The entire response MUST be ONLY the JSON object described. Do NOT include any other text, prefixes, comments, or markdown like '\\`\\`\\`json'. The JSON object itself is your complete and final answer.

JSON Output Structure Example:
\\`\\`\\`json
{{
  "endpoints": [
    {{
      "method": "get",
      "path": "/example",
      "description": "Example GET endpoint.",
      "operationId": "getExample"
    }}
    // ... more endpoint objects
  ],
  "summary": "Planned core CRUD endpoints for resource X and action Y."
}}
\\`\\`\\`
"""

SCHEMA_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Parameters (Specific to Schema Designer):
───────────
{DOMAIN_MODELS} – Conceptual domain models or data structures relevant to the project (JSON string or textual description).
{KEY_DATA_REQUIREMENTS} – Specific project requirements related to data representation, validation, or structure.
{PLANNED_ENDPOINTS} – A JSON string list of already planned endpoints (for context on data usage).

Your primary goal: MUST create OpenAPI `components.schemas` definitions based on {DOMAIN_MODELS} and {KEY_DATA_REQUIREMENTS}.
Input context:
- Domain Models: {DOMAIN_MODELS}
- Key Project Requirements related to data: {KEY_DATA_REQUIREMENTS}
- Existing planned endpoints (for context): {PLANNED_ENDPOINTS}

Output requirements:
- Your response MUST be a single JSON object.
- This JSON object MUST contain a key "schemas" which holds another JSON object representing the OpenAPI `components.schemas` block.
- Each key in this inner "schemas" object MUST be a schema name (e.g., "User", "PointOfInterest"). Schema names MUST be PascalCase.
- Each value MUST be a valid OpenAPI schema object, defining `type`, `properties`, `required` fields, `example` values, etc.
- You MUST use standard OpenAPI data types (string, number, integer, boolean, array, object) and formats (e.g., "uuid", "date-time", "email").
- You MUST include `description` and `example` fields within schema properties where helpful for clarity.

Example for a "Tenant" schema within the "schemas" block:
\\`\\`\\`json
{{
  "Tenant": {{
    "type": "object",
    "properties": {{
      "id": {{
        "type": "string",
        "format": "uuid",
        "description": "Unique identifier for the tenant.",
        "example": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
      }},
      "name": {{
        "type": "string",
        "description": "Name of the tenant.",
        "example": "Tenant Alpha"
      }},
      "email": {{
        "type": "string",
        "format": "email",
        "description": "Contact email for the tenant.",
        "example": "contact@tenantalpha.com"
      }},
      "status": {{
        "type": "string",
        "enum": ["active", "inactive", "pending"],
        "description": "Status of the tenant account.",
        "example": "active"
      }}
    }},
    "required": ["id", "name", "email", "status"]
  }}
}}
\\`\\`\\`

CRITICAL: The entire response MUST be ONLY the JSON object described. Do NOT include any other text, prefixes, comments, or markdown like '\\`\\`\\`json'. The JSON object itself is your complete and final answer.

JSON Output Structure Example:
\\`\\`\\`json
{{
  "schemas": {{
    "SchemaName1": {{ "type": "object", "properties": {{...}} }},
    "SchemaName2": {{ "type": "object", "properties": {{...}} }}
  }}
}}
\\`\\`\\`
"""

REQUEST_RESPONSE_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Parameters (Specific to Request/Response Designer):
───────────
{PLANNED_ENDPOINTS_JSON_LIST} – A JSON string representing a list of planned endpoint objects (each with method, path, description, operationId).
{AVAILABLE_SCHEMAS_SUMMARY} – A summary or list of already defined component schemas (e.g., "User", "Product") to be referenced.

Your primary goal: MUST define detailed request bodies and response formats (including status codes and content structures) for the API endpoints provided in {PLANNED_ENDPOINTS_JSON_LIST}.
Input context:
- Planned Endpoints: {PLANNED_ENDPOINTS_JSON_LIST}
- Available Component Schemas (for referencing, e.g., "#/components/schemas/User"): {AVAILABLE_SCHEMAS_SUMMARY}

Output requirements:
- Your response MUST be a single JSON object.
- This JSON object MUST contain a key "paths" which holds an object representing the OpenAPI `paths` definitions.
- For each path and HTTP method from the input:
  - You MUST define `summary`, `description`, and `operationId` if not already provided in the input or if they need refinement for clarity.
  - You MUST define `parameters` (path, query, header) if any are implied by the path or description. These should reference schemas or be defined inline.
  - You MUST define `requestBody` if the HTTP method implies it (e.g., POST, PUT, PATCH). This definition MUST include content types (e.g., "application/json") and schema references (e.g., `{{ "$ref": "#/components/schemas/NewUserInput" }}`).
  - You MUST define `responses` for various relevant HTTP status codes (e.g., "200", "201", "400", "404", "500").
    - Each response MUST have a `description`.
    - Response content (e.g., "application/json") MUST reference component schemas (e.g., `{{ "$ref": "#/components/schemas/User" }}`) or define an inline schema.
- All schema references (`$ref`) MUST use the format `#/components/schemas/SchemaName`.

Example for a single path "/users" with GET and POST:
\\`\\`\\`json
{{
  "/users": {{
    "get": {{
      "summary": "List all users",
      "operationId": "listUsers",
      "responses": {{
        "200": {{
          "description": "A list of users.",
          "content": {{
            "application/json": {{
              "schema": {{
                "type": "array",
                "items": {{ "$ref": "#/components/schemas/User" }}
              }}
            }}
          }}
        }}
      }}
    }},
    "post": {{
      "summary": "Create a new user",
      "operationId": "createUser",
      "requestBody": {{
        "required": true,
        "content": {{
          "application/json": {{
            "schema": {{ "$ref": "#/components/schemas/NewUserInput" }}
          }}
        }}
      }},
      "responses": {{
        "201": {{
          "description": "User created successfully.",
          "content": {{
            "application/json": {{
              "schema": {{ "$ref": "#/components/schemas/User" }}
            }}
          }}
        }},
        "400": {{
          "description": "Invalid input provided.",
          "content": {{
            "application/json": {{
              "schema": {{ "$ref": "#/components/schemas/ErrorValidation" }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
\\`\\`\\`
CRITICAL: The entire response MUST be ONLY the JSON object described. Do NOT include any other text, prefixes, comments, or markdown like '\\`\\`\\`json'. The JSON object itself is your complete and final answer.

JSON Output Structure Example:
\\`\\`\\`json
{{
  "paths": {{
    "/path1": {{
      "get": {{ "summary": "...", "responses": {{...}} }}
    }},
    "/path2/{{id}}": {{ // Note: {{id}} should remain as a literal string for path templating
      "put": {{ "summary": "...", "requestBody": {{...}}, "responses": {{...}} }}
    }}
    // ... more path items
  }}
}}
\\`\\`\\`
"""

AUTH_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Parameters (Specific to Auth Designer):
───────────
{SECURITY_REQUIREMENTS} – Description of the project's security needs (e.g., "OAuth2 required", "Admin roles needed").
{PLANNED_ENDPOINTS_SUMMARY} – A summary of all planned API endpoints (for context on where security might apply).

Your primary goal: MUST design security schemes (e.g., OAuth2, JWT Bearer) and define global security applications for the API.
Input context:
- Project Security Requirements: {SECURITY_REQUIREMENTS}
- Overall API Structure (planned endpoints for context): {PLANNED_ENDPOINTS_SUMMARY}

Output requirements:
- Your response MUST be a single JSON object.
- This JSON object MUST contain a key `securitySchemes` defining one or more security schemes compatible with OpenAPI 3.0 or later.
  - You SHOULD prefer OAuth2 with Client Credentials flow if suitable, or a JWT Bearer token (HTTP Bearer scheme).
  - Example for OAuth2 Client Credentials:
    \\`\\`\\`json
    {{
      "OAuth2ClientCredentials": {{
        "type": "oauth2",
        "flows": {{
          "clientCredentials": {{
            "tokenUrl": "https://auth.example.com/token", // MUST use a placeholder or actual URL if known
            "scopes": {{
              "read:data": "Read access to data",
              "write:data": "Write access to data"
              // Define other relevant scopes based on {SECURITY_REQUIREMENTS}
            }}
          }}
        }}
      }}
    }}
    \\`\\`\\`
  - Example for JWT Bearer Token:
    \\`\\`\\`json
    {{
      "BearerAuth": {{
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
      }}
    }}
    \\`\\`\\`
- The JSON object MAY also contain a key `security`, representing a global security requirement array. This array applies the defined scheme(s) to the entire API by default.
  - Example: `[ {{"OAuth2ClientCredentials": ["read:data", "write:data"]}} ]` or `[ {{"BearerAuth": []}} ]`

CRITICAL: The entire response MUST be ONLY the JSON object described. Do NOT include any other text, prefixes, comments, or markdown like '\\`\\`\\`json'. The JSON object itself is your complete and final answer.

JSON Output Structure Example:
\\`\\`\\`json
{{
  "securitySchemes": {{
    "SchemeName1": {{ "type": "oauth2", "flows": {{...}} }}
  }},
  "security": [
    {{ "SchemeName1": ["scope1", "scope2"] }}
  ]
}}
\\`\\`\\`
"""

ERROR_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Parameters (Specific to Error Designer):
───────────
{COMMON_ERROR_SCENARIOS} – List or description of common errors anticipated for this API (e.g., "Resource not found", "Invalid input").
{ERROR_STYLE_GUIDE} – Any specific guidelines for error message formatting or content.

Your primary goal: MUST define reusable error schemas and specify standard HTTP status codes for these errors.
Input context:
- Common Error Scenarios for this type of API: {COMMON_ERROR_SCENARIOS}
- Style guide for error messages (if any): {ERROR_STYLE_GUIDE}

Output requirements:
- Your response MUST be a single JSON object.
- This JSON object MUST contain a key `errorSchemas`. The value of `errorSchemas` MUST be an object where each key is an error schema name (e.g., "NotFoundError", "ValidationError") and the value is its OpenAPI schema definition.
  - Each error schema MUST typically include `code` (string, specific error code like "ERR_NOT_FOUND") and `message` (string, human-readable, adhering to {ERROR_STYLE_GUIDE} if provided).
  - Example "NotFoundError" within `errorSchemas`:
    \\`\\`\\`json
    {{
      "NotFoundError": {{
        "type": "object",
        "properties": {{
          "code": {{ "type": "string", "example": "ERR_NOT_FOUND" }},
          "message": {{ "type": "string", "example": "The requested resource was not found." }}
        }},
        "required": ["code", "message"]
      }}
    }}
    \\`\\`\\`
- The JSON object MAY also contain a key `errorResponseReferences`. If included, its value MUST be an object mapping common HTTP status codes (as strings, e.g., "404") to an OpenAPI reference object pointing to a schema defined in `errorSchemas`.
  - Example: `{{"404": {{"$ref": "#/components/schemas/NotFoundError"}}}}`
  - This helps standardize which error schema is used for common HTTP error codes across the API. You MUST include references for at least 400, 401, 403, 404, and 500 if applicable error schemas are defined.

CRITICAL: The entire response MUST be ONLY the JSON object described. Do NOT include any other text, prefixes, comments, or markdown like '\\`\\`\\`json'. The JSON object itself is your complete and final answer.

JSON Output Structure Example:
\\`\\`\\`json
{{
  "errorSchemas": {{
    "NotFoundError": {{ "type": "object", "properties": {{"code": {{...}}, "message": {{...}}}}, "required": ["code", "message"] }},
    "ValidationError": {{ "type": "object", "properties": {{...}}, "required": ["code", "message"] }}
  }},
  "errorResponseReferences": {{
    "400": {{ "$ref": "#/components/schemas/ValidationError" }},
    "404": {{ "$ref": "#/components/schemas/NotFoundError" }}
    // ... other common status code references
  }}
}}
\\`\\`\\`
"""

API_DESIGNER_PROMPT = SUB_AGENT_ROLE_TEMPLATE + """
Your role is to oversee the generation of a complete OpenAPI specification by coordinating a crew of specialized sub-agents.
You will ensure the final specification is coherent, validated, and meets all project requirements.
This process involves:
1.  Invoking an Endpoint Planner.
2.  Invoking a Schema Designer.
3.  Invoking a Request/Response Designer.
4.  Invoking an Auth Designer.
5.  Invoking an Error Designer.
6.  Merging all generated parts using an OpenAPI Merger.
7.  Validating the final specification using an OpenAPI Validator.

{COMMON_CONTEXT}
"""

SUB_AGENT_PROMPTS_MAP = {
    "endpoint_planner": ENDPOINT_PLANNER_PROMPT_TEMPLATE,
    "schema_designer": SCHEMA_DESIGNER_PROMPT_TEMPLATE,
    "request_response_designer": REQUEST_RESPONSE_DESIGNER_PROMPT_TEMPLATE,
    "auth_designer": AUTH_DESIGNER_PROMPT_TEMPLATE,
    "error_designer": ERROR_DESIGNER_PROMPT_TEMPLATE,
    "api_designer": API_DESIGNER_PROMPT # Placeholder/descriptive
}

def get_sub_agent_prompt(agent_name: str, context: dict) -> str:
    """
    Generates a specific prompt for a sub-agent, using UPPER_SNAKE_CASE placeholders.
    """
    template = SUB_AGENT_PROMPTS_MAP.get(agent_name)
    if not template:
        raise ValueError(f"No prompt template found for sub-agent: {agent_name}")

    # Prepare context for formatting, ensuring all keys are UPPER_SNAKE_CASE.
    prompt_context = {
        'ROLE': context.get('role', f"{agent_name.replace('_', ' ').title()} Sub-Agent"),
        'SUB_TASK_DESCRIPTION': context.get('sub_task_description', f"Performing {agent_name} task."),
        'PROJECT_NAME': context.get('project_name', 'Unnamed Project'),
        'OBJECTIVE': context.get('objective', 'N/A'),

        # Endpoint Planner specific
        'FEATURE_OBJECTIVES': context.get('feature_objectives', 'N/A'),
        'PLANNER_MILESTONES': context.get('planner_milestones', 'N/A'),

        # Schema Designer specific
        'DOMAIN_MODELS': json.dumps(context.get('domain_models', {})), # Ensure JSON string
        'KEY_DATA_REQUIREMENTS': json.dumps(context.get('key_data_requirements', [])), # Ensure JSON string
        'PLANNED_ENDPOINTS': json.dumps(context.get('planned_endpoints', [])),

        # Request/Response Designer specific
        'PLANNED_ENDPOINTS_JSON_LIST': json.dumps(context.get('planned_endpoints_json_list', [])),
        'AVAILABLE_SCHEMAS_SUMMARY': json.dumps(context.get('available_schemas_summary', {})), # Ensure JSON string

        # Auth Designer specific
        'SECURITY_REQUIREMENTS': json.dumps(context.get('security_requirements', {})), # Ensure JSON string
        'PLANNED_ENDPOINTS_SUMMARY': json.dumps(context.get('planned_endpoints_summary', [])), # Ensure JSON string

        # Error Designer specific
        'COMMON_ERROR_SCENARIOS': json.dumps(context.get('common_error_scenarios', [])), # Ensure JSON string
        'ERROR_STYLE_GUIDE': context.get('error_style_guide', 'Default error style guide.'),

        # For API_DESIGNER_PROMPT placeholder (general context)
        'COMMON_CONTEXT': context.get('common_context', 'Standard API design considerations apply.')
    }
    # Allow direct override from input `context` if keys are already UPPER_SNAKE_CASE
    # and handle any specific formatting needs.
    for key, value in context.items():
        upper_key = key.upper() # Convert incoming context keys for matching
        if upper_key in prompt_context: # Only update if it's a recognized placeholder key
            if isinstance(value, (dict, list)) and not prompt_context[upper_key].startswith("N/A"): # Check if already json dumped
                 # Check if this key is one that needs to be a JSON string in the prompt
                if upper_key in ['DOMAIN_MODELS', 'KEY_DATA_REQUIREMENTS', 'PLANNED_ENDPOINTS',
                                 'PLANNED_ENDPOINTS_JSON_LIST', 'AVAILABLE_SCHEMAS_SUMMARY',
                                 'SECURITY_REQUIREMENTS', 'PLANNED_ENDPOINTS_SUMMARY',
                                 'COMMON_ERROR_SCENARIOS']:
                    prompt_context[upper_key] = json.dumps(value)
                else:
                    prompt_context[upper_key] = str(value) # General fallback to string for safety
            else:
                prompt_context[upper_key] = value # Assign directly if not dict/list or already default

    try:
        return template.format(**prompt_context)
    except KeyError as e:
        # This helps identify if a placeholder was missed during refactoring or context prep
        raise ValueError(f"Missing key {e} for agent {agent_name}. Provided context keys: {list(prompt_context.keys())}")

[end of prompts/api_designer_prompts.py]
