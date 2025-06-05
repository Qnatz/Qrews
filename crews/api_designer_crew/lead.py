from typing import Dict, Any, Optional
import json
import os

# Ensure imports can resolve 'crews.api_designer_crew'
LEAD_DESIGNER_IMPORTS_OK = False
try:
    from crews.api_designer_crew.runner import APIDesignCrewRunner # CORRECTED
    from crews.api_designer_crew.openapi_merger import OpenAPIMerger # CORRECTED
    from crews.api_designer_crew.openapi_validator import OpenAPIValidator # CORRECTED
    from crews.api_designer_crew.api_agents.models import ( # CORRECTED path to models
        OpenAPISpec, ValidationResult, ValidationIssue,
        EndpointList, SchemaComponents, RequestResponseMap,
        AuthDefinition, ErrorSchemaDefinition, OpenAPIInfo, OpenAPIComponents,
        OpenAPIPathItem, OpenAPIOperation, OpenAPISchema, SecurityScheme
    )
    from utils.api_crew_utils import LoggerPlaceholder # CORRECTED path to utils
    LEAD_DESIGNER_IMPORTS_OK = True
    print("LeadAPIDesigner: Successfully imported real crew components for Qz_crew.api_designer.")
except ImportError as e:
    print(f"LeadAPIDesigner in Qz_crew: ImportError: {e}. Using mock placeholders.")
    class LoggerPlaceholder:
        def log(self, msg, role="LeadAPI", level="INFO"): print(f"[{level}][{role}] {msg}")
    class MockRunner:
        def __init__(self, master_context, logger=None): self.logger = logger or LoggerPlaceholder(); self.master_context=master_context
        def run(self):
            self.logger.log("MockRunner run called");
            # Return structure with all expected keys for testing
            return {
                "endpoint_planner_output": {"endpoints": [{"method":"get", "path":"/mock", "description":"mock"}]},
                "schema_designer_output": {"schemas": {"MockSchema": {"type":"object"}}},
                "request_response_designer_output": {"paths": {"/mock": {"get":{"summary":"mock"}}}},
                "auth_designer_output": {"securitySchemes": {"mockAuth":{"type":"apiKey"}}},
                "error_designer_output": {"errorSchemas": {"MockError":{"type":"object"}}}
            }
    class MockMerger:
        def __init__(self, logger=None): self.logger = logger or LoggerPlaceholder()
        def merge_openapi_parts(self, **kwargs):
            self.logger.log("MockMerger merge_openapi_parts called");
            # Return a dict that can be minimally processed
            project_name_val = kwargs.get("project_name", "Mock Project")
            info_obj_or_dict = {"title": f"{project_name_val} API", "version": kwargs.get("api_version","1.0"), "description":kwargs.get("project_objective","mock obj")}

            # Simulate Pydantic model_dump behavior for mocks if they are dict-like
            def _dump_if_needed(data_obj, key_name):
                val = kwargs.get(data_obj, {})
                return val.get(key_name, {}) if isinstance(val, dict) else getattr(val, key_name, {})

            return {
                "openapi":"3.0.3",
                "info": info_obj_or_dict,
                "paths":_dump_if_needed("request_response_map", "paths"),
                "components":{
                    "schemas": {
                        **(_dump_if_needed("schema_components", "schemas")),
                        **(_dump_if_needed("error_definition", "error_schemas")) # error_schemas is the alias
                    },
                    "securitySchemes": _dump_if_needed("auth_definition", "security_schemes") # security_schemes is the alias
                 },
                 "security": kwargs.get("auth_definition",{}).get("global_security",[]) # global_security is the alias
            }
    class MockValidator:
        def __init__(self, logger=None): self.logger = logger or LoggerPlaceholder()
        def validate_spec(self, spec_model_or_dict):
            self.logger.log("MockValidator validate_spec called");
            return {"is_valid": True, "issues": []}

    APIDesignCrewRunner = MockRunner
    OpenAPIMerger = MockMerger
    OpenAPIValidator = MockValidator

    class MockPydanticModel:
        def __init__(self, **kwargs): self.__dict__.update(kwargs)
        @classmethod
        def model_validate(cls, data_dict, **kwargs): return cls(**data_dict)
        def model_dump(self, **kwargs): return self.__dict__

    OpenAPISpec, ValidationResult, ValidationIssue = MockPydanticModel, MockPydanticModel, MockPydanticModel
    EndpointList, SchemaComponents, RequestResponseMap, AuthDefinition, ErrorSchemaDefinition, OpenAPIInfo, OpenAPIComponents = MockPydanticModel, MockPydanticModel, MockPydanticModel, MockPydanticModel, MockPydanticModel, MockPydanticModel, MockPydanticModel
    OpenAPIPathItem, OpenAPIOperation, OpenAPISchema, SecurityScheme = MockPydanticModel, MockPydanticModel, MockPydanticModel, MockPydanticModel


