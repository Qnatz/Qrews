-- -----------------------------------------------------------------------------
-- Agents Table: Stores information about each agent.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,  -- Unique identifier for the agent (e.g., "code_writer")
    role TEXT NOT NULL,          -- The agent's role (e.g., "Code Writer")
    current_task TEXT,          -- Description of the task the agent is currently working on
    model_used TEXT,            -- Name of the LLM model being used (e.g., "gemini-2.0-flash")
    api_key TEXT,               -- API Key for the specific agent
    creation_time REAL,         -- Timestamp when the agent was created or last updated
    description TEXT,            -- Description for the agent.
    FOREIGN KEY (model_used) REFERENCES models(model_id) -- Link to models table
);

-- -----------------------------------------------------------------------------
-- Projects Table: Stores information about each project.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    project_name TEXT PRIMARY KEY,  -- Unique name of the project
    objective TEXT NOT NULL,       -- The overall objective of the project
    project_type TEXT,            -- Type of project (e.g., "fullstack", "backend")
    start_time REAL,             -- Timestamp when the project started
    end_time REAL,               -- Timestamp when the project ended (or NULL if still in progress)
    status TEXT,                 -- Current status of the project (e.g., "planning")
    user_input TEXT,            -- Original prompt.
    model_used TEXT,                -- track model
    FOREIGN KEY (model_used) REFERENCES models(model_id)
);

-- -----------------------------------------------------------------------------
-- Memory Table: Stores agent memories with vector embeddings.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS memory (
    item_id TEXT PRIMARY KEY,  -- Unique ID for this memory
    agent_id TEXT NOT NULL,       -- ID of the agent that created this memory
    role TEXT,                    -- The entity's role (e.g., "user", "system", "assistant")
    content TEXT NOT NULL,        -- The actual content of the memory
    embedding BLOB NOT NULL,      -- The vector embedding of the content
    creation_time REAL,        -- The time this was created

    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) -- Link to agents table
);

-- Index for efficient retrieval of memories by agent
CREATE INDEX idx_memory_agent_id ON memory (agent_id);

-- -----------------------------------------------------------------------------
-- Feedback Table: Stores feedback on agent outputs and evaluation results.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique ID for the feedback entry
    agent_id TEXT NOT NULL,                         -- ID of the agent that generated the output
    item_id TEXT NOT NULL,                      --  ID of the project, memory, code.
    timestamp REAL,                           -- Timestamp when the feedback was received
    feedback_type TEXT,                         -- Type of feedback (e.g., "test_result", "code_quality")
    message TEXT,                               -- The feedback message
    score REAL,                               -- A numerical score (if applicable)
    related_task TEXT,                          -- What task this feedback is related to
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),  -- Link to agents table
    FOREIGN KEY (item_id) REFERENCES memory(item_id)        -- Link to memory table (if applicable)
);

-- Index for efficient retrieval of feedback by agent and item
CREATE INDEX idx_feedback_agent_item ON feedback (agent_id, item_id);

-- -----------------------------------------------------------------------------
-- Tools Table: Stores information about available tools and their descriptions.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tools (
    tool_name TEXT PRIMARY KEY,   -- Unique name of the tool (e.g., "read_file")
    description TEXT,             -- Description of the tool's purpose and usage
    parameters TEXT,              -- JSON string describing the tool's parameters
    used_by_agent TEXT,             -- Who used the tool.
    FOREIGN KEY (used_by_agent) REFERENCES agents(agent_id) -- Link to which agent has used it.
);

-- -----------------------------------------------------------------------------
-- Ctags Table: Stores ctags data for symbol lookup.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ctags (
    symbol TEXT,                    -- The name of the symbol (e.g., function name)
    file_path TEXT,                 -- The path to the file where the symbol is defined
    line_number INTEGER,            -- The line number where the symbol is defined
    pattern TEXT,                   -- The Exuberant Ctags pattern string (optional)
    PRIMARY KEY (symbol, file_path, line_number) -- Composite primary key
);

CREATE TABLE IF NOT EXISTS models (
  model_id TEXT PRIMARY KEY,   -- The Model ID "gemini-2.0-pro"
  model_name TEXT,               -- the Model Name Gemini 2.0 Pro
  max_tokens INTEGER,            -- token limitations
  supports_tools BOOLEAN,       -- whether it has tools
  cost_per_1k_tokens REAL       -- cost per 1000 tokens
);

INSERT or IGNORE INTO models (model_id, model_name, max_tokens, supports_tools, cost_per_1k_tokens) VALUES
  ('gemini-2.0-flash', 'Gemini 2.0 Flash', 8192, TRUE, 0.075),
  ('gemini-1.5-pro', 'Gemini 1.5 Pro', 2048, TRUE, 0.125),
  ('deepseek-coder-1.3', 'DeepSeek Coder 1.3 (Local)', 8192, TRUE, 0.0), -- Assuming it supports tools
  ('deepseek-r1', 'DeepSeek R1 (Local)', 8192, TRUE, 0.0); -- Assuming it supports tools and a local model
