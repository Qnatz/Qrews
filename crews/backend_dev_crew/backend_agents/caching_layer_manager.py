# crews/backend_dev_crew/backend_agents/caching_layer_manager.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class CachingLayerManager(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="caching_layer_manager", role="CachingLayerManager - Integrate a caching solution.", logger=logger, db=db, model_name_override=model_name_override)