class APIDesigner: # This is Qz_crew.api_designer.APIDesigner
    def __init__(self, context: Dict[str, Any], logger: Optional[LoggerPlaceholder] = None):
        self.context = context
        self.logger = logger or LoggerPlaceholder()
        self.logger.log("Lead APIDesigner (Qz_crew) initialized.", role="LeadAPIDesigner")

        if not LEAD_DESIGNER_IMPORTS_OK:
            self.logger.log("Lead APIDesigner (Qz_crew) running with MOCKED dependencies for crew components.", role="LeadAPIDesigner", level="WARNING")

        self.crew_runner = APIDesignCrewRunner(master_context=self.context, logger=self.logger)
        self.merger = OpenAPIMerger(logger=self.logger)
        self.validator = OpenAPIValidator(logger=self.logger)

    def _reconstruct_pydantic_model(self, model_cls, data_dict: Optional[Dict[str, Any]]):
        if not isinstance(data_dict, dict):
            self.logger.log(f"Cannot reconstruct Pydantic model {model_cls.__name__ if hasattr(model_cls, '__name__') else 'UnknownModel'} because input data is not a dict: {type(data_dict)}", level="ERROR", role="LeadAPIDesigner")
            return None # Return None if data is not a dict

        # Check if model_cls is one of the Pydantic models imported when LEAD_DESIGNER_IMPORTS_OK is true
        # If LEAD_DESIGNER_IMPORTS_OK is false, model_cls would be MockPydanticModel
        is_real_pydantic_model_class = LEAD_DESIGNER_IMPORTS_OK and hasattr(model_cls, 'model_validate')

        if is_real_pydantic_model_class:
            try:
                return model_cls.model_validate(data_dict) # Pydantic v2+
            except Exception as e:
                self.logger.log(f"Pydantic validation/reconstruction failed for {model_cls.__name__}: {e}. Data: {str(data_dict)[:200]}", level="ERROR", role="LeadAPIDesigner")
                return data_dict # Return original dict on failure for potential downstream raw use

        # If not a real Pydantic model (i.e., using mocks, where model_cls is MockPydanticModel)
        # or if reconstruction failed and returned data_dict
        return model_cls(**data_dict) if isinstance(model_cls, type) and model_cls.__name__ == 'MockPydanticModel' else data_dict


    def run(self) -> Dict[str, Any]:
        self.logger.log("Lead APIDesigner (Qz_crew): Starting API design process...", role="LeadAPIDesigner")
        crew_outputs = self.crew_runner.run()

        if not isinstance(crew_outputs, dict) or crew_outputs.get("error"):
            error_msg = f"APIDesignCrewRunner failed or returned errors: {crew_outputs.get('error', 'Unknown runner error') if isinstance(crew_outputs, dict) else 'Runner returned non-dict or critical error.'}"
            self.logger.log(error_msg, role="LeadAPIDesigner", level="ERROR")
            return {"error": "API Design Crew execution failed", "details": error_msg}

        required_part_keys = ["endpoint_planner_output", "schema_designer_output", "request_response_designer_output", "auth_designer_output", "error_designer_output"]
        for key in required_part_keys:
            output_part = crew_outputs.get(key)
            if not output_part or (not isinstance(output_part, dict)) or (isinstance(output_part, dict) and output_part.get("error")):
                error_msg = f"Missing, invalid, or failed output for '{key}': {output_part.get('error', 'Part not found or error in part') if isinstance(output_part, dict) else 'Part data invalid or not a dict'}"
                self.logger.log(error_msg, role="LeadAPIDesigner", level="ERROR")
                return {"error": "Incomplete/failed outputs from API Design Crew", "details": error_msg, "crew_outputs": crew_outputs}

        merged_spec_obj: Any
        try:
            ep_list_obj = self._reconstruct_pydantic_model(EndpointList, crew_outputs["endpoint_planner_output"])
            schema_comps_obj = self._reconstruct_pydantic_model(SchemaComponents, crew_outputs["schema_designer_output"])
            req_resp_map_obj = self._reconstruct_pydantic_model(RequestResponseMap, crew_outputs["request_response_designer_output"])
            auth_def_obj = self._reconstruct_pydantic_model(AuthDefinition, crew_outputs["auth_designer_output"])
            error_def_obj = self._reconstruct_pydantic_model(ErrorSchemaDefinition, crew_outputs["error_designer_output"])

            if not all(item is not None for item in [ep_list_obj, schema_comps_obj, req_resp_map_obj, auth_def_obj, error_def_obj]):
                 self.logger.log("One or more sub-agent output DTOs are None after reconstruction. Halting merge.", level="ERROR", role="LeadAPIDesigner")
                 return {"error": "Failed to reconstruct sub-agent DTOs for merging (resulted in None).", "crew_outputs": crew_outputs}

            merged_spec_obj = self.merger.merge_openapi_parts(
                project_name=self.context.get("project_name", "API Project"),
                project_objective=self.context.get("project_objective", "API Objective"),
                api_version=self.context.get("api_version", "1.0.0"),
                endpoint_list=ep_list_obj,
                schema_components=schema_comps_obj,
                request_response_map=req_resp_map_obj,
                auth_definition=auth_def_obj,
                error_definition=error_def_obj
            )
        except Exception as e_merge:
            error_msg = f"Error during merging of OpenAPI parts: {type(e_merge).__name__} - {e_merge}"
            self.logger.log(error_msg, role="LeadAPIDesigner", level="ERROR")
            return {"error": "OpenAPI merging failed", "details": str(e_merge)}

        if not merged_spec_obj: # Could be None or empty dict from mock merger
             return {"error": "OpenAPI merging failed", "details": "Merger returned no result."}

        validation_input = merged_spec_obj
        # If real models were used, merged_spec_obj is an OpenAPISpec instance.
        # If mocks were used, merged_spec_obj is a dict from MockMerger.
        # The validator (real or mock) needs to handle its input type.
        # Our MockValidator takes dict and returns dict. Real validator takes Pydantic model.

        if LEAD_DESIGNER_IMPORTS_OK and OpenAPISpec.__name__ != 'dict' and not isinstance(merged_spec_obj, OpenAPISpec):
             # This happens if merger was mocked and returned a dict, but we have real OpenAPISpec model
             validation_input = self._reconstruct_pydantic_model(OpenAPISpec, merged_spec_obj if isinstance(merged_spec_obj, dict) else {})
             if not validation_input: # Reconstruction failed
                  return {"error": "Failed to reconstruct final spec for validation", "details": "Merged spec could not be parsed into OpenAPISpec model."}

        validation_result_data = self.validator.validate_spec(validation_input)

        # Determine how to get the final dictionary output
        if hasattr(merged_spec_obj, 'model_dump'): # Real Pydantic model
            final_spec_dict_to_return = merged_spec_obj.model_dump(by_alias=True, exclude_none=True)
        elif isinstance(merged_spec_obj, dict): # Mock merger returned a dict
            final_spec_dict_to_return = merged_spec_obj
        else: # Should not happen
            final_spec_dict_to_return = {"error": "Merged spec is of unexpected type"}


        if not isinstance(validation_result_data, dict) or 'is_valid' not in validation_result_data:
            return {"error": "Validation step failed", "details": "Validator returned unexpected data", "unvalidated_spec": final_spec_dict_to_return}

        if not validation_result_data.get('is_valid'):
            return {"error": "Spec validation failed", "validation_issues": validation_result_data.get('issues', []), "spec": final_spec_dict_to_return}

        self.logger.log("OpenAPI specification generated and validated successfully by LeadAPIDesigner.", role="LeadAPIDesigner")
        return final_spec_dict_to_return


