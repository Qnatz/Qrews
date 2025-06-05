"""
Enhanced Agent class with Gemini 2.0 Flash for all agents
All agents now use Gemini instead of DeepSeek
"""
import time
import numpy
import json
import requests
import os
from typing import Optional, Dict, Any
from pathlib import Path # Added

from utils.general_utils import Logger # MODIFIED
from utils.database import Database # MODIFIED
from utils.crew_llm_service import LocalLLMClient # MODIFIED
from prompts.general_prompts import get_agent_prompt # MODIFIED
from utils.tools import ToolKit # MODIFIED
from configs.global_config import MODEL_STRATEGY_CONFIG, GeminiConfig, ModelConfig # MODIFIED

import socket
import threading
# from models import ProjectAnalysis, AgentOutput # Removed as ProjectAnalysis is part of context_handler
from pydantic import ValidationError # Already present
from utils.models import ( # MODIFIED
    PlatformRequirements, TechProposal, PlannerOutputModel,
    APIDesignerOutputModel, ArchitectOutputModel, MobileOutputModel # Models are already imported
)
from typing import List, Dict, Any, Optional # Ensure all are here if used in new logic
# import json # Ensure json is imported for .dumps in new logic # json is already imported above

# Import from context_handler
from utils.context_handler import ProjectContext, AnalysisOutput, TechStack, load_context, save_context # MODIFIED
from utils.validation_utils import validate_tech_stack, get_tech_stack_validation_prompt_segment # MODIFIED

# Define context file path
CONTEXT_JSON_FILE = Path("project_context.json") # Changed from context.json to project_context.json to match example in context_handler

