import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any # Added Dict and Any

from pydantic import BaseModel, ValidationError, Field # Added Field
from models import PlatformRequirements, TechProposal, ApprovedTechStack # New models

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TechStack(BaseModel):
    frontend: Optional[str] = None
    backend: Optional[str] = None
    database: Optional[str] = None

class AnalysisOutput(BaseModel):
    project_type_confirmed: Optional[str] = None
    key_requirements: Optional[List[str]] = None
    backend_needed: Optional[bool] = None
    frontend_needed: Optional[bool] = None
    mobile_needed: Optional[bool] = None
    suggested_tech_stack: Optional[TechStack] = None # <-- ADDED THIS NEW FIELD

class ProjectContext(BaseModel):
    project_name: str
    project_type: str  # e.g., "fullstack", "api", "mobile_app"
    tech_stack: TechStack
    db_choice: str  # e.g., "PostgreSQL", "MongoDB", "SQLite"
    deployment_target: str  # e.g., "AWS", "GCP", "Azure", "Heroku"
    security_level: str  # e.g., "standard", "enhanced"
    analysis: Optional[AnalysisOutput] = None

    # New fields for Tech Council framework
    platform_requirements: Optional[PlatformRequirements] = Field(None, description="Specifies the target platforms (web, iOS, Android) for the project.")
    tech_proposals: Optional[Dict[str, List[TechProposal]]] = Field(default_factory=dict, description="Stores technology proposals from agents, categorized by area (e.g., 'database', 'web_backend').")
    approved_tech_stack: Optional[ApprovedTechStack] = Field(None, description="The final technology stack approved by the Tech Council.")
    decision_rationale: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Rationale behind technology choices, dependency checks, mandatory review notes, and consensus outcomes.")

    plan: Optional[str] = None
    architecture: Optional[str] = None
    api_specs: Optional[str] = None
    current_dir: Optional[str] = "/"
    objective: Optional[str] = ""
    project_summary: Optional[str] = ""
    current_code_snippet: Optional[str] = ""
    error_report: Optional[str] = ""

def load_context(context_file_path: Path) -> ProjectContext:
    """
    Loads project context from a JSON file.

    If the file doesn't exist, creates a default ProjectContext and saves it.
    Validates data against Pydantic models. Logs errors and returns a default
    context if the file is corrupted or validation fails.
    """
    default_tech_stack = TechStack(frontend="React", backend="Python/FastAPI", database="SQLite")
    # Initialize new models for the default context
    default_platform_requirements = PlatformRequirements()
    default_approved_tech_stack = ApprovedTechStack()

    default_context = ProjectContext(
        project_name="New Project",
        project_type="fullstack",
        tech_stack=default_tech_stack,
        db_choice="SQLite",
        deployment_target="Heroku",
        security_level="standard",
        # Initialize new fields
        platform_requirements=default_platform_requirements,
        tech_proposals={},
        approved_tech_stack=default_approved_tech_stack,
        decision_rationale={}
    )

    if context_file_path.exists():
        try:
            with open(context_file_path, 'r') as f:
                data = json.load(f)
            context = ProjectContext(**data)
            logging.info(f"Project context loaded successfully from {context_file_path}")
            return context
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from {context_file_path}. Returning default context.")
            return default_context
        except ValidationError as e:
            logging.error(f"Validation error loading context from {context_file_path}: {e}. Returning default context.")
            return default_context
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading context from {context_file_path}: {e}. Returning default context.")
            return default_context
    else:
        logging.info(f"Context file {context_file_path} not found. Creating a default context and saving it.")
        try:
            if save_context(default_context, context_file_path):
                logging.info(f"Successfully saved initial default context to {context_file_path}")
            else:
                # The save_context function itself logs detailed errors, 
                # so we just add a specific message for the load_context scenario.
                logging.error(f"Failed to save initial default context to {context_file_path} during load_context. Check previous errors for details.")
            return default_context
        except Exception as e:
            # This catch block is for unexpected errors during the save_context call itself,
            # beyond what save_context handles (like network issues if saving remotely, though not applicable here).
            logging.error(f"Unexpected error occurred while attempting to save initial default context to {context_file_path}: {e}. Returning in-memory default context.")
            return default_context


def save_context(context_data: ProjectContext, context_file_path: Path) -> bool:
    """
    Saves the project context model data to a JSON file.

    Uses model_dump_json for Pydantic model serialization.
    Returns True if successful, False otherwise. Logs errors if saving fails.
    """
    try:
        json_data = context_data.model_dump_json(indent=4)
        if not json_data:
            logging.error(f"Failed to serialize context data to JSON for {context_file_path}. model_dump_json returned empty or None.")
            return False

        with open(context_file_path, 'w') as f:
            f.write(json_data)
        logging.info(f"Project context saved successfully to {context_file_path}")
        return True
    except IOError as e:
        logging.error(f"IOError saving context to {context_file_path}: {e}")
        return False
    except Exception as e:  # This will catch errors from model_dump_json or file IO
        logging.error(f"An unexpected error occurred while saving context to {context_file_path} (possibly during serialization or file write): {e}")
        return False

if __name__ == '__main__':
    # Example usage:
    context_path = Path("project_context.json")

    # Load context (or create default if not exists)
    current_context = load_context(context_path)
    logging.info(f"Loaded project name: {current_context.project_name}")

    # Modify context (example)
    current_context.project_name = "My Awesome AI Project"
    current_context.objective = "To demonstrate context handling"
    if current_context.analysis is None:
        current_context.analysis = AnalysisOutput()
    current_context.analysis.key_requirements = ["Scalability", "User-friendly interface"]

    # Save context
    if save_context(current_context, context_path):
        logging.info("Context updated and saved successfully.")
    else:
        logging.error("Failed to save updated context.")

    # Load again to verify
    reloaded_context = load_context(context_path)
    logging.info(f"Reloaded project objective: {reloaded_context.objective}")
    if reloaded_context.analysis:
        logging.info(f"Reloaded key requirements: {reloaded_context.analysis.key_requirements}")
