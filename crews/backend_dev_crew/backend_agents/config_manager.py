# crews/backend_dev_crew/backend_agents/config_manager.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
from utils.context_handler import ProjectContext

class ConfigManager(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(
            name="config_manager", # This name MUST match the key in BACKEND_DEV_AGENT_PROMPTS
            role="ConfigManager - Centralize and validate all runtime and environment configuration.",
            logger=logger,
            db=db,
            model_name_override=model_name_override
        )

    # run method can be inherited from BackendSubAgent if no specific pre/post processing is needed
    # or overridden if specific crew_inputs need to be passed or outputs handled uniquely.
    # For now, assume it inherits run() and _enhance_prompt_context will be key.
