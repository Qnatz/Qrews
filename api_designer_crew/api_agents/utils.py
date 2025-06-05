import json
import time
import requests
import os
from typing import Type, TypeVar, Dict, Any, Optional

from pydantic import BaseModel, ValidationError

# Assuming GeminiConfig and Logger might be needed from the main project
# This will require adjusting sys.path or making these globally available if running standalone
# For now, let's define placeholders or assume they can be imported if PYTHONPATH is set up.

# Placeholder for GeminiConfig - in a real scenario, this would be imported or passed
class GeminiConfigPlaceholder:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    API_KEY = os.environ.get("GEMINI_API_KEY") # Needs API key
    DEFAULT_MODEL_NAME = "gemini-pro"
    SAFETY_SETTINGS = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    GENERATION_CONFIG = {
        "temperature": 0.7,
        "topP": 0.9,
        "topK": 40,
        "maxOutputTokens": 8192, # Increased from 2048 for potentially larger outputs
    }

    @staticmethod
    def get_generation_config(agent_name: Optional[str] = None) -> Dict[str, Any]:
        # Simplified: real one might have agent-specific configs
        return GeminiConfigPlaceholder.GENERATION_CONFIG.copy()

# Placeholder for Logger
class LoggerPlaceholder:
    def log(self, message: str, role: str = "SubAgentUtil", level: str = "INFO"):
        print(f"[{level}] [{role}] {message}")

# Generic Type Variable for Pydantic models
T = TypeVar('T', bound=BaseModel)

# Load agent configurations
AGENT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'agent_config.json')
AGENT_MODEL_CONFIG = {}
if os.path.exists(AGENT_CONFIG_PATH):
    with open(AGENT_CONFIG_PATH, 'r') as f:
        try:
            AGENT_MODEL_CONFIG = json.load(f)
        except json.JSONDecodeError as e:
            LoggerPlaceholder().log(f"Error decoding JSON from {AGENT_CONFIG_PATH}: {e}", level="ERROR")
            AGENT_MODEL_CONFIG = {} # Default to empty if config is malformed
else:
    LoggerPlaceholder().log(f"Agent config file not found at {AGENT_CONFIG_PATH}", level="WARNING")


