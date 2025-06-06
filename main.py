import os
import sys
import json
import time
import builtins
from pathlib import Path # Added
import re # Added re
import traceback # Added for full stack trace logging
from dotenv import load_dotenv
# Import numpy and time if you were to use them globally!
import numpy as np
builtins.time = time
#Import pydantic
from pydantic import ValidationError
load_dotenv()
from agents.base_agent import (
    ProjectAnalyzer, Planner, Architect, APIDesigner,
    CodeWriter, FrontendBuilder, MobileDeveloper,
    Tester, Debugger)
from utils.general_utils import Logger, DEEPSEEK_TIMEOUT # DEEPSEEK_TIMEOUT might be unused now
from utils.local_llm_client import LocalLLMClient # CORRECTED
from utils.database import Database
from prompts.general_prompts import get_agent_prompt
from utils.tools import ToolKit, TOOL_DESCRIPTIONS
from utils.models import AgentOutput, ApprovedTechStack, TechProposal # Added ApprovedTechStack, TechProposal
from configs.global_config import GeminiConfig, ModelConfig, AGENT_SPECIALIZATIONS # Added AGENT_SPECIALIZATIONS
from utils.context_handler import ProjectContext, TechStack, load_context, save_context, AnalysisOutput, PlatformRequirements # Added TechStack, AnalysisOutput, PlatformRequirements
from typing import List, Dict, Any # For type hinting

# Define Context File Path
CONTEXT_JSON_FILE = Path("project_context.json") # Added

