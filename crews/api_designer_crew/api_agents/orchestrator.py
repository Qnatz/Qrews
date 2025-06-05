from typing import Optional, Dict, Any

# Import Pydantic models for type hinting and data exchange
try:
    from .models import (
        OpenAPISpec, ValidationResult, EndpointList, SchemaComponents,
        RequestResponseMap, AuthDefinition, ErrorSchemaDefinition
    )
    # Import agent classes
    from .endpoint_planner import EndpointPlannerAgent
    from .schema_designer import SchemaDesignerAgent
    from .request_response_designer import RequestResponseDesignerAgent
    from .auth_designer import AuthDesignerAgent
    from .error_designer import ErrorDesignerAgent
    from .openapi_merger import OpenAPIMerger
    from .openapi_validator import OpenAPIValidator
    from utils.api_crew_utils import LoggerPlaceholder # CORRECTED
except ImportError:
    # Fallbacks for testing or if imports are tricky during development
    class LoggerPlaceholder: # This local definition is fine as a fallback
        def log(self, message: str, role: str = "Test", level: str = "INFO"):
            print(f"[{level}][{role}] {message}")

    class MockBaseModel:
        def __init__(self, **kwargs): self.__dict__.update(kwargs)
        def model_dump_json(self, **kwargs): import json; return json.dumps(self.__dict__)
        def model_dump(self, **kwargs): return self.__dict__ # Simplified for mock

    OpenAPISpec, ValidationResult, EndpointList, SchemaComponents = MockBaseModel, MockBaseModel, MockBaseModel, MockBaseModel
    RequestResponseMap, AuthDefinition, ErrorSchemaDefinition = MockBaseModel, MockBaseModel, MockBaseModel

    # For agent classes, mock them to be instantiable and have their primary method callable
    class MockAgent:
        def __init__(self, logger=None): self.logger = logger or LoggerPlaceholder()
        def __call__(self, *args, **kwargs): # Make instances callable like functions if needed
            self.logger.log(f"MockAgent {self.__class__.__name__} called", role=self.__class__.__name__)
            return MockBaseModel() # Return a generic mock model

    EndpointPlannerAgent = type('EndpointPlannerAgent', (MockAgent,), {'plan_endpoints': lambda s, **kw: MockBaseModel(endpoints=[])})
    SchemaDesignerAgent = type('SchemaDesignerAgent', (MockAgent,), {'design_schemas': lambda s, **kw: MockBaseModel(schemas={})})
    RequestResponseDesignerAgent = type('RequestResponseDesignerAgent', (MockAgent,), {'design_requests_responses': lambda s, **kw: MockBaseModel(paths={})})
    AuthDesignerAgent = type('AuthDesignerAgent', (MockAgent,), {'design_auth_components': lambda s, **kw: MockBaseModel(security_schemes={}, global_security=[])})
    ErrorDesignerAgent = type('ErrorDesignerAgent', (MockAgent,), {'design_error_handling': lambda s, **kw: MockBaseModel(error_schemas={}, error_responses_references={})})
    OpenAPIMerger = type('OpenAPIMerger', (MockAgent,), {'merge_openapi_parts': lambda s, **kw: MockBaseModel(info=MockBaseModel(title='Mock API'), paths={}, components=MockBaseModel(schemas={}))})
    OpenAPIValidator = type('OpenAPIValidator', (MockAgent,), {'validate_spec': lambda s, **kw: MockBaseModel(is_valid=True, issues=[])})


# Placeholder for the main project's ProjectContext
class ProjectContext:
    def __init__(self, project_name: str, objective: str, api_version: str = "1.0.0"):
        self.project_name = project_name
        self.objective = objective
        self.api_version = api_version
        self.analysis: Optional[Dict[str, Any]] = {}
        self.plan: Optional[Dict[str, Any]] = {}
        self.architecture: Optional[Dict[str, Any]] = {}


