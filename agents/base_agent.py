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

from utils.general_utils import Logger
from utils.database import Database
from utils.local_llm_client import LocalLLMClient # CORRECTED
from prompts.general_prompts import get_agent_prompt
from utils.tools import ToolKit
from configs.global_config import MODEL_STRATEGY_CONFIG, GeminiConfig, ModelConfig

import socket
import threading
# from models import ProjectAnalysis, AgentOutput # Removed as ProjectAnalysis is part of context_handler
from pydantic import ValidationError # Already present
from utils.models import (
    PlatformRequirements, TechProposal, PlannerOutputModel,
    APIDesignerOutputModel, ArchitectOutputModel, MobileOutputModel
)
from typing import List, Dict, Any, Optional

# Import from context_handler
from utils.context_handler import ProjectContext, AnalysisOutput, TechStack, load_context, save_context
from utils.validation_utils import validate_tech_stack, get_tech_stack_validation_prompt_segment

# Define context file path
CONTEXT_JSON_FILE = Path("project_context.json")

class Agent:
    def __init__(self, name, role, logger: Logger, model_type='gemini', db: Database = None):
        self.name = name
        self.role = role
        self.model_type = model_type  # Always use 'gemini' now
        self.logger = logger
        self.tool_kit: Optional[ToolKit] = None
        self.tools = []

        self.db = db

        self.gemini_config = GeminiConfig()
        self.model_config = ModelConfig()
        self.generation_config = GeminiConfig.get_generation_config(name)

        self.strategy_config = MODEL_STRATEGY_CONFIG
        if self.name in self.strategy_config.CODING_AGENT_NAMES:
            self.primary_model_name = self.strategy_config.CODING_MODEL_NAME
        else:
            self.primary_model_name = self.strategy_config.DEFAULT_GEMINI_MODEL

        self.current_model = self.primary_model_name

        self.local_client = LocalLLMClient(logger=self.logger) # Pass logger
        
        if not GeminiConfig.validate_api_key():
            self.logger.log(f"Warning: Gemini API key not properly configured for {name}", role, level="WARNING")

    def perform_task(self, project_context: ProjectContext) -> dict:
        analysis_data = {}
        if project_context.analysis:
            analysis_data = project_context.analysis.model_dump()

        self.logger.log(f"[{self.name}] Pre-prompt_context: project_context.tech_stack is: {project_context.tech_stack}", self.role)
        if project_context.tech_stack:
            self.logger.log(f"[{self.name}] Pre-prompt_context: tech_stack.frontend={project_context.tech_stack.frontend}, backend={project_context.tech_stack.backend}, database={project_context.tech_stack.database}", self.role)

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
            'memories': project_context.project_summary or "No specific memories retrieved for this task yet.",
            'tool_names': [tool['name'] for tool in self.tools],
            'tools': self.tools,
            'analysis': analysis_data,
            'current_code_snippet': project_context.current_code_snippet or "",
            'error_report': project_context.error_report or "",
            'tech_stack': project_context.tech_stack.model_dump() if project_context.tech_stack else {},
            'tech_stack_frontend': project_context.tech_stack.frontend if project_context.tech_stack and project_context.tech_stack.frontend is not None else "not specified",
            'tech_stack_frontend_lowercase': project_context.tech_stack.frontend.lower() if project_context.tech_stack and project_context.tech_stack.frontend is not None else "not_specified",
            'tech_stack_backend': project_context.tech_stack.backend if project_context.tech_stack and project_context.tech_stack.backend is not None else "not specified",
            'tech_stack_backend_lowercase': project_context.tech_stack.backend.lower() if project_context.tech_stack and project_context.tech_stack.backend is not None else "not_specified",
            'tech_stack_database': project_context.tech_stack.database if project_context.tech_stack and project_context.tech_stack.database is not None else "not specified",
            'tech_stack_database_lowercase': project_context.tech_stack.database.lower() if project_context.tech_stack and project_context.tech_stack.database is not None else "not_specified",
        }

        if self.name == "architect" or self.name == "api_designer":
            prompt_context['tech_stack_frontend_name'] = project_context.tech_stack.frontend if project_context.tech_stack and project_context.tech_stack.frontend is not None else "Not Specified"
            prompt_context['tech_stack_backend_name'] = project_context.tech_stack.backend if project_context.tech_stack and project_context.tech_stack.backend is not None else "Not Specified"
            prompt_context['tech_stack_database_name'] = project_context.tech_stack.database if project_context.tech_stack and project_context.tech_stack.database is not None else "Not Specified"
        
        self.logger.log(f"[{self.name}] Constructed prompt_context: {json.dumps(prompt_context, indent=2, default=str)}", self.role)
        self.logger.log(f"[{self.name}] About to call get_agent_prompt.", self.role)

        generated_prompt_str = get_agent_prompt(self.name, prompt_context)
        
        self.logger.log(f"[{self.name}] Returned from get_agent_prompt. Prompt length: {len(generated_prompt_str)}. First 200 chars: {generated_prompt_str[:200]}", self.role)

        if self.name in ["planner", "architect", "api_designer"]:
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

        parsed_result = self._parse_response(response_content, project_context)
        self.add_to_memory(response_content)
        return parsed_result

    def reserve_port(self, port: int = 0) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return s.getsockname()[1]

    def _invoke_model(self, model_name: str, prompt: str, uses_tools: bool) -> str:
        self.logger.log(f"[{self.name}] Invoking model: {model_name}", self.role)
        self.current_model = model_name

        if model_name.startswith("gemini-"):
            if uses_tools:
                return self._call_gemini_with_tools(prompt)
            else:
                return self._call_gemini(prompt)
        elif model_name in self.strategy_config.LOCAL_MODEL_ENDPOINTS:
            endpoint_url = self.strategy_config.LOCAL_MODEL_ENDPOINTS[model_name]
            if uses_tools:
                self.logger.log(f"[{self.name}] Tool use with local model {model_name} requested but not yet implemented. Falling back to text generation.", self.role, level="WARNING")
                return self.local_client.generate(base_api_url=endpoint_url, prompt=prompt, model_name=model_name)
            else:
                return self.local_client.generate(base_api_url=endpoint_url, prompt=prompt, model_name=model_name)
        else:
            self.logger.log(f"[{self.name}] Unknown model_name: {model_name}. Cannot invoke.", self.role, level="ERROR")
            return f"Error: Unknown model_name {model_name}"

    def _execute_task_with_retry_and_fallback(self, prompt: str, uses_tools: bool) -> str:
        primary_model_to_try = self.primary_model_name
        self.current_model = primary_model_to_try

        try:
            self.logger.log(f"[{self.name}] Primary attempt with {self.current_model}", self.role)
            response = self._invoke_model(self.current_model, prompt, uses_tools)

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
                                                "Request failed" in str(e)

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
        return self._execute_task_with_retry_and_fallback(prompt, uses_tools=False)

    def _call_model_with_tools(self, prompt: str) -> str:
        return self._execute_task_with_retry_and_fallback(prompt, uses_tools=True)

    def _call_gemini_with_retry(self, prompt: str, max_retries: int = 2) -> str:
        for attempt in range(max_retries + 1):
            try:
                return self._call_gemini(prompt)
            except Exception as e:
                self.logger.log(f"[{self.name}] Attempt {attempt + 1} failed: {e}", self.role, level="WARNING")
                
                if attempt < max_retries:
                    old_model = self.current_model
                    self.current_model = self.model_config.get_fallback_model(self.current_model)
                    self.logger.log(f"[{self.name}] Falling back from {old_model} to {self.current_model}", self.role)
                    time.sleep(1)
                else:
                    return f"Error: All Gemini model attempts failed: {str(e)}"
        return f"Error: All Gemini model attempts failed (exhausted retries)." # Should be unreachable due to else above

    def _call_gemini_with_tools_retry(self, prompt: str, max_retries: int = 2) -> str:
        for attempt in range(max_retries + 1):
            try:
                return self._call_gemini_with_tools(prompt)
            except Exception as e:
                self.logger.log(f"[{self.name}] Tools attempt {attempt + 1} failed: {e}", self.role, level="WARNING")
                
                if attempt < max_retries:
                    old_model = self.current_model
                    self.current_model = self.model_config.get_fallback_model(self.current_model)
                    self.logger.log(f"[{self.name}] Falling back from {old_model} to {self.current_model}", self.role)
                    time.sleep(1)
                else:
                    return f"Error: All Gemini tool attempts failed: {str(e)}"
        return f"Error: All Gemini tool attempts failed (exhausted retries)." # Should be unreachable

    def _call_gemini(self, prompt: str) -> str:
        url = f"{GeminiConfig.BASE_URL}/{self.current_model}:generateContent"
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': self.generation_config,
            'safetySettings': GeminiConfig.SAFETY_SETTINGS
        }
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(
                url, params={'key': GeminiConfig.API_KEY}, headers=headers, json=payload, timeout=90
            )
            response.raise_for_status()
            data = response.json()
            
            if 'usageMetadata' in data:
                usage = data['usageMetadata']
                self.logger.log(f"[{self.name}] Tokens: {usage.get('totalTokenCount', 0)} "
                              f"(prompt: {usage.get('promptTokenCount', 0)}, "
                              f"response: {usage.get('candidatesTokenCount', 0)})", self.role)
            
            candidates = data.get('candidates', [])
            if candidates and 'content' in candidates[0]:
                parts = candidates[0]['content'].get('parts', [])
                if parts and 'text' in parts[0]:
                    response_text = parts[0]['text'].strip()
                    finish_reason = candidates[0].get('finishReason', 'UNKNOWN')
                    if finish_reason != 'STOP':
                        self.logger.log(f"[{self.name}] Finish reason: {finish_reason}", self.role, level="WARNING")
                    return response_text
            
            if candidates and candidates[0].get('finishReason') == 'SAFETY':
                return "Response blocked by safety filters. Please rephrase your request."
            
            self.logger.log(f"[{self.name}] Empty response from {self.current_model}", self.role, level="WARNING")
            return "No response generated"
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429: raise Exception(f"Rate limit exceeded for {self.current_model}")
            elif e.response.status_code == 403: raise Exception(f"API key invalid or quota exceeded for {self.current_model}")
            else: raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except requests.exceptions.RequestException as e: raise Exception(f"Request failed for {self.current_model}: {str(e)}")
        except Exception as e: raise Exception(f"Processing error for {self.current_model}: {str(e)}")

    def _call_gemini_with_tools(self, prompt: str) -> str:
        url = f"{GeminiConfig.BASE_URL}/{self.current_model}:generateContent"
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': self.generation_config,
            'safetySettings': GeminiConfig.SAFETY_SETTINGS,
            'tools': [{'functionDeclarations': self.tools}]
        }
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(
                url, params={'key': GeminiConfig.API_KEY}, headers=headers, json=payload, timeout=90
            )
            response.raise_for_status()
            data = response.json()
            
            if 'usageMetadata' in data:
                usage = data['usageMetadata']
                self.logger.log(f"[{self.name}] Tools Tokens: {usage.get('totalTokenCount', 0)}", self.role)
            
            candidates = data.get('candidates', [])
            if candidates and 'content' in candidates[0]:
                parts = candidates[0]['content'].get('parts', [])
                for part in parts:
                    if 'functionCall' in part:
                        function_call = part['functionCall']
                        function_name = function_call.get('name', '')
                        function_args = function_call.get('args', {})
                        self.logger.log(f"[{self.name}] Tool call: {function_name}", self.role)
                        if self.tool_kit and hasattr(self.tool_kit, function_name):
                            try:
                                tool_result = getattr(self.tool_kit, function_name)(**function_args)
                                return f"Tool executed: {function_name}\nResult: {tool_result}"
                            except Exception as e: return f"Tool execution failed: {function_name}\nError: {str(e)}"
                        else: return f"Tool not found: {function_name}"
                for part in parts:
                    if 'text' in part:
                        response_text = part['text'].strip()
                        if response_text: return response_text
            
            if candidates and candidates[0].get('finishReason') == 'SAFETY':
                return "Response blocked by safety filters. Please rephrase your request."
            self.logger.log(f"[{self.name}] Empty tools response from {self.current_model}", self.role, level="WARNING")
            return "No response generated with tools"
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429: raise Exception(f"Rate limit exceeded for {self.current_model}")
            elif e.response.status_code == 403: raise Exception(f"API key invalid or quota exceeded for {self.current_model}")
            else: raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        except requests.exceptions.RequestException as e: raise Exception(f"Request failed for {self.current_model}: {str(e)}")
        except Exception as e: raise Exception(f"Processing error for {self.current_model}: {str(e)}")

    def _parse_response(self, response_text: str, project_context: ProjectContext) -> dict:
        parsed_result = {
            "status": "complete", "errors": [], "warnings": [], "raw_response": response_text,
            "agent_name": self.name, "agent_role": self.role, "model_used": self.current_model
        }
        if not response_text or response_text.startswith("Error:") or "Response blocked by safety filters" in response_text or "No response generated" in response_text:
            parsed_result["status"] = "error"
            error_message = response_text if response_text else "Empty response from LLM."
            parsed_result["errors"].append(error_message)
            self.logger.log(f"LLM call failed or returned error for {self.name}: {error_message}", self.role, level="ERROR")
            return parsed_result
        try:
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                if json_end > json_start:
                    json_str = response_text[json_start:json_end].strip()
                    parsed_json = json.loads(json_str)
                    parsed_result['parsed_json_content'] = parsed_json
                else:
                    parsed_result["warnings"].append("Found '```json' but could not parse a valid JSON block.")
        except json.JSONDecodeError as e:
            parsed_result["warnings"].append(f"Could not parse JSON from LLM response: {e}")
            self.logger.log(f"JSON parsing failed for {self.name}: {e}", self.role, level="WARNING")
        return parsed_result

    def add_to_memory(self, content: str):
        item_id = f"{self.name}_{time.time()}"
        try:
          embedding = numpy.random.rand(384).astype(numpy.float32)
        except Exception as e:
            self.logger.log(f"Numpy didn't work for embedding generation: {e}","ToolKit", level="ERROR")
            return
        if self.db:
           if self.db.store_embedding(item_id=item_id, agent_id=self.name, role=self.role, content=content, embedding=embedding):
               self.logger.log(f"Added content to memory store for {self.name}: {item_id[:20]}...", self.role)

    def set_tools(self, tool_kit: ToolKit):
        self.tool_kit = tool_kit
        self.tools = tool_kit.get_tool_definitions() if tool_kit else []
        self.logger.log(f"[{self.name}] Configured with {len(self.tools)} tools", self.role)

    def validate_stack(self, approved_stack: Dict[str, Any], platform_requirements: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.log(f"[{self.name}] Validating stack (base implementation): {approved_stack}", self.role)
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

def _process_tech_proposals(logger: Logger, agent_name: str, agent_role: str, raw_proposals_dict: Optional[Dict[str, Any]], project_context: ProjectContext):
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
        except Exception as e:
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
        for proposal_item in proposals_list:
            logger.log(f"[_process_tech_proposals] Processing proposal item for category '{category}' by agent '{agent_name}': {proposal_item.model_dump_json(indent=2)}", agent_role, level="DEBUG")
            if not isinstance(proposal_item, TechProposal):
                logger.log(f"[_process_tech_proposals] Proposal item in category '{category}' for agent '{agent_name}' is not a TechProposal object. Skipping. Item: {str(proposal_item)}", agent_role, level="WARNING")
                continue
            try:
                if not proposal_item.proponent:
                    logger.log(f"[_process_tech_proposals] TechProposal object for '{proposal_item.technology}' is missing 'proponent' field. Setting it now to agent_name '{agent_name}'. This should ideally be set by the Architect agent.", agent_role, level="WARNING")
                    proposal_item.proponent = agent_name
                project_context.tech_proposals[category].append(proposal_item)
                logger.log(f"[_process_tech_proposals] Agent '{agent_name}' successfully added tech proposal for '{category}': {proposal_item.technology}", agent_role)
            except ValidationError as e:
                logger.log(f"[_process_tech_proposals] Unexpected ValidationError for an already validated TechProposal for category '{category}'. Item: {proposal_item.model_dump_json(indent=2)}. Error: {e}", agent_role, level="ERROR")
            except Exception as e:
                logger.log(f"[_process_tech_proposals] Unexpected error processing TechProposal for category '{category}'. Item: {str(proposal_item)}. Error: {e}", agent_role, level="ERROR")

class ProjectAnalyzer(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('project_analyzer', 'Project Analyst', logger, db=db)
    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        if self.tool_kit and project_context.objective:
            try:
                detected_platforms_dict = self.tool_kit.detect_platforms(objective=project_context.objective)
                project_context.platform_requirements = PlatformRequirements(**detected_platforms_dict)
                self.logger.log(f"ProjectAnalyzer: Platform requirements detected and set: {project_context.platform_requirements.model_dump()}", self.role)
            except Exception as e:
                self.logger.log(f"ProjectAnalyzer: Error during platform detection: {e}", self.role, level="ERROR")
                project_context.platform_requirements = PlatformRequirements()
        base_parsed_output = super()._parse_response(text, project_context)
        if base_parsed_output["status"] == "error": return base_parsed_output
        try:
            json_str = None
            if 'parsed_json_content' in base_parsed_output:
                analysis_data = base_parsed_output['parsed_json_content']
            else:
                self.logger.log(f"ProjectAnalyzer: No '```json' block found by base parser. Attempting to parse entire response.", self.role, level="INFO")
                json_str = base_parsed_output["raw_response"]
                analysis_data = json.loads(json_str)
            suggested_tech_stack_data = analysis_data.get("suggested_tech_stack")
            if suggested_tech_stack_data is not None:
                try:
                    final_suggested_data = {
                        'frontend': suggested_tech_stack_data.get('frontend'),
                        'backend': suggested_tech_stack_data.get('backend'),
                        'database': suggested_tech_stack_data.get('database')
                    }
                    new_tech_stack = TechStack(**final_suggested_data)
                    project_context.tech_stack = new_tech_stack
                    self.logger.log(f"ProjectAnalyzer updated project_context.tech_stack with suggested: Frontend='{new_tech_stack.frontend}', Backend='{new_tech_stack.backend}', Database='{new_tech_stack.database}'", self.role)
                except Exception as e_techstack:
                    self.logger.log(f"ProjectAnalyzer: Error processing suggested_tech_stack: {e_techstack}. Data: {suggested_tech_stack_data}", self.role, level="WARNING")
            project_context.analysis = AnalysisOutput(**analysis_data)
            self.logger.log(f"ProjectAnalyzer: Analysis data parsed and validated successfully.", self.role)
            base_parsed_output["analysis_summary"] = f"Type: {project_context.analysis.project_type_confirmed}, Backend: {project_context.analysis.backend_needed}, Frontend: {project_context.analysis.frontend_needed}"
        except json.JSONDecodeError as e:
            error_msg = f"Failed to decode JSON analysis from LLM: {e}. Response: {base_parsed_output['raw_response'][:200]}"
            self.logger.log(error_msg, self.role, level="ERROR")
            base_parsed_output["status"] = "error"
            base_parsed_output["errors"].append(error_msg)
            project_context.analysis = AnalysisOutput(project_type_confirmed="error_parsing_failed", key_requirements=[error_msg])
        except ValidationError as e:
            error_msg = f"Analysis data validation failed: {e}. Data: {analysis_data if 'analysis_data' in locals() else 'N/A'}"
            self.logger.log(error_msg, self.role, level="ERROR")
            base_parsed_output["status"] = "error"
            base_parsed_output["errors"].append(error_msg)
            project_context.analysis = AnalysisOutput(project_type_confirmed="error_validation_failed", key_requirements=[str(e)])
        except Exception as e:
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
        if base_parsed_output["status"] == "error": return base_parsed_output
        tech_stack_validation_errors = validate_tech_stack(base_parsed_output["raw_response"], project_context.tech_stack)
        if tech_stack_validation_errors:
            base_parsed_output["status"] = "error"
            base_parsed_output["errors"].extend(tech_stack_validation_errors)
            self.logger.log(f"[{self.name}] Tech stack validation failed for Planner output: {tech_stack_validation_errors}", self.role, level="ERROR")
            project_context.plan = None
            return base_parsed_output
        if 'parsed_json_content' in base_parsed_output and base_parsed_output['parsed_json_content']:
            plan_json_data = base_parsed_output['parsed_json_content']
            try:
                validated_plan = PlannerOutputModel(**plan_json_data)
                project_context.plan = validated_plan.model_dump_json(indent=2)
                self.logger.log(f"Planner: Plan parsed, Pydantic-validated, and updated in project context (length: {len(project_context.plan)}).", self.role)
                num_milestones = len(validated_plan.milestones)
                num_risks = len(validated_plan.key_risks)
                base_parsed_output["plan_summary"] = f"Plan (validated JSON): {num_milestones} milestones, {num_risks} key risks. First milestone: '{validated_plan.milestones[0].name if num_milestones > 0 else 'N/A'}'"
            except ValidationError as e:
                self.logger.log(f"Planner: Plan JSON schema validation failed: {e}", self.role, level="ERROR")
                base_parsed_output["status"] = "error"
                base_parsed_output["errors"].append(f"Plan Schema Error: Invalid structure - {str(e)}")
                project_context.plan = None
            return base_parsed_output
        raw_response = base_parsed_output.get("raw_response", "")
        plan_json_data = None
        parsing_method_description = "Primary ```json``` block"
        if not base_parsed_output.get('parsed_json_content'):
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
                    base_parsed_output["raw_response"] = new_response_text
                    if new_response_text.startswith("Error:"):
                        self.logger.log(f"Planner: LLM call for JSON correction failed: {new_response_text}", self.role, level="ERROR")
                        base_parsed_output["errors"].append(f"LLM correction call failed: {new_response_text}")
                        break
                    retry_parsed_json = None
                    if '```json' in new_response_text:
                        json_start = new_response_text.find('```json') + 7
                        json_end = new_response_text.find('```', json_start)
                        if json_end > json_start:
                            json_str = new_response_text[json_start:json_end].strip()
                            try: retry_parsed_json = json.loads(json_str)
                            except json.JSONDecodeError as e_retry: self.logger.log(f"Planner: JSON syntax error in retry response: {e_retry}. Content: {json_str[:200]}...", self.role, level="WARNING")
                    if isinstance(retry_parsed_json, dict):
                        plan_json_data = retry_parsed_json
                        parsing_method_description = f"LLM-Correction-Retry attempt {i+1}"
                        self.logger.log(f"Planner: Successfully parsed JSON using {parsing_method_description}.", self.role, level="INFO")
                        base_parsed_output['parsed_json_content'] = plan_json_data
                        break
                    else: self.logger.log(f"Planner: Retry attempt {i+1} did not yield a valid JSON dictionary.", self.role, level="WARNING")
        if plan_json_data is not None:
            try:
                validated_plan = PlannerOutputModel(**plan_json_data)
                project_context.plan = validated_plan.model_dump_json(indent=2)
                self.logger.log(f"Planner: Plan parsed via {parsing_method_description}, Pydantic-validated, and updated in project context (length: {len(project_context.plan)}).", self.role)
                num_milestones = len(validated_plan.milestones); num_risks = len(validated_plan.key_risks)
                base_parsed_output["plan_summary"] = f"Plan (validated JSON via {parsing_method_description}): {num_milestones} milestones, {num_risks} key risks. First: '{validated_plan.milestones[0].name if num_milestones > 0 else 'N/A'}'"
                base_parsed_output["status"] = "complete"
                if not base_parsed_output.get('parsed_json_content'): base_parsed_output['parsed_json_content'] = plan_json_data
                base_parsed_output["errors"] = []
            except ValidationError as e:
                self.logger.log(f"Planner: ({parsing_method_description}) Plan JSON schema validation failed: {e}. Data: {plan_json_data}", self.role, level="ERROR")
                base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(f"Plan Schema Error ({parsing_method_description}): Invalid structure - {str(e)}"); project_context.plan = None
        else:
            self.logger.log("Planner: No valid JSON content found for the plan after all primary, fallback, and retry attempts.", self.role, level="ERROR")
            base_parsed_output["status"] = "error"
            if not any("Planner failed to produce" in err for err in base_parsed_output.get("errors", [])):
                 base_parsed_output["errors"].append("Planner failed to produce a valid JSON plan after all attempts, including LLM-correction retry.")
            project_context.plan = None
        return base_parsed_output

class Architect(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('architect', 'System Architect', logger, db=db)
    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)
        if base_parsed_output["status"] == "error" and not base_parsed_output["raw_response"]: return base_parsed_output
        current_response_text_for_attempt = base_parsed_output["raw_response"]
        max_content_retries = 1; attempt_successful = False; base_parsed_output["errors"] = []
        for attempt_num in range(max_content_retries + 1):
            self.logger.log(f"Architect: Parsing attempt {attempt_num + 1}/{max_content_retries + 1}", self.role); arch_json_data = None
            max_syntax_correction_retries = 1; current_syntax_attempt_text = current_response_text_for_attempt
            for syntax_retry_num in range(max_syntax_correction_retries + 1):
                extracted_json_str = None
                if '```json' in current_syntax_attempt_text:
                    json_start_index = current_syntax_attempt_text.find('```json')
                    if json_start_index != -1:
                        json_start_actual = json_start_index + 7
                        json_end_index = current_syntax_attempt_text.find('```', json_start_actual)
                        if json_end_index != -1: extracted_json_str = current_syntax_attempt_text[json_start_actual:json_end_index].strip()
                        else: extracted_json_str = current_syntax_attempt_text[json_start_actual:].strip(); base_parsed_output["warnings"].append("Found '```json' but no closing '```'. Attempting to parse partial content for Architect.")
                else: extracted_json_str = current_syntax_attempt_text
                if not extracted_json_str:
                    self.logger.log(f"Architect: Could not extract JSON content on syntax attempt {syntax_retry_num + 1}. Raw: {current_syntax_attempt_text[:200]}", self.role, level="WARNING")
                    if syntax_retry_num < max_syntax_correction_retries: base_parsed_output["errors"].append("Failed to extract JSON content."); break
                    else: base_parsed_output["status"] = "error"; base_parsed_output["errors"].append("Persistent failure to extract JSON content from Architect response."); project_context.architecture = None; return base_parsed_output
                try:
                    arch_json_data = json.loads(extracted_json_str)
                    if syntax_retry_num > 0: base_parsed_output["warnings"].append(f"JSON syntax self-correction for Architect successful on syntax attempt {syntax_retry_num}.")
                    self.logger.log("Architect: JSON syntax appears valid for current attempt.", self.role); break
                except json.JSONDecodeError as e_json:
                    self.logger.log(f"Architect: JSON parsing failed on syntax attempt {syntax_retry_num + 1}: {e_json}. Snippet: '{extracted_json_str[max(0, e_json.pos-25):e_json.pos+25]}'", self.role, level="WARNING")
                    if syntax_retry_num < max_syntax_correction_retries:
                        syntax_correction_prompt = (f"The following JSON output for system architecture has a syntax error: {e_json}\n" f"Malformed JSON text:\n```json\n{extracted_json_str}\n```\n" "Correct ONLY the syntax error and return the full, corrected, valid JSON. Do not add explanatory text.")
                        current_syntax_attempt_text = self._call_model(syntax_correction_prompt); base_parsed_output["raw_response"] = current_syntax_attempt_text
                        if current_syntax_attempt_text.startswith("Error:"): base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(f"Architect syntax correction LLM call failed: {current_syntax_attempt_text}"); project_context.architecture = None; return base_parsed_output
                    else: base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(f"Architect JSON syntax error persisted after syntax correction attempts. Last error: {e_json}"); project_context.architecture = None; return base_parsed_output
            if arch_json_data is None:
                self.logger.log("Architect: Failed to obtain valid JSON data after syntax correction attempts for this iteration.", self.role, level="ERROR")
                base_parsed_output["status"] = "error"
                if attempt_num >= max_content_retries: break
                else: current_response_text_for_attempt = base_parsed_output["raw_response"]; continue
            if 'tech_proposals' in arch_json_data and arch_json_data['tech_proposals'] is not None:
                for category_proposals in arch_json_data['tech_proposals'].values():
                    if isinstance(category_proposals, list):
                        for proposal_item in category_proposals:
                            if isinstance(proposal_item, dict): proposal_item['proponent'] = self.name
            base_parsed_output['parsed_json_content'] = arch_json_data
            validated_arch_data = None
            try:
                validated_arch_data = ArchitectOutputModel(**arch_json_data)
                self.logger.log(f"Architect: ArchitectOutputModel Pydantic validation successful for attempt {attempt_num + 1}.", self.role)
            except ValidationError as e_pydantic:
                self.logger.log(f"Architect: ArchitectOutputModel Pydantic validation failed on attempt {attempt_num + 1}: {e_pydantic}", self.role, level="ERROR")
                base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(f"Attempt {attempt_num + 1} Pydantic Schema Error: {str(e_pydantic)}"); project_context.architecture = None; break
            tech_stack_validation_errors = validate_tech_stack(current_response_text_for_attempt, project_context.tech_stack)
            if not tech_stack_validation_errors:
                self.logger.log(f"Architect: Tech stack validation successful for attempt {attempt_num + 1}.", self.role)
                project_context.architecture = validated_arch_data.architecture_design.model_dump_json(indent=2)
                self.logger.log(f"Architect: Architecture design updated (JSON, Pydantic-validated, length: {len(project_context.architecture)}).", self.role)
                base_parsed_output["architecture_summary"] = f"Architecture (validated JSON): {validated_arch_data.architecture_design.description[:100]}..."
                if validated_arch_data.tech_proposals is not None: _process_tech_proposals(self.logger, self.name, self.role, validated_arch_data.tech_proposals, project_context)
                else: self.logger.log(f"Architect: No 'tech_proposals' in validated JSON for attempt {attempt_num + 1}.", self.role, level="INFO")
                base_parsed_output["status"] = "complete"; base_parsed_output["errors"] = []; attempt_successful = True; break
            else:
                self.logger.log(f"Architect: Tech stack validation failed on attempt {attempt_num + 1}. Violations: {tech_stack_validation_errors}", self.role, level="WARNING")
                base_parsed_output["errors"].append(f"Attempt {attempt_num + 1} Tech Stack Violations: {', '.join(tech_stack_validation_errors)}"); project_context.architecture = None
                if attempt_num < max_content_retries:
                    self.logger.log(f"Architect: Attempting LLM correction for tech stack violations (Retry {attempt_num + 1}/{max_content_retries}).", self.role)
                    corrective_prompt_text = (
                        "Your previous architecture design mentioned technologies not allowed by the fixed tech stack.\n"
                        f"Violations: {', '.join(tech_stack_validation_errors)}\n"
                        f"You MUST strictly use ONLY: Frontend: {project_context.tech_stack.frontend}, Backend: {project_context.tech_stack.backend}, Database: {project_context.tech_stack.database}. "
                        "Do not mention or use any other technologies for these components. Provide a revised architecture_design and tech_proposals that strictly adhere to this fixed stack. Ensure the entire response is a single JSON object wrapped in ```json ... ```."
                    )
                    current_response_text_for_attempt = self._call_model(corrective_prompt_text)
                    base_parsed_output["raw_response"] = current_response_text_for_attempt
                    if current_response_text_for_attempt.startswith("Error:"):
                        self.logger.log(f"Architect: LLM call for tech stack correction failed: {current_response_text_for_attempt}", self.role, level="ERROR")
                        base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(f"LLM tech stack correction call failed: {current_response_text_for_attempt}"); attempt_successful = False; break
                else:
                    self.logger.log(f"Architect: Max content retries ({max_content_retries}) reached. Tech stack validation failed.", self.role, level="ERROR")
                    base_parsed_output["status"] = "error"; attempt_successful = False; break
        if not attempt_successful:
            self.logger.log("Architect: All parsing and validation attempts failed.", self.role, level="ERROR")
            base_parsed_output["status"] = "error"
            if not base_parsed_output["errors"]: base_parsed_output["errors"].append("Architect failed to produce a valid and compliant architecture after all attempts.")
            project_context.architecture = None
        return base_parsed_output

class APIDesigner(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('api_designer', 'API Designer', logger, db=db)
    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)
        if base_parsed_output["status"] == "error" and not base_parsed_output["raw_response"]: return base_parsed_output
        current_response_text = base_parsed_output["raw_response"]; max_retries = 1; retry_count = 0; parsed_json_content = None
        while retry_count <= max_retries:
            extracted_json_str = None
            if '```json' in current_response_text:
                json_start_index = current_response_text.find('```json')
                if json_start_index != -1:
                    json_start_actual = json_start_index + 7
                    json_end_index = current_response_text.find('```', json_start_actual)
                    if json_end_index != -1: extracted_json_str = current_response_text[json_start_actual:json_end_index].strip()
                    else: extracted_json_str = current_response_text[json_start_actual:].strip(); base_parsed_output["warnings"].append("Found '```json' but no closing '```'. Attempting to parse partial content.")
                else: extracted_json_str = current_response_text
            else: extracted_json_str = current_response_text
            if not extracted_json_str:
                message = "Could not extract JSON content from the response."
                self.logger.log(f"[{self.name}] {message} Raw response: {current_response_text[:500]}", self.role, level="WARNING")
                base_parsed_output["warnings"].append(message)
                if retry_count >= max_retries: base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(message)
                retry_count += 1; continue
            try:
                parsed_json_content = json.loads(extracted_json_str)
                base_parsed_output['parsed_json_content'] = parsed_json_content
                if retry_count > 0:
                    warning_msg = f"JSON syntax self-correction successful on attempt {retry_count}."
                    base_parsed_output["warnings"].append(warning_msg)
                    self.logger.log(f"[{self.name}] {warning_msg}", self.role, level="WARNING")
                base_parsed_output["status"] = "complete"
                if "errors" in base_parsed_output: base_parsed_output["errors"] = [e for e in base_parsed_output.get("errors", []) if "JSONDecodeError" not in str(e)]
                break
            except json.JSONDecodeError as e:
                self.logger.log(f"[{self.name}] Attempt {retry_count + 1}: JSON parsing failed: {e}. Problematic text snippet (approx 100 chars around error): '{extracted_json_str[max(0, e.pos-50):e.pos+50]}'", self.role, level="WARNING")
                if retry_count < max_retries:
                    retry_count += 1
                    correction_prompt = (
                        f"The following JSON output, intended for an OpenAPI specification for project '{project_context.project_name}', has a syntax error.\n"
                        f"Original Objective: {project_context.objective}\n" f"Error: {e}\n"
                        f"Malformed JSON text:\n```json\n{extracted_json_str}\n```\n"
                        "Please correct ONLY the syntax error in the JSON content and return the full, corrected, valid JSON object. "
                        "Do not add any explanatory text, markdown, or change the data structure beyond fixing the syntax. "
                        "Ensure all strings are double-quoted, all commas are correctly placed (no trailing commas), and all curly braces and square brackets are correctly paired and balanced. "
                        "Output ONLY the corrected JSON object."
                    )
                    self.logger.log(f"[{self.name}] Attempting self-correction for JSON (attempt {retry_count}/{max_retries}).", self.role)
                    current_response_text = self._call_model(correction_prompt)
                    base_parsed_output["raw_response"] = current_response_text
                    if current_response_text.startswith("Error:"):
                        self.logger.log(f"[{self.name}] LLM call for JSON correction failed: {current_response_text}", self.role, level="ERROR")
                        base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(f"JSON correction LLM call failed: {current_response_text}"); break
                else:
                    final_error_msg = f"JSON syntax error persisted after {max_retries} correction attempt(s). Last error: {e}"
                    base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(final_error_msg)
                    self.logger.log(f"[{self.name}] {final_error_msg}", self.role, level="ERROR"); break
        if base_parsed_output.get('parsed_json_content') and base_parsed_output["status"] != "error":
            validation_errors = validate_tech_stack(base_parsed_output["raw_response"], project_context.tech_stack)
            if validation_errors:
                base_parsed_output["status"] = "error"; base_parsed_output["errors"].extend(validation_errors)
                self.logger.log(f"[{self.name}] Tech stack validation failed for APIDesigner: {validation_errors}", self.role, level="ERROR")
                project_context.api_specs = None; return base_parsed_output
            api_json_data = base_parsed_output.get('parsed_json_content')
            if api_json_data:
                try:
                    self.logger.log("[APIDesigner] Attempting Pydantic schema validation for OpenAPI spec...", self.role, level="INFO")
                    validated_spec = APIDesignerOutputModel(**api_json_data)
                    self.logger.log("[APIDesigner] OpenAPI spec schema validation successful.", self.role, level="INFO")
                    project_context.api_specs = validated_spec.model_dump_json(indent=2, by_alias=True)
                    base_parsed_output["api_specs_summary"] = f"API specs updated (JSON, schema validated): {project_context.api_specs[:100]}..."
                    self.logger.log(f"APIDesigner: API specs updated in project context after Pydantic validation (length: {len(project_context.api_specs)}).", self.role)
                except ValidationError as e:
                    self.logger.log(f"APIDesigner: OpenAPI schema validation failed: {e}", self.role, level="ERROR")
                    base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(f"OpenAPI Schema Error: Invalid structure - {str(e)}"); project_context.api_specs = None
                except Exception as e_schema:
                    self.logger.log(f"APIDesigner: Unexpected error during Pydantic schema validation: {e_schema}", self.role, level="ERROR")
                    base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(f"Unexpected Schema Validation Error: {str(e_schema)}"); project_context.api_specs = None
            else:
                self.logger.log("[APIDesigner] No parsed_json_content available for schema validation, though syntax check might have passed.", self.role, level="WARNING")
                if base_parsed_output["status"] != "error": base_parsed_output["warnings"].append("APIDesigner: JSON content was missing or empty before schema validation step.")
                project_context.api_specs = None
        elif base_parsed_output["status"] != "error":
            if not base_parsed_output["raw_response"]: base_parsed_output["warnings"].append("APIDesigner returned an empty response.")
            else: base_parsed_output["warnings"].append(f"APIDesigner did not produce a usable JSON output for API specs. Raw response: {base_parsed_output['raw_response'][:200]}")
            project_context.api_specs = None
        else:
            project_context.api_specs = None
            self.logger.log(f"[{self.name}] Finalizing with error status. API specs not updated due to prior errors (e.g., JSON syntax or tech stack mismatch).", self.role, level="ERROR")
        return base_parsed_output

class CodeWriter(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('code_writer', 'Backend Developer', logger, db=db)
    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)
        if base_parsed_output["status"] == "error":
            if "Tool execution failed" in base_parsed_output["raw_response"] or "Tool not found" in base_parsed_output["raw_response"]:
                base_parsed_output["errors"].append(f"CodeWriter: Tool execution error - {base_parsed_output['raw_response']}")
            return base_parsed_output
        backend_code = base_parsed_output["raw_response"]
        project_context.current_code_snippet = backend_code
        self.logger.log(f"CodeWriter: Backend code updated in project context (length: {len(backend_code)}).", self.role)
        if not backend_code: base_parsed_output["warnings"].append("CodeWriter returned empty code.")
        elif "error" in backend_code.lower()[:100]: base_parsed_output["warnings"].append(f"CodeWriter: Generated code might contain errors: {backend_code[:100]}...")
        base_parsed_output["backend_code_summary"] = f"Generated backend code length: {len(backend_code)}"
        return base_parsed_output

class FrontendBuilder(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('frontend_builder', 'Frontend Developer', logger, db=db)
    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)
        if base_parsed_output["status"] == "error": return base_parsed_output
        ui_design_code = base_parsed_output["raw_response"]
        project_context.current_code_snippet = ui_design_code
        self.logger.log(f"FrontendBuilder: UI design/code updated (length: {len(ui_design_code)}).", self.role)
        if not ui_design_code: base_parsed_output["warnings"].append("FrontendBuilder returned empty UI design/code.")
        base_parsed_output["ui_design_summary"] = f"Generated UI design/code length: {len(ui_design_code)}"
        return base_parsed_output

class MobileDeveloper(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('mobile_developer', 'Mobile Developer', logger, db=db)
    def validate_stack(self, approved_stack: Dict[str, Any], platform_requirements: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.log(f"[{self.name}] Validating stack with mobile specialization: {approved_stack}", self.role)
        is_mobile_project = platform_requirements.get("ios") or platform_requirements.get("android")
        if is_mobile_project:
            mobile_db = approved_stack.get("mobile_database")
            if not mobile_db:
                concern_msg = f"{self.name} ({self.role}): Mobile platform required but no mobile_database specified."
                self.logger.log(concern_msg, self.role, level="WARNING"); return {"approved": False, "concerns": concern_msg}
            unsuitable_standalone_mobile_dbs = ["elasticsearch", "dynamodb"]
            if mobile_db and any(unsuitable_db in mobile_db.lower() for unsuitable_db in unsuitable_standalone_mobile_dbs):
                if "firestore" not in mobile_db.lower() and "sqlite" not in mobile_db.lower() and "roomdb" not in mobile_db.lower() and "realm" not in mobile_db.lower():
                    concern_msg = f"{self.name} ({self.role}): Proposed mobile_database '{mobile_db}' seems unsuitable for standalone mobile use. Consider a mobile-first DB or a clear hybrid pattern."
                    self.logger.log(concern_msg, self.role, level="WARNING")
        is_approved = True; concerns = []
        mobile_db = approved_stack.get("mobile_database")
        is_android_project = platform_requirements.get("android", False)
        if mobile_db:
            mobile_db_lower = mobile_db.lower()
            if "realm" in mobile_db_lower and is_android_project:
                concerns.append("Realm selected for mobile_database on Android. Ensure justification in decision_rationale is robust, detailing specific needs (e.g., complex data, existing Realm codebase) versus Room's typical advantages for Kotlin/Jetpack.")
            cloud_only_keywords = ["dynamodb", "cassandra", "cosmosdb"]; local_sync_keywords = ["sqlite", "room", "realm", "cache", "sync", "offline", "local", "embedded"]
            is_cloud_only_db = any(keyword in mobile_db_lower for keyword in cloud_only_keywords)
            has_local_strategy = any(keyword in mobile_db_lower for keyword in local_sync_keywords)
            if is_cloud_only_db and not has_local_strategy:
                is_approved = False; concerns.append(f"Mobile database '{mobile_db}' appears unsuitable for direct mobile use without an explicitly stated local persistence/synchronization strategy. Please clarify or revise.")
        super_result = super().validate_stack(approved_stack, platform_requirements)
        if not super_result.get("approved", True): is_approved = False
        if super_result.get("concerns"): concerns.append(super_result["concerns"])
        return {"approved": is_approved, "concerns": " | ".join(concerns) if concerns else None}
    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)
        if base_parsed_output["status"] == "error" and not base_parsed_output["raw_response"]: return base_parsed_output
        current_response_text = base_parsed_output["raw_response"]; max_retries = 1; retry_count = 0; parsed_json_content = None
        while retry_count <= max_retries:
            extracted_json_str = None
            if '```json' in current_response_text:
                json_start_index = current_response_text.find('```json')
                if json_start_index != -1:
                    json_start_actual = json_start_index + 7
                    json_end_index = current_response_text.find('```', json_start_actual)
                    if json_end_index != -1: extracted_json_str = current_response_text[json_start_actual:json_end_index].strip()
                    else: extracted_json_str = current_response_text[json_start_actual:].strip(); base_parsed_output["warnings"].append("Found '```json' but no closing '```'. Attempting to parse partial content.")
                else: extracted_json_str = current_response_text
            else: extracted_json_str = current_response_text
            if not extracted_json_str:
                message = "Could not extract JSON content for MobileDeveloper."
                self.logger.log(f"[{self.name}] {message} Raw response: {current_response_text[:500]}", self.role, level="WARNING")
                if retry_count >= max_retries: base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(message)
                retry_count += 1; continue
            try:
                parsed_json_content = json.loads(extracted_json_str)
                base_parsed_output['parsed_json_content'] = parsed_json_content
                if retry_count > 0: base_parsed_output["warnings"].append(f"JSON syntax self-correction successful for MobileDeveloper on attempt {retry_count}.")
                base_parsed_output["status"] = "complete"; base_parsed_output["errors"] = [e for e in base_parsed_output.get("errors", []) if "JSONDecodeError" not in str(e)]; break
            except json.JSONDecodeError as e:
                self.logger.log(f"[{self.name}] Attempt {retry_count + 1}: JSON parsing failed: {e}. Snippet: '{extracted_json_str[max(0, e.pos-50):e.pos+50]}'", self.role, level="WARNING")
                if retry_count < max_retries:
                    retry_count += 1
                    correction_prompt = (f"The following JSON output, intended for mobile application design details for project '{project_context.project_name}', has a syntax error.\n" f"Error: {e}\n" f"Malformed JSON text:\n```json\n{extracted_json_str}\n```\n" "Correct ONLY the syntax error and return the full, corrected, valid JSON object for 'mobile_details' and 'tech_proposals'. " "Do not add explanatory text or change the data structure. Ensure valid JSON.")
                    current_response_text = self._call_model(correction_prompt); base_parsed_output["raw_response"] = current_response_text
                    if current_response_text.startswith("Error:"): base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(f"MobileDeveloper JSON correction LLM call failed: {current_response_text}"); break
                else: base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(f"MobileDeveloper JSON syntax error persisted after {max_retries} attempts. Last error: {e}"); break
        if base_parsed_output["status"] == "error": project_context.current_code_snippet = None; return base_parsed_output
        tech_stack_validation_errors = validate_tech_stack(base_parsed_output["raw_response"], project_context.tech_stack)
        if tech_stack_validation_errors:
            base_parsed_output["status"] = "error"; base_parsed_output["errors"].extend(tech_stack_validation_errors)
            self.logger.log(f"[{self.name}] Tech stack validation failed for MobileDeveloper output: {tech_stack_validation_errors}", self.role, level="ERROR")
            project_context.current_code_snippet = None; return base_parsed_output
        if base_parsed_output.get('parsed_json_content'):
            mobile_json_data = base_parsed_output['parsed_json_content']
            if 'tech_proposals' in mobile_json_data and mobile_json_data['tech_proposals'] is not None:
                for category, proposals_list in mobile_json_data['tech_proposals'].items():
                    if isinstance(proposals_list, list):
                        for proposal_item_dict in proposals_list:
                            if isinstance(proposal_item_dict, dict): proposal_item_dict['proponent'] = self.name
            if 'mobile_details' in mobile_json_data and isinstance(mobile_json_data['mobile_details'], dict):
                details_dict = mobile_json_data['mobile_details']
                fields_to_join = ["component_structure", "navigation", "state_management", "api_integration", "framework_solutions"]
                for field_name in fields_to_join:
                    if field_name in details_dict and isinstance(details_dict[field_name], list):
                        string_elements = [str(item) for item in details_dict[field_name]]
                        details_dict[field_name] = '\n'.join(string_elements)
                        self.logger.log(f"MobileDeveloper: Joined list for field '{field_name}' in mobile_details.", self.role, level="DEBUG")
            try:
                validated_mobile_data = MobileOutputModel(**mobile_json_data)
                self.logger.log(f"MobileDeveloper: Output JSON schema validation successful.", self.role)
                project_context.current_code_snippet = validated_mobile_data.mobile_details.model_dump_json(indent=2)
                self.logger.log(f"MobileDeveloper: Mobile details updated (JSON, Pydantic-validated, length: {len(project_context.current_code_snippet)}).", self.role)
                base_parsed_output["mobile_code_summary"] = f"Mobile details (validated JSON): {validated_mobile_data.mobile_details.component_structure[:100]}..."
                if validated_mobile_data.tech_proposals is not None: _process_tech_proposals(self.logger, self.name, self.role, validated_mobile_data.tech_proposals, project_context)
                else: self.logger.log(f"MobileDeveloper: No 'tech_proposals' in validated JSON.", self.role, level="INFO")
            except ValidationError as e:
                self.logger.log(f"MobileDeveloper: Output JSON schema validation failed: {e}", self.role, level="ERROR")
                base_parsed_output["status"] = "error"; base_parsed_output["errors"].append(f"Mobile Output Schema Error: Invalid structure - {str(e)}"); project_context.current_code_snippet = None
        else:
            self.logger.log("MobileDeveloper: No valid JSON content for schema validation.", self.role, level="ERROR")
            base_parsed_output["status"] = "error"; base_parsed_output["errors"].append("MobileDeveloper failed to produce valid JSON for schema validation."); project_context.current_code_snippet = None
        return base_parsed_output

class Tester(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('tester', 'QA Engineer', logger, db=db)
    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)
        if base_parsed_output["status"] == "error": return base_parsed_output
        test_plan_or_results = base_parsed_output["raw_response"]
        self.logger.log(f"Tester: Test plan/results received (length: {len(test_plan_or_results)}).", self.role)
        if not test_plan_or_results: base_parsed_output["warnings"].append("Tester returned empty test plan/results.")
        base_parsed_output["test_summary"] = f"Test plan/results length: {len(test_plan_or_results)}"
        return base_parsed_output

class Debugger(Agent):
    def __init__(self, logger, db: Database = None):
        super().__init__('debugger', 'Debug Specialist', logger, db=db)
    def _parse_response(self, text: str, project_context: ProjectContext) -> dict:
        base_parsed_output = super()._parse_response(text, project_context)
        if base_parsed_output["status"] == "error": return base_parsed_output
        fixed_code_or_analysis = base_parsed_output["raw_response"]
        project_context.current_code_snippet = fixed_code_or_analysis
        project_context.error_report = ""
        self.logger.log(f"Debugger: Fixed code/analysis received (length: {len(fixed_code_or_analysis)}). Error report cleared.", self.role)
        if not fixed_code_or_analysis: base_parsed_output["warnings"].append("Debugger returned empty fixed code/analysis.")
        base_parsed_output["debug_summary"] = f"Fixed code/analysis length: {len(fixed_code_or_analysis)}"
        return base_parsed_output
