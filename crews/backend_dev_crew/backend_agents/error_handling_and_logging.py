# crews/backend_dev_crew/backend_agents/error_handling_and_logging.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class ErrorHandlingAndLogging(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="error_handling_and_logging", role="ErrorHandlingAndLogging - Standardize error formats and implement centralized logging.", logger=logger, db=db, model_name_override=model_name_override)
