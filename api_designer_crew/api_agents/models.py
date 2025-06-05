from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional, Literal

# Common OpenAPI objects that might be reused
class OpenAPIInfo(BaseModel):
    title: str
    version: str
    description: Optional[str] = None

class OpenAPIExternalDocs(BaseModel):
    description: Optional[str] = None
    url: HttpUrl

class OpenAPITag(BaseModel):
    name: str
    description: Optional[str] = None
    externalDocs: Optional[OpenAPIExternalDocs] = None

class OpenAPIReference(BaseModel):
    ref: str = Field(..., alias='$ref')

class OpenAPISchema(BaseModel):
    # This can be a very complex model. For now, we'll allow Any
    # but ideally, this would be fully defined as per OpenAPI spec.
    # Examples: type, format, properties, items, required, enum, default etc.
    type: Optional[str] = None
    format: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None # Could be Dict[str, OpenAPISchema | OpenAPIReference]
    items: Optional[Any] = None # Could be OpenAPISchema | OpenAPIReference
    required: Optional[List[str]] = None
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None
    description: Optional[str] = None
    example: Optional[Any] = None
    ref: Optional[str] = Field(None, alias='$ref') # For referencing other schemas

    model_config = {
        "extra": "allow" # Allow other valid OpenAPI schema fields
    }

class OpenAPIParameter(BaseModel):
    name: str
    param_in: Literal["query", "header", "path", "cookie"] = Field(..., alias="in")
    description: Optional[str] = None
    required: Optional[bool] = None
    deprecated: Optional[bool] = False
    allowEmptyValue: Optional[bool] = False
    schema_ref: Optional[OpenAPISchema | OpenAPIReference] = Field(None, alias="schema") # schema or $ref

    model_config = {
        "populate_by_name": True # Allows using 'param_in' and 'schema_ref' in Python code
    }

class OpenAPIRequestBody(BaseModel):
    description: Optional[str] = None
    content: Dict[str, Dict[str, OpenAPISchema | OpenAPIReference]] # e.g. {"application/json": {"schema": ...}}
    required: Optional[bool] = False

class OpenAPIResponse(BaseModel):
    description: str
    headers: Optional[Dict[str, Any]] = None # More specific model later if needed
    content: Optional[Dict[str, Dict[str, OpenAPISchema | OpenAPIReference]]] = None # e.g. {"application/json": {"schema": ...}}
    links: Optional[Dict[str, Any]] = None # More specific model later if needed

class OpenAPIOperation(BaseModel):
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    operationId: Optional[str] = None
    parameters: Optional[List[OpenAPIParameter | OpenAPIReference]] = None
    requestBody: Optional[OpenAPIRequestBody | OpenAPIReference] = None
    responses: Dict[str, OpenAPIResponse | OpenAPIReference] # e.g. {"200": ..., "404": ...}
    security: Optional[List[Dict[str, List[str]]]] = None # e.g. [{"oauth2": ["read", "write"]}]
    # ... other fields like callbacks, deprecated, servers, externalDocs

    model_config = {
        "extra": "allow"
    }

class OpenAPIPathItem(BaseModel):
    ref: Optional[str] = Field(None, alias='$ref')
    summary: Optional[str] = None
    description: Optional[str] = None
    get: Optional[OpenAPIOperation] = None
    put: Optional[OpenAPIOperation] = None
    post: Optional[OpenAPIOperation] = None
    delete: Optional[OpenAPIOperation] = None
    options: Optional[OpenAPIOperation] = None
    head: Optional[OpenAPIOperation] = None
    patch: Optional[OpenAPIOperation] = None
    trace: Optional[OpenAPIOperation] = None
    # servers: Optional[List[OpenAPIServer]] = None
    parameters: Optional[List[OpenAPIParameter | OpenAPIReference]] = None

    model_config = {
        "extra": "allow"
    }

class OpenAPIComponents(BaseModel):
    schemas: Optional[Dict[str, OpenAPISchema | OpenAPIReference]] = None
    responses: Optional[Dict[str, OpenAPIResponse | OpenAPIReference]] = None
    parameters: Optional[Dict[str, OpenAPIParameter | OpenAPIReference]] = None
    examples: Optional[Dict[str, Any]] = None # More specific later
    requestBodies: Optional[Dict[str, OpenAPIRequestBody | OpenAPIReference]] = None
    headers: Optional[Dict[str, Any]] = None # More specific later
    securitySchemes: Optional[Dict[str, Any | OpenAPIReference]] = None # More specific later (e.g. APIKey, OAuth2Flows)
    links: Optional[Dict[str, Any]] = None # More specific later
    callbacks: Optional[Dict[str, Any | OpenAPIReference]] = None # More specific later

    model_config = {
        "extra": "allow"
    }

# 1. Endpoint Planner Output
class Endpoint(BaseModel):
    method: Literal["get", "put", "post", "delete", "options", "head", "patch", "trace"]
    path: str = Field(..., examples=["/users/{id}"])
    description: str
    operation_id: Optional[str] = Field(None, alias="operationId", examples=["getUserById"])

