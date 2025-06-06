# crews/backend_dev_crew/backend_agents/storage_service_manager.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class StorageServiceManager(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="storage_service_manager", role="StorageServiceManager - Abstract file storage.", logger=logger, db=db, model_name_override=model_name_override)
