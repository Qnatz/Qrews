# crews/backend_dev_crew/backend_agents/data_access_layer_builder.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class DataAccessLayerBuilder(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="data_access_layer_builder", role="DataAccessLayerBuilder - Wrap raw ORM calls in a clean, reusable DAL interface.", logger=logger, db=db, model_name_override=model_name_override)
