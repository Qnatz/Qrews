# Web Crew Prompt Engineering Guidelines

This document outlines the standards and best practices for creating effective prompts for AI assistants within the Web Crew. Adherence to these guidelines is crucial for ensuring clarity, consistency, and optimal performance from our AI agents.

## 1. Parameterization

Effective prompts are reusable and adaptable. Parameterization is key to achieving this.

*   **Always use placeholders instead of fixed values.**
    *   Replace any literal filenames, paths, URLs, or configuration values with clearly named variables.
    *   Enclose each variable in curly braces to distinguish it from natural text.
    *   **Example:** "Write a new file at `{PROJECT_ROOT}/src/utils/{HELPER_NAME}.js` exporting a function called `{FUNCTION_NAME}()`."
    *   **Anti‐pattern:** "Write a new file at /home/user/myapp/src/utils/helpers.js exporting a function called formatDate()."
*   **Use uppercase snake_case for placeholders:** `{DB_HOST}`, `{API_KEY}`, `{PROJECT_ROOT}`.
*   **Group related parameters under consistent naming conventions.**
*   **Maintain a “Parameter Reference” at the top of complex prompts** when multiple placeholders appear. This section should list each placeholder, its purpose, and an example value or default.
    *   **Example:**
        ```
        Parameters:
        ───────────
        {SERVICE_NAME} – Name of the microservice (e.g., “user‐service”)
        {PORT} – Listening port (e.g., 8080)
        {DB_URL} – Connection string for PostgreSQL
        {RETRY_COUNT} – Number of retry attempts on failure

        Prompt:
        "Generate a Kubernetes Deployment manifest for {SERVICE_NAME}, listening on port {PORT}, connecting to database at {DB_URL}. Implement a retry policy with {RETRY_COUNT} attempts on container crash."
        ```
*   **Do not hard‐code environment‐specific details.**
    *   Even “standard” defaults (e.g., port 3000, localhost) should be parameterized: “Use `{DEFAULT_PORT}` as the fallback if `{PORT}` is not set.”

## 2. ReAct Format

When the assistant needs to reason through a multi‐step requirement or debugging task, structure every reasoning chain according to the ReAct pattern. This provides clarity into the agent's process and helps in debugging the agent's behavior.

*   **Thought:** (Internal reasoning, chain‐of‐thought step)
    *   Summarize why you’re choosing a particular action.
    *   Be concise; show your intent.