class SubAgentLLMInvoker:
    def __init__(self, agent_name: str, logger: Optional[LoggerPlaceholder] = None, gemini_config: Optional[GeminiConfigPlaceholder] = None):
        self.agent_name = agent_name
        self.logger = logger or LoggerPlaceholder()
        self.gemini_config = gemini_config or GeminiConfigPlaceholder()
        self.model_name = AGENT_MODEL_CONFIG.get(agent_name, self.gemini_config.DEFAULT_MODEL_NAME)
        self.generation_config = self.gemini_config.get_generation_config(agent_name)

        if not self.gemini_config.API_KEY:
            self.logger.log(f"Gemini API key not found for {self.agent_name}.", level="ERROR")
            # Not raising ValueError here to allow SubAgentWrapper to be instantiated
            # The error will be caught if invoke is actually called without an API key.

    def invoke(self, prompt: str, max_retries: int = 2, initial_delay: float = 1.0) -> str:
        if not self.gemini_config.API_KEY:
            return "Error: Gemini API key is not configured."

        if self.model_name == "system":
            self.logger.log(f"Agent {self.agent_name} is a system agent. Bypassing LLM call.", role=self.agent_name)
            return "Error: System agents should not use invoke_llm directly through this method."

        url = f"{self.gemini_config.BASE_URL}/{self.model_name}:generateContent"
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': self.generation_config,
            'safetySettings': self.gemini_config.SAFETY_SETTINGS
        }
        headers = {'Content-Type': 'application/json'}

        current_retry = 0
        delay = initial_delay
        while current_retry <= max_retries:
            try:
                self.logger.log(f"Attempting to call {self.model_name} for {self.agent_name} (Attempt {current_retry + 1})", role=self.agent_name)
                response = requests.post(
                    url,
                    params={'key': self.gemini_config.API_KEY},
                    headers=headers,
                    json=payload,
                    timeout=120
                )
                response.raise_for_status()

                data = response.json()

                if 'candidates' in data and data['candidates'] and 'content' in data['candidates'][0] and \
                   'parts' in data['candidates'][0]['content'] and data['candidates'][0]['content']['parts'] and \
                   'text' in data['candidates'][0]['content']['parts'][0]:
                    self.logger.log(f"Successfully received response from {self.model_name} for {self.agent_name}", role=self.agent_name)
                    return data['candidates'][0]['content']['parts'][0]['text'].strip()

                if data.get('candidates') and data['candidates'][0].get('finishReason') == 'SAFETY':
                    error_msg = "Response blocked by safety filters."
                    self.logger.log(error_msg, role=self.agent_name, level="ERROR")
                    return f"Error: {error_msg}"

                self.logger.log(f"Empty or malformed response from {self.model_name} for {self.agent_name}. Data: {data}", role=self.agent_name, level="WARNING")
                return "Error: No valid response generated by LLM."

            except requests.exceptions.HTTPError as e:
                error_text = e.response.text
                status_code = e.response.status_code
                self.logger.log(f"HTTP Error {status_code} for {self.agent_name}: {error_text}", role=self.agent_name, level="ERROR")
                if status_code == 429 or status_code >= 500: # Retry on rate limit or server errors
                    if current_retry < max_retries:
                        self.logger.log(f"Retrying in {delay}s...", role=self.agent_name, level="WARNING")
                        time.sleep(delay)
                        delay *= 2
                        current_retry += 1
                        continue
                    else:
                        return f"Error: Failed after {max_retries + 1} attempts. Last error: HTTP {status_code}: {error_text}"
                return f"Error: HTTP {status_code}: {error_text}"
            except requests.exceptions.RequestException as e:
                self.logger.log(f"Request failed for {self.agent_name}: {e}", role=self.agent_name, level="ERROR")
                if current_retry < max_retries:
                    self.logger.log(f"Retrying in {delay}s...", role=self.agent_name, level="WARNING")
                    time.sleep(delay)
                    delay *= 2
                    current_retry += 1
                    continue
                return f"Error: Request failed after {max_retries + 1} attempts: {e}"
            except Exception as e:
                self.logger.log(f"Unexpected error during LLM call for {self.agent_name}: {e}", role=self.agent_name, level="ERROR")
                return f"Error: Unexpected error during LLM call: {e}"

        return f"Error: Failed to get response from LLM for {self.agent_name} after {max_retries + 1} attempts."


