# AI-Powered Development Team (Qnatz Crew)

Qnatz Crew is an experimental framework designed to simulate an AI-powered software development team. It leverages a crew of specialized AI agents, each contributing to different phases of the software development lifecycle, from initial analysis and planning to code generation, testing, and debugging. The system aims to automate and streamline development tasks using Large Language Models (LLMs) and a structured workflow.

## Core Features

*   **Agent-Based Architecture:** Specialized agents (e.g., Project Analyzer, Planner, Architect, Code Writer, Tester) collaborate on tasks.
*   **Dynamic Workflow:** The system can adapt its workflow based on project type (backend, web, mobile, fullstack).
*   **ToolKit for Agents:** Agents are equipped with a variety of tools for file operations, code analysis (linting, ctags), and more.
*   **Project Context Management:** A `project_context.json` file maintains the state of the project, including objectives, tech stack, analysis, plans, and code snippets.
*   **Tech Council Framework:** An automated system for technology negotiation, conflict resolution, and ensuring stack cohesion (see details below).
*   **Local LLM Support:** Includes configurations for potentially using local LLMs alongside cloud-based models like Gemini.
*   **Vector Database Memory:** Agents can store and retrieve information from a vector database, providing a form of memory.

## Tech Council Framework

The Tech Council Framework is a key component of this AI development system, designed to automate and manage the selection of technologies for a project. It facilitates a collaborative negotiation process among AI agents to arrive at a cohesive and validated technology stack.

### Purpose

The primary purpose of the Tech Council is to:
*   Ensure that technology choices are well-reasoned and aligned with project requirements and platform needs.
*   Resolve conflicts when different agents propose competing technologies for the same component.
*   Check for dependencies and potential incompatibilities within the chosen tech stack.
*   Achieve consensus among key specialized agents before locking the final technology stack.

### Key Phases

The Tech Council workflow involves several distinct phases:

1.  **Platform Detection:**
    *   The `ProjectAnalyzer` agent, using the `detect_platforms` tool, determines the target platforms for the project (e.g., web, iOS, Android) based on the project objective. This information is stored in `project_context.platform_requirements`.

2.  **Tech Proposal:**
    *   Specialized agents (e.g., `Architect`, `MobileDeveloper`) propose specific technologies for different categories relevant to their expertise (e.g., web backend, mobile database).
    *   These proposals, including the technology name, justification (reason), confidence score, and effort estimate, are stored in `project_context.tech_proposals`.

3.  **Conflict Resolution:**
    *   If multiple proposals are made for the same category, the `resolve_tech_conflict` tool is used.
    *   It selects a proposal based on confidence scores. If confidence scores are close, it may suggest a hybrid solution.
    *   The `create_hybrid_solution` tool can then be used to generate a description for combining technologies (e.g., RoomDB + Firestore for a mobile database with cloud sync).
    *   Decisions and their reasons are recorded in `project_context.decision_rationale`.

4.  **Dependency Checking:**
    *   Once an initial set of technologies is chosen, the `check_technology_dependencies` tool examines the proposed stack for known incompatibilities or important considerations (e.g., a database requiring internet for an offline-first mobile app).
    *   Conflicts and warnings are logged and added to `project_context.decision_rationale`.

5.  **Consensus Locking:**
    *   Key validating agents (e.g., `Architect`, `MobileDeveloper` if a mobile platform is targeted) review the proposed `approved_tech_stack`.
    *   Each relevant agent calls its `validate_stack` method to check for concerns based on its specialization.
    *   The `lock_tech_stack` tool (currently a simulation) aggregates these validations.
    *   If all relevant agents approve, the tech stack is considered locked. Otherwise, concerns are recorded, potentially leading to re-negotiation.
    *   The final consensus status is stored in `project_context.decision_rationale`.

### Agent Participation

*   **`ProjectAnalyzer`**: Detects platforms and may propose initial general technologies (e.g., a default database).
*   **`Architect`**: Proposes technologies for backend systems, media storage, etc., and validates the overall stack.
*   **`MobileDeveloper`**: Proposes technologies for mobile-specific components (e.g., mobile database, native features) and validates the stack from a mobile perspective.
*   Other agents can be integrated into this process as needed (e.g., a `SecurityAnalyst`).

### Project Context Additions

The Tech Council Framework significantly enhances `project_context.json` by adding the following key fields:

*   `platform_requirements`: Stores boolean flags for `web`, `ios`, `android` platforms. (Type: `PlatformRequirements`)
*   `tech_proposals`: A dictionary where keys are technology categories (e.g., "database", "web_backend") and values are lists of `TechProposal` objects, each detailing a proposed technology, its proponent, reason, confidence, etc.
*   `approved_tech_stack`: Stores the final chosen technologies for each category after negotiation and conflict resolution. (Type: `ApprovedTechStack`)
*   `decision_rationale`: A dictionary storing reasons for technology choices, outcomes of conflict resolution, dependency check results, and consensus status.

This framework aims to make technology selection more transparent, reasoned, and robust within the automated development process.

## Getting Started

(Instructions for setting up and running the project would go here - currently under development)

1.  **Environment Setup:**
    *   Ensure Python 3.8+ is installed.
    *   Set up a virtual environment: `python -m venv venv` and `source venv/bin/activate`.
    *   Install dependencies: `pip install -r requirements.txt` (A `requirements.txt` would need to be generated).
    *   Configure API keys: Set your `GEMINI_API_KEY` in a `.env` file.

2.  **Running the System:**
    *   Execute the main script: `python main.py "Your project objective here"`

## Future Development

*   More sophisticated agent interaction models.
*   Enhanced error handling and recovery.
*   Deeper integration of tools and agent capabilities.
*   GUI/Web interface for interaction.

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests.
(Details on contribution guidelines would go here).
