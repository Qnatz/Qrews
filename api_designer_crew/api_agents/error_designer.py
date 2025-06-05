from typing import Optional, Dict, Any, List
import json
import os

try:
    from .models import ErrorSchemaDefinition # Relative import
    from .utils import SubAgentWrapper, LoggerPlaceholder
except ImportError:
    from models import ErrorSchemaDefinition # Fallback
    from utils import SubAgentWrapper, LoggerPlaceholder

class ErrorDesignerAgent:
    def __init__(self, logger: Optional[LoggerPlaceholder] = None):
        self.agent_name = "error_designer"
        self.logger = logger or LoggerPlaceholder()
        self.wrapper = SubAgentWrapper(
            sub_agent_name=self.agent_name,
            output_model=ErrorSchemaDefinition,
            logger=self.logger
        )
        self.logger.log(f"{self.agent_name.capitalize()} initialized.", role=self.agent_name)

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Designs reusable error schemas and their integration based on context.
        Context keys: 'project_name', 'project_objective',
                      'common_error_scenarios' (Optional[List[str]]),
                      'error_style_guide' (Optional[str]).
        Returns a dictionary (JSON-serializable) of the error definitions
        or an error dictionary.
        """
        project_name = context.get("project_name", "Unknown Project")
        self.logger.log(f"Starting error handling design for project: {project_name}", role=self.agent_name)

        common_error_scenarios = context.get("common_error_scenarios")
        error_style_guide = context.get("error_style_guide")
        # Use objective from context if provided, otherwise create a default one for this agent's task
        project_objective = context.get("project_objective", f"Design standardized error responses for {project_name}")


        context_for_prompt = {
            "project_name": project_name,
            "objective": project_objective,
            "common_error_scenarios": common_error_scenarios or ["Resource not found", "Invalid input", "Unauthorized access", "Internal server error"],
            "error_style_guide": error_style_guide or "Error messages should be concise and provide a unique error code.",
        }
        self.logger.log(f"Context for {self.agent_name} prompt (first 300 chars): {str(context_for_prompt)[:300]}", role=self.agent_name, level="DEBUG")

        error_definition_model: Optional[ErrorSchemaDefinition] = self.wrapper.execute(context_for_prompt)

        if error_definition_model and isinstance(error_definition_model, ErrorSchemaDefinition):
            num_schemas = len(error_definition_model.error_schemas) if hasattr(error_definition_model, 'error_schemas') and error_definition_model.error_schemas else 0
            self.logger.log(f"Successfully designed {num_schemas} error schema(s).", role=self.agent_name)
            return error_definition_model.model_dump(by_alias=True)
        else:
            error_msg = "Error handling design failed or returned no valid output from LLM wrapper."
            self.logger.log(error_msg, role=self.agent_name, level="ERROR")
            return {"error": error_msg, "agent_name": self.agent_name, "details": "LLM wrapper returned None or invalid type."}

if __name__ == '__main__':
    logger = LoggerPlaceholder()
    logger.log("Testing ErrorDesignerAgent standalone...")
    designer_agent = ErrorDesignerAgent(logger=logger)
    sample_run_context = {
        "project_name": "Inventory Management API (Error Test)",
        "project_objective": "To define robust error handling for the API.",
        "common_error_scenarios": [
            "Item not found (404)",
            "Insufficient stock (400)",
            "Invalid item ID (400)",
        ],
        "error_style_guide": "Codes: UPPER_SNAKE_CASE. Messages: User-friendly."
    }
    if not os.environ.get("GEMINI_API_KEY"):
        logger.log("GEMINI_API_KEY not set. Skipping live LLM call for ErrorDesignerAgent in __main__.", level="WARNING")
        from unittest.mock import MagicMock
        mock_output_data = {
            "errorSchemas": {"ITEM_NOT_FOUND": {"type": "object", "properties": {"code": {"type": "string"}, "message": {"type": "string"}}}},
            "errorResponseReferences": {"404": {"$ref": "#/components/schemas/ITEM_NOT_FOUND"}}
        }
        RealErrorSchemaDef = None
        try: from models import ErrorSchemaDefinition as RealErrorSchemaDef
        except: pass
        if RealErrorSchemaDef and RealErrorSchemaDef.__name__ != "MockBaseModel":
            designer_agent.wrapper.execute = MagicMock(return_value=RealErrorSchemaDef(**mock_output_data))
        else:
            class TempMockErrDef:
                def __init__(self, data):
                    # Pydantic aliases: error_schemas to errorSchemas, error_responses_references to errorResponseReferences
                    self.error_schemas = data.get("errorSchemas", {})
                    self.error_responses_references = data.get("errorResponseReferences", {})
                def model_dump(self, **kwargs):
                    if kwargs.get('by_alias'):
                        return {"errorSchemas": self.error_schemas, "errorResponseReferences": self.error_responses_references}
                    return {"error_schemas": self.error_schemas, "error_responses_references": self.error_responses_references}

            designer_agent.wrapper.execute = MagicMock(return_value=TempMockErrDef(mock_output_data))
        logger.log("Running ErrorDesignerAgent with MOCKED LLM call.", role="TestMain")
        result_dict = designer_agent.run(sample_run_context)
    else:
        logger.log("GEMINI_API_KEY found. Proceeding with LIVE LLM call for ErrorDesignerAgent in __main__.")
        result_dict = designer_agent.run(sample_run_context)
    logger.log(f"Result from ErrorDesignerAgent run:\n{json.dumps(result_dict, indent=2)}")
    if "error" not in result_dict and "errorSchemas" in result_dict:
        logger.log("ErrorDesignerAgent __main__ test deemed successful.")
    else:
        logger.log("ErrorDesignerAgent __main__ test deemed failed.", level="ERROR")