if __name__ == '__main__':
    logger = LoggerPlaceholder()
    logger.log("--- Testing Lead APIDesigner (Qz_crew) Standalone ---", role="TestMain")
    sample_master_context = {
        "project_name": "My Awesome App", "project_objective": "To create the best app ever.", "api_version": "1.0.1",
        "analysis": {"key_requirements": ["CRUD items"], "domain_models_text": "Item(id, name, description)"},
        "plan": {"feature_objectives_text": ["Manage items"]},
        "architecture": {"security_requirements_text": ["API Key auth"]}
    }

    if not LEAD_DESIGNER_IMPORTS_OK or not os.environ.get("GEMINI_API_KEY"):
        logger.log("LeadAPIDesigner (Qz_crew) __main__: Using MOCKED crew components for test run.", level="WARNING", role="TestMain")
    else:
        logger.log("LeadAPIDesigner (Qz_crew) __main__: Attempting test with REAL crew components.", role="TestMain")

    lead_api_designer = APIDesigner(context=sample_master_context, logger=logger)
    final_api_spec_dict = lead_api_designer.run()

    logger.log(f"--- Lead APIDesigner (Qz_crew) Test Output ---", role="TestMain")
    logger.log(json.dumps(final_api_spec_dict, indent=2), role="TestMain")

    if isinstance(final_api_spec_dict, dict) and "error" not in final_api_spec_dict and "openapi" in final_api_spec_dict:
        logger.log("Lead APIDesigner (Qz_crew) __main__ test deemed successful.", role="TestMain")
    else:
        logger.log(f"Lead APIDesigner (Qz_crew) __main__ test deemed failed. Output: {str(final_api_spec_dict)[:500]}", level="ERROR", role="TestMain")
    logger.log("--- Lead APIDesigner (Qz_crew) Test Finished ---", role="TestMain")
