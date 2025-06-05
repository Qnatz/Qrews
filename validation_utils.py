from typing import List, Dict, Any # Or more specific types as needed
# Assuming context_handler.py is in the same directory or Python path
from context_handler import ProjectContext, TechStack

def validate_tech_stack(agent_output_string: str, expected_tech_stack: TechStack) -> List[str]:
    validation_errors = []
    if not agent_output_string: # Handle empty output string
        validation_errors.append("Agent output string is empty. Cannot validate tech stack.")
        return validation_errors

    output_lower = agent_output_string.lower()

    # Database validation
    if expected_tech_stack.database:
        db_lower = expected_tech_stack.database.lower()
        # General check: if expected DB is mentioned, it's usually good.
        # The problem is when an *alternative* is mentioned.

        if "postgres" in db_lower or "postgresql" in db_lower:
            if "mongodb" in output_lower or "mongo" in output_lower:
                validation_errors.append(f"Tech stack mismatch: Output mentions MongoDB/Mongo, but PostgreSQL is expected.")
        elif "mongodb" in db_lower or "mongo" in db_lower:
            if "postgres" in output_lower or "postgresql" in output_lower or "sql" in output_lower: # Simple check for SQL
                validation_errors.append(f"Tech stack mismatch: Output mentions PostgreSQL/SQL, but MongoDB is expected.")
        elif "mysql" in db_lower:
            if "postgres" in output_lower or "mongodb" in output_lower:
                 validation_errors.append(f"Tech stack mismatch: Output mentions PostgreSQL or MongoDB, but MySQL is expected.")
        elif "sqlite" in db_lower:
            if "postgres" in output_lower or "mongodb" in output_lower or "mysql" in output_lower:
                 validation_errors.append(f"Tech stack mismatch: Output mentions PostgreSQL, MongoDB or MySQL, but SQLite is expected.")
        # Add more DB specific checks if necessary

    # Backend validation
    if expected_tech_stack.backend:
        backend_lower = expected_tech_stack.backend.lower()
        if "node.js" in backend_lower or "express" in backend_lower or "javascript" in backend_lower and "react" not in backend_lower and "vue" not in backend_lower and "angular" not in backend_lower : # ensure not frontend JS
            if "python" in output_lower or "flask" in output_lower or "django" in output_lower or "java" in output_lower or "spring" in output_lower or "ruby" in output_lower or "rails" in output_lower:
                validation_errors.append(f"Tech stack mismatch: Output mentions Python/Flask/Django/Java/Spring/Ruby/Rails, but Node.js/Express (JavaScript backend) is expected.")
        elif "python" in backend_lower or "flask" in backend_lower or "django" in backend_lower:
            if "node.js" in output_lower or "express" in output_lower or "require(" in output_lower or "java" in output_lower or "spring" in output_lower:
                validation_errors.append(f"Tech stack mismatch: Output mentions Node.js/Express/Java/Spring, but Python (e.g., Flask/Django) is expected for the backend.")
        elif "java" in backend_lower or "spring" in backend_lower:
            if "node.js" in output_lower or "python" in output_lower or "ruby" in output_lower:
                 validation_errors.append(f"Tech stack mismatch: Output mentions Node.js/Python/Ruby, but Java/Spring is expected for the backend.")
        # Add more backend specific checks

    # Frontend validation
    if expected_tech_stack.frontend:
        frontend_lower = expected_tech_stack.frontend.lower()
        if "react" in frontend_lower:
            if "angular" in output_lower or "<ng-" in output_lower or "vue" in output_lower or "v-if" in output_lower:
                 validation_errors.append(f"Tech stack mismatch: Output mentions Angular/Vue, but React is expected for the frontend.")
        elif "angular" in frontend_lower:
            if "react" in output_lower or "create-react-app" in output_lower or "vue" in output_lower:
                 validation_errors.append(f"Tech stack mismatch: Output mentions React/Vue, but Angular is expected for the frontend.")
        elif "vue" in frontend_lower:
            if "react" in output_lower or "angular" in output_lower:
                 validation_errors.append(f"Tech stack mismatch: Output mentions React/Angular, but Vue is expected for the frontend.")
        # Add more frontend specific checks

    return validation_errors