*   **Action:** (Explicit tool call or operation)
    *   Specify exactly which function, command, or tool to invoke (e.g., WRITE_FILE, RUN_LINTER, CHECK_SYNTAX).
    *   Use a standardized syntax. Example: `Action: write_file Path: {PROJECT_ROOT}/src/index.js Content: ```js console.log("Hello, World!"); ``` ` (Note: Actual tool invocation syntax may vary based on the agent's capabilities).
*   **Observation:** (Result of the action)
    *   State the immediate outcome or content returned by the action.
    *   If the action returned an error, document it verbatim.
*   **(Loop)** Repeat Thought → Action → Observation until you arrive at a final deliverable or conclusion.

### 2.1. ReAct Skeleton Example

Use this as a template for any multi‐step prompt where the agent needs to show its work:

```
Thought: I need to create a helper that formats dates in ISO format. We should write a JS module under `{PROJECT_ROOT}/src/utils/`.
Action: write_file Path: {PROJECT_ROOT}/src/utils/formatDate.js Content: \`\`\`js
export function formatDate(date) {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
\`\`\`
Observation: File written successfully.

Thought: Next, add a unit test for that helper.
Action: write_file Path: {PROJECT_ROOT}/tests/utils/formatDate.test.js Content: \`\`\`js
import { formatDate } from "../../src/utils/formatDate";
test("formatDate should produce YYYY-MM-DD", () => {
  expect(formatDate("2025-06-01T00:00:00Z")).toBe("2025-06-01");
});
\`\`\`
Observation: File written successfully.

Final Answer:
“Two files created:
• {PROJECT_ROOT}/src/utils/formatDate.js
• {PROJECT_ROOT}/tests/utils/formatDate.test.js
Both contain the helper and its corresponding test as specified.”
```

## 3. Hard (Directive) Language

All prompts must be written in **clear, authoritative, and unambiguous commands**. Use an imperative tone, avoid conditional phrasing, and never show uncertainty. This ensures the AI agent has precise instructions.

### 3.1. Tone and Style Guidelines:

1.  **Use the imperative mood:**
    *   Begin instructions with verbs like “Create,” “Write,” “Generate,” “Ensure,” “Validate,” “Implement,” etc.
    *   ❌ Don’t say: “You might want to create a file…”
    *   ✔️ Do say: “Create a new file at `{FILE_PATH}` containing the following content…”
2.  **Be explicit about requirements:**
    *   If something is required, state “REQUIRED:” or “MUST.”
    *   Example:
        ```
        “MUST use Node.js v14 as the runtime. Do NOT use any other version.”
        “REQUIRED: All API endpoints must validate input against the JSON schema before processing.”
        ```
3.  **Prohibit undesired actions tersely:**
    *   Use “Do not” instead of “Should avoid,” “Must not” instead of “Prefer not.”
    *   Example:
        ```
        “Do not include any inline CSS; use only Tailwind classes.”
        “Must not reference any deprecated functions or libraries.”
        ```
4.  **Enumerate steps precisely:**
    *   Number or bullet‐point tasks if more than one step is required within the prompt's instructions to the AI.
    *   Example:
        ```
        1. Initialize a new React application by running `{NPM_INIT_COMMAND}`.
        2. Install dependencies `{DEPENDENCY_LIST}`.
        3. Configure ESLint with the standard Airbnb rules.
        4. Create the following folder structure under `{PROJECT_ROOT}`:
           - src/components
           - src/pages
           - src/utils
        5. Create a sample component in `src/components/HelloWorld.jsx` that renders a `<div>` with “Hello, World!”.
        ```
5.  **Define expected outputs verbatim when possible:**
    *   If you expect a JSON schema, embed it exactly:
        ```
        “Generate the following JSON schema under `{PROJECT_ROOT}/schemas/user.json`:
        \`\`\`json
        {
          "$schema": "http://json-schema.org/draft-07/schema#",
          "title": "User",
          "type": "object",
          "properties": {
            "id": { "type": "string", "format": "uuid" },
            "email": { "type": "string", "format": "email" },
            "createdAt": { "type": "string", "format": "date-time" }
          },
          "required": ["id", "email", "createdAt"]
        }
        \`\`\`
        “
        ```

### 3.2. Example of Hard‐Directive Prompt

```
PROMPT:
• Create a Python virtual environment in {PROJECT_ROOT} named {VENV_NAME}.
  Command: python3 -m venv {VENV_NAME}
• Activate the virtual environment.
• Install the following packages: {PACKAGE_LIST}.
• Create a .env file at the project root containing:
  DATABASE_URL={DB_URL}
  SECRET_KEY={SECRET_KEY}
• Write a config.py module that reads DATABASE_URL and SECRET_KEY from environment variables and raises an error if either is missing.
• Generate a unit test under tests/test_config.py that verifies the error is raised when DATABASE_URL is absent.
MUST NOT use any package other than those specified.

OUTPUT:
Only provide the sequence of shell commands and file contents as code blocks. Do not include additional narrative or analysis.
```

## 4. Combining All Three Requirements

When constructing or revising any prompt in your system:

1.  **Declare all parameters up‐front.**
    *   List each placeholder name, its purpose, and any default or example value in a "Parameter Reference" section if the prompt is complex.
2.  **Adopt the ReAct skeleton for any multi‐step or iterative tasks.**
    *   Always show “Thought: / Action: / Observation:” until you reach a final answer for these types of tasks.
3.  **Write each instruction as an imperative, unambiguous directive.**
    *   Number each step, use “MUST,” “Do not,” “Ensure,” etc.
    *   Prohibit any deviation explicitly.

### 4.1. Full‐Stack Prompt Example (Illustrating combination of principles)

```
Parameters:
───────────
{PROJECT_ROOT} – Absolute path to the project’s root directory.
{VENV_NAME} – Name for the Python virtual environment (e.g., “venv”).
{PACKAGE_LIST} – Comma-separated list of required Python packages (e.g., “fastapi, uvicorn, pydantic”).
{DB_URL} – PostgreSQL connection URL (e.g., “postgresql://user:pass@localhost:5432/dbname”).
{SECRET_KEY} – A 32-character random string for JWT signing.

Prompt:
You are an expert Python backend developer. Your task is to set up a FastAPI project.
MUST follow these steps precisely:
1.  Create a Python virtual environment in `{PROJECT_ROOT}` named `{VENV_NAME}`.
    Command: `python3 -m venv {VENV_NAME}`
2.  Activate the virtual environment.
    Command: `source {PROJECT_ROOT}/{VENV_NAME}/bin/activate`
3.  Install dependencies: `{PACKAGE_LIST}`.
    Command: `pip install {PACKAGE_LIST}`
4.  Create a `.env` file at `{PROJECT_ROOT}/.env` with the following content:
    DATABASE_URL={DB_URL}
    SECRET_KEY={SECRET_KEY}
5.  Write a `config.py` module at `{PROJECT_ROOT}/src/config.py`.
    *   This module MUST read `DATABASE_URL` and `SECRET_KEY` from environment variables.
    *   It MUST use Pydantic for settings management.
    *   It MUST raise a `RuntimeError` if either variable is missing.
6.  Generate a unit test under `{PROJECT_ROOT}/tests/test_config.py`.
    *   This test MUST verify that the `RuntimeError` is raised when `DATABASE_URL` is absent from the environment.
    *   MUST NOT use any package other than `pytest` and standard library modules for this test.

Output Expectations:
Provide your response using the ReAct format (Thought/Action/Observation).
The `Action` should specify the command to run or the file to write.
Example Action for writing a file:
Action: write_file Path: {PROJECT_ROOT}/src/config.py Content: \`\`\`python
# ... python code ...
\`\`\`
The final answer should summarize the files created and actions taken.
Ensure all code is compatible with Python 3.10+.
Do NOT deviate from FastAPI or Pydantic usage for the config module.

Expected ReAct flow:
Thought: I need to set up a Python backend with FastAPI, environment variables, and config validation. First, I will create the virtual environment.
Action: run_command Command: python3 -m venv {PROJECT_ROOT}/{VENV_NAME}
Observation: Virtual environment created successfully.

Thought: Activate the virtual environment.
Action: run_command Command: source {PROJECT_ROOT}/{VENV_NAME}/bin/activate
Observation: Virtual environment activated.

Thought: Install dependencies.
Action: run_command Command: pip install {PACKAGE_LIST}
Observation: Packages installed without errors.

Thought: Create .env at project root.
Action: write_file Path: {PROJECT_ROOT}/.env Content:
DATABASE_URL={DB_URL}
SECRET_KEY={SECRET_KEY}
Observation: File written successfully.

Thought: Write config.py to validate environment variables using Pydantic.
Action: write_file Path: {PROJECT_ROOT}/src/config.py Content: \`\`\`python
import os
from pydantic import BaseSettings, ValidationError

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

try:
    settings = Settings()
except ValidationError as e:
    raise RuntimeError(f"Missing required environment variables: {e}")

# Example usage (optional, for testing)
# if __name__ == "__main__":
#     print(f"Database URL: {settings.DATABASE_URL}")
#     print(f"Secret Key: Loaded")
\`\`\`
Observation: File written successfully.

Thought: Generate a unit test for missing DATABASE_URL.
Action: write_file Path: {PROJECT_ROOT}/tests/test_config.py Content: \`\`\`python
import os
import pytest

def test_missing_database_url(monkeypatch):
    # Ensure DATABASE_URL is not set for this test
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Set a dummy SECRET_KEY as it's also required by Settings
    monkeypatch.setenv("SECRET_KEY", "dummy_test_secret_key_1234567890")

    with pytest.raises(RuntimeError) as excinfo:
        # Attempt to import config, which will load settings and trigger validation
        from src import config
        # If settings were successfully loaded without raising RuntimeError (e.g. if module was already loaded and not reloaded)
        # we might need to explicitly try to access settings again or reload the module.
        # For simplicity, assuming direct import triggers it. A more robust test might involve module reloading.
        # config.settings # Accessing it if not automatically loaded
    assert "Missing required environment variables" in str(excinfo.value)

def test_all_variables_present(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/testdb")
    monkeypatch.setenv("SECRET_KEY", "another_dummy_secret_key_for_test")

    try:
        from importlib import reload # Python 3.4+
        from src import config
        reload(config) # Reload to pick up new env vars
        assert config.settings.DATABASE_URL == "postgresql://test:test@localhost/testdb"
        assert config.settings.SECRET_KEY == "another_dummy_secret_key_for_test"
    except RuntimeError:
        pytest.fail("RuntimeError raised even when all variables are present.")
\`\`\`
Observation: File written successfully.

Final Answer:
“Completed environment setup, config validation module, and unit test. All files are located under {PROJECT_ROOT} as described.
- Virtual environment '{VENV_NAME}' created.
- Dependencies '{PACKAGE_LIST}' installed.
- '{PROJECT_ROOT}/.env' created.
- '{PROJECT_ROOT}/src/config.py' created with Pydantic settings.
- '{PROJECT_ROOT}/tests/test_config.py' created with tests for config validation.
No further steps required.”
```

## 5. Implementation Checklist

Before you deploy these guidelines, verify:

- [ ] All existing prompts use `{UPPER_SNAKE_CASE_PLACEHOLDER}` not hard‐coded values.
- [ ] Every multi‐step prompt follows the ReAct format exactly (Thought/Action/Observation cycles) in its output.
- [ ] All instructions within prompts are phrased imperatively and include “MUST,” “Do not,” or explicit numbering where appropriate.
- [ ] No extra narrative or hedging language remains in prompt instructions (e.g., “You might,” “Consider,” “Perhaps”).
- [ ] A parameter reference block appears at the top of every complex prompt.
