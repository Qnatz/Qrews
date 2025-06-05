import json

# ============== BASE TEMPLATES (can be shared or adapted) ==============
# Simplified for sub-agents, assuming they don't use complex tools directly
# The SubAgentWrapper will handle the direct LLM call.

SUB_AGENT_ROLE_TEMPLATE = """
You are a specialized AI sub-agent: {role}, part of an API Design Crew.
Your current task is: {sub_task_description}
You are working on the project: {project_name}
Overall Project Objective: {objective}
"""

# ============== SUB-AGENT SPECIFIC PROMPTS ==============

ENDPOINT_PLANNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Your goal: Identify all RESTful endpoints based on feature objectives and planner milestones.
Input context:
- Feature Objectives: {feature_objectives}
- Planner Milestones: {planner_milestones}

Output requirements:
- A JSON list of endpoint objects.
- Each endpoint object MUST have:
  - "method": (string) HTTP method (e.g., "get", "post", "put", "delete").
  - "path": (string) The URL path (e.g., "/users", "/users/{{user_id}}"). Use conventional RESTful path patterns.
  - "description": (string) A brief description of what the endpoint does.
  - "operationId": (string, optional) A unique identifier for the operation, typically camelCase (e.g., "listUsers", "getUserById").

Example for a single endpoint object:
{{
  "method": "get",
  "path": "/tenants",
  "description": "Retrieves a list of all tenants.",
  "operationId": "listTenants"
}}

The entire response MUST be a single JSON object with a key "endpoints" containing a list of these endpoint objects.
Do NOT include any other text, prefixes, or markdown like '\\`\\`\\`json'. The JSON object is your complete answer.

JSON Output Structure:
\\`\\`\\`json
{{
  "endpoints": [
    {{
      "method": "...",
      "path": "...",
      "description": "...",
      "operationId": "..."
    }}
    // ... more endpoint objects
  ],
  "summary": "Optional summary of the planned endpoints."
}}
\\`\\`\\`
"""

SCHEMA_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Your goal: Create OpenAPI `components.schemas` from domain models and project requirements.
Input context:
- Domain Models (conceptual, if provided): {domain_models}
- Key Project Requirements related to data: {key_data_requirements}
- Existing planned endpoints (for context): {planned_endpoints}

Output requirements:
- An OpenAPI 3.0 or later compatible `components.schemas` block as a JSON object.
- Each key in the main JSON object should be a schema name (e.g., "User", "PointOfInterest").
- Each value should be a valid OpenAPI schema object (defining type, properties, required fields, examples, etc.).
- Use standard OpenAPI data types (string, number, integer, boolean, array, object).
- Include `description` and `example` fields in your schema properties where helpful.

Example for a "Tenant" schema:
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

The entire response MUST be a single JSON object where keys are schema names and values are their definitions.
This will form the content of the `schemas` field within the `SchemaComponents` Pydantic model.
Do NOT include any other text, prefixes, or markdown like '\\`\\`\\`json'. The JSON object is your complete answer.

JSON Output Structure:
\\`\\`\\`json
{{
  "schemas": {{
    "SchemaName1": {{ ...schema definition... }},
    "SchemaName2": {{ ...schema definition... }}
  }}
}}
\\`\\`\\`
"""

REQUEST_RESPONSE_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Your goal: Define request bodies and response formats (status codes, structures) for planned API endpoints.
You will be given a list of planned endpoints and available component schemas.
Input context:
- Planned Endpoints: {planned_endpoints_json_list}
- Available Component Schemas (for referencing, e.g., "#/components/schemas/User"): {available_schemas_summary}

Output requirements:
- A JSON object mapping API paths to their detailed operation definitions.
- For each path and HTTP method:
  - Define `summary`, `description`, and `operationId` if not already provided or if needs refinement.
  - Define `parameters` (path, query, header) if any, referencing schemas or defining them inline.
  - Define `requestBody` if applicable, with content types (e.g., "application/json") and schema references.
  - Define `responses` for various HTTP status codes (e.g., "200", "201", "400", "404").
    - Each response MUST have a `description`.
    - Response content (e.g., "application/json") should reference component schemas.
- Ensure all schema references ($ref) point to `#/components/schemas/SchemaName`.

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
The entire response MUST be a single JSON object representing the `paths` part of an OpenAPI specification.
Do NOT include any other text, prefixes, or markdown like '\\`\\`\\`json'. The JSON object is your complete answer.

