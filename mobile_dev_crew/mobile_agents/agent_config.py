# mobile_developer_crew/agent_config.py
import json
import os

# Assuming agent_config.json is in the same directory as this script
AGENT_CONFIG_JSON_PATH = os.path.join(os.path.dirname(__file__), "agent_config.json")

def load_agent_config_from_json() -> dict:
    """Loads the agent model configuration from the agent_config.json file."""
    try:
        with open(AGENT_CONFIG_JSON_PATH, 'r') as f:
            config = json.load(f)
            # print(f"Loaded agent config from {AGENT_CONFIG_JSON_PATH}: {config}")
            return config
    except FileNotFoundError:
        print(f"ERROR: Agent configuration file not found at {AGENT_CONFIG_JSON_PATH}")
        return {} # Return empty dict if file not found
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from {AGENT_CONFIG_JSON_PATH}")
        return {} # Return empty dict if JSON is malformed
    except Exception as e:
        print(f"ERROR: Unexpected error loading agent config: {e}")
        return {}

if __name__ == '__main__':
    configs = load_agent_config_from_json()
    if configs:
        print("Successfully loaded agent configurations:")
        for agent, model in configs.items():
            print(f"- {agent}: {model}")
    else:
        print("Failed to load agent configurations.")
