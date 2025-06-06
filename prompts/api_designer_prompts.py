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
{RESOURCE_NAME_SLUG} – Generic slug for resource names in URLs (e.g., "data-items", "generic-entries").
{RESOURCE_NAME_PASCALCASE_PLURAL} – Generic PascalCase plural for resource names (e.g., "DataItems", "GenericEntries").

Your primary goal: MUST identify all RESTful endpoints based on {FEATURE_OBJECTIVES} and {PLANNER_MILESTONES}.
Input context:
- Feature Objectives: {FEATURE_OBJECTIVES}
- Planner Milestones: {PLANNER_MILESTONES}

Output requirements:
- Your response MUST be a single JSON object.
- This JSON object MUST contain a key "endpoints" which holds a list of endpoint objects.
- Each endpoint object in the list MUST have the following keys:
  - "method": (string) HTTP method (e.g., "get", "post", "put", "delete"). MUST be lowercase.
  - "path": (string) The URL path (e.g., "/{RESOURCE_NAME_SLUG}", "/{RESOURCE_NAME_SLUG}/{{item_id}}"). Use conventional RESTful path patterns. Placeholders like `{{item_id}}` should remain as is.
  - "description": (string) A brief, clear description of what the endpoint does (e.g., "Retrieves a list of all {RESOURCE_NAME_PLURAL}.").
  - "operationId": (string, optional but RECOMMENDED) A unique identifier for the operation, typically camelCase (e.g., "list{RESOURCE_NAME_PASCALCASE_PLURAL}", "get{RESOURCE_NAME_PASCALCASE_SINGULAR}ById").
- The JSON object MAY also contain an optional "summary" key with a brief textual summary of the planned endpoints.

Example for a single endpoint object:
{{
  "method": "get",
  "path": "/{RESOURCE_NAME_SLUG}",
  "description": "Retrieves a list of all {RESOURCE_NAME_PLURAL}.",
  "operationId": "list{RESOURCE_NAME_PASCALCASE_PLURAL}"
}}

CRITICAL: The entire response MUST be ONLY the JSON object described. Do NOT include any other text, prefixes, comments, or markdown like '\\`\\`\\`json'. The JSON object itself is your complete and final answer.