def get_tech_stack_validation_prompt_segment(project_context: ProjectContext) -> str:
    segments = ["CRITICAL INSTRUCTIONS: You MUST adhere to the following technology stack defined in the project context."]

    has_specific_tech = False
    if project_context.tech_stack:
        if project_context.tech_stack.database:
            segments.append(f"- Database: You MUST use {project_context.tech_stack.database}. Do NOT use or suggest any other database system. Avoid generic SQL terms if a NoSQL DB is specified, and vice-versa.")
            has_specific_tech = True
        if project_context.tech_stack.backend:
            segments.append(f"- Backend: You MUST use {project_context.tech_stack.backend}. Do NOT use or suggest any other backend technologies or languages.")
            has_specific_tech = True
        if project_context.tech_stack.frontend:
            segments.append(f"- Frontend: You MUST use {project_context.tech_stack.frontend}. Do NOT use or suggest any other frontend frameworks or libraries.")
            has_specific_tech = True

    if not has_specific_tech: # Checks if any specific tech was actually listed
        segments.append("The technology stack is not fully specified. Proceed with caution and make reasonable, modern technology choices where not specified. Clearly state your choices.")

    segments.append("Failure to adhere to these technology choices where specified will result in an error and require rework.")
    return "\n".join(segments)


if __name__ == '__main__':
    # Example TechStack and ProjectContext for testing
    sample_tech_stack_node_pg = TechStack(frontend="React", backend="Node.js/Express", database="PostgreSQL")
    sample_context_node_pg = ProjectContext(
        project_name="Test Project NodePG",
        project_type="fullstack",
        tech_stack=sample_tech_stack_node_pg,
        db_choice="PostgreSQL", # Ensure this matches tech_stack for consistency
        deployment_target="AWS",
        security_level="standard"
    )

    sample_tech_stack_py_mongo = TechStack(frontend="Vue", backend="Python/Flask", database="MongoDB")
    sample_context_py_mongo = ProjectContext(
        project_name="Test Project PyMongo",
        project_type="fullstack",
        tech_stack=sample_tech_stack_py_mongo,
        db_choice="MongoDB",
        deployment_target="GCP",
        security_level="enhanced"
    )

    print("--- Testing validate_tech_stack ---")
    output1 = "The architecture will use MongoDB and a Python backend."
    errors1 = validate_tech_stack(output1, sample_tech_stack_node_pg)
    print(f"Output: '{output1}'\nErrors for Node/PG: {errors1}") # Expect errors

    output2 = "We will use PostgreSQL as the database and Node.js for the server."
    errors2 = validate_tech_stack(output2, sample_tech_stack_node_pg)
    print(f"Output: '{output2}'\nErrors for Node/PG: {errors2}") # Expect no errors

    output3 = "For the API, we'll implement it using Flask." # Python Flask
    errors3 = validate_tech_stack(output3, sample_tech_stack_node_pg) # Expect Node.js
    print(f"Output: '{output3}'\nErrors for Node/PG: {errors3}") # Expect backend error

    output4 = "The system uses SQL and a Node.js backend."
    errors4 = validate_tech_stack(output4, sample_tech_stack_py_mongo) # Expect MongoDB
    print(f"Output: '{output4}'\nErrors for Py/Mongo: {errors4}") # Expect DB error

    output5 = "Frontend will be Angular."
    errors5 = validate_tech_stack(output5, sample_tech_stack_node_pg) # Expect React
    print(f"Output: '{output5}'\nErrors for Node/PG (React): {errors5}")

    output6 = "This is a Java Spring backend with a React frontend and MySQL database."
    errors6 = validate_tech_stack(output6, sample_tech_stack_node_pg) # Expect Node/PG/React
    print(f"Output: '{output6}'\nErrors for Node/PG/React: {errors6}")


    print("\n--- Testing get_tech_stack_validation_prompt_segment ---")
    prompt_segment_node_pg = get_tech_stack_validation_prompt_segment(sample_context_node_pg)
    print(f"Prompt for Node/PG:\n{prompt_segment_node_pg}")

    prompt_segment_py_mongo = get_tech_stack_validation_prompt_segment(sample_context_py_mongo)
    print(f"Prompt for Py/Mongo:\n{prompt_segment_py_mongo}")

    empty_tech_stack = TechStack(frontend=None, backend=None, database=None)
    empty_context = ProjectContext(
        project_name="Empty Stack Project",
        project_type="fullstack",
        tech_stack=empty_tech_stack,
        db_choice="",
        deployment_target="Heroku",
        security_level="standard"
        )
    prompt_segment_empty = get_tech_stack_validation_prompt_segment(empty_context)
    print(f"Prompt for Empty Stack:\n{prompt_segment_empty}")

    partially_empty_tech_stack = TechStack(frontend="React", backend=None, database="SQLite")
    partially_empty_context = ProjectContext(
        project_name="Partial Stack Project",
        project_type="fullstack",
        tech_stack=partially_empty_tech_stack,
        db_choice="SQLite",
        deployment_target="AWS",
        security_level="standard"
    )
    prompt_segment_partial = get_tech_stack_validation_prompt_segment(partially_empty_context)
    print(f"Prompt for Partial Stack (React, SQLite):\n{prompt_segment_partial}")
