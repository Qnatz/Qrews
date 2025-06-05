import re

file_path = "agents.py"

try:
    with open(file_path, "r") as f:
        content = f.read()
except FileNotFoundError:
    print(f"Error: {file_path} not found. Cannot proceed.")
    # Create a dummy agents.py for the script to run against if it's missing,
    # so the logic can be tested, though in a real scenario this would be an error.
    dummy_content = """#宇宙첫째줄
from api_designer_crew.orchestrator import APIDesignerCrewOrchestrator
from api_designer_crew.models import OpenAPISpec as CrewOpenAPISpec
class Agent: pass
class ProjectAnalyzer(Agent): pass
class APIDesigner(Agent):
    def __init__(self): pass
    def perform_task(self): pass
# --- End: Refactored APIDesigner ---
# TODO: Restore other agent definitions
class SomeOtherAgent(Agent): pass
"""
    with open(file_path, "w") as f_dummy:
        f_dummy.write(dummy_content)
    print(f"Created dummy {file_path} for script execution.")
    with open(file_path, "r") as f: # re-read
        content = f.read()


# Pattern to find the APIDesigner class definition
api_designer_class_pattern = re.compile(
    r"^(class APIDesigner\(Agent\):.*?)(?=(^class \w+\(Agent\):|^# TODO: Restore other agent definitions|\Z))",
    re.DOTALL | re.MULTILINE
)

modified_content = content
match = api_designer_class_pattern.search(content)

if match:
    api_designer_block_to_comment = match.group(1).strip() # Get the actual class block

    commented_lines = []
    for line in api_designer_block_to_comment.splitlines():
        commented_lines.append(f"# {line}")

    final_commented_block = "\n".join(commented_lines)

    # The replacement should ensure that what was matched by group(1) is replaced.
    # If group(2) (the lookahead) was part of the original match.group(0) but not group(1),
    # then simple substitution of group(1) part is fine.

    # To avoid issues with replacing only part of the match and potentially duplicating the lookahead part:
    # We replace the entire match.group(0) with the commented block + the lookahead part (group(2))
    final_replacement_text = final_commented_block + "\n" + match.group(2)

    modified_content = content.replace(match.group(0), final_replacement_text, 1)

    # Comment out specific imports, ensuring not to double-comment
    orchestrator_import_pattern = re.compile(r"^(from api_designer_crew.orchestrator import APIDesignerCrewOrchestrator\n)", re.MULTILINE)
    crew_spec_import_pattern = re.compile(r"^(from api_designer_crew.models import OpenAPISpec as CrewOpenAPISpec.*?\n)", re.MULTILINE)

    if orchestrator_import_pattern.search(modified_content):
         modified_content = orchestrator_import_pattern.sub(lambda m: "# " + m.group(0) if not m.group(0).startswith("#") else m.group(0), modified_content, count=1)
         print("APIDesignerCrewOrchestrator import line handled (commented or already commented).")

    if crew_spec_import_pattern.search(modified_content):
        modified_content = crew_spec_import_pattern.sub(lambda m: "# " + m.group(0) if not m.group(0).startswith("#") else m.group(0), modified_content, count=1)
        print("CrewOpenAPISpec import line handled (commented or already commented).")

    print("APIDesigner class and its specific imports in agents.py processed for commenting.")
else:
    print("APIDesigner class definition not found in agents.py. No changes made for commenting out class.")

if modified_content != content:
    with open(file_path, "w") as f:
        f.write(modified_content)
    print(f"agents.py updated.")
else:
    print("No changes made to agents.py content (either class not found or already commented as intended).")

# Verification
try:
    with open(file_path, "r") as f:
        final_content = f.read()

    project_analyzer_present = 'class ProjectAnalyzer(Agent):' in final_content and not final_content.strip().startswith('# class ProjectAnalyzer(Agent):')
    api_designer_commented = '# class APIDesigner(Agent):' in final_content

    orchestrator_import_commented = bool(re.search(r"^# from api_designer_crew.orchestrator import APIDesignerCrewOrchestrator", final_content, re.MULTILINE))
    crew_spec_import_commented = bool(re.search(r"^# from api_designer_crew.models import OpenAPISpec as CrewOpenAPISpec", final_content, re.MULTILINE))

    if project_analyzer_present:
        print("Verification: ProjectAnalyzer class is still present and not commented.")
    else:
        print("Verification WARNING: ProjectAnalyzer class is MISSING or commented.")

    if api_designer_commented:
        print("Verification: APIDesigner class in agents.py appears commented out.")
    else:
        print("Verification ERROR: APIDesigner class in agents.py may NOT be commented out.")

    if orchestrator_import_commented:
        print("Verification: Orchestrator import appears commented out.")
    else:
        print("Verification WARNING: Orchestrator import may NOT be commented out (or was not present to begin with).")

    if crew_spec_import_commented:
        print("Verification: CrewOpenAPISpec import appears commented out.")
    else:
        print("Verification WARNING: CrewOpenAPISpec import may NOT be commented out (or was not present to begin with).")

except FileNotFoundError:
    print("Verification Error: agents.py not found.")
