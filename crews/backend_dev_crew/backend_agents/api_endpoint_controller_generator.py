# crews/backend_dev_crew/backend_agents/api_endpoint_controller_generator.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class ApiEndpointControllerGenerator(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="api_endpoint_controller_generator", role="ApiEndpointControllerGenerator - Expose service methods via REST (or GraphQL) endpoints.", logger=logger, db=db, model_name_override=model_name_override)