class APIDesignerCrewOrchestrator:
    def __init__(self, logger: Optional[LoggerPlaceholder] = None):
        self.logger = logger or LoggerPlaceholder()
        self.logger.log("APIDesignerCrewOrchestrator initialized.", role="Orchestrator")

        self.endpoint_planner = EndpointPlannerAgent(logger=self.logger)
        self.schema_designer = SchemaDesignerAgent(logger=self.logger)
        self.request_response_designer = RequestResponseDesignerAgent(logger=self.logger)
        self.auth_designer = AuthDesignerAgent(logger=self.logger)
        self.error_designer = ErrorDesignerAgent(logger=self.logger)
        self.openapi_merger = OpenAPIMerger(logger=self.logger)
        self.openapi_validator = OpenAPIValidator(logger=self.logger)

    def generate_openapi_spec(self, project_context: ProjectContext) -> Optional[OpenAPISpec]:
        """
        Orchestrates the API design sub-agents to generate and validate an OpenAPI specification.
        Returns the validated OpenAPISpec or None if a critical error occurs.
        """
        self.logger.log(f"Starting OpenAPI generation process for project: {project_context.project_name}", role="Orchestrator")

        # 1. Endpoint Planning
        plan_data = project_context.plan or {}
        ep_list: Optional[EndpointList] = self.endpoint_planner.plan_endpoints(
            project_name=project_context.project_name,
            project_objective=project_context.objective,
            feature_objectives=plan_data.get("feature_objectives_text", []),
            planner_milestones=plan_data.get("milestones", [])
        )
        if not ep_list or not hasattr(ep_list, 'endpoints'): # Check if it's a valid-like model
            self.logger.log("Endpoint planning failed or returned invalid data. Halting.", level="ERROR", role="Orchestrator")
            return None
        self.logger.log(f"Endpoint Planner produced {len(ep_list.endpoints)} endpoints.", role="Orchestrator")

        # 2. Schema Design
        analysis_data = project_context.analysis or {}
        schemas: Optional[SchemaComponents] = self.schema_designer.design_schemas(
            project_name=project_context.project_name,
            project_objective=project_context.objective,
            domain_models=analysis_data.get("domain_models_text"),
            key_data_requirements=analysis_data.get("key_requirements", []),
            planned_endpoints=ep_list
        )
        if not schemas or not hasattr(schemas, 'schemas'):
            self.logger.log("Schema design failed or returned invalid data. Halting.", level="ERROR", role="Orchestrator")
            return None
        self.logger.log(f"Schema Designer produced {len(schemas.schemas)} schemas.", role="Orchestrator")

        # 3. Request/Response Design
        req_resp_map: Optional[RequestResponseMap] = self.request_response_designer.design_requests_responses(
            project_name=project_context.project_name,
            project_objective=project_context.objective,
            planned_endpoints=ep_list,
            available_schemas=schemas
        )
        if not req_resp_map or not hasattr(req_resp_map, 'paths'):
            self.logger.log("Request/Response design failed or returned invalid data. Halting.", level="ERROR", role="Orchestrator")
            return None
        self.logger.log(f"Request/Response Designer produced definitions for {len(req_resp_map.paths)} paths.", role="Orchestrator")

        # 4. Auth Design
        arch_data = project_context.architecture or {}
        auth_def: Optional[AuthDefinition] = self.auth_designer.design_auth_components(
            project_name=project_context.project_name,
            project_objective=project_context.objective,
            security_requirements=arch_data.get("security_requirements_text", []),
            planned_endpoints_summary=getattr(ep_list, 'summary', "N/A")
        )
        if not auth_def or not hasattr(auth_def, 'security_schemes'):
            self.logger.log("Auth design failed or returned invalid data. Halting.", level="ERROR", role="Orchestrator")
            return None
        self.logger.log(f"Auth Designer produced {len(auth_def.security_schemes)} security schemes.", role="Orchestrator")

        # 5. Error Design
        error_def: Optional[ErrorSchemaDefinition] = self.error_designer.design_error_handling(
            project_name=project_context.project_name,
            common_error_scenarios=analysis_data.get("common_error_scenarios"),
            error_style_guide=arch_data.get("error_style_guide_text")
        )
        if not error_def or not hasattr(error_def, 'error_schemas'):
            self.logger.log("Error design failed or returned invalid data. Halting.", level="ERROR", role="Orchestrator")
            return None
        self.logger.log(f"Error Designer produced {len(error_def.error_schemas)} error schemas.", role="Orchestrator")

        # 6. Merge OpenAPI Parts
        merged_spec: OpenAPISpec = self.openapi_merger.merge_openapi_parts(
            project_name=project_context.project_name,
            project_objective=project_context.objective,
            api_version=project_context.api_version,
            endpoint_list=ep_list,
            schema_components=schemas,
            request_response_map=req_resp_map,
            auth_definition=auth_def,
            error_definition=error_def
        )
        self.logger.log("OpenAPI parts merged successfully.", role="Orchestrator")

        # 7. Validate OpenAPI Spec
        validation_result: ValidationResult = self.openapi_validator.validate_spec(merged_spec)
        if not hasattr(validation_result, 'is_valid') or not validation_result.is_valid:
            self.logger.log("OpenAPI specification validation failed.", level="ERROR", role="Orchestrator")
            if hasattr(validation_result, 'issues'):
                for issue in validation_result.issues:
                    msg = getattr(issue, 'message', 'Unknown issue')
                    path = getattr(issue, 'path', 'N/A')
                    severity = getattr(issue, 'severity', 'error')
                    self.logger.log(f"Validation Issue: {msg} (Path: {path}, Severity: {severity})", level="ERROR", role="Orchestrator")
            return None

        self.logger.log("OpenAPI specification validated successfully.", role="Orchestrator")
        return merged_spec