class EndpointList(BaseModel):
    endpoints: List[Endpoint]
    summary: Optional[str] = None # Optional summary of the planned endpoints

# 2. Schema Designer Output
class SchemaComponents(BaseModel):
    schemas: Dict[str, OpenAPISchema] = Field(..., description="A dictionary of schema definitions, e.g., for User, Product.")
    # Example: {"User": {"type": "object", "properties": {"id": {"type": "string"}}}}

# 3. Request/Response Designer Output
class PathItemWithOperations(BaseModel):
    # Re-using OpenAPIPathItem but ensuring operations are defined directly
    # This model represents the expected output for a single path from the RequestResponseDesigner
    get: Optional[OpenAPIOperation] = None
    put: Optional[OpenAPIOperation] = None
    post: Optional[OpenAPIOperation] = None
    delete: Optional[OpenAPIOperation] = None
    options: Optional[OpenAPIOperation] = None
    head: Optional[OpenAPIOperation] = None
    patch: Optional[OpenAPIOperation] = None
    trace: Optional[OpenAPIOperation] = None
    parameters: Optional[List[OpenAPIParameter | OpenAPIReference]] = None # Parameters applicable to all operations on this path

class RequestResponseMap(BaseModel):
    paths: Dict[str, PathItemWithOperations] = Field(..., description="Maps path strings to their detailed operation definitions including request bodies and responses.")
    # Example: {"/users": {"get": {...}, "post": {...}}}

# 4. Auth Designer Output
class SecurityScheme(BaseModel):
    type: Literal["apiKey", "http", "oauth2", "openIdConnect"]
    description: Optional[str] = None
    # Fields specific to type, e.g. for apiKey: name, in
    # For http: scheme, bearerFormat
    # For oauth2: flows
    # For openIdConnect: openIdConnectUrl
    # Using Any for now, can be made more specific with discriminated unions if needed
    name: Optional[str] = None # For apiKey
    param_in: Optional[Literal["query", "header", "cookie"]] = Field(None, alias="in") # For apiKey
    scheme: Optional[str] = None # For http
    bearerFormat: Optional[str] = None # For http bearer
    flows: Optional[Dict[str, Any]] = None # For oauth2, e.g. {"clientCredentials": {"tokenUrl": ..., "scopes": ...}}
    openIdConnectUrl: Optional[HttpUrl] = None # For openIdConnect

    model_config = {
        "populate_by_name": True,
        "extra": "allow"
    }

class AuthDefinition(BaseModel):
    security_schemes: Dict[str, SecurityScheme] = Field(..., alias="securitySchemes", description="Definitions of security schemes (e.g., OAuth2, APIKey).")
    global_security: Optional[List[Dict[str, List[str]]]] = Field(None, alias="security", description="Global security requirements for the API.")
    # Example security_schemes: {"ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-KEY"}}
    # Example global_security: [{"ApiKeyAuth": []}]

# 5. Error Designer Output
class ErrorSchemaDefinition(BaseModel):
    # Contains new error schemas to be added to components.schemas
    error_schemas: Dict[str, OpenAPISchema] = Field(..., alias="errorSchemas", description="Reusable error schemas (e.g., NotFoundError, ValidationError).")
    # Specifies how to reference these errors in endpoint responses
    # Maps an HTTP status code (e.g., "404") to a schema reference (e.g., "#/components/schemas/NotFoundError")
    error_responses_references: Optional[Dict[str, OpenAPIReference]] = Field(None, alias="errorResponseReferences", description="Mapping of status codes to error schema references for use in responses.")
    # Example error_schemas: {"NotFoundError": {"type": "object", "properties": {"message": {"type": "string"}}}}
    # Example error_responses_references: {"404": {"$ref": "#/components/schemas/NotFoundError"}}

# 6. OpenAPI Merger Output / Final OpenAPI Spec
class OpenAPISpec(BaseModel):
    openapi: str = Field(..., examples=["3.0.3"])
    info: OpenAPIInfo
    externalDocs: Optional[OpenAPIExternalDocs] = None
    servers: Optional[List[Dict[str, Any]]] = None # List of OpenAPIServer objects
    security: Optional[List[Dict[str, List[str]]]] = None # Global security requirements
    tags: Optional[List[OpenAPITag]] = None
    paths: Dict[str, OpenAPIPathItem] = Field(default_factory=dict)
    components: Optional[OpenAPIComponents] = None

    model_config = {
        "extra": "allow" # Allow other valid OpenAPI fields
    }


# 7. OpenAPI Validator Output
class ValidationIssue(BaseModel):
    message: str
    path: Optional[List[str]] = None # Path to the issue in the OpenAPI document
    severity: Literal["error", "warning"] = "error"

class ValidationResult(BaseModel):
    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    raw_output: Optional[str] = None # If validation tool provides raw output
