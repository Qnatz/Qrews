# crews/backend_dev_crew/backend_agents/config_manager.py
from . import BackendSubAgent # Imports BackendSubAgent from the __init__.py in the same directory
from utils.general_utils import Logger
from utils.database import Database

class ConfigManager(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(
            name="config_manager",
            role="ConfigManager - Centralize and validate all runtime and environment configuration.",
            logger=logger,
            db=db,
            model_name_override=model_name_override
        )