JSON Output Structure Example:
\\`\\`\\`json
{{
  "endpoints": [
    {{
      "method": "get",
      "path": "/{RESOURCE_NAME_SLUG}",
      "description": "Retrieves all {RESOURCE_NAME_PLURAL}.",
      "operationId": "list{RESOURCE_NAME_PASCALCASE_PLURAL}"
    }},
    {{
      "method": "post",
      "path": "/{RESOURCE_NAME_SLUG}",
      "description": "Creates a new {RESOURCE_NAME_SINGULAR}.",
      "operationId": "create{RESOURCE_NAME_PASCALCASE_SINGULAR}"
    }}
    // ... more endpoint objects
  ],
  "summary": "Planned CRUD endpoints for {RESOURCE_NAME_PLURAL}."
}}
\\`\\`\\`
"""

SCHEMA_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Parameters (Specific to Schema Designer):
───────────
{DOMAIN_MODELS} – Conceptual domain models or data structures relevant to the project (JSON string or textual description).
{KEY_DATA_REQUIREMENTS} – Specific project requirements related to data representation, validation, or structure.
{PLANNED_ENDPOINTS} – A JSON string list of already planned endpoints (for context on data usage).
{DATA_MODEL_NAME} – Generic PascalCase name for a data model (e.g., "GenericDataStructure", "StandardEntity").
{RESOURCE_NAME_PASCALCASE_SINGULAR} - Generic PascalCase singular for resource names (e.g., "Item", "Entry").

Your primary goal: MUST create OpenAPI `components.schemas` definitions based on {DOMAIN_MODELS} and {KEY_DATA_REQUIREMENTS}.
Input context:
- Domain Models: {DOMAIN_MODELS}
- Key Project Requirements related to data: {KEY_DATA_REQUIREMENTS}
- Existing planned endpoints (for context): {PLANNED_ENDPOINTS}

Output requirements:
- Your response MUST be a single JSON object.
- This JSON object MUST contain a key "schemas" which holds another JSON object representing the OpenAPI `components.schemas` block.
- Each key in this inner "schemas" object MUST be a schema name (e.g., "{DATA_MODEL_NAME}", "{RESOURCE_NAME_PASCALCASE_SINGULAR}Input", "{RESOURCE_NAME_PASCALCASE_SINGULAR}Output"). Schema names MUST be PascalCase.
- Each value MUST be a valid OpenAPI schema object, defining `type`, `properties`, `required` fields, `example` values, etc.
- You MUST use standard OpenAPI data types (string, number, integer, boolean, array, object) and formats (e.g., "uuid", "date-time", "email").
- You MUST include `description` and `example` fields within schema properties where helpful for clarity.

Example for a "{DATA_MODEL_NAME}" schema within the "schemas" block:
\\`\\`\\`json
{{
  "{DATA_MODEL_NAME}": {{
    "type": "object",
    "properties": {{
      "id": {{
        "type": "string",
        "format": "uuid",
        "description": "Unique identifier for the {DATA_MODEL_NAME}.",
        "example": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
      }},
      "name": {{
        "type": "string",
        "description": "Name or title of the {DATA_MODEL_NAME}.",
        "example": "Sample {DATA_MODEL_NAME} Name"
      }},
      "description": {{
        "type": "string",
        "description": "Detailed description.",
        "example": "This is a sample description for the {DATA_MODEL_NAME}."
      }},
      "status": {{
        "type": "string",
        "enum": ["active", "inactive", "pending_review"],
        "description": "Status of the {DATA_MODEL_NAME}.",
        "example": "active"
      }}
    }},
    "required": ["id", "name", "status"]
  }}
}}
\\`\\`\\`

CRITICAL: The entire response MUST be ONLY the JSON object described. Do NOT include any other text, prefixes, comments, or markdown like '\\`\\`\\`json'. The JSON object itself is your complete and final answer.

JSON Output Structure Example:
\\`\\`\\`json
{{
  "schemas": {{
    "{DATA_MODEL_NAME}": {{ "type": "object", "properties": {{ "id": {{"type": "string", "format": "uuid"}}, "name": {{"type": "string"}} }} }},
    "{RESOURCE_NAME_PASCALCASE_SINGULAR}Input": {{ "type": "object", "properties": {{ "name": {{"type": "string"}} }} }}
  }}
}}
\\`\\`\\`
"""

REQUEST_RESPONSE_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Parameters (Specific to Request/Response Designer):
───────────
{PLANNED_ENDPOINTS_JSON_LIST} – A JSON string representing a list of planned endpoint objects (each with method, path, description, operationId).
{AVAILABLE_SCHEMAS_SUMMARY} – A summary or list of already defined component schemas (e.g., "{DATA_MODEL_NAME}", "{RESOURCE_NAME_PASCALCASE_SINGULAR}Input") to be referenced.
{RESOURCE_NAME_SLUG} – Generic slug for resource names in URLs.
{RESOURCE_NAME_PASCALCASE_SINGULAR} – Generic PascalCase singular for resource names.
{RESOURCE_NAME_PASCALCASE_PLURAL} – Generic PascalCase plural for resource names.
{DATA_MODEL_NAME} – Generic PascalCase name for a data model.

Your primary goal: MUST define detailed request bodies and response formats (including status codes and content structures) for the API endpoints provided in {PLANNED_ENDPOINTS_JSON_LIST}.
Input context:
- Planned Endpoints: {PLANNED_ENDPOINTS_JSON_LIST}
- Available Component Schemas (for referencing, e.g., "#/components/schemas/{DATA_MODEL_NAME}"): {AVAILABLE_SCHEMAS_SUMMARY}

