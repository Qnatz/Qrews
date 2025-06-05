import os
import subprocess
import ast
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from .general_utils import Logger # CORRECTED
from .database import Database # CORRECTED
import socket


class ToolKit:
    """Enhanced tool collection with code patching, linting, and file operations"""
    def __init__(self, project_root=".", logger=None, auto_lint=True, db: Database = None):
        self.project_root = Path(project_root).resolve()
        self.logger = logger or Logger() # Uses the imported Logger
        self.auto_lint = auto_lint
        self.db = db # Database from TaskMaster
        
    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Resolve path and ensure it's within project boundaries"""
        full_path = (self.project_root / path).resolve()
        if not full_path.is_relative_to(self.project_root):
            raise ValueError(f"Path {full_path} is outside project root")
        return full_path

    def read_file(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        """Read file content with optional line range"""
        try:
            full_path = self._validate_path(file_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if start_line is not None or end_line is not None:
                    start = start_line or 0
                    end = end_line or len(lines)
                    # Convert to 0-indexed and clamp
                    start = max(0, start - 1) if start > 0 else 0
                    end = min(len(lines), end)
                    lines = lines[start:end]
                return ''.join(lines)
        except Exception as e:
            self.logger.log(f"Read error: {str(e)}", "ToolKit")
            return f"Error reading file: {str(e)}"

    def write_file(self, file_path: str, content: str) -> str:
        """Write content to file with path validation and optional linting"""
        try:
            full_path = self._validate_path(file_path)
            os.makedirs(full_path.parent, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Lint if enabled and it's a Python file
            if self.auto_lint and full_path.suffix == '.py':
                lint_result = self.lint_file(str(full_path))
                return f"File written successfully. Lint results:\n{lint_result}"
            return "File written successfully."
        except Exception as e:
            self.logger.log(f"Write error: {str(e)}", "ToolKit")
            return f"Error writing file: {str(e)}"

    def patch_file(self, file_path: str, patch: str) -> str:
        """Apply a patch to a file using the provided patch format"""
        try:
            full_path = self._validate_path(file_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            new_content = self.apply_patch(current_content, patch)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return "File patched successfully."
        except Exception as e:
            return f"Error patching file: {str(e)}"

    def apply_patch(self, content: str, patch: str) -> str:
        """Apply patch operations to content"""
        operations = self.parse_patch(patch)
        lines = content.split('\n')
        output_lines = []
        last_index = 0
        
        for op in operations:
            # Add lines before this operation
            output_lines.extend(lines[last_index:op['start']])
            
            # Apply operation
            if op['type'] == 'replace' or op['type'] == 'insert':
                output_lines.extend(op['content'].split('\n'))
            
            # Update last index
            if op['type'] == 'replace' or op['type'] == 'remove':
                last_index = op['end']
            elif op['type'] == 'insert':
                last_index = op['start']
        
        # Add remaining lines
        output_lines.extend(lines[last_index:])
        return '\n'.join(output_lines)

    def parse_patch(self, patch: str) -> List[Dict[str, Any]]:
        """Parse patch instructions into operations"""
        operations = []
        lines = patch.strip().split('\n')
        i = 0
        
        while i < len(lines):
            # Match range specifier: [start-end] or [line]
            if re.match(r'^\[\d+(-\d+)?\]$', lines[i]):
                range_str = lines[i][1:-1]
                if '-' in range_str:
                    start, end = map(int, range_str.split('-'))
                    op_type = 'replace'
                else:
                    start = end = int(range_str)
                    op_type = 'insert'
                
                # Move to content
                i += 1
                content_lines = []
                while i < len(lines) and not re.match(r'^\[\d+(-\d+)?\]$', lines[i]):
                    content_lines.append(lines[i])
                    i += 1
                
                operations.append({
                    'type': op_type,
                    'start': start - 1,  # Convert to 0-indexed
                    'end': end,
                    'content': '\n'.join(content_lines)
                })
            else:
                i += 1
        
        return operations

    def lint_file(self, file_path: str) -> str:
        """Lint a single Python file using Pylint"""
        try:
            full_path = self._validate_path(file_path)
            if full_path.suffix != '.py':
                return "Skipping non-Python file"
                
            cmd = ["pylint", str(full_path), "-E", "--output-format=text"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            output = result.stdout
            if result.returncode != 0 and not output:
                output = result.stderr
            return output[:3000]  # Truncate long output
        except Exception as e:
            return f"Linting error: {str(e)}"

    def lint_project(self, path: str = ".") -> str:
        """Lint the entire project or specific directory"""
        try:
            full_path = self._validate_path(path)
            cmd = ["pylint", str(full_path), "-E", "--output-format=text"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            output = result.stdout
            if result.returncode != 0 and not output:
                output = result.stderr
            return output[:5000]  # Truncate long output
        except Exception as e:
            return f"Linting error: {str(e)}"

    def search_in_files(self, search_query: str, path: str = ".") -> str:
        """Search for text in project files"""
        try:
            full_path = self._validate_path(path)
            results = []
            
            for root, _, files in os.walk(full_path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if search_query in line:
                                    rel_path = file_path.relative_to(self.project_root)
                                    results.append(f"{rel_path}:{line_num}: {line.strip()}")
                    except Exception:
                        continue
            
            return "\n".join(results[:50]) or "No matches found"  # Limit results
        except Exception as e:
            return f"Search error: {str(e)}"

    def analyze_code(self, code: str, file_path: str) -> str:
        """Perform static code analysis using AST and output JSON string to file"""
        try:
            full_path = self._validate_path(file_path)
            tree = ast.parse(code)
            analysis = {
                "functions": [],
                "classes": [],
                "imports": []
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis["functions"].append(node.name)
                elif isinstance(node, ast.ClassDef):
                    analysis["classes"].append(node.name)
                elif isinstance(node, ast.Import):
                    for n in node.names:
                        analysis["imports"].append(n.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module + "." if node.module else ""
                    for n in node.names:
                        analysis["imports"].append(module + n.name)

            # Write analysis to a JSON file
            with open(full_path, 'w') as f:
                json.dump(analysis, f, indent=4)

            return f"Code analysis written to: {file_path}"
        except Exception as e:
            return f"Error during analysis: {str(e)}"
            
    def run_command(self, command: str, cwd: str = None) -> str:
        """Execute shell command safely"""
        try:
            cwd_path = self._validate_path(cwd) if cwd else self.project_root
            result = subprocess.run(
                command.split(),
                cwd=cwd_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout or result.stderr
        except Exception as e:
            return f"Command error: {str(e)}"

    def generate_ctags(self, path: str = ".") -> str:
        """Generate ctags index only if source files exist"""
        try:
            full_path = self._validate_path(path)
            
            # Check if source files exist
            has_source_files = any(full_path.glob("**/*.py")) or any(full_path.glob("**/*.js"))
            if not has_source_files:
                return "Skipping ctags: No source files found"
            
            tags_path = full_path / "tags"
            
            # Run ctags command
            cmd = ["ctags", "-R", "-f", str(tags_path), "."]
            result = subprocess.run(
                cmd,
                cwd=full_path,
                capture_output=True,
                text=True,
                timeout=120  # Longer timeout for large projects
            )
            
            if result.returncode != 0:
                return f"ctags error: {result.stderr}"
            
            return f"ctags generated at: {tags_path.relative_to(self.project_root)}"
        except Exception as e:
            return f"ctags generation error: {str(e)}"

    def search_ctags(self, symbol: str, path: str = ".") -> str:
        """Search for a symbol only if tags file exists"""
        try:
            full_path = self._validate_path(path)
            tags_path = full_path / "tags"
            
            if not tags_path.exists():
                return "tags file not found. Generate ctags first or create source files"
                
            # Search for symbol in tags file
            with open(tags_path, 'r', encoding='utf-8', errors='ignore') as f:
                matches = []
                for line in f:
                    if line.startswith(symbol + "\t"):
                        parts = line.split("\t")
                        if len(parts) > 2:
                            file_path = parts[1]
                            pattern = parts[2].strip()
                            
                            # Extract line number from pattern
                            line_match = re.search(r'(\d+);"', pattern)
                            line_num = line_match.group(1) if line_match else "?"
                            
                            matches.append(f"{file_path}:{line_num}")
                
                if matches:
                    return "Found in:\n" + "\n".join(matches[:10])  # Limit results
                return "Symbol not found in ctags index"
        except Exception as e:
            return f"ctags search error: {str(e)}"

    def get_symbol_context(self, symbol: str, path: str = ".") -> str:
        """Get context for a symbol using ctags"""
        try:
            search_result = self.search_ctags(symbol, path)
            if not search_result.startswith("Found in:"):
                return search_result
                
            # Extract first match
            match_line = search_result.split("\n")[1]
            file_path, line_num = match_line.split(":")
            
            # Read context around the symbol
            full_file_path = self._validate_path(file_path)
            with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                line_index = int(line_num) - 1
                start = max(0, line_index - 3)
                end = min(len(lines), line_index + 4)
                context = "".join(
                    f"{i+1}: {line}" 
                    for i, line in enumerate(lines[start:end], start=start)
                )
                
            return f"Context for {symbol} in {file_path}:\n{context}"
        except Exception as e:
            return f"Context error: {str(e)}"

    # Add port management tool
    def reserve_port(self, port: int = 0) -> str:
        """Reserve and return an available port"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return str(s.getsockname()[1])
        except Exception as e:
            return f"Port reservation error: {str(e)}"

    def get_tool_definitions(self):
        return [TOOL_DESCRIPTIONS[tool_name] for tool_name in TOOL_DESCRIPTIONS]

    def list_template_files(self, template_type: str, base_path: str = "templates") -> List[str]:
        """Lists available template files for a given type (e.g., 'frontend', 'mobile') and specific framework.
        The framework is derived from project_context.tech_stack.
        Example: template_type='frontend/React' -> lists files in 'templates/frontend/React'
        """
        # The agent calling this tool will construct the template_type path based on project_context
        target_dir = Path(base_path) / template_type # template_type is path relative to base_path
        self.logger.log(f"Listing template files in: {target_dir}", "ToolKit")

        # Resolve and validate the target directory to ensure it's within the project root's "templates" subdirectory
        try:
            # Ensure base_path itself is safe and within project_root
            safe_base_path = self._validate_path(base_path)
            # Now combine with template_type
            # This still needs care if template_type contains '..'
            # A more robust way is to ensure template_type is a simple relative path

            # Simplification: Assume base_path is "templates" and template_type is "frontend/react"
            # The _validate_path should ideally be used on the final constructed path.
            # Let's construct path first, then validate.
            # target_dir = (self.project_root / base_path / template_type).resolve()
            # if not target_dir.is_relative_to((self.project_root / base_path).resolve()):
            #    raise ValueError(f"Template path {template_type} attempts to escape base template directory {base_path}")
            # More simply, ensure template_type doesn't have '..'
            if ".." in template_type:
                 raise ValueError("template_type cannot contain '..'")

            final_target_dir = (self.project_root / base_path / template_type).resolve()
            # Check if final_target_dir is within project_root/base_path
            if not final_target_dir.is_relative_to((self.project_root / base_path).resolve()):
                 raise ValueError(f"Template path {template_type} is outside allowed template directory.")

            if not final_target_dir.is_dir():
                return [f"Template directory not found: {final_target_dir.relative_to(self.project_root)}"]

            files = [f.name for f in final_target_dir.iterdir() if f.is_file()]
            return files if files else ["No template files found in this directory."]
        except ValueError as ve: # Catch path validation errors
            self.logger.log(f"Path validation error for template listing: {ve}", "ToolKit", level="ERROR")
            return [f"Path validation error: {str(ve)}"]
        except Exception as e:
            self.logger.log(f"Error listing template files in {template_type}: {e}", "ToolKit", level="ERROR")
            return [f"Error listing templates: {str(e)}"]

    def detect_platforms(self, objective: str) -> Dict[str, bool]:
        """Detects required platforms based on project objective."""
        platforms = {"web": False, "ios": False, "android": False} # Note: "mobile" general flag removed as per issue context, direct ios/android
        objective_lower = objective.lower()
        if "web app" in objective_lower or "website" in objective_lower:
            platforms["web"] = True
        # If specific mobile platforms aren't mentioned, but "mobile" is, we might infer, but problem implies directness
        if "ios" in objective_lower:
            platforms["ios"] = True
        if "android" in objective_lower:
            platforms["android"] = True

        # If "mobile" is mentioned but not ios or android specifically, we could default or leave as is.
        # For now, sticking to explicit mentions for ios/android as per provided snippet.
        # The original snippet also had a general "mobile" flag. If that's needed:
        # if "mobile" in objective_lower and not platforms["ios"] and not platforms["android"]:
        #    platforms["mobile"] = True # Or perhaps set both ios and android to a default?
                                        # For now, let's stick to the Pydantic model PlatformRequirements which has web, ios, android

        self.logger.log(f"Detected platforms: {platforms} for objective: '{objective}'", "ToolKit")
        return platforms

    def resolve_tech_conflict(self, proposals: List[Dict]) -> Dict:
        """Resolves conflicts between multiple technology proposals based on confidence scores."""
        if not proposals:
            self.logger.log("resolve_tech_conflict: No proposals received.", "ToolKit", level="WARNING")
            return {"decision": "error", "reason": "No proposals to resolve."}

        if len(proposals) == 1:
            self.logger.log(f"resolve_tech_conflict: Single proposal received: {proposals[0].get('technology')}", "ToolKit")
            return {"decision": "use_proposal", "proposal": proposals[0], "reason": "Single proposal."}

        # Sort by confidence, handling potential missing 'confidence' key by defaulting to 0.0
        sorted_proposals = sorted(proposals, key=lambda p: p.get('confidence', 0.0), reverse=True)
        highest_confidence_proposal = sorted_proposals[0]
        second_highest_confidence_proposal = sorted_proposals[1]

        self.logger.log(f"resolve_tech_conflict: Highest confidence: {highest_confidence_proposal.get('technology')} ({highest_confidence_proposal.get('confidence', 0.0)}), Second: {second_highest_confidence_proposal.get('technology')} ({second_highest_confidence_proposal.get('confidence', 0.0)})", "ToolKit")

        confidence_threshold = 0.15 # As per issue's "Conflict Resolution Triggers"

        if abs(highest_confidence_proposal.get('confidence', 0.0) - second_highest_confidence_proposal.get('confidence', 0.0)) > confidence_threshold:
            self.logger.log(f"resolve_tech_conflict: Decided to use proposal {highest_confidence_proposal.get('technology')} due to confidence diff > {confidence_threshold}", "ToolKit")
            return {"decision": "use_proposal", "proposal": highest_confidence_proposal, "reason": f"Highest confidence (>{confidence_threshold} difference)."}
        else:
            self.logger.log("resolve_tech_conflict: Confidence scores are close. Needs hybrid or further evaluation.", "ToolKit")
            # The decision to call create_hybrid_solution will be made by the orchestrator/agent based on this outcome.
            return {"decision": "needs_hybrid", "proposals": proposals, "reason": "Confidence scores are close, explore hybrid solution or require further review."}

    def create_hybrid_solution(self, proposals: List[Dict], category: str) -> Dict:
        """Creates a hybrid technology solution from a list of proposals for a specific category."""
        self.logger.log(f"create_hybrid_solution: Attempting for category '{category}' with proposals: {[p.get('technology') for p in proposals]}", "ToolKit")
        if not proposals:
            return {"solution_type": "error", "description": "No proposals provided to create a hybrid solution.", "reason": "Input list was empty."}

        # Example specific to 'database' from the issue
        if category == "database":
            tech_names = [p.get('technology', '').lower() for p in proposals]
            has_roomdb = any("roomdb" in name or "room" in name for name in tech_names) # شويه flexible
            has_firestore = any("firestore" in name for name in tech_names)

            if has_roomdb and has_firestore:
                # Find the original proposals to ensure we use their exact names/details if needed
                roomdb_proposal = next((p for p in proposals if "roomdb" in p.get('technology', '').lower() or "room" in p.get('technology', '').lower()), None)
                firestore_proposal = next((p for p in proposals if "firestore" in p.get('technology', '').lower()), None)

                roomdb_name = roomdb_proposal.get('technology') if roomdb_proposal else "RoomDB compatible"
                firestore_name = firestore_proposal.get('technology') if firestore_proposal else "Firestore compatible"

                self.logger.log(f"create_hybrid_solution: Found RoomDB and Firestore for database category. Creating hybrid.", "ToolKit")
                return {
                    "solution_type": "hybrid",
                    "description": f"{roomdb_name} for local offline storage + {firestore_name} for cloud sync.",
                    "components": [roomdb_name, firestore_name],
                    "integration_points": ["WorkManager data synchronization via FirestoreSyncService"], # From issue
                    "reason": "Combines offline capability with cloud synchronization."
                }

        # Generic fallback: Combine top 2 or list them.
        # For now, this indicates a failure to find a specific hybrid rule and suggests manual review or a combined approach.
        # An agent receiving this might then decide to pick the highest confidence, or re-prompt.
        sorted_proposals = sorted(proposals, key=lambda p: p.get('confidence', 0.0), reverse=True)
        top_technologies = [p.get('technology', 'Unknown') for p in sorted_proposals[:2] if p.get('technology')]

        if len(top_technologies) > 1:
            desc = f"Consider a combined approach using {top_technologies[0]} and {top_technologies[1]}, or prioritize based on detailed requirements."
            components = top_technologies
        elif len(top_technologies) == 1:
            desc = f"No specific hybrid rule matched. Highest confidence proposal was {top_technologies[0]}."
            components = top_technologies
        else: # Should not happen if proposals list is not empty, but as a safeguard
            return {"solution_type": "error", "description": "Could not create a hybrid solution.", "reason": "No valid technologies in proposals."}

        self.logger.log(f"create_hybrid_solution: No specific hybrid rule for '{category}'. Fallback: {desc}", "ToolKit")
        return {
            "solution_type": "combined_suggestion",
            "description": desc,
            "components": components,
            "reason": "No specific hybrid rule matched for this category. Suggesting combination or prioritization of top proposals."
        }

    def lock_tech_stack(self, approved_stack_dict: Dict[str, Any], platform_requirements_dict: Dict[str, Any], agent_details: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Simulates the process of locking the tech stack by consulting various agents
        (represented by agent_details) for validation.
        This tool itself performs a simplified, role-based validation.
        """
        all_concerns = []
        overall_approval = True
        self.logger.log(f"lock_tech_stack: Validating stack {approved_stack_dict} with agents: {[a.get('name') for a in agent_details]}", "ToolKit")

        for agent_info in agent_details:
            agent_name = agent_info.get("name", "Unknown Agent")
            agent_role = agent_info.get("role", "Unknown Role").lower() # Use role for simulation logic

            current_agent_approved = True
            concern_details = []

            # Simulate MobileDeveloper validation logic (based on Agent.validate_stack base and MobileDeveloper override)
            if "mobile developer" in agent_role or "mobile_specialist" in agent_role:
                is_mobile_project = platform_requirements_dict.get("ios") or platform_requirements_dict.get("android")
                if is_mobile_project:
                    mobile_db = approved_stack_dict.get("mobile_database")
                    if not mobile_db:
                        current_agent_approved = False
                        concern_details.append("Mobile platform required but no mobile_database specified.")
                    else:
                        # Example of a more specific mobile check from MobileDeveloper.validate_stack
                        unsuitable_standalone_mobile_dbs = ["elasticsearch", "dynamodb"]
                        if any(unsuitable_db in mobile_db.lower() for unsuitable_db in unsuitable_standalone_mobile_dbs) and \
                           not any(hybrid_indicator in mobile_db.lower() for hybrid_indicator in ["firestore", "sqlite", "roomdb", "realm"]):
                            # This concern is noted, but might not set current_agent_approved to False,
                            # depending on how strict the simulated veto is.
                            # For this simulation, let's make it a strong concern that prevents overall_approval.
                            current_agent_approved = False
                            concern_details.append(f"Proposed mobile_database '{mobile_db}' may be unsuitable for standalone mobile use by {agent_name}.")


            # Simulate Architect validation logic (based on Agent.validate_stack base)
            # Also includes generic checks that other agents might perform if they were a base Agent type.
            if platform_requirements_dict.get("web") and not approved_stack_dict.get("web_backend"):
                current_agent_approved = False
                concern_details.append(f"Web platform required but no web_backend specified (concern for {agent_name}).")

            # Check for mobile_database again, as a general check if no mobile specialist was present,
            # or if the mobile specialist didn't veto but a generalist might still note its absence.
            # This is a bit redundant if a mobile specialist is always present for mobile projects,
            # but included for completeness of simulated base checks.
            is_mobile_project_for_generalist = platform_requirements_dict.get("ios") or platform_requirements_dict.get("android")
            if is_mobile_project_for_generalist and not approved_stack_dict.get("mobile_database"):
                # Only add this concern if a mobile specialist didn't already flag it more specifically
                if not ("mobile developer" in agent_role or "mobile_specialist" in agent_role):
                    current_agent_approved = False
                    concern_details.append(f"Mobile platform required but no mobile_database specified (general concern by {agent_name}).")

            if not current_agent_approved:
                overall_approval = False
                for detail in concern_details:
                    formatted_concern = f"Concern from {agent_name} ({agent_info.get('role', 'N/A')}): {detail}"
                    all_concerns.append(formatted_concern)
                    self.logger.log(formatted_concern, "ToolKit", level="WARNING")
            else:
                 self.logger.log(f"lock_tech_stack: Agent {agent_name} ({agent_info.get('role', 'N/A')}) approves the stack.", "ToolKit")


        if overall_approval:
            self.logger.log("lock_tech_stack: Consensus achieved. Tech stack locked.", "ToolKit")
            return {"consensus_locked": True, "message": "Consensus achieved. Tech stack locked.", "concerns": []}
        else:
            self.logger.log(f"lock_tech_stack: Consensus failed. Concerns: {all_concerns}", "ToolKit", level="ERROR")
            return {"consensus_locked": False, "message": "Consensus failed. Re-negotiation may be needed.", "concerns": all_concerns}

    def check_technology_dependencies(self, tech_stack: Dict[str, Any]) -> Dict[str, Any]:
        """Checks a given tech stack for known incompatibilities or important dependency notes."""
        self.logger.log(f"check_technology_dependencies: Checking stack: {tech_stack}", "ToolKit")

        # Define rules within the method for simplicity, or load from a config file for more complex scenarios.
        KNOWN_INCOMPATIBILITIES = {
            "SQLite": {"does_not_integrate_natively_with": ["MongoDB Atlas", "Amazon DocumentDB", "Firestore"]}, # Added Firestore
            # Example: If 'React Server Components' were chosen for frontend, but 'Express.js' for backend,
            # there might be specific considerations or alternative backend choices that are more tightly integrated.
            # "React Server Components": {"better_with_frameworks_like": ["Next.js", "Remix"]},
        }
        DEPENDENCY_NOTES = {
            "MongoDB Atlas": {"requires_internet_for_full_sync": True, "note": "Consider implications for offline-first mobile apps if Atlas is the primary mobile DB."},
            "Firestore": {"requires_internet_for_full_sync": True, "note": "Excellent for real-time sync and web/mobile integration, but ensure offline strategy for mobile."},
            "Amazon S3": {"note": "Highly scalable for media storage, ensure appropriate IAM permissions and CDN for performance."},
            "Elasticsearch": {"note": "Powerful for search, but resource-intensive. Ensure it's justified by search requirements."},
            # General notes for categories
            "mobile_database": {"general_note": "For mobile databases, consider offline capabilities, synchronization complexity, and native performance."},
        }
        # REQUIRED_PAIRINGS could be added if specific technologies *must* go together.
        # e.g., REQUIRED_PAIRINGS = {"SpecificPaymentGatewaySDK": {"requires_specific_version_of": "OurInternalAuthLibrary"}}

        conflicts_found = []
        warnings = []

        tech_list_in_stack = [value.lower() for value in tech_stack.values() if value]

        for tech_category, tech_name in tech_stack.items():
            if not tech_name:
                continue

            tech_name_lower = tech_name.lower()

            # Check direct incompatibilities
            for known_tech_key, rules in KNOWN_INCOMPATIBILITIES.items():
                if known_tech_key.lower() in tech_name_lower: # If the current tech_name matches a known_tech key
                    if "does_not_integrate_natively_with" in rules:
                        for incompatible_other_tech_name in rules["does_not_integrate_natively_with"]:
                            # Check if this incompatible tech is ALSO in the stack (in any category)
                            if any(incompatible_other_tech_name.lower() in other_val_lower for other_val_lower in tech_list_in_stack if other_val_lower != tech_name_lower):
                                # Find which category the incompatible tech belongs to for a more informative message
                                conflicting_cat_and_tech = next(
                                    (f"{cat} ({val})" for cat, val in tech_stack.items() if val and incompatible_other_tech_name.lower() in val.lower()),
                                    incompatible_other_tech_name # Fallback to just the name
                                )
                                conflict_msg = f"Potential conflict: {tech_name} (in {tech_category}) may not integrate natively with {conflicting_cat_and_tech}."
                                if conflict_msg not in conflicts_found: # Avoid duplicates
                                    conflicts_found.append(conflict_msg)
                                    self.logger.log(f"check_technology_dependencies: {conflict_msg}", "ToolKit", level="WARNING")

            # Check for dependency notes
            for known_tech_key, notes in DEPENDENCY_NOTES.items():
                if known_tech_key.lower() in tech_name_lower:
                    if "note" in notes:
                        warning_msg = f"Note for {tech_name} (in {tech_category}): {notes['note']}"
                        if warning_msg not in warnings: warnings.append(warning_msg)
                    if notes.get("requires_internet_for_full_sync"):
                        warning_msg = f"Note: {tech_name} (in {tech_category}) requires internet for full sync capabilities."
                        if warning_msg not in warnings: warnings.append(warning_msg)

            # Check general category notes
            if tech_category in DEPENDENCY_NOTES and "general_note" in DEPENDENCY_NOTES[tech_category]:
                warning_msg = f"General note for {tech_category}: {DEPENDENCY_NOTES[tech_category]['general_note']}"
                if warning_msg not in warnings: warnings.append(warning_msg)

        if not conflicts_found and not warnings:
            self.logger.log("check_technology_dependencies: No conflicts or warnings found.", "ToolKit")
        else:
            for warning in warnings:
                 self.logger.log(f"check_technology_dependencies: {warning}", "ToolKit", level="INFO")


        return {"conflicts": conflicts_found, "warnings": warnings}


# Tool descriptions for agent prompts
TOOL_DESCRIPTIONS = {
    "check_technology_dependencies": {
        "name": "check_technology_dependencies",
        "description": "Checks a given technology stack (dictionary of category: tech_name) for known incompatibilities or important considerations/warnings. Returns a dictionary with 'conflicts' (list of strings) and 'warnings' (list of strings).",
        "parameters": {
            "type": "object",
            "properties": {
                "tech_stack": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "A dictionary representing the technology stack, e.g., {'web_backend': 'Node.js', 'database': 'MongoDB Atlas'}."
                }
            },
            "required": ["tech_stack"]
        }
    },
    "lock_tech_stack": {
        "name": "lock_tech_stack",
        "description": "Simulates validating and locking the tech stack after consulting specified agents. Input: approved_stack_dict, platform_requirements_dict, and a list of agent details (name, role). Output: dictionary indicating if consensus was locked, a message, and any concerns.",
        "parameters": {
            "type": "object",
            "properties": {
                "approved_stack_dict": {
                    "type": "object",
                    "description": "The proposed ApprovedTechStack as a dictionary."
                },
                "platform_requirements_dict": {
                    "type": "object",
                    "description": "The PlatformRequirements as a dictionary."
                },
                "agent_details": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "role": {"type": "string"}
                        },
                        "required": ["name", "role"]
                    },
                    "description": "List of agent details (name, role) to simulate consultation for validation."
                }
            },
            "required": ["approved_stack_dict", "platform_requirements_dict", "agent_details"]
        }
    },
    "resolve_tech_conflict": {
        "name": "resolve_tech_conflict",
        "description": "Resolves conflicts between multiple technology proposals. Input: a list of proposal dictionaries. Output: a dictionary with a decision ('use_proposal', 'needs_hybrid', 'error') and relevant data.",
        "parameters": {
            "type": "object",
            "properties": {
                "proposals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "proponent": {"type": "string"},
                            "technology": {"type": "string"},
                            "reason": {"type": "string"},
                            "confidence": {"type": "number"},
                            "compatibility_score": {"type": ["number", "null"]},
                            "effort_estimate": {"type": ["string", "null"]}
                        },
                        "required": ["proponent", "technology", "reason", "confidence"]
                    },
                    "description": "List of technology proposal objects (as dictionaries)."
                }
            },
            "required": ["proposals"]
        }
    },
    "create_hybrid_solution": {
        "name": "create_hybrid_solution",
        "description": "Attempts to create a hybrid technology solution from a list of proposals for a specific category. Input: list of proposal dictionaries and the category string. Output: dictionary describing the hybrid solution or an error.",
        "parameters": {
            "type": "object",
            "properties": {
                "proposals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "proponent": {"type": "string"},
                            "technology": {"type": "string"},
                            "reason": {"type": "string"},
                            "confidence": {"type": "number"},
                            "compatibility_score": {"type": ["number", "null"]},
                            "effort_estimate": {"type": ["string", "null"]}
                        },
                        "required": ["proponent", "technology", "reason", "confidence"]
                    },
                    "description": "List of technology proposal objects (as dictionaries) that are candidates for a hybrid solution."
                },
                "category": {
                    "type": "string",
                    "description": "The technology category for which to create a hybrid solution (e.g., 'database', 'web_backend')."
                }
            },
            "required": ["proposals", "category"]
        }
    },
    "detect_platforms": {
        "name": "detect_platforms",
        "description": "Detects required platforms (web, iOS, Android) from the project objective. Returns a dictionary like {'web': True, 'ios': False, 'android': True}, suitable for creating a PlatformRequirements model.",
        "parameters": {
            "type": "object",
            "properties": {
                "objective": {
                    "type": "string",
                    "description": "The project objective or description."
                }
            },
            "required": ["objective"]
        }
    },
    "list_template_files": {
        "name": "list_template_files",
        "description": "Lists available template files in a specified subdirectory under the main 'templates' folder (e.g., 'templates/frontend/react'). Use this to discover available UI or code templates. The agent should construct the 'template_type' argument based on the project context (e.g., 'frontend/react' or 'mobile/swift').",
        "parameters": { # Corrected schema definition
            "type": "object",
            "properties": {
                "template_type": {
                    "type": "string",
                    "description": "The path relative to the 'templates' directory (e.g., 'frontend/react' or 'mobile/swift')."
                }
            },
            "required": ["template_type"]
        }
    },
    "read_file": {
        "name": "read_file",
        "description": "Read file contents. Input: {'file_path': 'path', 'start_line': int, 'end_line': int}",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"}
            },
            "required": ["file_path"]
        }
    },
    "write_file": {
        "name": "write_file",
        "description": "Write content to file. Input: {'file_path': 'path', 'content': 'text'}",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["file_path", "content"]
        }
    },
    "patch_file": {
        "name": "patch_file",
        "description": "Patch file content. Input: {'file_path': 'path', 'patch': 'patch instructions'}",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "patch": {"type": "string"}
            },
            "required": ["file_path", "patch"]
        }
    },
    "lint_file": {
        "name": "lint_file",
        "description": "Lint a Python file. Input: {'file_path': 'path'}",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"}
            },
            "required": ["file_path"]
        }
    },
    "lint_project": {
        "name": "lint_project",
        "description": "Lint entire project. Input: {'path': 'optional subpath'}",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            }
        }
    },
    "run_command": {
        "name": "run_command",
        "description": "Execute shell command. Input: {'command': 'shell cmd', 'cwd': 'optional dir'}",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string"}
            },
            "required": ["command"]
        }
    },
     "analyze_code": {
        "name": "analyze_code",
        "description": "Analyze code structure, writes result to a JSON file. Input: {'code': 'python code', 'file_path':'path to write json'}",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "file_path": {"type": "string"},
            },
            "required": ["code", "file_path"]
        }
    },
    # --- New ctags and search_in_files tools below ---
    "search_ctags": {
        "name": "search_ctags",
        "description": "Find symbol definitions (FAST). Input: {'symbol': 'name', 'path': 'optional subpath'}",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "path": {"type": "string"}
            },
            "required": ["symbol"]
        }
    },
    "search_in_files": {
        "name": "search_in_files",
        "description": "Find text patterns (SLOW). Input: {'search_query': 'text', 'path': 'optional subpath'}",
        "parameters": {
            "type": "object",
            "properties": {
                "search_query": {"type": "string"},
                "path": {"type": "string"}
            },
            "required": ["search_query"]
        }
    },
    "get_symbol_context": {
        "name": "get_symbol_context",
        "description": "Get code around symbol. Input: {'symbol': 'name', 'path': 'optional subpath'}",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "path": {"type": "string"}
            },
            "required": ["symbol"]
        }
    },
    "generate_ctags": {
        "name": "generate_ctags",
        "description": "Build code index. Run after major changes. Input: {'path': 'optional subpath'}",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            }
        }
    },
    "reserve_port": {
        "name": "reserve_port",
        "description": "Reserve an available network port. Input: {'port': 'optional port number'}",
        "parameters": {
            "type": "object",
            "properties": {
                "port": {"type": "integer"}
            }
        }
    },
}