if __name__ == '__main__':
    import os

    main_logger = LoggerPlaceholder()
    main_logger.log("--- Testing APIDesignerCrewOrchestrator ---", role="TestMain")

    if not os.environ.get("GEMINI_API_KEY"):
        main_logger.log("GEMINI_API_KEY not set. Orchestrator test will use MOCKED sub-agents.", level="WARNING", role="TestMain")
        # Mocking is handled by the ImportError block at the top of the file string for this test.
    else:
        main_logger.log("GEMINI_API_KEY is set. Orchestrator test will attempt to use REAL sub-agents (which will make LLM calls).", role="TestMain")

    orchestrator = APIDesignerCrewOrchestrator(logger=main_logger)
    sample_context = ProjectContext(
        project_name="E-commerce Platform",
        objective="To design an API for an e-commerce platform supporting products, orders, and users."
    )
    sample_context.analysis = {
        "key_requirements": ["User authentication", "Product catalog", "Order management"],
        "domain_models_text": "User, Product, Order, Cart, Payment",
        "common_error_scenarios": ["Product out of stock", "Invalid coupon code"]
    }
    sample_context.plan = {
        "feature_objectives_text": ["Allow users to browse products", "Allow users to place orders"],
        "milestones": [{"name": "M1: User & Product Setup"}, {"name": "M2: Order Processing"}]
    }
    sample_context.architecture = {
        "security_requirements_text": ["OAuth2 for user authentication", "API Key for service accounts"],
        "error_style_guide_text": "Provide error codes and clear messages."
    }

    final_spec = orchestrator.generate_openapi_spec(sample_context)

    if final_spec and hasattr(final_spec, 'info') and final_spec.info : # Check if it's a valid-like model
        main_logger.log("Orchestrator run completed successfully!", role="TestMain")
        main_logger.log(f"Generated OpenAPI Spec Title: {final_spec.info.title if hasattr(final_spec.info, 'title') else 'N/A'}", role="TestMain")
        main_logger.log(f"Number of paths: {len(final_spec.paths) if hasattr(final_spec, 'paths') and final_spec.paths else 0}", role="TestMain")
        schemas_count = 0
        if hasattr(final_spec, 'components') and final_spec.components and hasattr(final_spec.components, 'schemas') and final_spec.components.schemas:
            schemas_count = len(final_spec.components.schemas)
        main_logger.log(f"Number of component schemas: {schemas_count}", role="TestMain")
    else:
        main_logger.log("Orchestrator run failed or produced an invalid/incomplete spec.", level="ERROR", role="TestMain")

    main_logger.log("--- APIDesignerCrewOrchestrator Test Finished ---", role="TestMain")
