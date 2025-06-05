import re
import os

file_path = "prompts.py" # Target the root prompts.py

try:
    with open(file_path, "r") as f:
        content = f.read()
except FileNotFoundError:
    # Create a dummy prompts.py if not found
    print(f"Warning: {file_path} not found. Creating a placeholder for it.")
    with open(file_path, "w") as f_create:
        f_create.write("""
AGENT_ROLE_TEMPLATE = ""
RESPONSE_FORMAT_TEMPLATE = ""
COMMON_CONTEXT_TEMPLATE = ""

API_DESIGNER_PROMPT = AGENT_ROLE_TEMPLATE + \"\"\"
Old API Designer prompt content.
{common_context}
\"\"\" + RESPONSE_FORMAT_TEMPLATE + \"\"\"
=== OUTPUT FORMAT ===
Thought: Old thoughts.
Final Answer: Old final answer.
\"\"\"

AGENT_PROMPTS = {}
def get_agent_prompt(agent_name, context): return ""
""")
    with open(file_path, "r") as f: # Re-read after creation
        content = f.read()


# Ensure AGENT_ROLE_TEMPLATE and RESPONSE_FORMAT_TEMPLATE are in the content for the new prompt string
if 'AGENT_ROLE_TEMPLATE' not in content:
    content = "AGENT_ROLE_TEMPLATE = ''\\n" + content # Add dummy if missing
if 'RESPONSE_FORMAT_TEMPLATE' not in content:
    content = "RESPONSE_FORMAT_TEMPLATE = ''\\n" + content # Add dummy if missing


new_api_designer_prompt_definition_str = """API_DESIGNER_PROMPT = AGENT_ROLE_TEMPLATE + \\
\"\"\"
Your role as the main API Designer is to oversee the generation of a complete OpenAPI specification.
This is achieved by coordinating a dedicated crew of specialized sub-agents.
You will ensure the final specification is coherent, validated, and meets all project requirements.
The process involves orchestrating the following sub-tasks:
1.  Endpoint Planning
2.  Schema Design
3.  Request/Response Definition
4.  Authentication and Authorization Design
5.  Standardized Error Design
6.  Merging all generated parts into a single OpenAPI document.
7.  Validating the final specification.

The actual LLM-driven generation for these sub-tasks is handled by the respective sub-agents in the 'api_designer_crew'.
Your primary function in 'perform_task' is to manage this crew.
{common_context}
\"\"\" + RESPONSE_FORMAT_TEMPLATE + \\
\"\"\"
=== OUTPUT FORMAT ===
Thought: [As the main APIDesigner agent, your thought process focuses on initiating the APIDesignerCrewOrchestrator and processing its final output. You are not directly calling an LLM with this prompt to generate an OpenAPI spec.]
Final Answer: The API specification will be generated and validated by the API Designer Crew, orchestrated by this agent.
\"\"\"
"""

# Pattern to find the API_DESIGNER_PROMPT assignment
api_designer_prompt_pattern = re.compile(
    r"^(API_DESIGNER_PROMPT\s*=\s*)(?:(?:AGENT_ROLE_TEMPLATE\s*\+\s*)?\"\"\"(?:.|\n)*?\"\"\"(?:\s*\+\s*RESPONSE_FORMAT_TEMPLATE\s*\+\s*\"\"\"(?:.|\n)*?\"\"\"|\s*\+\s*RESPONSE_FORMAT_TEMPLATE)?|.*?)",
    re.MULTILINE
)

replacement_text_for_var = new_api_designer_prompt_definition_str.strip() + "\\n"

if re.search(r"^API_DESIGNER_PROMPT\s*=", content, re.MULTILINE):
    content = api_designer_prompt_pattern.sub(replacement_text_for_var, content, count=1)
    print("Root API_DESIGNER_PROMPT was found and replaced with a new placeholder.")
else:
    print("Root API_DESIGNER_PROMPT variable definition not found. Adding it.")
    agent_prompts_match = re.search(r"^AGENT_PROMPTS\s*=\s*\{", content, re.MULTILINE)
    if agent_prompts_match:
        content = content[:agent_prompts_match.start()] + replacement_text_for_var + "\\n" + content[agent_prompts_match.start():]
    else:
        content += "\\n" + replacement_text_for_var


# Ensure AGENT_PROMPTS['api_designer'] points to the (now placeholder) API_DESIGNER_PROMPT
agent_prompts_dict_pattern = re.compile(r"(AGENT_PROMPTS\s*=\s*\{)((?:.|\n)*?)(\})", re.DOTALL)
match = agent_prompts_dict_pattern.search(content)

if match:
    map_start_group = match.group(1)
    dict_internal_content = match.group(2).strip()
    map_end_group = match.group(3)

    new_entry_key_value = '"api_designer": API_DESIGNER_PROMPT'

    # Remove existing entry if present
    dict_internal_content = re.sub(r'"api_designer"\s*:\s*[^,}\s]+,?\s*', '', dict_internal_content).strip()

    # Add the new entry
    if not dict_internal_content: # Empty or became empty
        processed_dict_content = f"\\n    {new_entry_key_value}\\n"
    elif dict_internal_content.endswith(','):
        processed_dict_content = f"\\n{dict_internal_content}\\n    {new_entry_key_value}\\n"
    else: # Has content, doesn't end with comma
        processed_dict_content = f"\\n{dict_internal_content},\\n    {new_entry_key_value}\\n"

    content = map_start_group + processed_dict_content + map_end_group
    # Clean up any potential double commas or commas before '}'
    content = re.sub(r',\s*,', ',', content)
    content = re.sub(r',\s*(\})', r'\\1', content) # Corrected escaping for \1
    print("Root AGENT_PROMPTS dictionary updated/verified for 'api_designer'.")
else:
    print("Root AGENT_PROMPTS dictionary definition not found. Creating it.")
    content += """
AGENT_PROMPTS = {
    "api_designer": API_DESIGNER_PROMPT
}
"""

with open(file_path, "w") as f:
    f.write(content)

print(f"Root {file_path} refactored for API_DESIGNER_PROMPT.")

# Verification
with open(file_path, "r") as f:
    final_content = f.read()

verification_checks_passed = True
if "Functionality is now orchestrated by APIDesignerCrewOrchestrator" not in final_content:
    print("Verification FAILED: Orchestrator note not found in API_DESIGNER_PROMPT.")
    verification_checks_passed = False

if not re.search(r'"api_designer"\s*:\s*API_DESIGNER_PROMPT', final_content):
    print("Verification FAILED: AGENT_PROMPTS mapping for 'api_designer' not found or incorrect.")
    verification_checks_passed = False

if verification_checks_passed:
    print("Verification: Root API_DESIGNER_PROMPT content and AGENT_PROMPTS mapping appear updated.")
else:
    print("Verification: Update to root prompts.py might not be as expected. Please review.")