Output requirements:
- Your response MUST be a single JSON object.
- This JSON object MUST contain a key "paths" which holds an object representing the OpenAPI `paths` definitions.
- For each path and HTTP method from the input:
  - You MUST define `summary`, `description`, and `operationId` (e.g. "list{RESOURCE_NAME_PASCALCASE_PLURAL}", "create{RESOURCE_NAME_PASCALCASE_SINGULAR}") if not already provided or if they need refinement for clarity.
  - You MUST define `parameters` (path, query, header) if any are implied by the path or description. These should reference schemas or be defined inline.
  - You MUST define `requestBody` if the HTTP method implies it (e.g., POST, PUT, PATCH). This definition MUST include content types (e.g., "application/json") and schema references (e.g., `{{ "$ref": "#/components/schemas/{RESOURCE_NAME_PASCALCASE_SINGULAR}Input" }}`).
  - You MUST define `responses` for various relevant HTTP status codes (e.g., "200", "201", "400", "404", "500").
    - Each response MUST have a `description`.
    - Response content (e.g., "application/json") MUST reference component schemas (e.g., `{{ "$ref": "#/components/schemas/{DATA_MODEL_NAME}" }}`) or define an inline schema.
- All schema references (`$ref`) MUST use the format `#/components/schemas/SchemaName`.

Example for a single path "/{RESOURCE_NAME_SLUG}" with GET and POST:
\\`\\`\\`json
{{
  "/{RESOURCE_NAME_SLUG}": {{
    "get": {{
      "summary": "List all {RESOURCE_NAME_PLURAL}",
      "operationId": "list{RESOURCE_NAME_PASCALCASE_PLURAL}",
      "responses": {{
        "200": {{
          "description": "A list of {RESOURCE_NAME_PLURAL}.",
          "content": {{
            "application/json": {{
              "schema": {{
                "type": "array",
                "items": {{ "$ref": "#/components/schemas/{DATA_MODEL_NAME}" }}
              }}
            }}
          }}
        }}
      }}
    }},
    "post": {{
      "summary": "Create a new {RESOURCE_NAME_SINGULAR}",
      "operationId": "create{RESOURCE_NAME_PASCALCASE_SINGULAR}",
      "requestBody": {{
        "required": true,
        "content": {{
          "application/json": {{
            "schema": {{ "$ref": "#/components/schemas/{RESOURCE_NAME_PASCALCASE_SINGULAR}Input" }}
          }}
        }}
      }},
      "responses": {{
        "201": {{
          "description": "{RESOURCE_NAME_SINGULAR} created successfully.",
          "content": {{
            "application/json": {{
              "schema": {{ "$ref": "#/components/schemas/{DATA_MODEL_NAME}" }}
            }}
          }}
        }},
        "400": {{
          "description": "Invalid input provided.",
          "content": {{
            "application/json": {{
              "schema": {{ "$ref": "#/components/schemas/ValidationError" }} // Assuming generic error schema
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
    "/{RESOURCE_NAME_SLUG}": {{
      "get": {{ "summary": "List {RESOURCE_NAME_PLURAL}", "responses": {{...}} }}
    }},
    "/{RESOURCE_NAME_SLUG}/{{item_id}}": {{
      "put": {{ "summary": "Update a {RESOURCE_NAME_SINGULAR}", "requestBody": {{...}}, "responses": {{...}} }}
    }}
  }}
}}
\\`\\`\\`
"""

AUTH_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Parameters (Specific to Auth Designer):
───────────
{SECURITY_REQUIREMENTS} – Description of the project's security needs (e.g., "OAuth2 required", "Admin roles needed").
{PLANNED_ENDPOINTS_SUMMARY} – A summary of all planned API endpoints (for context on where security might apply).
{SCOPE_NOUN} – Generic noun for defining security scopes (e.g., "data", "resource", "entity").
{SCOPE_ACTION} – Generic action for defining security scopes (e.g., "read", "write", "manage").

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
              "{SCOPE_NOUN}:{SCOPE_ACTION}": "Allows {SCOPE_ACTION} access to {SCOPE_NOUN}.",
              "admin:{SCOPE_NOUN}:manage": "Allows full management of {SCOPE_NOUN}."
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
  - Example: `[ {{"OAuth2ClientCredentials": ["{SCOPE_NOUN}:{SCOPE_ACTION}"]}} ]` or `[ {{"BearerAuth": []}} ]`

CRITICAL: The entire response MUST be ONLY the JSON object described. Do NOT include any other text, prefixes, comments, or markdown like '\\`\\`\\`json'. The JSON object itself is your complete and final answer.

JSON Output Structure Example:
\\`\\`\\`json
{{
  "securitySchemes": {{
    "DefaultAuthScheme": {{ "type": "http", "scheme": "bearer", "bearerFormat": "JWT" }}
  }},
  "security": [
    {{ "DefaultAuthScheme": [] }}
  ]
}}
\\`\\`\\`
"""