class SubAgentWrapper:
    def __init__(self, sub_agent_name: str, output_model: Type[T], logger: Optional[LoggerPlaceholder] = None):
        self.sub_agent_name = sub_agent_name
        self.output_model = output_model
        self.logger = logger or LoggerPlaceholder()
        self.llm_invoker = SubAgentLLMInvoker(agent_name=sub_agent_name, logger=self.logger)

        try:
            from .prompts import get_sub_agent_prompt as ext_get_sub_agent_prompt
            self.get_prompt_function = ext_get_sub_agent_prompt
        except ImportError as e:
            self.logger.log(f"Could not import get_sub_agent_prompt from .prompts: {e}. Ensure api_designer_crew is in PYTHONPATH or structure is correct.", level="ERROR")
            def _default_prompt_fn(agent_name: str, context: dict) -> str:
                self.logger.log("Using fallback prompt function due to import error.", level="WARNING")
                return f"Prompt for {agent_name} with context: {json.dumps(context)}"
            self.get_prompt_function = _default_prompt_fn


    def execute(self, context_for_prompt: Dict[str, Any], llm_call_kwargs: Optional[Dict[str, Any]] = None) -> Optional[T]:
        if self.llm_invoker.model_name == "system":
            self.logger.log(f"{self.sub_agent_name} is a system agent. System agent execution should be handled by specific methods, not this generic LLM execute flow.", level="INFO")
            return None

        try:
            prompt_str = self.get_prompt_function(self.sub_agent_name, context_for_prompt)
            self.logger.log(f"Generated prompt for {self.sub_agent_name} (first 300 chars):\n{prompt_str[:300]}...", role=self.sub_agent_name)

            llm_response_str = self.llm_invoker.invoke(prompt_str, **(llm_call_kwargs or {}))

            if llm_response_str.startswith("Error:"):
                self.logger.log(f"LLM call failed for {self.sub_agent_name}: {llm_response_str}", role=self.sub_agent_name, level="ERROR")
                return None

            self.logger.log(f"Raw LLM response for {self.sub_agent_name} (first 300 chars):\n{llm_response_str[:300]}...", role=self.sub_agent_name)

            try:
                # Attempt to find JSON within ```json ... ```, otherwise assume whole response is JSON
                if '```json' in llm_response_str:
                    json_start = llm_response_str.find('```json') + 7
                    json_end = llm_response_str.rfind('```')
                    if json_end > json_start:
                        json_str_to_parse = llm_response_str[json_start:json_end].strip()
                    else: # Fallback if ```json is present but closing ``` is missing or misplaced
                        json_str_to_parse = llm_response_str[json_start:].strip()
                        self.logger.log("Found '```json' but no clear closing '```'. Attempting to parse from '```json' onwards.", level="WARNING")
                else:
                    json_str_to_parse = llm_response_str

                parsed_json = json.loads(json_str_to_parse)
            except json.JSONDecodeError as e:
                self.logger.log(f"Failed to decode JSON for {self.sub_agent_name}: {e}. Response snippet: {llm_response_str[:500]}", role=self.sub_agent_name, level="ERROR")
                return None

            try:
                validated_output = self.output_model(**parsed_json)
                self.logger.log(f"Successfully parsed and validated output for {self.sub_agent_name} using {self.output_model.__name__}.", role=self.sub_agent_name)
                return validated_output
            except ValidationError as e:
                self.logger.log(f"Pydantic validation failed for {self.sub_agent_name} with model {self.output_model.__name__}: {e}. Parsed JSON: {json.dumps(parsed_json, indent=2)}", role=self.sub_agent_name, level="ERROR")
                return None

        except Exception as e:
            self.logger.log(f"An unexpected error occurred during execution for {self.sub_agent_name}: {e}", role=self.sub_agent_name, level="ERROR")
            return None

if __name__ == "__main__":
    print("Testing SubAgentWrapper...")

    class TestOutputModel(BaseModel):
        message: str
        value: int

    test_context = {
        "role": "Test Sub-Agent",
        "sub_task_description": "Testing the wrapper.",
        "project_name": "WrapperTest",
        "objective": "To ensure SubAgentWrapper works.",
        "feature_objectives": "Test feature",
        "planner_milestones": "Test milestone",
    }

    logger = LoggerPlaceholder()
    logger.log("Starting SubAgentWrapper test.")

    dummy_agent_name_for_test = "test_llm_agent"
    # Ensure GEMINI_API_KEY is set in your environment
    if not os.environ.get("GEMINI_API_KEY"):
        logger.log("GEMINI_API_KEY not set. Skipping LLM call test.", level="WARNING")
    else:
        if not AGENT_MODEL_CONFIG.get(dummy_agent_name_for_test):
            AGENT_MODEL_CONFIG[dummy_agent_name_for_test] = GeminiConfigPlaceholder.DEFAULT_MODEL_NAME

        def mock_get_prompt_for_test(agent_name, context):
            return f"You are {agent_name}. Based on context: {json.dumps(context)}, provide ONLY a JSON response with 'message' (string) and 'value' (integer). Example: {{\"message\": \"Test success\", \"value\": 123}}"

        wrapper = SubAgentWrapper(sub_agent_name=dummy_agent_name_for_test, output_model=TestOutputModel, logger=logger)
        wrapper.get_prompt_function = mock_get_prompt_for_test

        logger.log(f"Attempting to execute wrapper for {dummy_agent_name_for_test}...")
        result = wrapper.execute(test_context)

        if result:
            logger.log(f"Wrapper execution successful for {dummy_agent_name_for_test}! Result: {result.model_dump_json(indent=2)}")
        else:
            logger.log(f"Wrapper execution failed or returned None for {dummy_agent_name_for_test}.")
