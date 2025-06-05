import re
import os

# file_path should point to api_designer_crew/prompts.py from the repo root
file_path = os.path.join("api_designer_crew", "prompts.py")

try:
    with open(file_path, "r") as f:
        content = f.read()
except FileNotFoundError:
    print(f"Error: {file_path} not found. Ensure it exists at api_designer_crew/prompts.py")
    exit(1)

# New simplified content for API_DESIGNER_PROMPT
api_designer_prompt_variable_content = """API_DESIGNER_PROMPT = SUB_AGENT_ROLE_TEMPLATE + \"\"\"
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
\"\"\"
"""

if 'SUB_AGENT_ROLE_TEMPLATE' not in content:
    print("Error: SUB_AGENT_ROLE_TEMPLATE not found in prompts.py. Cannot define API_DESIGNER_PROMPT correctly.")
    # Adding a dummy one for script to proceed, in a real scenario, this would be an issue.
    content = "SUB_AGENT_ROLE_TEMPLATE = ''\\n" + content # Prepend if missing for script logic

# Check if API_DESIGNER_PROMPT exists, if not, add it.
if 'API_DESIGNER_PROMPT' not in content:
    sub_agent_map_match = re.search(r"SUB_AGENT_PROMPTS_MAP\s*=\s*{", content, re.MULTILINE)
    if sub_agent_map_match:
        insertion_point = sub_agent_map_match.start()
        content = content[:insertion_point] + api_designer_prompt_variable_content + "\\n\\n" + content[insertion_point:]
        print("API_DESIGNER_PROMPT variable added.")
    else:
        get_prompt_func_match = re.search(r"def get_sub_agent_prompt\(", content, re.MULTILINE)
        if get_prompt_func_match:
            insertion_point = get_prompt_func_match.start()
            content = content[:insertion_point] + api_designer_prompt_variable_content + "\\n\\n" + content[insertion_point:]
        else:
            content += "\\n\\n" + api_designer_prompt_variable_content
        print("API_DESIGNER_PROMPT variable added (fallback location).")
else:
    api_designer_prompt_pattern = re.compile(
        r"(API_DESIGNER_PROMPT\s*=\s*)(?:SUB_AGENT_ROLE_TEMPLATE\s*\+\s*)?\"\"\"(?:.|\n)*?\"\"\"",
        re.DOTALL
    )
    # Ensure new_rhs_for_replacement is correctly formatted as a Python string literal
    new_rhs_for_replacement = api_designer_prompt_variable_content.split("=", 1)[1].strip()
    # We need to make sure that new_rhs_for_replacement is a valid raw string or has escapes handled
    # For example, if new_rhs_for_replacement was `"""Hello"""`, it should become `r"""Hello"""` or `\"\"\"Hello\"\"\"` in the f-string
    # The current new_rhs_for_replacement is already `SUB_AGENT_ROLE_TEMPLATE + """..."""` which is fine.

    full_replacement_text = f"API_DESIGNER_PROMPT = {new_rhs_for_replacement}"

    if api_designer_prompt_pattern.search(content):
        content = api_designer_prompt_pattern.sub(full_replacement_text, content, count=1)
        print("API_DESIGNER_PROMPT was found and its content replaced.")
    else:
        print("API_DESIGNER_PROMPT found, but its structure was not as expected for replacement. Adding as new.")
        sub_agent_map_match = re.search(r"SUB_AGENT_PROMPTS_MAP\s*=\s*{", content, re.MULTILINE)
        if sub_agent_map_match:
            insertion_point = sub_agent_map_match.start()
            content = content[:insertion_point] + api_designer_prompt_variable_content + "\\n\\n" + content[insertion_point:]
        else:
            content += "\\n\\n" + api_designer_prompt_variable_content
        print("API_DESIGNER_PROMPT added as new due to replacement pattern mismatch.")

# Update SUB_AGENT_PROMPTS_MAP
agent_prompts_dict_pattern = re.compile(r"(SUB_AGENT_PROMPTS_MAP\s*=\s*\{)((?:.|\n)*?)(\})", re.DOTALL)
match = agent_prompts_dict_pattern.search(content)

if match:
    map_start_str = match.group(1)
    dict_content_str = match.group(2)
    map_end_str = match.group(3)

    new_entry_text = '"api_designer": API_DESIGNER_PROMPT'

    if '"api_designer":' in dict_content_str:
        # More robust replacement that handles potential trailing comma on the matched line
        dict_content_str = re.sub(r'"api_designer":\s*[^,}\s]+(,\s*)?', new_entry_text + '\\g<1>', dict_content_str)
        print("Existing 'api_designer' entry updated in SUB_AGENT_PROMPTS_MAP.")
    else:
        # Add new entry, ensuring comma handling and proper indentation
        if dict_content_str.strip() and not dict_content_str.strip().endswith(','):
            dict_content_str = dict_content_str.rstrip() + ',\\n'

        lines = dict_content_str.splitlines()
        indentation = "    " # Default indentation
        if lines and lines[-1].strip(): # Check if last line is not empty
            match_indent = re.match(r"^(\s*)", lines[-1])
            if match_indent:
                indentation = match_indent.group(1)
        elif not lines: # Empty dict content
             dict_content_str = "\n" # Start with a newline if dict was empty

        dict_content_str += f"{indentation}{new_entry_text},\\n"
        print("'api_designer' entry added to SUB_AGENT_PROMPTS_MAP.")

    content = map_start_str + dict_content_str.rstrip().rstrip(',') + '\n' + map_end_str # Ensure no double comma if last entry
else:
    print("SUB_AGENT_PROMPTS_MAP dictionary definition not found. Manual check required.")

with open(file_path, "w") as f:
    f.write(content)

print(f"Refactoring of {file_path} completed.")

with open(file_path, "r") as f:
    final_content = f.read()

verification_checks_passed = True
if "Functionality is now orchestrated by APIDesignerCrewOrchestrator" not in final_content:
    print("Verification FAILED: Orchestrator note not found in API_DESIGNER_PROMPT.")
    verification_checks_passed = False

# Ensure the check for mapping is precise
map_check_pattern = re.compile(r'"api_designer"\s*:\s*API_DESIGNER_PROMPT')
if not map_check_pattern.search(final_content):
    print("Verification FAILED: SUB_AGENT_PROMPTS_MAP mapping for 'api_designer' not found or incorrect.")
    verification_checks_passed = False

if verification_checks_passed:
    print("Verification: API_DESIGNER_PROMPT content and SUB_AGENT_PROMPTS_MAP mapping appear updated.")
else:
    print("Verification: Update to prompts.py might not be as expected. Please review.")