ERROR_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Parameters (Specific to Error Designer):
───────────
{COMMON_ERROR_SCENARIOS} – List or description of common errors anticipated for this API (e.g., "Resource not found", "Invalid input", "Unauthorized access").
{ERROR_STYLE_GUIDE} – Any specific guidelines for error message formatting or content.

Your primary goal: MUST define reusable error schemas and specify standard HTTP status codes for these errors.
Input context:
- Common Error Scenarios for this type of API: {COMMON_ERROR_SCENARIOS}
- Style guide for error messages (if any): {ERROR_STYLE_GUIDE}

Output requirements:
- Your response MUST be a single JSON object.
- This JSON object MUST contain a key `errorSchemas`. The value of `errorSchemas` MUST be an object where each key is an error schema name (e.g., "NotFoundError", "GenericValidationError", "AuthenticationError") and the value is its OpenAPI schema definition.
  - Each error schema MUST typically include `code` (string, specific error code like "ERR_RESOURCE_NOT_FOUND") and `message` (string, human-readable, adhering to {ERROR_STYLE_GUIDE} if provided).
  - Example "GenericNotFoundError" within `errorSchemas`:
    \\`\\`\\`json
    {{
      "GenericNotFoundError": {{
        "type": "object",
        "properties": {{
          "code": {{ "type": "string", "example": "ERR_NOT_FOUND" }},
          "message": {{ "type": "string", "example": "The requested item or resource was not found." }}
        }},
        "required": ["code", "message"]
      }}
    }}
    \\`\\`\\`
- The JSON object MAY also contain a key `errorResponseReferences`. If included, its value MUST be an object mapping common HTTP status codes (as strings, e.g., "404") to an OpenAPI reference object pointing to a schema defined in `errorSchemas`.
  - Example: `{{"404": {{"$ref": "#/components/schemas/GenericNotFoundError"}}}}`
  - You MUST include references for at least 400, 401, 403, 404, and 500 if applicable error schemas are defined.

CRITICAL: The entire response MUST be ONLY the JSON object described. Do NOT include any other text, prefixes, comments, or markdown like '\\`\\`\\`json'. The JSON object itself is your complete and final answer.