JSON Output Structure:
\\`\\`\\`json
{{
  "paths": {{
    "/path1": {{
      "get": {{ ...operation details... }},
      "post": {{ ...operation details... }}
    }},
    "/path2/{{id}}": {{
      "get": {{ ...operation details... }},
      "put": {{ ...operation details... }}
    }}
    // ... more path items
  }}
}}
\\`\\`\\`
"""

AUTH_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Your goal: Design security schemes (e.g., OAuth2, JWT) and integrate them globally into the API.
Input context:
- Project Security Requirements: {security_requirements}
- Overall API Structure (planned endpoints for context): {planned_endpoints_summary}

Output requirements:
- A JSON object containing:
  - `securitySchemes`: An object defining one or more security schemes compatible with OpenAPI 3.0 or later.
    - Prefer OAuth2 with Client Credentials flow if suitable, or JWT Bearer token (HTTP Bearer scheme).
    - Example for OAuth2 Client Credentials:
      \\`\\`\\`json
      {{
        "OAuth2ClientCredentials": {{
          "type": "oauth2",
          "flows": {{
            "clientCredentials": {{
              "tokenUrl": "https://auth.example.com/token", // Use a placeholder or actual if known
              "scopes": {{
                "read:data": "Read access to data",
                "write:data": "Write access to data"
                // Define other relevant scopes
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
  - `security`: (Optional) A global security requirement array applying the defined scheme(s) to the entire API.
    - Example: `[ {{"OAuth2ClientCredentials": ["read:data", "write:data"]}} ]` or `[ {{"BearerAuth": []}} ]`

The entire response MUST be a single JSON object with keys `securitySchemes` and optionally `security`.
Do NOT include any other text, prefixes, or markdown like '\\`\\`\\`json'. The JSON object is your complete answer.

JSON Output Structure:
\\`\\`\\`json
{{
  "securitySchemes": {{
    "SchemeName1": {{ ...scheme definition... }}
  }},
  "security": [
    {{ "SchemeName1": ["scope1", "scope2"] }}
  ]
}}
\\`\\`\\`
"""

ERROR_DESIGNER_PROMPT_TEMPLATE = SUB_AGENT_ROLE_TEMPLATE + """
Your goal: Define reusable error schemas and specify how they should be referenced in API endpoint responses.
Input context:
- Common Error Scenarios for this type of API: {common_error_scenarios}
- Style guide for error messages (if any): {error_style_guide}

Output requirements:
- A JSON object containing:
  - `errorSchemas`: An object where each key is an error schema name (e.g., "NotFoundError", "ValidationError") and the value is its OpenAPI schema definition.
    - Each error schema should typically include `code` (string, specific error code) and `message` (string, human-readable).
    - Example "NotFoundError":
      \\`\\`\\`json
      {{
        "NotFoundError": {{
          "type": "object",
          "properties": {{
            "code": {{ "type": "string", "example": "NOT_FOUND" }},
            "message": {{ "type": "string", "example": "The requested resource was not found." }}
          }}
        }}
      }}
      \\`\\`\\`
  - `errorResponseReferences`: (Optional) An object mapping HTTP status codes (e.g., "404") to an OpenAPI reference object pointing to a schema in `errorSchemas`.
    - Example: `{{"404": {{"$ref": "#/components/schemas/NotFoundError"}}}}`
    - This helps standardize which error schema is used for common HTTP error codes across the API.

The entire response MUST be a single JSON object with keys `errorSchemas` and optionally `errorResponseReferences`.
Do NOT include any other text, prefixes, or markdown like '\\`\\`\\`json'. The JSON object is your complete answer.

JSON Output Structure:
\\`\\`\\`json
{{
  "errorSchemas": {{
    "ErrorName1": {{ ...schema definition... }},
    "ErrorName2": {{ ...schema definition... }}
  }},
  "errorResponseReferences": {{
    "400": {{ "$ref": "#/components/schemas/ValidationError" }},
    "401": {{ "$ref": "#/components/schemas/AuthenticationError" }},
    "403": {{ "$ref": "#/components/schemas/AuthorizationError" }},
    "404": {{ "$ref": "#/components/schemas/NotFoundError" }},
    "500": {{ "$ref": "#/components/schemas/InternalServerError" }}
  }}
}}
\\`\\`\\`
"""

# API Designer main prompt - Functionality is now orchestrated by APIDesignerCrewOrchestrator.
# This prompt is a placeholder if direct display of a generic API Designer role is needed.
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

{common_context} # Placeholder for common context elements if this template were used
"""
# Note: The APIDesigner agent in agents.py is now refactored to call the orchestrator directly.
# It does not use this prompt for an LLM call to generate the full spec.
# This text serves as a description of its high-level role.


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
    """
    template = SUB_AGENT_PROMPTS_MAP.get(agent_name)
    if not template:
        raise ValueError(f"No prompt template found for sub-agent: {agent_name}")

    # Prepare context for formatting, ensuring all keys used in templates are present.
    # Default values are crucial here.
    prompt_context = {
        'role': context.get('role', f"{agent_name.replace('_', ' ').title()} Sub-Agent"),
        'sub_task_description': context.get('sub_task_description', f"Performing {agent_name} task."),
        'project_name': context.get('project_name', 'Unnamed Project'),
        'objective': context.get('objective', 'N/A'),
        'feature_objectives': context.get('feature_objectives', 'N/A'),
        'planner_milestones': context.get('planner_milestones', 'N/A'),
        'domain_models': context.get('domain_models', 'N/A'),
        'key_data_requirements': context.get('key_data_requirements', 'N/A'),
        'planned_endpoints': json.dumps(context.get('planned_endpoints', [])), # For schema designer
        'planned_endpoints_json_list': json.dumps(context.get('planned_endpoints_json_list', [])), # For req/res designer
        'available_schemas_summary': context.get('available_schemas_summary', 'N/A'),
        'security_requirements': context.get('security_requirements', 'N/A'),
        'planned_endpoints_summary': context.get('planned_endpoints_summary', 'N/A'),
        'common_error_scenarios': context.get('common_error_scenarios', 'N/A'),
        'error_style_guide': context.get('error_style_guide', 'N/A'),
        # Added common_context for the new API_DESIGNER_PROMPT, though it's a placeholder here
        'common_context': context.get('common_context', 'Standard API design considerations apply.')
    }
    # Update with any other context values passed in
    prompt_context.update(context)

    return template.format(**prompt_context)