class Agent:
    def __init__(self, name, role, logger: Logger, model_type='gemini', db: Database = None):
        self.name = name
        self.role = role
        self.model_type = model_type  # Always use 'gemini' now
        self.logger = logger
        # self.context = [] # Removed old context list
        self.tool_kit: Optional[ToolKit] = None
        self.tools = []

        # Database connection
        self.db = db  # Database instance passed from TaskMaster

        # Gemini 2.0 configuration
        self.gemini_config = GeminiConfig()
        self.model_config = ModelConfig()
        # self.current_model = GeminiConfig.MODEL_NAME # Replaced by new logic below
        self.generation_config = GeminiConfig.get_generation_config(name)

        self.strategy_config = MODEL_STRATEGY_CONFIG
        if self.name in self.strategy_config.CODING_AGENT_NAMES:
            self.primary_model_name = self.strategy_config.CODING_MODEL_NAME
        else:
            self.primary_model_name = self.strategy_config.DEFAULT_GEMINI_MODEL

        self.current_model = self.primary_model_name # Initialize current_model

        # Placeholder for local client instantiation
        self.local_client = LocalLLMClient() # This might need adjustment based on LocalLLMClient's final design
        
        # Validate API key on initialization
        if not GeminiConfig.validate_api_key():
            self.logger.log(f"Warning: Gemini API key not properly configured for {name}", role, level="WARNING")

    def perform_task(self, project_context: ProjectContext) -> dict:  # Changed context type
        analysis_data = {}
        if project_context.analysis:
            analysis_data = project_context.analysis.model_dump()

        # --- BEGIN Verbose Logging ---
        self.logger.log(f"[{self.name}] Pre-prompt_context: project_context.tech_stack is: {project_context.tech_stack}", self.role)
        if project_context.tech_stack:
            self.logger.log(f"[{self.name}] Pre-prompt_context: tech_stack.frontend={project_context.tech_stack.frontend}, backend={project_context.tech_stack.backend}, database={project_context.tech_stack.database}", self.role)
        # --- END Verbose Logging ---

        prompt_context = {
            'role': self.role,
            'specialty': self.role,
            'project_name': project_context.project_name,
            'objective': project_context.objective or "",
            'project_type': project_context.analysis.project_type_confirmed if project_context.analysis else project_context.project_type,
            'current_dir': project_context.current_dir or "/",
            'project_summary': project_context.project_summary or "",
            'architecture': project_context.architecture or "",
            'plan': project_context.plan or "",
            'memories': project_context.project_summary or "No specific memories retrieved for this task yet.", # Placeholder for actual memory retrieval
            'tool_names': [tool['name'] for tool in self.tools],
            'tools': self.tools,
            'analysis': analysis_data,  # Use dumped analysis data
            'current_code_snippet': project_context.current_code_snippet or "",
            'error_report': project_context.error_report or "",
            # General tech_stack info for prompts that might use it (like FrontendBuilder)
            'tech_stack': project_context.tech_stack.model_dump() if project_context.tech_stack else {},
            'tech_stack_frontend': project_context.tech_stack.frontend if project_context.tech_stack and project_context.tech_stack.frontend is not None else "not specified",
            'tech_stack_frontend_lowercase': project_context.tech_stack.frontend.lower() if project_context.tech_stack and project_context.tech_stack.frontend is not None else "not_specified",
            # Adding backend and database for completeness, similar to frontend, in case other prompts use them.
            'tech_stack_backend': project_context.tech_stack.backend if project_context.tech_stack and project_context.tech_stack.backend is not None else "not specified",
            'tech_stack_backend_lowercase': project_context.tech_stack.backend.lower() if project_context.tech_stack and project_context.tech_stack.backend is not None else "not_specified",
            'tech_stack_database': project_context.tech_stack.database if project_context.tech_stack and project_context.tech_stack.database is not None else "not specified",
            'tech_stack_database_lowercase': project_context.tech_stack.database.lower() if project_context.tech_stack and project_context.tech_stack.database is not None else "not_specified",
        }

        if self.name == "architect" or self.name == "api_designer":  # Specific additions for architect and api_designer prompt placeholders
            prompt_context['tech_stack_frontend_name'] = project_context.tech_stack.frontend if project_context.tech_stack and project_context.tech_stack.frontend is not None else "Not Specified"
            prompt_context['tech_stack_backend_name'] = project_context.tech_stack.backend if project_context.tech_stack and project_context.tech_stack.backend is not None else "Not Specified"
            prompt_context['tech_stack_database_name'] = project_context.tech_stack.database if project_context.tech_stack and project_context.tech_stack.database is not None else "Not Specified"
        
        # --- BEGIN Verbose Logging ---
        self.logger.log(f"[{self.name}] Constructed prompt_context: {json.dumps(prompt_context, indent=2, default=str)}", self.role)
        self.logger.log(f"[{self.name}] About to call get_agent_prompt.", self.role)
        # --- END Verbose Logging ---

        generated_prompt_str = get_agent_prompt(self.name, prompt_context)
        
        # --- BEGIN Verbose Logging ---
        self.logger.log(f"[{self.name}] Returned from get_agent_prompt. Prompt length: {len(generated_prompt_str)}. First 200 chars: {generated_prompt_str[:200]}", self.role)
        # --- END Verbose Logging ---

        if self.name in ["planner", "architect", "api_designer"]:  # This existing block is fine
            tech_stack_prompt_segment = get_tech_stack_validation_prompt_segment(project_context)
            generated_prompt_str = tech_stack_prompt_segment + "\n\n--- Original Prompt Begins ---\n\n" + generated_prompt_str
            self.logger.log(f"[{self.name}] Prepended tech stack validation prompt segment.", self.role)

        self.logger.log(f"[{self.name}] Starting task with {self.current_model}", self.role)
        start = time.time()
        
        if self.tools:
            response_content = self._call_model_with_tools(generated_prompt_str)
        else:
            response_content = self._call_model(generated_prompt_str)

        duration = time.time() - start
        self.logger.log(f"[{self.name}] Completed in {duration:.2f}s", self.role)

        # Pass project_context to _parse_response
        parsed_result = self._parse_response(response_content, project_context)

        # The add_to_memory function no longer handles self.context list.
        # It's now primarily for DB storage using the raw response content.
        self.add_to_memory(response_content)  # or parsed_result.get("raw_response", response_content)

        # Return the structured result from _parse_response, which includes status, errors, etc.
        return parsed_result

    def reserve_port(self, port: int = 0) -> int:
        """Reserve and return an available port"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return s.getsockname()[1]

    def _invoke_model(self, model_name: str, prompt: str, uses_tools: bool) -> str:
        # Log which model is being invoked (model_name)
        self.logger.log(f"[{self.name}] Invoking model: {model_name}", self.role)
        self.current_model = model_name # Update current_model when invoking

        if model_name.startswith("gemini-"): # Simple check for Gemini
            if uses_tools:
                # Using old _call_gemini_with_tools which internally uses self.current_model
                return self._call_gemini_with_tools(prompt)
            else:
                # Using old _call_gemini which internally uses self.current_model
                return self._call_gemini(prompt)
        elif model_name in self.strategy_config.LOCAL_MODEL_ENDPOINTS:
            endpoint_url = self.strategy_config.LOCAL_MODEL_ENDPOINTS[model_name]
            if uses_tools:
                self.logger.log(f"[{self.name}] Tool use with local model {model_name} requested but not yet implemented. Falling back to text generation.", self.role, level="WARNING")
                # Pass base_api_url and model_name to the local client's generate method
                return self.local_client.generate(base_api_url=endpoint_url, prompt=prompt, model_name=model_name)
            else:
                return self.local_client.generate(base_api_url=endpoint_url, prompt=prompt, model_name=model_name)
        else:
            self.logger.log(f"[{self.name}] Unknown model_name: {model_name}. Cannot invoke.", self.role, level="ERROR")
            return f"Error: Unknown model_name {model_name}"

    def _execute_task_with_retry_and_fallback(self, prompt: str, uses_tools: bool) -> str:
        primary_model_to_try = self.primary_model_name
        self.current_model = primary_model_to_try # Set current_model for the primary attempt

        try:
            self.logger.log(f"[{self.name}] Primary attempt with {self.current_model}", self.role)
            response = self._invoke_model(self.current_model, prompt, uses_tools)

            # Crude check for error in response to simulate failure for fallback testing
            if response.startswith("Error:") or "Rate limit exceeded" in response or "overloaded" in response or "503" in response:
                raise Exception(response)

            return response
        except Exception as e:
            self.logger.log(f"[{self.name}] Primary attempt with {self.current_model} failed: {e}", self.role, level="WARNING")

            if self.strategy_config.ENABLE_LOCAL_FALLBACK and self.current_model.startswith("gemini-"):
                is_network_or_overload_error = "Rate limit exceeded" in str(e) or \
                                                "overloaded" in str(e) or \
                                                "503" in str(e) or \
                                                "ConnectionError" in str(e) or \
                                                "Request failed" in str(e) # Added from Gemini error text

                if is_network_or_overload_error:
                    self.logger.log(f"[{self.name}] Attempting fallback to local model {self.strategy_config.LOCAL_FALLBACK_MODEL_NAME}", self.role)
                    self.current_model = self.strategy_config.LOCAL_FALLBACK_MODEL_NAME
                    try:
                        return self._invoke_model(self.current_model, prompt, uses_tools)
                    except Exception as fallback_e:
                        self.logger.log(f"[{self.name}] Local fallback attempt with {self.current_model} also failed: {fallback_e}", self.role, level="ERROR")
                        return f"Error: Primary model failed ({e}) and local fallback also failed ({fallback_e})"
                else:
                    return f"Error: Primary model {self.primary_model_name} failed: {e}"
            else:
                return f"Error: Primary model {self.primary_model_name} failed: {e}"

    def _call_model(self, prompt: str) -> str:
        """Call chosen model with retry and fallback logic"""
        return self._execute_task_with_retry_and_fallback(prompt, uses_tools=False)

    def _call_model_with_tools(self, prompt: str) -> str:
        """Call chosen model with tools, retry and fallback logic"""
        return self._execute_task_with_retry_and_fallback(prompt, uses_tools=True)

    def _call_gemini_with_retry(self, prompt: str, max_retries: int = 2) -> str:
        """Call Gemini with automatic retry and fallback"""
        for attempt in range(max_retries + 1):
            try:
                return self._call_gemini(prompt)
            except Exception as e:
                self.logger.log(f"[{self.name}] Attempt {attempt + 1} failed: {e}", self.role, level="WARNING")
                
                if attempt < max_retries:
                    # Try fallback model
                    old_model = self.current_model
                    self.current_model = self.model_config.get_fallback_model(self.current_model)
                    self.logger.log(f"[{self.name}] Falling back from {old_model} to {self.current_model}", self.role)
                    time.sleep(1)  # Brief delay before retry
                else:
                    return f"Error: All Gemini model attempts failed: {str(e)}"

    def _call_gemini_with_tools_retry(self, prompt: str, max_retries: int = 2) -> str:
        """Call Gemini with tools with automatic retry and fallback"""
        for attempt in range(max_retries + 1):
            try:
                return self._call_gemini_with_tools(prompt)
            except Exception as e:
                self.logger.log(f"[{self.name}] Tools attempt {attempt + 1} failed: {e}", self.role, level="WARNING")
                
                if attempt < max_retries:
                    # Try fallback model
                    old_model = self.current_model
                    self.current_model = self.model_config.get_fallback_model(self.current_model)
                    self.logger.log(f"[{self.name}] Falling back from {old_model} to {self.current_model}", self.role)
                    time.sleep(1)  # Brief delay before retry
                else:
                    return f"Error: All Gemini tool attempts failed: {str(e)}"

    def _call_gemini(self, prompt: str) -> str:
        """Enhanced Gemini 2.0 Flash API call"""
        url = f"{GeminiConfig.BASE_URL}/{self.current_model}:generateContent"
        
        payload = {
            'contents': [
                {
                    'parts': [
                        {
                            'text': prompt
                        }
                    ]
                }
            ],
            'generationConfig': self.generation_config,
            'safetySettings': GeminiConfig.SAFETY_SETTINGS
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                url,
                params={'key': GeminiConfig.API_KEY},
                headers=headers,
                json=payload,
                timeout=90
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Log usage metadata if available
            if 'usageMetadata' in data:
                usage = data['usageMetadata']
                self.logger.log(f"[{self.name}] Tokens: {usage.get('totalTokenCount', 0)} "
                              f"(prompt: {usage.get('promptTokenCount', 0)}, "
                              f"response: {usage.get('candidatesTokenCount', 0)})", self.role)
            
            # Handle the response structure
            candidates = data.get('candidates', [])
            if candidates and 'content' in candidates[0]:
                parts = candidates[0]['content'].get('parts', [])
                if parts and 'text' in parts[0]:
                    response_text = parts[0]['text'].strip()
                    
                    # Log finish reason for debugging
                    finish_reason = candidates[0].get('finishReason', 'UNKNOWN')
                    if finish_reason != 'STOP':
                        self.logger.log(f"[{self.name}] Finish reason: {finish_reason}", self.role, level="WARNING")
                    
                    return response_text
            
            # Handle blocked or empty responses
            if candidates and candidates[0].get('finishReason') == 'SAFETY':
                return "Response blocked by safety filters. Please rephrase your request."
            
            self.logger.log(f"[{self.name}] Empty response from {self.current_model}", self.role, level="WARNING")
            return "No response generated"
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise Exception(f"Rate limit exceeded for {self.current_model}")
            elif e.response.status_code == 403:
                raise Exception(f"API key invalid or quota exceeded for {self.current_model}")
            else:
                raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed for {self.current_model}: {str(e)}")
        
        except Exception as e:
            raise Exception(f"Processing error for {self.current_model}: {str(e)}")

    def _call_gemini_with_tools(self, prompt: str) -> str:
        """Enhanced Gemini 2.0 Flash API call with tools"""
        url = f"{GeminiConfig.BASE_URL}/{self.current_model}:generateContent"
        
        payload = {
            'contents': [
                {
                    'parts': [
                        {
                            'text': prompt
                        }
                    ]
                }
            ],
            'generationConfig': self.generation_config,
            'safetySettings': GeminiConfig.SAFETY_SETTINGS,
            'tools': [
                {
                    'functionDeclarations': self.tools
                }
            ]
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                url,
                params={'key': GeminiConfig.API_KEY},
                headers=headers,
                json=payload,
                timeout=90
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Log usage metadata if available
            if 'usageMetadata' in data:
                usage = data['usageMetadata']
                self.logger.log(f"[{self.name}] Tools Tokens: {usage.get('totalTokenCount', 0)}", self.role)
            
            # Handle the response structure with tools
            candidates = data.get('candidates', [])
            if candidates and 'content' in candidates[0]:
                parts = candidates[0]['content'].get('parts', [])
                
                # Check for function calls first
                for part in parts:
                    if 'functionCall' in part:
                        function_call = part['functionCall']
                        function_name = function_call.get('name', '')
                        function_args = function_call.get('args', {})
                        
                        self.logger.log(f"[{self.name}] Tool call: {function_name}", self.role)
                        
                        # Execute the tool
                        if self.tool_kit and hasattr(self.tool_kit, function_name):
                            try:
                                tool_result = getattr(self.tool_kit, function_name)(**function_args)
                                return f"Tool executed: {function_name}\nResult: {tool_result}"
                            except Exception as e:
                                return f"Tool execution failed: {function_name}\nError: {str(e)}"
                        else:
                            return f"Tool not found: {function_name}"
                
                # If no function calls, check for regular text response
                for part in parts:
                    if 'text' in part:
                        response_text = part['text'].strip()
                        if response_text:
                            return response_text
            
            # Handle blocked or empty responses
            if candidates and candidates[0].get('finishReason') == 'SAFETY':
                return "Response blocked by safety filters. Please rephrase your request."
            
            self.logger.log(f"[{self.name}] Empty tools response from {self.current_model}", self.role, level="WARNING")
            return "No response generated with tools"
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise Exception(f"Rate limit exceeded for {self.current_model}")
            elif e.response.status_code == 403:
                raise Exception(f"API key invalid or quota exceeded for {self.current_model}")
            else:
                raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed for {self.current_model}: {str(e)}")
        
        except Exception as e:
            raise Exception(f"Processing error for {self.current_model}: {str(e)}")

    def _parse_response(self, response_text: str, project_context: ProjectContext) -> dict:
        """
        Base method to parse LLM response, checking for errors and extracting JSON.
        Specific agents should override this to perform their detailed parsing.
        """
        parsed_result = {
            "status": "complete",  # Default to complete
            "errors": [],
            "warnings": [],
            "raw_response": response_text, # Store the raw response for debugging
            # Include some agent identifiers for convenience in the returned dict
            "agent_name": self.name,
            "agent_role": self.role,
            "model_used": self.current_model
        }

        if not response_text or response_text.startswith("Error:") or "Response blocked by safety filters" in response_text or "No response generated" in response_text:
            parsed_result["status"] = "error"
            error_message = response_text if response_text else "Empty response from LLM."
            parsed_result["errors"].append(error_message)
            self.logger.log(f"LLM call failed or returned error for {self.name}: {error_message}", self.role, level="ERROR")
            return parsed_result

        # Attempt to parse JSON content if present
        try:
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                if json_end > json_start:
                    json_str = response_text[json_start:json_end].strip()
                    parsed_json = json.loads(json_str)
                    # Merge parsed_json carefully, avoid overwriting status fields unless intended
                    # For base class, we'll store it under a specific key.
                    # Specific agents can decide to merge it differently.
                    parsed_result['parsed_json_content'] = parsed_json
                else: # JSON block started but not properly ended
                    parsed_result["warnings"].append("Found '```json' but could not parse a valid JSON block.")
            # else: No JSON block found, response_text is treated as plain text by default.
        except json.JSONDecodeError as e:
            parsed_result["warnings"].append(f"Could not parse JSON from LLM response: {e}")
            self.logger.log(f"JSON parsing failed for {self.name}: {e}", self.role, level="WARNING")
        
        return parsed_result

    def add_to_memory(self, content: str):
        """Add content to agent's memory (Vector DB)"""
        item_id = f"{self.name}_{time.time()}"  #Unique
        try:
          embedding = numpy.random.rand(384).astype(numpy.float32)  # Replace with actual embedding generation
        except Exception as e:
            self.logger.log(f"Numpy didn't work for embedding generation: {e}","ToolKit", level="ERROR")
            return # Do not proceed if embedding fails

        if self.db:
           if self.db.store_embedding(item_id=item_id, agent_id=self.name, role=self.role, content=content, embedding=embedding):
               self.logger.log(f"Added content to memory store for {self.name}: {item_id[:20]}...", self.role)
        # self.context.append(f"[{self.name}]: {content}") # Removed old context list update
        # if len(self.context) > 10: # Removed old context list trimming
            # self.context = self.context[-10:]

    def set_tools(self, tool_kit: ToolKit):
        """Set the tool kit and available tools for this agent"""
        self.tool_kit = tool_kit
        self.tools = tool_kit.get_tool_definitions() if tool_kit else []
        self.logger.log(f"[{self.name}] Configured with {len(self.tools)} tools", self.role)

    # save_context and load_context methods removed from Agent class

    def validate_stack(self, approved_stack: Dict[str, Any], platform_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Base method for an agent to validate a proposed ApprovedTechStack against platform requirements.
        Specialist agents should override this for more specific checks.
        Input:
            approved_stack: Dict representation of ApprovedTechStack.
            platform_requirements: Dict representation of PlatformRequirements.
        Output:
            Dict {"approved": bool, "concerns": Optional[str]}
        """
        self.logger.log(f"[{self.name}] Validating stack (base implementation): {approved_stack}", self.role)

        # Example: Basic check if any tech is None when its platform is required
        if platform_requirements.get("web") and not approved_stack.get("web_backend"):
            concern_msg = f"{self.name} ({self.role}): Web platform required but no web_backend specified."
            self.logger.log(concern_msg, self.role, level="WARNING")
            return {"approved": False, "concerns": concern_msg}

        is_mobile_project = platform_requirements.get("ios") or platform_requirements.get("android")
        if is_mobile_project and not approved_stack.get("mobile_database"):
            concern_msg = f"{self.name} ({self.role}): Mobile platform required but no mobile_database specified."
            self.logger.log(concern_msg, self.role, level="WARNING")
            return {"approved": False, "concerns": concern_msg}

        return {"approved": True, "concerns": None}


# Helper function for processing tech proposals
def _process_tech_proposals(logger: Logger, agent_name: str, agent_role: str, raw_proposals_dict: Optional[Dict[str, Any]], project_context: ProjectContext):
    """
    Processes a dictionary of raw technology proposals (typically from LLM JSON output)
    and populates the project_context.tech_proposals field.

    Args:
        logger: Instance of the Logger class.
        agent_name: Name of the agent whose response contains these proposals.
        agent_role: Role of the agent.
        raw_proposals_dict: A dictionary where keys are technology categories (e.g., "database")
                            and values are lists of proposal dictionaries. # Actually Optional[Dict[str, List[TechProposal]]]
        project_context: The ProjectContext object to update.
    """
    # Correctly serialize TechProposal objects for logging
    serializable_proposals_for_log = {}
    if raw_proposals_dict:
        try:
            serializable_proposals_for_log = {
                category: [
                    proposal.model_dump() if isinstance(proposal, TechProposal) else proposal
                    for proposal in proposals_list
                ]
                for category, proposals_list in raw_proposals_dict.items()
            }
        except Exception as e: # Fallback in case of unexpected structure
            logger.log(f"[_process_tech_proposals] Error preparing proposals for logging for agent '{agent_name}': {e}", agent_role, level="ERROR")
            serializable_proposals_for_log = {"error": "Could not serialize proposals for logging"}

    logger.log(f"[_process_tech_proposals] Received for agent '{agent_name}': {json.dumps(serializable_proposals_for_log, indent=2)} for project_context update.", agent_role, level="DEBUG")

    if not raw_proposals_dict:
        logger.log(f"[_process_tech_proposals] Received empty or None raw_proposals_dict for agent '{agent_name}'. No proposals to process.", agent_role, level="WARNING")
        return

    for category, proposals_list in raw_proposals_dict.items():
        if not isinstance(proposals_list, list):
            logger.log(f"[_process_tech_proposals] Tech proposals for category '{category}' for agent '{agent_name}' is not a list. Skipping.", agent_role, level="WARNING")
            continue

        if category not in project_context.tech_proposals:
            project_context.tech_proposals[category] = []

        for proposal_item in proposals_list: # proposal_item is already a TechProposal object
            # Log the proposal item (which is a TechProposal model instance)
            logger.log(f"[_process_tech_proposals] Processing proposal item for category '{category}' by agent '{agent_name}': {proposal_item.model_dump_json(indent=2)}", agent_role, level="DEBUG")

            if not isinstance(proposal_item, TechProposal):
                logger.log(f"[_process_tech_proposals] Proposal item in category '{category}' for agent '{agent_name}' is not a TechProposal object. Skipping. Item: {str(proposal_item)}", agent_role, level="WARNING")
                continue
            try:
                # proposal_item is already a TechProposal object, directly append it.
                # The 'proponent' field should have been set by the Architect agent.
                if not proposal_item.proponent: # Defensive check
                    logger.log(f"[_process_tech_proposals] TechProposal object for '{proposal_item.technology}' is missing 'proponent' field. Setting it now to agent_name '{agent_name}'. This should ideally be set by the Architect agent.", agent_role, level="WARNING")
                    proposal_item.proponent = agent_name # Fallback, though ideally this shouldn't be needed.

                project_context.tech_proposals[category].append(proposal_item)
                logger.log(f"[_process_tech_proposals] Agent '{agent_name}' successfully added tech proposal for '{category}': {proposal_item.technology}", agent_role)
            except ValidationError as e: # Should ideally not happen if proposal_item is already a validated TechProposal
                logger.log(f"[_process_tech_proposals] Unexpected ValidationError for an already validated TechProposal for category '{category}'. Item: {proposal_item.model_dump_json(indent=2)}. Error: {e}", agent_role, level="ERROR")
            except Exception as e:
                logger.log(f"[_process_tech_proposals] Unexpected error processing TechProposal for category '{category}'. Item: {str(proposal_item)}. Error: {e}", agent_role, level="ERROR")


# Individual Agent Classes - All now use Gemini
class ProjectAnalyzer(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('project_analyzer', 'Project Analyst', logger, db=db)

    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        # Platform detection using the new tool
        if self.tool_kit and project_context.objective:
            try:
                detected_platforms_dict = self.tool_kit.detect_platforms(objective=project_context.objective)
                project_context.platform_requirements = PlatformRequirements(**detected_platforms_dict)
                self.logger.log(f"ProjectAnalyzer: Platform requirements detected and set: {project_context.platform_requirements.model_dump()}", self.role)
            except Exception as e:
                self.logger.log(f"ProjectAnalyzer: Error during platform detection: {e}", self.role, level="ERROR")
                # Optionally, set a default or error state for platform_requirements
                project_context.platform_requirements = PlatformRequirements() # Default empty

        base_parsed_output = super()._parse_response(text, project_context)

        if base_parsed_output["status"] == "error":
            # If LLM call itself failed, no further specific parsing is typically needed.
            # However, if there was a response but it was an error message (e.g. safety)
            # we might log it or add more context specific to ProjectAnalyzer here.
            # For now, just returning the base error is fine.
            return base_parsed_output

        try:
            json_str = None
            # Prioritize JSON content from base parser if it found one
            if 'parsed_json_content' in base_parsed_output:
                # This assumes the agent is designed to output its primary data as the *only* JSON block
                analysis_data = base_parsed_output['parsed_json_content']
            else: # Fallback: try to parse the whole raw response as JSON
                self.logger.log(f"ProjectAnalyzer: No '```json' block found by base parser. Attempting to parse entire response.", self.role, level="INFO")
                json_str = base_parsed_output["raw_response"]
                analysis_data = json.loads(json_str)

            # (analysis_data has been populated from JSON at this point)

            suggested_tech_stack_data = analysis_data.get("suggested_tech_stack")
            if suggested_tech_stack_data is not None:
                try:
                    # Ensure all expected keys are at least present as None if missing in LLM output for TechStack model
                    # This makes TechStack(**data) more robust if LLM omits a null field.
                    final_suggested_data = {
                        'frontend': suggested_tech_stack_data.get('frontend'),
                        'backend': suggested_tech_stack_data.get('backend'),
                        'database': suggested_tech_stack_data.get('database')
                    }
                    new_tech_stack = TechStack(**final_suggested_data)
                    project_context.tech_stack = new_tech_stack # Update the main project tech_stack
                    self.logger.log(f"ProjectAnalyzer updated project_context.tech_stack with suggested: Frontend='{new_tech_stack.frontend}', Backend='{new_tech_stack.backend}', Database='{new_tech_stack.database}'", self.role)
                except Exception as e_techstack: # Catch potential errors during TechStack instantiation
                    self.logger.log(f"ProjectAnalyzer: Error processing suggested_tech_stack: {e_techstack}. Data: {suggested_tech_stack_data}", self.role, level="WARNING")
                    # Do not update project_context.tech_stack if suggestion is malformed, keep the initial empty one.
                    # The error will be caught later by AnalysisOutput validation if suggested_tech_stack structure is wrong for it.

            # project_context.analysis will be set in the next line using the original analysis_data,
            # which includes the suggested_tech_stack for storage within AnalysisOutput itself.
            project_context.analysis = AnalysisOutput(**analysis_data)
            self.logger.log(f"ProjectAnalyzer: Analysis data parsed and validated successfully.", self.role)
            base_parsed_output["analysis_summary"] = f"Type: {project_context.analysis.project_type_confirmed}, Backend: {project_context.analysis.backend_needed}, Frontend: {project_context.analysis.frontend_needed}"

        except json.JSONDecodeError as e:
            error_msg = f"Failed to decode JSON analysis from LLM: {e}. Response: {base_parsed_output['raw_response'][:200]}"
            self.logger.log(error_msg, self.role, level="ERROR")
            base_parsed_output["status"] = "error"
            base_parsed_output["errors"].append(error_msg)
            # Optionally, create a default/error AnalysisOutput in project_context
            project_context.analysis = AnalysisOutput(project_type_confirmed="error_parsing_failed", key_requirements=[error_msg])
        except ValidationError as e: # Pydantic validation error
            error_msg = f"Analysis data validation failed: {e}. Data: {analysis_data if 'analysis_data' in locals() else 'N/A'}"
            self.logger.log(error_msg, self.role, level="ERROR")
            base_parsed_output["status"] = "error"
            base_parsed_output["errors"].append(error_msg)
            project_context.analysis = AnalysisOutput(project_type_confirmed="error_validation_failed", key_requirements=[str(e)])
        except Exception as e: # Catch any other unexpected errors
            error_msg = f"Unexpected error processing analysis: {e}. Response: {base_parsed_output['raw_response'][:200]}"
            self.logger.log(error_msg, self.role, level="ERROR")
            base_parsed_output["status"] = "error"
            base_parsed_output["errors"].append(error_msg)
            project_context.analysis = AnalysisOutput(project_type_confirmed="error_unexpected", key_requirements=[error_msg])

        return base_parsed_output


class Planner(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('planner', 'Project Planner', logger, db=db)

    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)

        if base_parsed_output["status"] == "error":
            return base_parsed_output

        # Tech stack validation should run on the raw_response which might contain descriptive text
        # This is run before attempting to parse and validate the JSON plan structure.
        tech_stack_validation_errors = validate_tech_stack(base_parsed_output["raw_response"], project_context.tech_stack)
        if tech_stack_validation_errors:
            base_parsed_output["status"] = "error"
            base_parsed_output["errors"].extend(tech_stack_validation_errors)
            self.logger.log(f"[{self.name}] Tech stack validation failed for Planner output: {tech_stack_validation_errors}", self.role, level="ERROR")
            project_context.plan = None # Ensure plan is not set if tech validation fails
            return base_parsed_output

        # Now, attempt to parse and validate the JSON plan
        if 'parsed_json_content' in base_parsed_output and base_parsed_output['parsed_json_content']:
            plan_json_data = base_parsed_output['parsed_json_content']
            try:
                validated_plan = PlannerOutputModel(**plan_json_data)
                project_context.plan = validated_plan.model_dump_json(indent=2)
                self.logger.log(f"Planner: Plan parsed, Pydantic-validated, and updated in project context (length: {len(project_context.plan)}).", self.role)
                # Create a more meaningful summary from the structured data
                num_milestones = len(validated_plan.milestones)
                num_risks = len(validated_plan.key_risks)
                base_parsed_output["plan_summary"] = f"Plan (validated JSON): {num_milestones} milestones, {num_risks} key risks. First milestone: '{validated_plan.milestones[0].name if num_milestones > 0 else 'N/A'}'"
            except ValidationError as e:
                self.logger.log(f"Planner: Plan JSON schema validation failed: {e}", self.role, level="ERROR")
                base_parsed_output["status"] = "error"
                base_parsed_output["errors"].append(f"Plan Schema Error: Invalid structure - {str(e)}")
                project_context.plan = None # Do not store invalid plan
            return base_parsed_output # Return after handling primary parsing path

        # --- Fallback and Retry Logic ---
        # This section is reached if base_parsed_output['parsed_json_content'] was initially empty/missing.
        raw_response = base_parsed_output.get("raw_response", "")
        plan_json_data = None
        parsing_method_description = "Primary ```json``` block" # Default if primary_parsed_content was used by caller

        if not base_parsed_output.get('parsed_json_content'): # Double check, though this is the main else branch
            parsing_method_description = "Fallback: Marker-based ('FINAL PLAN:')"
            marker = "FINAL PLAN:"
            marker_index = raw_response.lower().find(marker.lower())
            if marker_index != -1:
                json_substring = raw_response[marker_index + len(marker):].strip()
                try:
                    potential_json = json.loads(json_substring)
                    if isinstance(potential_json, dict):
                        plan_json_data = potential_json
                        self.logger.log(f"Planner: Successfully parsed JSON using {parsing_method_description}.", self.role, level="INFO")
                except json.JSONDecodeError as e:
                    self.logger.log(f"Planner: {parsing_method_description} parsing failed: {e}. Substring: {json_substring[:200]}...", self.role, level="WARNING")

            if plan_json_data is None:
                parsing_method_description = "Fallback: Whole response"
                try:
                    potential_json = json.loads(raw_response)
                    if isinstance(potential_json, dict):
                        plan_json_data = potential_json
                        self.logger.log(f"Planner: Successfully parsed JSON using {parsing_method_description}.", self.role, level="INFO")
                except json.JSONDecodeError as e:
                    self.logger.log(f"Planner: {parsing_method_description} parsing failed: {e}. Response: {raw_response[:200]}...", self.role, level="WARNING")

            # Retry logic if all above methods failed
            if plan_json_data is None:
                max_retries = 1
                for i in range(max_retries):
                    self.logger.log(f"Planner: All direct JSON parsing attempts failed. Attempting LLM-correction retry {i+1}/{max_retries}.", self.role, level="WARNING")
                    corrective_prompt_text = (
                        "Your previous response was not in the required JSON format and could not be parsed.\n"
                        f"The previous response started with: '{raw_response[:150]}...'\n"
                        "Please provide the entire plan *only* as a valid JSON object, wrapped in ```json ... ```, "
                        "conforming to the PlannerOutputModel.\n"
                        "The JSON must have top-level keys 'milestones' (a list of milestone objects) and 'key_risks' (a list of risk objects).\n"
                        "Detailed structure requirements:\n"
                        "- Each element in the 'milestones' list must be an object with the following string fields: 'name', 'description' (for the milestone's goal), and a field 'tasks' which must be a list of task objects.\n"
                        "- Each task object within a milestone's 'tasks' list must be an object with the following string fields: 'id' (e.g., '1.1', '1.2'), 'description' (detailing the task), and 'assignee_type'.\n"
                        "- Each element in the 'key_risks' list must be an object with the following string fields: 'risk' (describing the potential risk) and 'mitigation' (describing the mitigation strategy).\n"
                        "Ensure your JSON strictly follows this structure: `{\"milestones\": [{\"name\": \"...\", \"description\": \"...\", \"tasks\": [{\"id\": \"...\", \"description\": \"...\", \"assignee_type\": \"...\"}]}], \"key_risks\": [{\"risk\": \"...\", \"mitigation\": \"...\"}]}`. Replace '...' with appropriate content."
                    )
                    new_response_text = self._call_model(corrective_prompt_text)
                    base_parsed_output["raw_response"] = new_response_text # Update with the new response for transparency

                    if new_response_text.startswith("Error:"):
                        self.logger.log(f"Planner: LLM call for JSON correction failed: {new_response_text}", self.role, level="ERROR")
                        base_parsed_output["errors"].append(f"LLM correction call failed: {new_response_text}")
                        break # Break retry loop if LLM call itself fails

                    retry_parsed_json = None
                    if '```json' in new_response_text:
                        json_start = new_response_text.find('```json') + 7
                        json_end = new_response_text.find('```', json_start)
                        if json_end > json_start:
                            json_str = new_response_text[json_start:json_end].strip()
                            try:
                                retry_parsed_json = json.loads(json_str)
                            except json.JSONDecodeError as e_retry:
                                self.logger.log(f"Planner: JSON syntax error in retry response: {e_retry}. Content: {json_str[:200]}...", self.role, level="WARNING")

                    if isinstance(retry_parsed_json, dict):
                        plan_json_data = retry_parsed_json
                        parsing_method_description = f"LLM-Correction-Retry attempt {i+1}"
                        self.logger.log(f"Planner: Successfully parsed JSON using {parsing_method_description}.", self.role, level="INFO")
                        base_parsed_output['parsed_json_content'] = plan_json_data # Update for consistency
                        break
                    else:
                        self.logger.log(f"Planner: Retry attempt {i+1} did not yield a valid JSON dictionary.", self.role, level="WARNING")

        # Consolidated Pydantic Validation for plan_json_data (from any successful method)
        if plan_json_data is not None:
            try:
                validated_plan = PlannerOutputModel(**plan_json_data)
                project_context.plan = validated_plan.model_dump_json(indent=2)
                self.logger.log(f"Planner: Plan parsed via {parsing_method_description}, Pydantic-validated, and updated in project context (length: {len(project_context.plan)}).", self.role)
                num_milestones = len(validated_plan.milestones)
                num_risks = len(validated_plan.key_risks)
                base_parsed_output["plan_summary"] = f"Plan (validated JSON via {parsing_method_description}): {num_milestones} milestones, {num_risks} key risks. First: '{validated_plan.milestones[0].name if num_milestones > 0 else 'N/A'}'"
                base_parsed_output["status"] = "complete"
                # Ensure parsed_json_content is updated if not already (e.g. if primary parse was successful)
                if not base_parsed_output.get('parsed_json_content'):
                    base_parsed_output['parsed_json_content'] = plan_json_data
                base_parsed_output["errors"] = []
            except ValidationError as e:
                self.logger.log(f"Planner: ({parsing_method_description}) Plan JSON schema validation failed: {e}. Data: {plan_json_data}", self.role, level="ERROR")
                base_parsed_output["status"] = "error"
                base_parsed_output["errors"].append(f"Plan Schema Error ({parsing_method_description}): Invalid structure - {str(e)}")
                project_context.plan = None
        else:
            # All parsing attempts (primary, fallback, retry) failed
            self.logger.log("Planner: No valid JSON content found for the plan after all primary, fallback, and retry attempts.", self.role, level="ERROR")
            base_parsed_output["status"] = "error"
            # Add a generic error if no specific parsing errors were added yet, or ensure one exists
            if not any("Planner failed to produce" in err for err in base_parsed_output.get("errors", [])):
                 base_parsed_output["errors"].append("Planner failed to produce a valid JSON plan after all attempts, including LLM-correction retry.")
            project_context.plan = None

        return base_parsed_output


class Architect(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('architect', 'System Architect', logger, db=db)

    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)

        if base_parsed_output["status"] == "error" and not base_parsed_output["raw_response"]:
            return base_parsed_output

        # Initial response text for the first attempt
        current_response_text_for_attempt = base_parsed_output["raw_response"]

        max_content_retries = 1  # Max retries for tech_stack validation issues
        attempt_successful = False
        # Clear errors at the start of parsing attempts, will be populated if errors occur
        base_parsed_output["errors"] = []

        for attempt_num in range(max_content_retries + 1): # Allows for initial attempt + max_content_retries
            self.logger.log(f"Architect: Parsing attempt {attempt_num + 1}/{max_content_retries + 1}", self.role)
            arch_json_data = None # Reset for each attempt

            # 1. JSON Extraction and Syntax Correction (reusing existing loop but scoped to current attempt)
            # This inner loop is for syntax correction of the current response text
            # It's simplified here; the original has a specific retry count for syntax. Let's assume one syntax correction attempt.
            max_syntax_correction_retries = 1
            current_syntax_attempt_text = current_response_text_for_attempt

            for syntax_retry_num in range(max_syntax_correction_retries + 1):
                extracted_json_str = None
                if '```json' in current_syntax_attempt_text:
                    json_start_index = current_syntax_attempt_text.find('```json')
                    if json_start_index != -1:
                        json_start_actual = json_start_index + 7
                        json_end_index = current_syntax_attempt_text.find('```', json_start_actual)
                        if json_end_index != -1:
                            extracted_json_str = current_syntax_attempt_text[json_start_actual:json_end_index].strip()
                        else: # Unclosed ```json block
                            extracted_json_str = current_syntax_attempt_text[json_start_actual:].strip()
                            base_parsed_output["warnings"].append("Found '```json' but no closing '```'. Attempting to parse partial content for Architect.")
                else: # No ```json block found, assume whole response is JSON
                    extracted_json_str = current_syntax_attempt_text

                if not extracted_json_str:
                    self.logger.log(f"Architect: Could not extract JSON content on syntax attempt {syntax_retry_num + 1}. Raw: {current_syntax_attempt_text[:200]}", self.role, level="WARNING")
                    if syntax_retry_num < max_syntax_correction_retries:
                         # This would ideally trigger the syntax correction prompt from original logic
                         # For this refactor, we'll note it and outer loop might retry if tech stack fails
                        base_parsed_output["errors"].append("Failed to extract JSON content.")
                        # To prevent immediate failure of outer loop, let's break syntax attempts and let tech stack retry handle it
                        break
                    else: # Final syntax attempt failed
                        base_parsed_output["status"] = "error"
                        base_parsed_output["errors"].append("Persistent failure to extract JSON content from Architect response.")
                        project_context.architecture = None
                        return base_parsed_output # Fatal error if no JSON can be extracted after syntax retries

                try:
                    arch_json_data = json.loads(extracted_json_str)
                    if syntax_retry_num > 0:
                         base_parsed_output["warnings"].append(f"JSON syntax self-correction for Architect successful on syntax attempt {syntax_retry_num}.")
                    self.logger.log("Architect: JSON syntax appears valid for current attempt.", self.role)
                    break # Successfully parsed JSON for this attempt
                except json.JSONDecodeError as e_json:
                    self.logger.log(f"Architect: JSON parsing failed on syntax attempt {syntax_retry_num + 1}: {e_json}. Snippet: '{extracted_json_str[max(0, e_json.pos-25):e_json.pos+25]}'", self.role, level="WARNING")
                    if syntax_retry_num < max_syntax_correction_retries:
                        syntax_correction_prompt = (
                            f"The following JSON output for system architecture has a syntax error: {e_json}\n"
                            f"Malformed JSON text:\n```json\n{extracted_json_str}\n```\n"
                            "Correct ONLY the syntax error and return the full, corrected, valid JSON. Do not add explanatory text."
                        )
                        current_syntax_attempt_text = self._call_model(syntax_correction_prompt)
                        base_parsed_output["raw_response"] = current_syntax_attempt_text # Update main raw_response
                        if current_syntax_attempt_text.startswith("Error:"):
                            base_parsed_output["status"] = "error"
                            base_parsed_output["errors"].append(f"Architect syntax correction LLM call failed: {current_syntax_attempt_text}")
                            project_context.architecture = None
                            return base_parsed_output # Fatal error
                    else: # Final syntax attempt failed
                        base_parsed_output["status"] = "error"
                        base_parsed_output["errors"].append(f"Architect JSON syntax error persisted after syntax correction attempts. Last error: {e_json}")
                        project_context.architecture = None
                        return base_parsed_output # Fatal error

            if arch_json_data is None: # If JSON could not be parsed/corrected
                self.logger.log("Architect: Failed to obtain valid JSON data after syntax correction attempts for this iteration.", self.role, level="ERROR")
                # Error already set by inner logic, outer loop will decide to retry or fail.
                base_parsed_output["status"] = "error" # Ensure status reflects error
                if attempt_num >= max_content_retries: # If it's the last content retry attempt
                    break # Exit main retry loop
                else: # Prepare for corrective prompt based on other errors or try again
                    current_response_text_for_attempt = base_parsed_output["raw_response"] # Use the latest raw response for next attempt
                    continue # Go to next iteration of content retry loop

            # 2. Populate Proponent (on the current attempt's arch_json_data)
            if 'tech_proposals' in arch_json_data and arch_json_data['tech_proposals'] is not None:
                for category_proposals in arch_json_data['tech_proposals'].values():
                    if isinstance(category_proposals, list):
                        for proposal_item in category_proposals:
                            if isinstance(proposal_item, dict):
                                proposal_item['proponent'] = self.name

            base_parsed_output['parsed_json_content'] = arch_json_data # Make it available for Pydantic validation

            # 3. Pydantic Model Validation
            validated_arch_data = None
            try:
                validated_arch_data = ArchitectOutputModel(**arch_json_data)
                self.logger.log(f"Architect: ArchitectOutputModel Pydantic validation successful for attempt {attempt_num + 1}.", self.role)
            except ValidationError as e_pydantic:
                self.logger.log(f"Architect: ArchitectOutputModel Pydantic validation failed on attempt {attempt_num + 1}: {e_pydantic}", self.role, level="ERROR")
                base_parsed_output["status"] = "error"
                base_parsed_output["errors"].append(f"Attempt {attempt_num + 1} Pydantic Schema Error: {str(e_pydantic)}")
                project_context.architecture = None
                # If structural validation fails, a tech stack retry might not fix it. Break and report.
                break # Exit main retry loop

            # 4. Tech Stack Content Validation
            # Use current_response_text_for_attempt for validate_tech_stack, as it might contain natural language hints
            tech_stack_validation_errors = validate_tech_stack(current_response_text_for_attempt, project_context.tech_stack)

            if not tech_stack_validation_errors:
                self.logger.log(f"Architect: Tech stack validation successful for attempt {attempt_num + 1}.", self.role)
                project_context.architecture = validated_arch_data.architecture_design.model_dump_json(indent=2)
                self.logger.log(f"Architect: Architecture design updated (JSON, Pydantic-validated, length: {len(project_context.architecture)}).", self.role)
                base_parsed_output["architecture_summary"] = f"Architecture (validated JSON): {validated_arch_data.architecture_design.description[:100]}..."

                if validated_arch_data.tech_proposals is not None:
                    _process_tech_proposals(self.logger, self.name, self.role, validated_arch_data.tech_proposals, project_context)
                else:
                    self.logger.log(f"Architect: No 'tech_proposals' in validated JSON for attempt {attempt_num + 1}.", self.role, level="INFO")

                base_parsed_output["status"] = "complete"
                base_parsed_output["errors"] = [] # Clear errors on success
                attempt_successful = True
                break # Exit main retry loop on success
            else:
                # Tech stack validation failed for the current attempt
                self.logger.log(f"Architect: Tech stack validation failed on attempt {attempt_num + 1}. Violations: {tech_stack_validation_errors}", self.role, level="WARNING")
                base_parsed_output["errors"].append(f"Attempt {attempt_num + 1} Tech Stack Violations: {', '.join(tech_stack_validation_errors)}")
                project_context.architecture = None # Ensure arch is not set with invalid stack

                if attempt_num < max_content_retries:
                    self.logger.log(f"Architect: Attempting LLM correction for tech stack violations (Retry {attempt_num + 1}/{max_content_retries}).", self.role)
                    corrective_prompt_text = (
                        "Your previous architecture design mentioned technologies not allowed by the fixed tech stack.\n"
                        f"Violations: {', '.join(tech_stack_validation_errors)}\n"
                        f"You MUST strictly use ONLY: Frontend: {project_context.tech_stack.frontend}, Backend: {project_context.tech_stack.backend}, Database: {project_context.tech_stack.database}. "
                        "Do not mention or use any other technologies for these components. Provide a revised architecture_design and tech_proposals that strictly adhere to this fixed stack. Ensure the entire response is a single JSON object wrapped in ```json ... ```."
                    )
                    current_response_text_for_attempt = self._call_model(corrective_prompt_text)
                    base_parsed_output["raw_response"] = current_response_text_for_attempt # Update for next loop or final output

                    if current_response_text_for_attempt.startswith("Error:"):
                        self.logger.log(f"Architect: LLM call for tech stack correction failed: {current_response_text_for_attempt}", self.role, level="ERROR")
                        base_parsed_output["status"] = "error"
                        base_parsed_output["errors"].append(f"LLM tech stack correction call failed: {current_response_text_for_attempt}")
                        attempt_successful = False # Ensure failure state
                        break # Exit main retry loop
                    # Loop continues with new current_response_text_for_attempt
                else:
                    self.logger.log(f"Architect: Max content retries ({max_content_retries}) reached. Tech stack validation failed.", self.role, level="ERROR")
                    base_parsed_output["status"] = "error" # Ensure error status
                    attempt_successful = False # Ensure failure state
                    break # Exit main retry loop

        # After the loop, if no attempt was successful
        if not attempt_successful:
            self.logger.log("Architect: All parsing and validation attempts failed.", self.role, level="ERROR")
            base_parsed_output["status"] = "error" # Ensure this is set
            if not base_parsed_output["errors"]: # If no specific errors were added, add a generic one
                 base_parsed_output["errors"].append("Architect failed to produce a valid and compliant architecture after all attempts.")
            project_context.architecture = None

        return base_parsed_output


class APIDesigner(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('api_designer', 'API Designer', logger, db=db)

    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)

        if base_parsed_output["status"] == "error" and not base_parsed_output["raw_response"]:
            # If LLM call itself failed completely (no response text), return immediately.
            return base_parsed_output

        current_response_text = base_parsed_output["raw_response"]
        max_retries = 1
        retry_count = 0
        parsed_json_content = None

        while retry_count <= max_retries:
            extracted_json_str = None
            # Attempt to extract JSON block
            if '```json' in current_response_text:
                json_start_index = current_response_text.find('```json')
                if json_start_index != -1:
                    json_start_actual = json_start_index + 7 # Length of "```json\n"
                    json_end_index = current_response_text.find('```', json_start_actual)
                    if json_end_index != -1:
                        extracted_json_str = current_response_text[json_start_actual:json_end_index].strip()
                    else:
                        # Malformed block (started but not ended), try to recover if it's the only content
                        if json_start_index == 0 and current_response_text.endswith('```'): # Unlikely but possible
                             extracted_json_str = current_response_text[7:-3].strip()
                        else: #Could be text after an unclosed JSON block. Try to parse what's there.
                             extracted_json_str = current_response_text[json_start_actual:].strip()
                             base_parsed_output["warnings"].append("Found '```json' but no closing '```'. Attempting to parse partial content.")
                else: # Should not happen if '```json' is in current_response_text, but as a safeguard
                    extracted_json_str = current_response_text # Assume whole response is JSON
            else: # No triple backticks, assume the whole response is JSON
                extracted_json_str = current_response_text

            if not extracted_json_str:
                message = "Could not extract JSON content from the response."
                self.logger.log(f"[{self.name}] {message} Raw response: {current_response_text[:500]}", self.role, level="WARNING")
                base_parsed_output["warnings"].append(message)
                if retry_count >= max_retries: # If it's already the last attempt
                    base_parsed_output["status"] = "error"
                    base_parsed_output["errors"].append(message)
                retry_count += 1
                continue # Try correction if retries left

            try:
                parsed_json_content = json.loads(extracted_json_str)
                base_parsed_output['parsed_json_content'] = parsed_json_content
                if retry_count > 0:
                    warning_msg = f"JSON syntax self-correction successful on attempt {retry_count}."
                    base_parsed_output["warnings"].append(warning_msg)
                    self.logger.log(f"[{self.name}] {warning_msg}", self.role, level="WARNING")
                base_parsed_output["status"] = "complete" # Mark as complete on successful parse
                if "errors" in base_parsed_output: # Clear previous retry errors if successful now
                    base_parsed_output["errors"] = [e for e in base_parsed_output.get("errors", []) if "JSONDecodeError" not in str(e)]
                break  # Successful parse, exit loop
            except json.JSONDecodeError as e:
                self.logger.log(f"[{self.name}] Attempt {retry_count + 1}: JSON parsing failed: {e}. Problematic text snippet (approx 100 chars around error): '{extracted_json_str[max(0, e.pos-50):e.pos+50]}'", self.role, level="WARNING")

                if retry_count < max_retries:
                    retry_count += 1
                    correction_prompt = (
                        f"The following JSON output, intended for an OpenAPI specification for project '{project_context.project_name}', has a syntax error.\n"
                        f"Original Objective: {project_context.objective}\n"
                        f"Error: {e}\n"
                        f"Malformed JSON text:\n```json\n{extracted_json_str}\n```\n"
                        "Please correct ONLY the syntax error in the JSON content and return the full, corrected, valid JSON object. "
                        "Do not add any explanatory text, markdown, or change the data structure beyond fixing the syntax. "
                        "Ensure all strings are double-quoted, all commas are correctly placed (no trailing commas), and all curly braces and square brackets are correctly paired and balanced. "
                        "Output ONLY the corrected JSON object."
                    )
                    self.logger.log(f"[{self.name}] Attempting self-correction for JSON (attempt {retry_count}/{max_retries}).", self.role)
                    current_response_text = self._call_model(correction_prompt) # LLM call for correction
                    base_parsed_output["raw_response"] = current_response_text # Update raw_response with the attempt
                    if current_response_text.startswith("Error:"): # If LLM call for correction fails
                        self.logger.log(f"[{self.name}] LLM call for JSON correction failed: {current_response_text}", self.role, level="ERROR")
                        base_parsed_output["status"] = "error"
                        base_parsed_output["errors"].append(f"JSON correction LLM call failed: {current_response_text}")
                        break # Break loop if correction call fails
                else:
                    final_error_msg = f"JSON syntax error persisted after {max_retries} correction attempt(s). Last error: {e}"
                    base_parsed_output["status"] = "error"
                    base_parsed_output["errors"].append(final_error_msg)
                    self.logger.log(f"[{self.name}] {final_error_msg}", self.role, level="ERROR")
                    break

        # After the loop, proceed with further validation if JSON was successfully parsed
        if base_parsed_output.get('parsed_json_content') and base_parsed_output["status"] != "error":
            # 1. Tech stack validation (operates on raw response or descriptive text)
            # This should happen BEFORE schema validation, as it might invalidate the attempt based on textual content.
            validation_errors = validate_tech_stack(base_parsed_output["raw_response"], project_context.tech_stack)
            if validation_errors:
                base_parsed_output["status"] = "error"
                base_parsed_output["errors"].extend(validation_errors)
                self.logger.log(f"[{self.name}] Tech stack validation failed for APIDesigner: {validation_errors}", self.role, level="ERROR")
                project_context.api_specs = None # Do not set if tech validation fails
                return base_parsed_output # Return early if tech stack validation fails

            # 2. Pydantic Schema Validation
            api_json_data = base_parsed_output.get('parsed_json_content')
            if api_json_data: # Ensure there is JSON data to validate
                try:
                    self.logger.log("[APIDesigner] Attempting Pydantic schema validation for OpenAPI spec...", self.role, level="INFO")
                    validated_spec = APIDesignerOutputModel(**api_json_data)
                    self.logger.log("[APIDesigner] OpenAPI spec schema validation successful.", self.role, level="INFO")
                    project_context.api_specs = validated_spec.model_dump_json(indent=2, by_alias=True) # Use by_alias for fields like 'in'
                    base_parsed_output["api_specs_summary"] = f"API specs updated (JSON, schema validated): {project_context.api_specs[:100]}..."
                    self.logger.log(f"APIDesigner: API specs updated in project context after Pydantic validation (length: {len(project_context.api_specs)}).", self.role)

                except ValidationError as e:
                    self.logger.log(f"APIDesigner: OpenAPI schema validation failed: {e}", self.role, level="ERROR")
                    base_parsed_output["status"] = "error"
                    base_parsed_output["errors"].append(f"OpenAPI Schema Error: Invalid structure - {str(e)}")
                    project_context.api_specs = None
                    # TODO: Consider a self-correction loop here for schema errors, similar to syntax errors.
                except Exception as e_schema: # Catch any other unexpected error during validation
                    self.logger.log(f"APIDesigner: Unexpected error during Pydantic schema validation: {e_schema}", self.role, level="ERROR")
                    base_parsed_output["status"] = "error"
                    base_parsed_output["errors"].append(f"Unexpected Schema Validation Error: {str(e_schema)}")
                    project_context.api_specs = None
            else: # This case should ideally not be reached if syntax check passed and found content, but as a safeguard
                self.logger.log("[APIDesigner] No parsed_json_content available for schema validation, though syntax check might have passed.", self.role, level="WARNING")
                if base_parsed_output["status"] != "error": # If not already an error from syntax check phase
                    base_parsed_output["warnings"].append("APIDesigner: JSON content was missing or empty before schema validation step.")
                project_context.api_specs = None


        elif base_parsed_output["status"] != "error":
            # This block handles cases where JSON syntax parsing itself failed or produced no usable content,
            # and tech_stack validation (which runs on raw_response) also didn't set status to "error".
            if not base_parsed_output["raw_response"]:
                 base_parsed_output["warnings"].append("APIDesigner returned an empty response.")
            else: # Had raw response, but it wasn't a valid JSON block for the plan
                 base_parsed_output["warnings"].append(f"APIDesigner did not produce a usable JSON output for API specs. Raw response: {base_parsed_output['raw_response'][:200]}")
            project_context.api_specs = None
        else: # Explicit error status from syntax parsing loop or tech_stack validation
            project_context.api_specs = None
            self.logger.log(f"[{self.name}] Finalizing with error status. API specs not updated due to prior errors (e.g., JSON syntax or tech stack mismatch).", self.role, level="ERROR")

        return base_parsed_output


class CodeWriter(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('code_writer', 'Backend Developer', logger, db=db)

    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)

        if base_parsed_output["status"] == "error":
            # Specific check for tool execution errors that might be in the response text
            if "Tool execution failed" in base_parsed_output["raw_response"] or \
               "Tool not found" in base_parsed_output["raw_response"]:
                base_parsed_output["errors"].append(f"CodeWriter: Tool execution error - {base_parsed_output['raw_response']}")
            return base_parsed_output

        # Assuming the raw response is the code or contains the code
        backend_code = base_parsed_output["raw_response"]
        project_context.current_code_snippet = backend_code # Or a more specific field like project_context.backend_code

        self.logger.log(f"CodeWriter: Backend code updated in project context (length: {len(backend_code)}).", self.role)

        if not backend_code:
            base_parsed_output["warnings"].append("CodeWriter returned empty code.")
        elif "error" in backend_code.lower()[:100]: # Check for early error indications in code
             base_parsed_output["warnings"].append(f"CodeWriter: Generated code might contain errors: {backend_code[:100]}...")

        base_parsed_output["backend_code_summary"] = f"Generated backend code length: {len(backend_code)}"
        # The actual code is not returned in this dict, it's on project_context.
        # If main.py needs it directly from result, add: base_parsed_output['backend_code'] = backend_code
        return base_parsed_output


class FrontendBuilder(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('frontend_builder', 'Frontend Developer', logger, db=db)

    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)

        if base_parsed_output["status"] == "error":
            return base_parsed_output

        ui_design_code = base_parsed_output["raw_response"]
        # Decide where to store this. Example: project_context.frontend_code
        # For now, let's assume it's a general snippet or a specific field if defined in ProjectContext
        project_context.current_code_snippet = ui_design_code # Or project_context.ui_code
        self.logger.log(f"FrontendBuilder: UI design/code updated (length: {len(ui_design_code)}).", self.role)

        if not ui_design_code:
            base_parsed_output["warnings"].append("FrontendBuilder returned empty UI design/code.")

        base_parsed_output["ui_design_summary"] = f"Generated UI design/code length: {len(ui_design_code)}"
        return base_parsed_output


class MobileDeveloper(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('mobile_developer', 'Mobile Developer', logger, db=db)

    def validate_stack(self, approved_stack: Dict[str, Any], platform_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """MobileDeveloper specific stack validation."""
        self.logger.log(f"[{self.name}] Validating stack with mobile specialization: {approved_stack}", self.role)

        is_mobile_project = platform_requirements.get("ios") or platform_requirements.get("android")

        if is_mobile_project:
            mobile_db = approved_stack.get("mobile_database")
            if not mobile_db:
                concern_msg = f"{self.name} ({self.role}): Mobile platform required but no mobile_database specified."
                self.logger.log(concern_msg, self.role, level="WARNING")
                return {"approved": False, "concerns": concern_msg}

            # Example of a more specific mobile check (can be expanded)
            # This checks if a purely web-centric DB is proposed for mobile without a known hybrid pattern.
            # For instance, if 'elasticsearch' was proposed directly as 'mobile_database'.
            # This is a simplistic example; real veto logic would be more nuanced.
            unsuitable_standalone_mobile_dbs = ["elasticsearch", "dynamodb"] # Example list
            if mobile_db and any(unsuitable_db in mobile_db.lower() for unsuitable_db in unsuitable_standalone_mobile_dbs):
                # This check needs to be smart about hybrid solutions.
                # If "firestore" is part of the mobile_db string, it might be a hybrid (e.g., "SQLite with Firestore Sync")
                # For now, this is a basic check. A more advanced check would look at `decision_rationale` or structure of `mobile_database`
                if "firestore" not in mobile_db.lower() and "sqlite" not in mobile_db.lower() and "roomdb" not in mobile_db.lower() and "realm" not in mobile_db.lower():
                    concern_msg = f"{self.name} ({self.role}): Proposed mobile_database '{mobile_db}' seems unsuitable for standalone mobile use. Consider a mobile-first DB or a clear hybrid pattern."
                    self.logger.log(concern_msg, self.role, level="WARNING")
                    # This might not be a hard "approved: False" yet, but a strong concern.
                    # For now, let's return it as a concern but still approved, to be reviewed.
                    # The orchestrator can decide if this type of concern halts the process.
                    # To make it a hard veto, set approved = False.
                    # return {"approved": False, "concerns": concern_msg}


        # If this agent has specific checks, it may or may not call super().
        # For this example, if mobile-specific checks pass, we assume it's okay from this agent's perspective.
        # A more robust approach might involve collecting concerns from super() as well.
        # return super().validate_stack(approved_stack, platform_requirements)
        # return {"approved": True, "concerns": None} # Defaulting to True if specific mobile checks pass or don't apply

        is_approved = True
        concerns = []

        mobile_db = approved_stack.get("mobile_database")
        is_android_project = platform_requirements.get("android", False)

        if mobile_db:
            mobile_db_lower = mobile_db.lower()
            if "realm" in mobile_db_lower and is_android_project:
                concerns.append(
                    "Realm selected for mobile_database on Android. Ensure justification in decision_rationale is robust, "
                    "detailing specific needs (e.g., complex data, existing Realm codebase) versus Room's typical advantages for Kotlin/Jetpack."
                )

            # Check for cloud-only DBs without local sync/cache strategy
            cloud_only_keywords = ["dynamodb", "cassandra", "cosmosdb"] # Add more as identified
            local_sync_keywords = ["sqlite", "room", "realm", "cache", "sync", "offline", "local", "embedded"] # Keywords indicating local persistence

            is_cloud_only_db = any(keyword in mobile_db_lower for keyword in cloud_only_keywords)
            has_local_strategy = any(keyword in mobile_db_lower for keyword in local_sync_keywords)

            if is_cloud_only_db and not has_local_strategy:
                is_approved = False
                concerns.append(
                    f"Mobile database '{mobile_db}' appears unsuitable for direct mobile use without an explicitly "
                    "stated local persistence/synchronization strategy. Please clarify or revise."
                )

        # Call super().validate_stack to include base validation and merge results
        super_result = super().validate_stack(approved_stack, platform_requirements)
        if not super_result.get("approved", True): # Default to True if "approved" key is missing
            is_approved = False
        if super_result.get("concerns"):
            concerns.append(super_result["concerns"])

        return {"approved": is_approved, "concerns": " | ".join(concerns) if concerns else None}

    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)

        if base_parsed_output["status"] == "error" and not base_parsed_output["raw_response"]:
            return base_parsed_output

        current_response_text = base_parsed_output["raw_response"]
        max_retries = 1
        retry_count = 0
        parsed_json_content = None # Initialize here

        while retry_count <= max_retries:
            extracted_json_str = None
            if '```json' in current_response_text:
                json_start_index = current_response_text.find('```json')
                if json_start_index != -1:
                    json_start_actual = json_start_index + 7
                    json_end_index = current_response_text.find('```', json_start_actual)
                    if json_end_index != -1:
                        extracted_json_str = current_response_text[json_start_actual:json_end_index].strip()
                    else:
                        extracted_json_str = current_response_text[json_start_actual:].strip()
                        base_parsed_output["warnings"].append("Found '```json' but no closing '```'. Attempting to parse partial content.")
            else:
                extracted_json_str = current_response_text

            if not extracted_json_str:
                message = "Could not extract JSON content for MobileDeveloper."
                self.logger.log(f"[{self.name}] {message} Raw response: {current_response_text[:500]}", self.role, level="WARNING")
                if retry_count >= max_retries:
                    base_parsed_output["status"] = "error"
                    base_parsed_output["errors"].append(message)
                retry_count += 1
                continue

            try:
                parsed_json_content = json.loads(extracted_json_str)
                base_parsed_output['parsed_json_content'] = parsed_json_content
                if retry_count > 0:
                    base_parsed_output["warnings"].append(f"JSON syntax self-correction successful for MobileDeveloper on attempt {retry_count}.")
                base_parsed_output["status"] = "complete"
                base_parsed_output["errors"] = [e for e in base_parsed_output.get("errors", []) if "JSONDecodeError" not in str(e)]
                break
            except json.JSONDecodeError as e:
                self.logger.log(f"[{self.name}] Attempt {retry_count + 1}: JSON parsing failed: {e}. Snippet: '{extracted_json_str[max(0, e.pos-50):e.pos+50]}'", self.role, level="WARNING")
                if retry_count < max_retries:
                    retry_count += 1
                    correction_prompt = (
                        f"The following JSON output, intended for mobile application design details for project '{project_context.project_name}', has a syntax error.\n"
                        f"Error: {e}\n"
                        f"Malformed JSON text:\n```json\n{extracted_json_str}\n```\n"
                        "Correct ONLY the syntax error and return the full, corrected, valid JSON object for 'mobile_details' and 'tech_proposals'. "
                        "Do not add explanatory text or change the data structure. Ensure valid JSON."
                    )
                    current_response_text = self._call_model(correction_prompt)
                    base_parsed_output["raw_response"] = current_response_text
                    if current_response_text.startswith("Error:"):
                        base_parsed_output["status"] = "error"
                        base_parsed_output["errors"].append(f"MobileDeveloper JSON correction LLM call failed: {current_response_text}")
                        break
                else:
                    base_parsed_output["status"] = "error"
                    base_parsed_output["errors"].append(f"MobileDeveloper JSON syntax error persisted after {max_retries} attempts. Last error: {e}")
                    break

        if base_parsed_output["status"] == "error":
            project_context.current_code_snippet = None # Or a more specific mobile_design field
            return base_parsed_output

        tech_stack_validation_errors = validate_tech_stack(base_parsed_output["raw_response"], project_context.tech_stack)
        if tech_stack_validation_errors:
            base_parsed_output["status"] = "error"
            base_parsed_output["errors"].extend(tech_stack_validation_errors)
            self.logger.log(f"[{self.name}] Tech stack validation failed for MobileDeveloper output: {tech_stack_validation_errors}", self.role, level="ERROR")
            project_context.current_code_snippet = None
            return base_parsed_output

        if base_parsed_output.get('parsed_json_content'):
            mobile_json_data = base_parsed_output['parsed_json_content']

            # START MODIFICATION: Populate proponent field before Pydantic validation
            if 'tech_proposals' in mobile_json_data and mobile_json_data['tech_proposals'] is not None:
                for category, proposals_list in mobile_json_data['tech_proposals'].items():
                    if isinstance(proposals_list, list):
                        for proposal_item_dict in proposals_list:
                            if isinstance(proposal_item_dict, dict):
                                proposal_item_dict['proponent'] = self.name
            # END MODIFICATION

            # START PREPROCESSING: Convert list fields in mobile_details to string
            if 'mobile_details' in mobile_json_data and isinstance(mobile_json_data['mobile_details'], dict):
                details_dict = mobile_json_data['mobile_details']
                fields_to_join = ["component_structure", "navigation", "state_management", "api_integration", "framework_solutions"]
                for field_name in fields_to_join:
                    if field_name in details_dict and isinstance(details_dict[field_name], list):
                        string_elements = [str(item) for item in details_dict[field_name]]
                        details_dict[field_name] = '\n'.join(string_elements)
                        self.logger.log(f"MobileDeveloper: Joined list for field '{field_name}' in mobile_details.", self.role, level="DEBUG")
            # END PREPROCESSING

            try:
                validated_mobile_data = MobileOutputModel(**mobile_json_data)
                self.logger.log(f"MobileDeveloper: Output JSON schema validation successful.", self.role)
                project_context.current_code_snippet = validated_mobile_data.mobile_details.model_dump_json(indent=2)
                self.logger.log(f"MobileDeveloper: Mobile details updated (JSON, Pydantic-validated, length: {len(project_context.current_code_snippet)}).", self.role)
                base_parsed_output["mobile_code_summary"] = f"Mobile details (validated JSON): {validated_mobile_data.mobile_details.component_structure[:100]}..."

                if validated_mobile_data.tech_proposals is not None:
                     _process_tech_proposals(self.logger, self.name, self.role, validated_mobile_data.tech_proposals, project_context)
                else:
                    self.logger.log(f"MobileDeveloper: No 'tech_proposals' in validated JSON.", self.role, level="INFO")
            except ValidationError as e:
                self.logger.log(f"MobileDeveloper: Output JSON schema validation failed: {e}", self.role, level="ERROR")
                base_parsed_output["status"] = "error"
                base_parsed_output["errors"].append(f"Mobile Output Schema Error: Invalid structure - {str(e)}")
                project_context.current_code_snippet = None
        else:
            self.logger.log("MobileDeveloper: No valid JSON content for schema validation.", self.role, level="ERROR")
            base_parsed_output["status"] = "error"
            base_parsed_output["errors"].append("MobileDeveloper failed to produce valid JSON for schema validation.")
            project_context.current_code_snippet = None

        return base_parsed_output


class Tester(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('tester', 'QA Engineer', logger, db=db)

    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)

        if base_parsed_output["status"] == "error":
            return base_parsed_output

        test_plan_or_results = base_parsed_output["raw_response"]
        # project_context.test_results = test_plan_or_results # Example storage
        self.logger.log(f"Tester: Test plan/results received (length: {len(test_plan_or_results)}).", self.role)

        if not test_plan_or_results:
            base_parsed_output["warnings"].append("Tester returned empty test plan/results.")

        base_parsed_output["test_summary"] = f"Test plan/results length: {len(test_plan_or_results)}"
        # If actual test execution happens and project_context has fields for test outcomes, update them.
        # e.g., project_context.test_passed = True/False
        return base_parsed_output


class Debugger(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('debugger', 'Debug Specialist', logger, db=db)

    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)

        if base_parsed_output["status"] == "error":
            return base_parsed_output

        fixed_code_or_analysis = base_parsed_output["raw_response"]
        project_context.current_code_snippet = fixed_code_or_analysis # Example: update current snippet with fix
        project_context.error_report = "" # Clear error report if debugger claims to have fixed it.

        self.logger.log(f"Debugger: Fixed code/analysis received (length: {len(fixed_code_or_analysis)}). Error report cleared.", self.role)

        if not fixed_code_or_analysis:
            base_parsed_output["warnings"].append("Debugger returned empty fixed code/analysis.")

        base_parsed_output["debug_summary"] = f"Fixed code/analysis length: {len(fixed_code_or_analysis)}"
        return base_parsed_output