JSON Output Structure Example:
\\`\\`\\`json
{{
  "errorSchemas": {{
    "StandardNotFoundError": {{ "type": "object", "properties": {{"code": {{"type": "string", "example": "E_NOT_FOUND"}}, "message": {{ "type": "string"}}}}, "required": ["code", "message"] }},
    "StandardValidationError": {{ "type": "object", "properties": {{...}}, "required": ["code", "message", "details"] }}
  }},
  "errorResponseReferences": {{
    "400": {{ "$ref": "#/components/schemas/StandardValidationError" }},
    "401": {{ "$ref": "#/components/schemas/AuthenticationError" }}, // Assuming AuthenticationError is defined
    "404": {{ "$ref": "#/components/schemas/StandardNotFoundError" }}
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
    "api_designer": API_DESIGNER_PROMPT
}

def get_sub_agent_prompt(agent_name: str, context: dict) -> str:
    """
    Generates a specific prompt for a sub-agent.
    Args:
        agent_name (str): The name of the sub-agent.
        context (dict): Data to format the prompt with.
                        Expected to contain `UPPER_SNAKE_CASE` keys.
    Returns:
        str: The formatted prompt.
    Raises:
        ValueError: If no template is found for the agent_name or if a key is missing.
    """
    template = SUB_AGENT_PROMPTS_MAP.get(agent_name)
    if not template:
        raise ValueError(f"No prompt template found for sub-agent: {agent_name}")

    prompt_context = {
        # Base placeholders expected by SUB_AGENT_ROLE_TEMPLATE
        'ROLE': context.get('ROLE', f"{agent_name.replace('_', ' ').title()} Sub-Agent"),
        'SUB_TASK_DESCRIPTION': context.get('SUB_TASK_DESCRIPTION', f"Performing {agent_name} task."),
        'PROJECT_NAME': context.get('PROJECT_NAME', 'Unnamed Project'),
        'OBJECTIVE': context.get('OBJECTIVE', 'N/A'),

        # Placeholders for ENDPOINT_PLANNER_PROMPT_TEMPLATE
        'FEATURE_OBJECTIVES': context.get('FEATURE_OBJECTIVES', 'N/A'),
        'PLANNER_MILESTONES': context.get('PLANNER_MILESTONES', 'N/A'),

        # Placeholders for SCHEMA_DESIGNER_PROMPT_TEMPLATE
        'DOMAIN_MODELS': json.dumps(context.get('DOMAIN_MODELS', {})),
        'KEY_DATA_REQUIREMENTS': json.dumps(context.get('KEY_DATA_REQUIREMENTS', [])),
        'PLANNED_ENDPOINTS': json.dumps(context.get('PLANNED_ENDPOINTS', [])),

        # Placeholders for REQUEST_RESPONSE_DESIGNER_PROMPT_TEMPLATE
        'PLANNED_ENDPOINTS_JSON_LIST': json.dumps(context.get('PLANNED_ENDPOINTS_JSON_LIST', [])),
        'AVAILABLE_SCHEMAS_SUMMARY': json.dumps(context.get('AVAILABLE_SCHEMAS_SUMMARY', {})),

        # Placeholders for AUTH_DESIGNER_PROMPT_TEMPLATE
        'SECURITY_REQUIREMENTS': json.dumps(context.get('SECURITY_REQUIREMENTS', {})),
        'PLANNED_ENDPOINTS_SUMMARY': json.dumps(context.get('PLANNED_ENDPOINTS_SUMMARY', [])),

        # Placeholders for ERROR_DESIGNER_PROMPT_TEMPLATE
        'COMMON_ERROR_SCENARIOS': json.dumps(context.get('COMMON_ERROR_SCENARIOS', [])),
        'ERROR_STYLE_GUIDE': context.get('ERROR_STYLE_GUIDE', 'Default error style guide.'),

        # Generic placeholders (provide defaults if not in context)
        'RESOURCE_NAME_SINGULAR': context.get('RESOURCE_NAME_SINGULAR', 'Resource'),
        'RESOURCE_NAME_PLURAL': context.get('RESOURCE_NAME_PLURAL', 'Resources'),
        'RESOURCE_NAME_SLUG': context.get('RESOURCE_NAME_SLUG', 'resources'),
        'RESOURCE_NAME_PASCALCASE_SINGULAR': context.get('RESOURCE_NAME_PASCALCASE_SINGULAR', 'Resource'),
        'RESOURCE_NAME_PASCALCASE_PLURAL': context.get('RESOURCE_NAME_PASCALCASE_PLURAL', 'Resources'),
        'DATA_MODEL_NAME': context.get('DATA_MODEL_NAME', 'DataModel'),
        'SCOPE_NOUN': context.get('SCOPE_NOUN', 'data'),
        'SCOPE_ACTION': context.get('SCOPE_ACTION', 'read'),

        # For API_DESIGNER_PROMPT placeholder
        'COMMON_CONTEXT': context.get('COMMON_CONTEXT', 'Standard API design considerations apply.')
    }

    # Ensure all values are strings for formatting, especially those from json.dumps
    # The initial context passed to this function should already have its complex types stringified by the caller if necessary.
    # Here, we primarily ensure that defaults or direct context values are strings.
    for key, value in prompt_context.items():
        if not isinstance(value, str):
            if isinstance(value, (dict, list)): # Should have been stringified by caller if complex
                 prompt_context[key] = json.dumps(value, default=str) # default=str for safety
            else:
                prompt_context[key] = str(value)

    try:
        return template.format(**prompt_context)
    except KeyError as e:
        raise ValueError(f"Missing key '{str(e)}' (expected in UPPER_SNAKE_CASE) in prompt_context for agent '{agent_name}'. Provided context keys: {list(prompt_context.keys())}")

[end of prompts/api_designer_prompts.py]