class TaskMaster:
    TOOL_MAPPING = {
        "project_analyzer": ["generate_ctags", "search_ctags", "get_symbol_context", "read_file", "search_in_files", "analyze_code"],
        "planner": ["generate_ctags", "search_ctags", "get_symbol_context", "read_file"],
        "architect": ["generate_ctags", "search_ctags", "get_symbol_context", "analyze_code", "search_in_files"],
        "api_designer": ["generate_ctags", "search_ctags", "get_symbol_context", "analyze_code"],
        "code_writer": ["generate_ctags", "search_ctags", "get_symbol_context", "read_file", "write_file", "patch_file", "analyze_code", "lint_file"],
        "frontend_builder": ["generate_ctags", "search_ctags", "get_symbol_context", "read_file", "write_file", "patch_file", "search_in_files", "list_template_files"],
        "mobile_developer": ["generate_ctags", "search_ctags", "get_symbol_context", "read_file", "write_file", "patch_file"],
        "tester": ["generate_ctags", "search_ctags", "get_symbol_context", "run_command", "lint_file", "lint_project", "read_file", "write_file"],
        "debugger": ["generate_ctags", "search_ctags", "get_symbol_context", "read_file", "write_file", "patch_file", "lint_file", "run_command", "search_in_files", "analyze_code"]
    }

    WORKFLOW_TEMPLATES = {
        "backend": ["planner", "architect", "api_designer", "code_writer", "tester"],
        "web": ["planner", "architect", "api_designer", "code_writer", "frontend_builder", "tester"],
        "mobile": ["planner", "architect", "api_designer", "code_writer", "frontend_builder", "mobile_developer", "tester"],
        "fullstack": ["planner", "architect", "api_designer", "code_writer", "frontend_builder", "mobile_developer", "tester"]
    }

    def __init__(self):
        self.logger = Logger()
        # self.deepseek = LocalLLMClient(default_timeout=DEEPSEEK_TIMEOUT) # OLD Instantiation
        self.deepseek = LocalLLMClient(logger=self.logger) # CORRECTED Instantiation
        self.db = Database()  # Database instance for TaskMaster
        self.tool_kit = ToolKit(logger=self.logger, auto_lint=True, db=self.db) # DB here

        self.agents = {
            "project_analyzer": ProjectAnalyzer(self.logger, db = self.db),
            "planner": Planner(self.logger, db = self.db),
            "architect": Architect(self.logger, db = self.db),
            "api_designer": APIDesigner(self.logger, db = self.db),
            "code_writer": CodeWriter(self.logger, db = self.db),
            "frontend_builder": FrontendBuilder(self.logger, db = self.db),
            "mobile_developer": MobileDeveloper(self.logger, db = self.db),
            "tester": Tester(self.logger, db = self.db),
            "debugger": Debugger(self.logger, db = self.db)
        }

        for agent_name, agent_instance in self.agents.items():
            tools_for_agent = self.TOOL_MAPPING.get(agent_name, [])
            agent_instance.tool_kit = self.tool_kit
            agent_instance.tools = [TOOL_DESCRIPTIONS[t] for t in tools_for_agent if t in TOOL_DESCRIPTIONS]
            agent_instance.db = self.db
            self.logger.log(f"Assigned tools to {agent_name}: {[t['name'] for t in agent_instance.tools]}")

        self.logger.log("TaskMaster initialized with dynamic workflows")

    def run_tech_council_negotiation(self, project_context: ProjectContext) -> ProjectContext:
        self.logger.log("Starting Tech Council Negotiation phase...", "TaskMaster")
        if not project_context.platform_requirements:
            self.logger.log("Platform requirements not found. This should have been populated by ProjectAnalyzer.", "TaskMaster", level="ERROR")
            project_context.decision_rationale["tech_council_negotiation_error"] = "Critical: Platform requirements missing at the start of negotiation."
        if project_context.approved_tech_stack is None:
            project_context.approved_tech_stack = ApprovedTechStack()
            self.logger.log("Initialized empty ApprovedTechStack in project_context.", "TaskMaster")
        if project_context.decision_rationale is None:
            project_context.decision_rationale = {}
            self.logger.log("Initialized empty decision_rationale in project_context.", "TaskMaster")
        self.logger.log(f"Tech Council: Initial tech proposals count: {sum(len(v) for v in project_context.tech_proposals.values()) if project_context.tech_proposals else 0}", "TaskMaster")
        self.logger.log("Tech Council: Starting Conflict Resolution sub-phase...", "TaskMaster")
        if not project_context.tech_proposals:
            self.logger.log("Tech Council: No tech proposals found. Skipping conflict resolution.", "TaskMaster", level="WARNING")
        else:
            for category, proposals_list_models in project_context.tech_proposals.items():
                self.logger.log(f"Tech Council: Processing category '{category}' with {len(proposals_list_models)} proposals.", "TaskMaster")
                if not proposals_list_models:
                    self.logger.log(f"Tech Council: No proposals for category '{category}'. Skipping.", "TaskMaster", level="WARNING")
                    project_context.decision_rationale[category] = "No proposals received for this category."
                    continue
                proposals_list_dicts = [p.model_dump() for p in proposals_list_models]
                chosen_technology_name: Optional[str] = None
                decision_reason: str = "No decision made."
                confidence_notes_for_category = []
                if len(proposals_list_dicts) == 1:
                    chosen_proposal_dict = proposals_list_dicts[0]
                    chosen_technology_name = chosen_proposal_dict.get("technology")
                    decision_reason = "Single proposal automatically selected."
                    self.logger.log(f"Tech Council: Category '{category}': Single proposal '{chosen_technology_name}' chosen.", "TaskMaster")
                    if chosen_proposal_dict.get('confidence', 1.0) < 0.8:
                        confidence_notes_for_category.append(f"Low confidence proposal ({chosen_proposal_dict.get('technology')}, {chosen_proposal_dict.get('confidence', 'N/A')}) included.")
                else:
                    if category == "mobile_database":
                        proposal_names = [p.get("technology", "").lower() for p in proposals_list_dicts]
                        has_room = any("room" in name for name in proposal_names)
                        has_realm = any("realm" in name for name in proposal_names)
                        if has_room and has_realm:
                            self.logger.log(f"Tech Council: Category '{category}': Both Room and Realm proposed. This combination requires careful review. Proceeding with general conflict resolution, but flagging for mandatory review.", "TaskMaster", level="WARNING")
                            decision_reason = "Proposals for both Room (SQL-based) and Realm (NoSQL) were received. Room is often preferred for standard Android/Kotlin projects due to Jetpack integration. Choosing Realm requires strong justification due to potential complexities. Current selection will be based on confidence and justification provided by proposals. MANDATORY REVIEW: Carefully assess if the chosen mobile DB aligns with project complexity and data model."
                    try:
                        resolution = self.tool_kit.resolve_tech_conflict(proposals=proposals_list_dicts)
                        self.logger.log(f"Tech Council: Category '{category}': Conflict resolution tool output: {resolution}", "TaskMaster")
                        if resolution["decision"] == "use_proposal":
                            chosen_proposal_dict = resolution.get("proposal", {})
                            chosen_technology_name = chosen_proposal_dict.get("technology")
                            if not (category == "mobile_database" and has_room and has_realm):
                                decision_reason = resolution.get("reason", "Resolved by confidence.")
                            if chosen_proposal_dict.get('confidence', 1.0) < 0.8:
                                confidence_notes_for_category.append(f"Low confidence proposal ({chosen_proposal_dict.get('technology')}, {chosen_proposal_dict.get('confidence', 'N/A')}) included.")
                        elif resolution["decision"] == "needs_hybrid":
                            hybrid_proposals_input = resolution.get("proposals", [])
                            hybrid_tech_names = {p.get("technology","").lower() for p in hybrid_proposals_input}
                            is_room_realm_hybrid_scenario = False
                            if category == "mobile_database":
                                room_present_in_hybrid_input = any("room" in name for name in hybrid_tech_names)
                                realm_present_in_hybrid_input = any("realm" in name for name in hybrid_tech_names)
                                if room_present_in_hybrid_input and realm_present_in_hybrid_input:
                                    is_room_realm_hybrid_scenario = True
                            if is_room_realm_hybrid_scenario:
                                self.logger.log(f"Tech Council: Category '{category}': Hybrid solution suggested for Room and Realm. This specific hybrid is disallowed. Defaulting to highest confidence single proposal from the Room/Realm pair.", "TaskMaster", level="WARNING")
                                room_realm_proposals = [p for p in proposals_list_dicts if "room" in p.get("technology","").lower() or "realm" in p.get("technology","").lower()]
                                sorted_proposals = sorted(room_realm_proposals, key=lambda p: p.get('confidence', 0.0), reverse=True)
                                if sorted_proposals:
                                    chosen_proposal_dict = sorted_proposals[0]
                                    chosen_technology_name = chosen_proposal_dict.get("technology")
                                    decision_reason = f"Room/Realm hybrid rejected. Defaulted to '{chosen_technology_name}' due to higher confidence. MANDATORY REVIEW still applies."
                                    if chosen_proposal_dict.get('confidence', 1.0) < 0.8:
                                        confidence_notes_for_category.append(f"Low confidence proposal ({chosen_proposal_dict.get('technology')}, {chosen_proposal_dict.get('confidence', 'N/A')}) chosen as fallback from Room/Realm pair.")
                                else:
                                    decision_reason = "Room/Realm hybrid rejected, but failed to find highest confidence fallback. Needs manual intervention."
                                    self.logger.log(f"Tech Council: {decision_reason}", "TaskMaster", level="ERROR")
                            else:
                                hybrid_result = self.tool_kit.create_hybrid_solution(proposals=hybrid_proposals_input, category=category)
                                self.logger.log(f"Tech Council: Category '{category}': Hybrid solution tool output: {hybrid_result}", "TaskMaster")
                                if hybrid_result.get("solution_type") not in ["error", None] and hybrid_result.get("description"):
                                    chosen_technology_name = hybrid_result.get("description")
                                    decision_reason = hybrid_result.get("reason", "Hybrid solution created.")
                                    for p_dict in hybrid_proposals_input:
                                        if p_dict.get('confidence', 1.0) < 0.8:
                                            confidence_notes_for_category.append(f"Low confidence proposal ({p_dict.get('technology')}, {p_dict.get('confidence', 'N/A')}) contributed to hybrid.")
                                else:
                                    decision_reason = f"Hybrid creation failed: {hybrid_result.get('description', 'Unknown')}. Defaulting to highest confidence."
                                    self.logger.log(f"Tech Council: {decision_reason}", "TaskMaster", level="WARNING")
                                    general_sorted_proposals = sorted(proposals_list_dicts, key=lambda p: p.get('confidence', 0.0), reverse=True)
                                    if general_sorted_proposals:
                                        chosen_proposal_dict = general_sorted_proposals[0]
                                        chosen_technology_name = chosen_proposal_dict.get("technology")
                                        if chosen_proposal_dict.get('confidence', 1.0) < 0.8:
                                            confidence_notes_for_category.append(f"Low confidence proposal ({chosen_proposal_dict.get('technology')}, {chosen_proposal_dict.get('confidence', 'N/A')}) chosen as fallback after general hybrid failure.")
                        else:
                             decision_reason = f"Conflict resolution error: {resolution.get('reason', 'Unknown')}. Defaulting to highest confidence."
                             self.logger.log(f"Tech Council: {decision_reason}", "TaskMaster", level="ERROR")
                             general_sorted_proposals_on_error = sorted(proposals_list_dicts, key=lambda p: p.get('confidence', 0.0), reverse=True)
                             if general_sorted_proposals_on_error:
                                 chosen_proposal_dict = general_sorted_proposals_on_error[0]
                                 chosen_technology_name = chosen_proposal_dict.get("technology")
                                 if chosen_proposal_dict.get('confidence', 1.0) < 0.8:
                                     confidence_notes_for_category.append(f"Low confidence proposal ({chosen_proposal_dict.get('technology')}, {chosen_proposal_dict.get('confidence', 'N/A')}) chosen as fallback after resolution error.")
                    except Exception as e:
                        self.logger.log(f"Tech Council: Exception during conflict resolution for '{category}': {e}\n{traceback.format_exc()}", "TaskMaster", level="ERROR")
                        decision_reason = f"Exception in conflict resolution: {e}. Defaulting to highest confidence."
                        sorted_proposals = sorted(proposals_list_dicts, key=lambda p: p.get('confidence', 0.0), reverse=True)
                        if sorted_proposals:
                            chosen_proposal_dict = sorted_proposals[0]
                            chosen_technology_name = chosen_proposal_dict.get("technology")
                            if chosen_proposal_dict.get('confidence', 1.0) < 0.8:
                                confidence_notes_for_category.append(f"Low confidence proposal ({chosen_proposal_dict.get('technology')}, {chosen_proposal_dict.get('confidence', 'N/A')}) chosen as fallback after exception.")
                if chosen_technology_name:
                    field_name = category
                    if hasattr(project_context.approved_tech_stack, field_name):
                        setattr(project_context.approved_tech_stack, field_name, chosen_technology_name)
                        self.logger.log(f"Tech Council: Approved '{chosen_technology_name}' for category '{category}'. Reason: {decision_reason}", "TaskMaster")
                        full_rationale = decision_reason
                        if confidence_notes_for_category:
                             full_rationale += " MANDATORY REVIEW NOTES: " + " | ".join(confidence_notes_for_category)
                        project_context.decision_rationale[category] = full_rationale
                    else:
                        self.logger.log(f"Tech Council: Category '{category}' (resolved to: {chosen_technology_name}) not a direct field in ApprovedTechStack. Storing in rationale.", "TaskMaster", level="WARNING")
                        full_rationale = f"Chosen for {category}: {chosen_technology_name}. Reason: {decision_reason}."
                        if confidence_notes_for_category:
                             full_rationale += " MANDATORY REVIEW NOTES: " + " | ".join(confidence_notes_for_category)
                        project_context.decision_rationale[category] = full_rationale
                else:
                    self.logger.log(f"Tech Council: No technology chosen for category '{category}' after conflict resolution.", "TaskMaster", level="WARNING")
                    project_context.decision_rationale[category] = "No technology could be conclusively chosen for this category."
        self.logger.log("Tech Council: Starting Dependency Check sub-phase...", "TaskMaster")
        if project_context.approved_tech_stack:
            try:
                stack_to_check = project_context.approved_tech_stack.model_dump(exclude_none=True)
                if stack_to_check:
                    dep_check_result = self.tool_kit.check_technology_dependencies(tech_stack=stack_to_check)
                    self.logger.log(f"Tech Council: Dependency check result: {dep_check_result}", "TaskMaster")
                    project_context.decision_rationale["dependency_checks"] = {
                        "conflicts": dep_check_result.get("conflicts", []),
                        "warnings": dep_check_result.get("warnings", [])
                    }
                    if dep_check_result.get("conflicts"):
                        self.logger.log(f"Tech Council: CRITICAL DEPENDENCY CONFLICTS FOUND: {dep_check_result.get('conflicts')}", "TaskMaster", level="ERROR")
                else:
                    self.logger.log("Tech Council: Approved tech stack is empty, skipping dependency check.", "TaskMaster", level="INFO")
                    project_context.decision_rationale["dependency_checks"] = {"conflicts": [], "warnings": ["Approved tech stack was empty, so no dependencies to check."]}
            except Exception as e:
                self.logger.log(f"Tech Council: Error during dependency check: {e}", "TaskMaster", level="ERROR")
                project_context.decision_rationale["dependency_checks_error"] = str(e)
        else:
            self.logger.log("Tech Council: Approved tech stack not available for dependency check.", "TaskMaster", level="WARNING")
        self.logger.log("Tech Council: Starting Consensus Locking sub-phase...", "TaskMaster")
        if not project_context.approved_tech_stack or not project_context.platform_requirements:
            self.logger.log("Tech Council: Cannot perform consensus locking: approved_tech_stack or platform_requirements missing.", "TaskMaster", level="ERROR")
            project_context.decision_rationale["consensus"] = "Skipped: Missing approved_tech_stack or platform_requirements."
        else:
            key_agent_roles_to_consult = ["architect"]
            if project_context.platform_requirements.ios or project_context.platform_requirements.android:
                key_agent_roles_to_consult.append("mobile developer")
            agents_to_consult_instances = []
            for role_keyword in key_agent_roles_to_consult:
                for agent_instance in self.agents.values():
                    if role_keyword in agent_instance.role.lower():
                        if agent_instance not in agents_to_consult_instances:
                             agents_to_consult_instances.append(agent_instance)
            if not agents_to_consult_instances:
                 self.logger.log("Tech Council: No specific validating agents found for consensus. Defaulting to approval (or review by human).", "TaskMaster", level="WARNING")
                 project_context.decision_rationale["consensus"] = "Conditionally Achieved (No specific AI validators for this configuration)."
            else:
                all_agents_approve = True
                all_concerns = []
                current_approved_stack_dict = project_context.approved_tech_stack.model_dump(exclude_none=True)
                current_platform_reqs_dict = project_context.platform_requirements.model_dump()
                for agent in agents_to_consult_instances:
                    try:
                        validation_result = agent.validate_stack(
                            approved_stack=current_approved_stack_dict,
                            platform_requirements=current_platform_reqs_dict
                        )
                        self.logger.log(f"Tech Council: Validation from {agent.name} ({agent.role}): {validation_result}", "TaskMaster")
                        if not validation_result.get("approved"):
                            all_agents_approve = False
                            if validation_result.get("concerns"):
                                all_concerns.append(f"{agent.name} ({agent.role}): {validation_result['concerns']}")
                    except Exception as e:
                        self.logger.log(f"Tech Council: Error during validation by agent {agent.name} ({agent.role}): {e}", "TaskMaster", level="ERROR")
                        all_agents_approve = False
                        all_concerns.append(f"{agent.name} ({agent.role}): Validation process failed with exception - {e}")
                if all_agents_approve:
                    self.logger.log("Tech Council: Consensus achieved. Tech stack locked.", "TaskMaster")
                    project_context.decision_rationale["consensus"] = "Achieved"
                else:
                    self.logger.log(f"Tech Council: Consensus failed. Concerns: {all_concerns}", "TaskMaster", level="ERROR")
                    project_context.decision_rationale["consensus"] = "Failed"
                    project_context.decision_rationale["consensus_concerns"] = all_concerns
        self.logger.log("Tech Council Negotiation phase finished.", "TaskMaster")
        return project_context

    def start_workflow(self, user_input):
        project_context = load_context(CONTEXT_JSON_FILE)
        if not project_context.objective and user_input:
            project_context.objective = user_input
            self.logger.log(f"Objective set from user input: {user_input}", "TaskMaster")

        if not project_context.platform_requirements:
            self.logger.log("Platform requirements not found, attempting to run ProjectAnalyzer for detection.", "TaskMaster", level="WARNING")
            if "project_analyzer" in self.agents:
                pass
            if not project_context.platform_requirements:
                 self.logger.log("CRITICAL: Platform requirements are still missing after attempting to ensure ProjectAnalyzer ran. Negotiation cannot proceed accurately.", "TaskMaster", level="ERROR")
                 if project_context.decision_rationale is None: project_context.decision_rationale = {}
                 project_context.decision_rationale["tech_council_negotiation_error"] = "Platform requirements missing."

        if project_context.approved_tech_stack is None:
            project_context.approved_tech_stack = ApprovedTechStack()
        if project_context.decision_rationale is None:
            project_context.decision_rationale = {}

        self.logger.log(f"Initial tech proposals: {project_context.tech_proposals}", "TaskMaster")
        self.logger.log("Starting Conflict Resolution sub-phase...", "TaskMaster")
        if not project_context.tech_proposals:
            self.logger.log("No tech proposals found in project_context. Skipping conflict resolution.", "TaskMaster", level="WARNING")
        else:
            for category, proposals_list_models in project_context.tech_proposals.items():
                self.logger.log(f"Processing category: {category} with {len(proposals_list_models)} proposals.", "TaskMaster")
                if not proposals_list_models:
                    self.logger.log(f"No proposals for category {category}. Skipping.", "TaskMaster", level="WARNING")
                    project_context.decision_rationale[category] = "No proposals received for this category."
                    continue
                proposals_list_dicts = [p.model_dump() for p in proposals_list_models]
                chosen_technology_name: Optional[str] = None
                decision_reason: str = ""
                confidence_notes_for_category = []
                if len(proposals_list_dicts) == 1:
                    chosen_proposal_dict = proposals_list_dicts[0]
                    chosen_technology_name = chosen_proposal_dict.get("technology")
                    decision_reason = "Single proposal automatically selected."
                    self.logger.log(f"Category '{category}': Single proposal '{chosen_technology_name}' chosen.", "TaskMaster")
                    if chosen_proposal_dict.get('confidence', 1.0) < 0.8:
                        confidence_notes_for_category.append(f"Low confidence proposal ({chosen_proposal_dict.get('technology')}, {chosen_proposal_dict.get('confidence')}) included.")
                else:
                    try:
                        resolution = self.tool_kit.resolve_tech_conflict(proposals=proposals_list_dicts)
                        self.logger.log(f"Category '{category}': Conflict resolution result: {resolution}", "TaskMaster")
                        if resolution["decision"] == "use_proposal":
                            chosen_proposal_dict = resolution.get("proposal", {})
                            chosen_technology_name = chosen_proposal_dict.get("technology")
                            decision_reason = resolution.get("reason", "Resolved by confidence.")
                            if chosen_proposal_dict.get('confidence', 1.0) < 0.8:
                                confidence_notes_for_category.append(f"Low confidence proposal ({chosen_proposal_dict.get('technology')}, {chosen_proposal_dict.get('confidence')}) included.")
                        elif resolution["decision"] == "needs_hybrid":
                            hybrid_proposals_input = resolution.get("proposals", [])
                            if hybrid_proposals_input and not isinstance(hybrid_proposals_input[0], dict):
                                hybrid_proposals_dicts = [p.model_dump() for p in hybrid_proposals_input]
                            else:
                                hybrid_proposals_dicts = hybrid_proposals_input
                            hybrid_result = self.tool_kit.create_hybrid_solution(proposals=hybrid_proposals_dicts, category=category)
                            self.logger.log(f"Category '{category}': Hybrid solution result: {hybrid_result}", "TaskMaster")
                            if hybrid_result.get("solution_type") not in ["error", None]:
                                chosen_technology_name = hybrid_result.get("description")
                                decision_reason = hybrid_result.get("reason", "Hybrid solution created.")
                                for p_dict in hybrid_proposals_dicts:
                                    if p_dict.get('confidence', 1.0) < 0.8:
                                         confidence_notes_for_category.append(f"Low confidence proposal ({p_dict.get('technology')}, {p_dict.get('confidence')}) contributed to hybrid.")
                            else:
                                decision_reason = f"Hybrid creation failed or not applicable: {hybrid_result.get('description', 'Unknown error')}. Defaulting to highest confidence."
                                self.logger.log(decision_reason, "TaskMaster", level="WARNING")
                                sorted_proposals = sorted(proposals_list_dicts, key=lambda p: p.get('confidence', 0.0), reverse=True)
                                if sorted_proposals:
                                    chosen_proposal_dict = sorted_proposals[0]
                                    chosen_technology_name = chosen_proposal_dict.get("technology")
                                    if chosen_proposal_dict.get('confidence', 1.0) < 0.8:
                                        confidence_notes_for_category.append(f"Low confidence proposal ({chosen_proposal_dict.get('technology')}, {chosen_proposal_dict.get('confidence')}) chosen as fallback.")
                        elif resolution["decision"] == "error":
                             decision_reason = f"Conflict resolution error: {resolution.get('reason', 'Unknown error')}. Defaulting to highest confidence."
                             self.logger.log(decision_reason, "TaskMaster", level="ERROR")
                             sorted_proposals = sorted(proposals_list_dicts, key=lambda p: p.get('confidence', 0.0), reverse=True)
                             if sorted_proposals:
                                 chosen_proposal_dict = sorted_proposals[0]
                                 chosen_technology_name = chosen_proposal_dict.get("technology")
                                 if chosen_proposal_dict.get('confidence', 1.0) < 0.8:
                                     confidence_notes_for_category.append(f"Low confidence proposal ({chosen_proposal_dict.get('technology')}, {chosen_proposal_dict.get('confidence')}) chosen as fallback.")
                    except Exception as e:
                        self.logger.log(f"Error during conflict resolution for {category}: {e}", "TaskMaster", level="ERROR")
                        decision_reason = f"Exception during conflict resolution: {e}. Defaulting to highest confidence."
                        sorted_proposals = sorted(proposals_list_dicts, key=lambda p: p.get('confidence', 0.0), reverse=True)
                        if sorted_proposals:
                            chosen_proposal_dict = sorted_proposals[0]
                            chosen_technology_name = chosen_proposal_dict.get("technology")
                            if chosen_proposal_dict.get('confidence', 1.0) < 0.8:
                                confidence_notes_for_category.append(f"Low confidence proposal ({chosen_proposal_dict.get('technology')}, {chosen_proposal_dict.get('confidence')}) chosen as fallback after exception.")
                if chosen_technology_name:
                    field_name = category
                    if hasattr(project_context.approved_tech_stack, field_name):
                        setattr(project_context.approved_tech_stack, field_name, chosen_technology_name)
                        self.logger.log(f"Approved '{chosen_technology_name}' for category '{category}'. Reason: {decision_reason}", "TaskMaster")
                        project_context.decision_rationale[category] = decision_reason
                        if confidence_notes_for_category:
                             project_context.decision_rationale[category] += " MANDATORY REVIEW NOTES: " + " | ".join(confidence_notes_for_category)
                    else:
                        self.logger.log(f"Category '{category}' (resolved to tech: {chosen_technology_name}) does not directly map to a field in ApprovedTechStack. Storing in rationale.", "TaskMaster", level="WARNING")
                        project_context.decision_rationale[category] = f"Chosen: {chosen_technology_name}. Reason: {decision_reason}."
                        if confidence_notes_for_category:
                             project_context.decision_rationale[category] += " MANDATORY REVIEW NOTES: " + " | ".join(confidence_notes_for_category)
        self.logger.log("Starting Dependency Check sub-phase...", "TaskMaster")
        if project_context.approved_tech_stack:
            try:
                dep_check_result = self.tool_kit.check_technology_dependencies(
                    tech_stack=project_context.approved_tech_stack.model_dump(exclude_none=True)
                )
                self.logger.log(f"Dependency check result: {dep_check_result}", "TaskMaster")
                project_context.decision_rationale["dependency_checks"] = {
                    "conflicts": dep_check_result.get("conflicts", []),
                    "warnings": dep_check_result.get("warnings", [])
                }
                if dep_check_result.get("conflicts"):
                    self.logger.log(f"CRITICAL DEPENDENCY CONFLICTS FOUND: {dep_check_result.get('conflicts')}", "TaskMaster", level="ERROR")
            except Exception as e:
                self.logger.log(f"Error during dependency check: {e}", "TaskMaster", level="ERROR")
                project_context.decision_rationale["dependency_checks_error"] = str(e)
        else:
            self.logger.log("Approved tech stack not available for dependency check.", "TaskMaster", level="WARNING")
        self.logger.log("Starting Consensus Locking sub-phase...", "TaskMaster")
        if not project_context.approved_tech_stack or not project_context.platform_requirements:
            self.logger.log("Cannot perform consensus locking: approved_tech_stack or platform_requirements missing.", "TaskMaster", level="ERROR")
            project_context.decision_rationale["consensus"] = "Skipped due to missing data."
        else:
            key_agent_roles_to_consult = ["architect"]
            if project_context.platform_requirements.ios or project_context.platform_requirements.android:
                key_agent_roles_to_consult.append("mobile developer")
            agents_to_consult_instances = []
            for role_keyword in key_agent_roles_to_consult:
                for agent_instance in self.agents.values():
                    if role_keyword in agent_instance.role.lower():
                        if agent_instance not in agents_to_consult_instances:
                             agents_to_consult_instances.append(agent_instance)
            if not agents_to_consult_instances:
                 self.logger.log("No specific validating agents found for consensus. Defaulting to approval.", "TaskMaster", level="WARNING")
                 project_context.decision_rationale["consensus"] = "Achieved (no specific validators configured for this setup)."
            else:
                all_agents_approve = True
                all_concerns = []
                for agent in agents_to_consult_instances:
                    try:
                        validation_result = agent.validate_stack(
                            approved_stack=project_context.approved_tech_stack.model_dump(exclude_none=True),
                            platform_requirements=project_context.platform_requirements.model_dump()
                        )
                        self.logger.log(f"Validation from {agent.name} ({agent.role}): {validation_result}", "TaskMaster")
                        if not validation_result.get("approved"):
                            all_agents_approve = False
                            if validation_result.get("concerns"):
                                all_concerns.append(f"{agent.name}: {validation_result['concerns']}")
                    except Exception as e:
                        self.logger.log(f"Error during validation by agent {agent.name}: {e}", "TaskMaster", level="ERROR")
                        all_agents_approve = False
                        all_concerns.append(f"{agent.name}: Validation process failed with exception - {e}")
                if all_agents_approve:
                    self.logger.log("Consensus achieved. Tech stack locked.", "TaskMaster")
                    project_context.decision_rationale["consensus"] = "Achieved"
                else:
                    self.logger.log(f"Consensus failed. Concerns: {all_concerns}", "TaskMaster", level="ERROR")
                    project_context.decision_rationale["consensus"] = "Failed"
                    project_context.decision_rationale["consensus_concerns"] = all_concerns
        self.logger.log("Tech Council Negotiation phase finished.", "TaskMaster")
        workflow: Optional[List[str]] = None
        sanitized_objective_for_name = re.sub(r'[^\w\s-]', '', user_input[:30]).strip()
        project_name = re.sub(r'[-\s]+', '_', sanitized_objective_for_name).lower()
        if not project_name:
            project_name = "unnamed_ai_project"
        project_output_base_dir = Path("projects")
        project_specific_dir = project_output_base_dir / project_name
        project_specific_dir.mkdir(parents=True, exist_ok=True)
        self.logger.log(f"Project name: '{project_name}', Output directory: '{project_specific_dir}'", "TaskMaster")
        user_input_lower = user_input.lower()
        tentative_db_choice = "TBD"
        tentative_project_type = "unknown"
        initial_frontend = None
        initial_backend = None
        initial_database = None
        if "database" in user_input_lower or "db" in user_input_lower:
            tentative_db_choice = "SQLite"
            initial_database = "SQLite"
            if tentative_project_type == "unknown":
                tentative_project_type = "backend"
        if "api" in user_input_lower:
            tentative_project_type = "backend"
            if initial_backend is None:
                initial_backend = "Python/FastAPI"
        if any(keyword in user_input_lower for keyword in ["website", "frontend", "ui", "user interface"]):
            if initial_frontend is None:
                initial_frontend = "React"
            if tentative_project_type == "unknown":
                tentative_project_type = "frontend"
            elif tentative_project_type == "backend":
                tentative_project_type = "fullstack"
        if any(keyword in user_input_lower for keyword in ["mobile app", "ios", "android"]):
            initial_frontend = "React Native"
            if "api" in user_input_lower or initial_backend is not None:
                 tentative_project_type = "fullstack"
            else:
                 tentative_project_type = "mobile"
        initial_tech_stack = TechStack(
            frontend=initial_frontend,
            backend=initial_backend,
            database=initial_database
        )
        project_context = ProjectContext(
            project_name=project_name,
            objective=user_input,
            project_type=tentative_project_type,
            tech_stack=initial_tech_stack,
            db_choice=tentative_db_choice,
            deployment_target="TBD",
            security_level="standard",
            current_dir=str(project_specific_dir.resolve()),
            analysis=None,
            plan=None,
            architecture=None,
            api_specs=None,
            project_summary="",
            current_code_snippet="",
            error_report="",
            tech_proposals={},
            approved_tech_stack=ApprovedTechStack(),
            decision_rationale={},
            platform_requirements=PlatformRequirements()
        )
        self.logger.log(f"Initial project context: {project_context.model_dump_json(indent=2)}", "TaskMaster")
        save_context(project_context, CONTEXT_JSON_FILE)
        self.logger.log(f"Fresh project context initialized and saved for '{project_name}'.", "TaskMaster")
        current_workflow_data = {
            "user_input": user_input,
            "start_time": time.time()
        }
        current_workflow_data, project_context = self.delegate("project_analyzer", current_workflow_data, project_context)
        save_context(project_context, CONTEXT_JSON_FILE)
        if current_workflow_data.get("error"):
             self.logger.log(f"Workflow halted after ProjectAnalyzer due to error: {current_workflow_data.get('error')}", "TaskMaster", level="ERROR")
        elif not project_context.analysis or not project_context.platform_requirements:
            self.logger.log("ProjectAnalyzer did not populate analysis or platform_requirements. Tech Council negotiation cannot proceed effectively.", "TaskMaster", level="ERROR")
            current_workflow_data["error"] = "ProjectAnalyzer output missing for Tech Council."
        else:
            self.logger.log("Running core proposing agents before Tech Council negotiation...", "TaskMaster")
            agents_to_run_before_council = ["architect"]
            for agent_name_pre_council in agents_to_run_before_council:
                if current_workflow_data.get("error"):
                    break
                if agent_name_pre_council in self.agents:
                    proposals_before_arch = {c: [p.model_dump() for p in pl] for c, pl in project_context.tech_proposals.items()} if project_context.tech_proposals else {}
                    self.logger.log(f"Before Architect (pre-council) run. Tech proposals so far: {json.dumps(proposals_before_arch, indent=2)}", "TaskMaster")
                    self.logger.log(f"Delegating to pre-council agent: {agent_name_pre_council}", "TaskMaster")
                    current_workflow_data, project_context = self.delegate(agent_name_pre_council, current_workflow_data, project_context)
                    save_context(project_context, CONTEXT_JSON_FILE)
                    proposals_after_arch = {c: [p.model_dump() for p in pl] for c, pl in project_context.tech_proposals.items()} if project_context.tech_proposals else {}
                    self.logger.log(f"After Architect (pre-council) run. Tech proposals now: {json.dumps(proposals_after_arch, indent=2)}", "TaskMaster")
                    if current_workflow_data.get("error"):
                        self.logger.log(f"Error after pre-council agent {agent_name_pre_council}: {current_workflow_data.get('error')}", "TaskMaster", level="ERROR")
                else:
                    self.logger.log(f"Agent {agent_name_pre_council} not found in self.agents. Skipping.", "TaskMaster", level="WARNING")
            if not current_workflow_data.get("error") and project_context.platform_requirements and \
               (project_context.platform_requirements.ios or project_context.platform_requirements.android):
                if "mobile_developer" in self.agents:
                    proposals_before_mob = {c: [p.model_dump() for p in pl] for c, pl in project_context.tech_proposals.items()} if project_context.tech_proposals else {}
                    self.logger.log(f"Before MobileDeveloper (pre-council) run. Tech proposals so far: {json.dumps(proposals_before_mob, indent=2)}", "TaskMaster")
                    self.logger.log("Mobile platform detected, delegating to MobileDeveloper pre-council.", "TaskMaster")
                    current_workflow_data, project_context = self.delegate("mobile_developer", current_workflow_data, project_context)
                    save_context(project_context, CONTEXT_JSON_FILE)
                    proposals_after_mob = {c: [p.model_dump() for p in pl] for c, pl in project_context.tech_proposals.items()} if project_context.tech_proposals else {}
                    self.logger.log(f"After MobileDeveloper (pre-council) run. Tech proposals now: {json.dumps(proposals_after_mob, indent=2)}", "TaskMaster")
                    if current_workflow_data.get("error"):
                         self.logger.log(f"Error after mobile_developer (pre-council): {current_workflow_data.get('error')}", "TaskMaster", level="ERROR")
                else:
                    self.logger.log("MobileDeveloper agent not found, though mobile platform is indicated.", "TaskMaster", level="WARNING")
            if not current_workflow_data.get("error"):
                final_proposals_for_council = {c: [p.model_dump() for p in pl] for c, pl in project_context.tech_proposals.items()} if project_context.tech_proposals else {}
                self.logger.log(f"Entering Tech Council Negotiation. Final tech proposals collected: {json.dumps(final_proposals_for_council, indent=2)}", "TaskMaster")
                project_context = self.run_tech_council_negotiation(project_context)
                save_context(project_context, CONTEXT_JSON_FILE)
                self.logger.log("Tech Council negotiation complete. Updated context saved.", "TaskMaster")
                if project_context.decision_rationale.get("consensus") == "Failed" or \
                   project_context.decision_rationale.get("dependency_checks", {}).get("conflicts"):
                    error_message = "Tech Council negotiation resulted in unresolved issues. Halting workflow."
                    if project_context.decision_rationale.get("consensus_concerns"):
                        error_message += f" Concerns: {project_context.decision_rationale['consensus_concerns']}"
                    if project_context.decision_rationale.get("dependency_checks", {}).get("conflicts"):
                        error_message += f" Conflicts: {project_context.decision_rationale['dependency_checks']['conflicts']}"
                    self.logger.log(error_message, "TaskMaster", level="ERROR")
                    current_workflow_data["error"] = error_message
                else:
                    self.logger.log("Tech Council decisions accepted. Proceeding with main agent workflow.", "TaskMaster")
                    project_type = project_context.analysis.project_type_confirmed if project_context.analysis and project_context.analysis.project_type_confirmed else project_context.project_type
                    base_workflow_steps = self.WORKFLOW_TEMPLATES.get(project_type, self.WORKFLOW_TEMPLATES["fullstack"])
                    agents_already_run = ["project_analyzer", "architect"]
                    if project_context.platform_requirements and (project_context.platform_requirements.ios or project_context.platform_requirements.android):
                        agents_already_run.append("mobile_developer")
                    remaining_workflow_steps = [step for step in base_workflow_steps if step not in agents_already_run]
                    workflow = remaining_workflow_steps
                    self.logger.log(f"Selected workflow (remaining steps): {workflow}", "TaskMaster")
                    if workflow:
                        for agent_name in workflow:
                            if current_workflow_data.get("error"):
                                self.logger.log(f"Halting main workflow before agent {agent_name} due to prior error.", "TaskMaster", level="WARNING")
                                break
                            current_workflow_data, project_context = self.delegate(agent_name, current_workflow_data, project_context)
                            save_context(project_context, CONTEXT_JSON_FILE)
                            if current_workflow_data.get("error"):
                                self.logger.log(f"Error at agent {agent_name}: {current_workflow_data['error']}", "TaskMaster", level="ERROR")
                                break
                    else:
                        self.logger.log("No remaining workflow steps after pre-council agents and filtering.", "TaskMaster", level="INFO")
            else:
                 self.logger.log("Skipping Tech Council and main workflow due to errors during pre-council agent runs.", "TaskMaster", level="WARNING")
            last_agent_status = current_workflow_data.get("status")
            if last_agent_status != "complete" and current_workflow_data.get("current_agent_name") == "code_writer":
                self.logger.log(f"CodeWriter agent status: {last_agent_status}. Launching debugger...", "TaskMaster")
                project_context.error_report = f"Issues detected after {current_workflow_data.get('current_agent_name', 'unknown agent')}. Errors: {current_workflow_data.get('errors')}"
                save_context(project_context, CONTEXT_JSON_FILE)
                current_workflow_data, project_context = self.delegate("debugger", current_workflow_data, project_context)
                save_context(project_context, CONTEXT_JSON_FILE)

        current_workflow_data["end_time"] = time.time()
        final_output_file = self._save_outputs(current_workflow_data, project_context)

        if final_output_file and Path(final_output_file).exists():
            self.logger.log(f"Final output snapshot (ProjectContext) saved to {final_output_file}", "TaskMaster")
            current_workflow_data["output_file_content_is_project_context_snapshot"] = True
        else:
            self.logger.log("Final output file (ProjectContext snapshot) not found or not created.", "TaskMaster", level="WARNING")
            current_workflow_data["output_file_error"] = "Output file (ProjectContext snapshot) not found or not created."
        self.store_project_details(current_workflow_data, project_context)
        current_workflow_data["output_file"] = final_output_file
        current_workflow_data['project_name'] = project_context.project_name
        current_workflow_data['objective'] = project_context.objective
        if project_context.analysis:
            current_workflow_data['analysis'] = project_context.analysis.model_dump()
        if project_context.plan:
            current_workflow_data['plan'] = project_context.plan
        if project_context.architecture:
            current_workflow_data['architecture'] = project_context.architecture
        if project_context.api_specs:
            current_workflow_data['api_specs'] = project_context.api_specs
        return current_workflow_data

    def delegate(self, agent_name: str, current_workflow_data: dict, project_context: ProjectContext) -> tuple[dict, ProjectContext]:
        if project_context.analysis:
            if agent_name == "mobile_developer" and not project_context.analysis.mobile_needed:
                self.logger.log(f"Skipping mobile_developer (not needed based on project context)", "TaskMaster")
                current_workflow_data[f"{agent_name}_skipped"] = "Not needed as per project analysis"
                return current_workflow_data, project_context
            if agent_name == "frontend_builder" and not project_context.analysis.frontend_needed:
                self.logger.log(f"Skipping frontend_builder (not needed based on project context)", "TaskMaster")
                current_workflow_data[f"{agent_name}_skipped"] = "Not needed as per project analysis"
                return current_workflow_data, project_context
        elif agent_name in ["mobile_developer", "frontend_builder"]:
             self.logger.log(f"Skipping {agent_name} as project analysis is not available or indicates not needed.", "TaskMaster")
             current_workflow_data[f"{agent_name}_skipped"] = "Project analysis not available or indicates not needed"
             return current_workflow_data, project_context

        agent = self.agents[agent_name]
        current_workflow_data['current_agent_name'] = agent_name
        current_workflow_data['current_agent_role'] = agent.role

        self.logger.log(f"Delegating to {agent.role} ({agent_name})", "TaskMaster")
        try:
            agent_result = agent.perform_task(project_context)
            if agent_result.get("warnings"):
                for warning_msg in agent_result["warnings"]:
                    self.logger.log(f"Warning from {agent_name}: {warning_msg}", "TaskMaster", level="WARNING")
            if agent_result.get("status") != "complete":
                error_msg = f"Agent {agent_name} did not complete successfully. Status: {agent_result.get('status')}."
                if agent_result.get("errors"):
                    error_msg += " Errors: " + "; ".join(agent_result["errors"])
                self.logger.log(error_msg, "TaskMaster", level="ERROR")
                current_workflow_data["error"] = error_msg
            current_workflow_data.update(agent_result)
            return current_workflow_data, project_context
        except Exception as e:
            self.logger.log(f"Full traceback for error during delegation to {agent_name}:\n{traceback.format_exc()}", "TaskMaster", level="ERROR")
            error_msg = f"Critical error during delegation to {agent_name}: {str(e)}"
            self.logger.log(error_msg, "TaskMaster", level="CRITICAL")
            current_workflow_data["error"] = error_msg
            if "status" not in current_workflow_data or current_workflow_data["status"] == "complete":
                 current_workflow_data["status"] = "critical_error"
            if "errors" not in current_workflow_data:
                current_workflow_data["errors"] = []
            current_workflow_data["errors"].append(error_msg)
            return current_workflow_data, project_context

    def _save_outputs(self, current_workflow_data: dict, project_context: ProjectContext):
        """Save agent output to a shared JSON file, sourcing from ProjectContext."""
        import os
    
        agent_name_for_output = current_workflow_data.get('current_agent_name', "TaskMaster")
        agent_role_for_output = current_workflow_data.get('current_agent_role', "System")
        model_used_for_output = current_workflow_data.get('current_model_used', 'N/A')
        output_details = {
            'agent_name': agent_name_for_output,
            'role': agent_role_for_output,
            'response_text': f'Workflow step by {agent_name_for_output} completed. See details in ProjectContext.',
            'timestamp': time.time(),
            'model_used': model_used_for_output,
            'duration': current_workflow_data.get("end_time", time.time()) - current_workflow_data.get("start_time", time.time())
        }
        output_content = project_context.model_dump()
        final_output_structure = {
            "workflow_metadata": {
                "start_time": current_workflow_data.get("start_time"),
                "end_time": current_workflow_data.get("end_time"),
                "duration": current_workflow_data.get("end_time", time.time()) - current_workflow_data.get("start_time", 0),
                "last_agent_processed": agent_name_for_output,
                "user_input": current_workflow_data.get("user_input"),
            },
            "project_context": project_context.model_dump()
        }
        current_workflow_data["agent_name_for_final_output"] = agent_name_for_output
        project_type_str = project_context.project_type
        if project_context.analysis and project_context.analysis.project_type_confirmed:
            project_type_str = project_context.analysis.project_type_confirmed
    
        os.makedirs("outputs", exist_ok=True)
        filename = f"outputs/{project_context.project_name.replace(' ', '_').replace(':', '_')}_{project_type_str}_context_snapshot.json"
    
        try:
            with open(filename, "w") as f:
                json.dump(final_output_structure, f, indent=2)
            self.logger.log(f"Project context snapshot saved to {filename}", "TaskMaster")
            return filename
        except Exception as e:
            self.logger.log(f"ERROR saving project context snapshot: {e}", "TaskMaster", level="ERROR")
            return None

    def store_project_details(self, current_workflow_data: dict, project_context: ProjectContext):
        try:
            project_name = project_context.project_name
            objective = project_context.objective
            project_type = project_context.analysis.project_type_confirmed if project_context.analysis else project_context.project_type
            start_time = current_workflow_data.get("start_time", time.time())
            end_time = current_workflow_data.get("end_time", time.time())
            status = "completed" if not current_workflow_data.get("error") else "error"
            user_input = current_workflow_data.get("user_input", project_context.objective)
            model_used = current_workflow_data.get('current_model_used', 'N/A')
            sql = """
            INSERT OR REPLACE INTO projects (project_name, objective, project_type, start_time, end_time, status, user_input, model_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (project_name, objective, project_type, start_time, end_time, status, user_input, model_used)
            self.db.execute(sql, params)
            self.logger.log(f"Project details stored in the database: {project_name}", "TaskMaster")
            return True
        except Exception as e:
            self.logger.log(f"Error storing project details: {e}", "TaskMaster", level="ERROR")
            return False

    def cleanup(self):
        """Disconnect from the database on shutdown"""
        self.db.close()
        self.logger.log("Disconnected from the database.", "TaskMaster")


if __name__ == "__main__":
    taskmaster = TaskMaster()
    try:
        requirements = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Build a task management API with user authentication"

        print(f"\n🚀 Starting project: {requirements}")
        context = taskmaster.start_workflow(requirements)

        duration = context.get("end_time", time.time()) - context.get("start_time", time.time())
        print(f"\n✅ Workflow completed in {duration:.1f} seconds")

        if "error" in context:
            print(f"❌ Error: {context['error']}")
        elif "validation_error" in context:
            print(f"❌ Validation Error: {context['validation_error']}")
        else:
            print(f"📦 Project type: {context.get('analysis', {}).get('project_type', 'unknown').upper()}")
            print(f"📝 Outputs saved to: {context.get('output_file', 'N/A')}")

        for key in ["backend_code", "ui_design", "mobile_design"]:
            if key in context and context[key] != "N/A":
                print(f"🔹 {key.replace('_', ' ').capitalize()}: {len(context[key])} chars")

        print("\n🔥 Project artifacts:")
        for k in ["plan", "architecture", "api_specs", "test_plan"]:
            if k in context and context[k] != "N/A":
                print(f"  - {k.capitalize()}: {len(context[k])} chars")
    finally:
        taskmaster.cleanup()  # Cleanly disconnect database
