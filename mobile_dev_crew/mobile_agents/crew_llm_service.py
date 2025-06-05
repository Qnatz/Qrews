# mobile_developer_crew/crew_llm_service.py
import json
import os
import time
import requests # This import is allowed as it's a standard library for HTTP calls

from .crew_internal_prompts import get_crew_internal_prompt
from .agent_config import load_agent_config_from_json # Use the new config loader

MAX_LLM_RETRIES = 3
RETRY_LLM_DELAY_SECONDS = 5
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models" # Standard Gemini base

# Default safety settings for Gemini
DEFAULT_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

def execute_crew_llm_task(agent_name: str, prompt_input_data: dict, api_key: str = None) -> dict:
    """
    Executes an LLM task for a given crew sub-agent.
    It fetches model config, generates a prompt, calls the LLM, and handles retries.
    """
    print(f"[{agent_name}] Initiating LLM task. Input data for prompt: {prompt_input_data}")

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY") # Standard Gemini key env var

    if not api_key:
        error_msg = f"[{agent_name}] Gemini API key not found. Set GEMINI_API_KEY environment variable or pass via argument."
        print(f"ERROR: {error_msg}")
        return {"status": "error", "message": error_msg}

    agent_configs = load_agent_config_from_json()
    model_name = agent_configs.get(agent_name)

    if not model_name:
        error_msg = f"[{agent_name}] Model configuration not found for agent."
        print(f"ERROR: {error_msg}")
        return {"status": "error", "message": error_msg}

    if model_name == "System": # Handle system tasks that don't call LLMs
        print(f"[{agent_name}] Identified as a System task. No LLM call needed.")
        return {
            "status": "success",
            "data": f"System task '{agent_name}' processed with input: {prompt_input_data}",
            "message": "System task executed locally."
        }

    try:
        prompt_string = get_crew_internal_prompt(agent_name, prompt_input_data)
        # print(f"[{agent_name}] Generated prompt (first 300 chars): {prompt_string[:300]}...")
    except ValueError as e_prompt:
        error_msg = f"[{agent_name}] Error generating prompt: {e_prompt}"
        print(f"ERROR: {error_msg}")
        return {"status": "error", "message": error_msg}

    model_identifier = model_name # Use the full model name from config e.g. "gemini-1.5-flash-latest"
    # The logic below for splitting model_identifier might be too specific if model_name is already clean.
    # model_identifier = model_name.split('/')[-1]
    # if ":" in model_identifier:
    #     model_identifier = model_identifier.split(":")[0]

    # Construct URL based on whether it's a tuned model or standard
    if model_name.startswith("tunedModels/"):
         llm_url = f"{GEMINI_API_BASE_URL}/{model_name}:generateContent?key={api_key}"
    else: # Standard model like "gemini-1.5-flash" or "gemini-1.0-pro"
         llm_url = f"{GEMINI_API_BASE_URL}/{model_identifier}:generateContent?key={api_key}"


    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt_string}]}],
        "safetySettings": DEFAULT_SAFETY_SETTINGS,
        # "generationConfig": {} # Add if specific generation params are needed per agent
    }

    for attempt in range(MAX_LLM_RETRIES):
        print(f"[{agent_name}] Attempting LLM call {attempt + 1}/{MAX_LLM_RETRIES} to model {model_name}...")
        try:
            response = requests.post(llm_url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()

            response_data = response.json()

            if 'candidates' in response_data and response_data['candidates']:
                candidate = response_data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content'] and candidate['content']['parts']:
                    llm_response_text = candidate['content']['parts'][0]['text']
                    print(f"[{agent_name}] LLM call successful. Response snippet: {llm_response_text[:100]}...")
                    return {"status": "success", "data": llm_response_text}
                elif 'finishReason' in candidate and candidate['finishReason'] == 'SAFETY':
                    safety_ratings = candidate.get('safetyRatings', [])
                    error_msg = f"[{agent_name}] LLM response blocked due to safety settings. Finish reason: SAFETY. Ratings: {safety_ratings}"
                    print(f"ERROR: {error_msg}")
                    return {"status": "error", "message": error_msg, "details": {"finish_reason": "SAFETY", "safety_ratings": safety_ratings}}

            error_msg = f"[{agent_name}] LLM response format unexpected: No valid content in candidates. Response: {response_data}"
            print(f"ERROR: {error_msg}")
            # Do not retry on unexpected format, it's likely a persistent issue.
            return {"status": "error", "message": error_msg}

        except requests.exceptions.HTTPError as http_err:
            error_text = http_err.response.text if http_err.response else "No response text"
            status_code = http_err.response.status_code if http_err.response is not None else 0
            error_msg = f"[{agent_name}] HTTP error {status_code} calling LLM: {error_text[:500]}"
            print(f"ERROR: {error_msg}")
            if status_code == 429 or status_code >= 500:
                if attempt < MAX_LLM_RETRIES - 1:
                    print(f"[{agent_name}] Retrying in {RETRY_LLM_DELAY_SECONDS}s...")
                    time.sleep(RETRY_LLM_DELAY_SECONDS)
                else:
                    return {"status": "error", "message": error_msg} # Failed after retries
            else:
                return {"status": "error", "message": error_msg} # Non-retryable HTTP error
        except requests.exceptions.RequestException as req_err:
            error_msg = f"[{agent_name}] Request exception calling LLM: {req_err}"
            print(f"ERROR: {error_msg}")
            if attempt < MAX_LLM_RETRIES - 1:
                print(f"[{agent_name}] Retrying in {RETRY_LLM_DELAY_SECONDS}s...")
                time.sleep(RETRY_LLM_DELAY_SECONDS)
            else:
                return {"status": "error", "message": error_msg} # Failed after retries
        except Exception as e:
            error_msg = f"[{agent_name}] Unexpected error during LLM call attempt {attempt + 1}: {e}"
            print(f"ERROR: {error_msg}")
            # Do not retry on general unexpected errors, could be code issue.
            return {"status": "error", "message": error_msg}

    final_error_msg = f"[{agent_name}] LLM task failed after {MAX_LLM_RETRIES} retries."
    print(f"ERROR: {final_error_msg}")
    return {"status": "error", "message": final_error_msg}

if __name__ == '__main__':
    print("--- Testing crew_llm_service.py ---")
    test_agent_name = "ui_structure_designer"
    test_prompt_input = {
        "tech_stack_mobile": "TestFramework",
        "project_details": "A simple test application.",
        "user_requirements": "One screen that displays 'Hello World'."
    }

    print(f"\nAttempting LLM task for: {test_agent_name}")
    # result = execute_crew_llm_task(test_agent_name, test_prompt_input)
    # print(f"Result for {test_agent_name}:")
    # print(json.dumps(result, indent=2))

    print("\nSimulating system task for mobile_merger:")
    merger_input = {"data_to_merge": "example"}
    # Ensure mobile_merger is in agent_config.json with model "System" for this to work
    merger_result = execute_crew_llm_task("mobile_merger", merger_input)
    print(f"Result for mobile_merger:")
    print(json.dumps(merger_result, indent=2))

    print("\nNOTE: Actual LLM call for ui_structure_designer is commented out in __main__.")
    print("To test live, uncomment, ensure GEMINI_API_KEY is set, and agent_config.json is correct and accessible.")
