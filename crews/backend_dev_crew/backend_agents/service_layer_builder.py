# crews/backend_dev_crew/backend_agents/service_layer_builder.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class ServiceLayerBuilder(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="service_layer_builder", role="ServiceLayerBuilder - Implement business logic on top of the DAL.", logger=logger, db=db, model_name_override=model_name_override)
