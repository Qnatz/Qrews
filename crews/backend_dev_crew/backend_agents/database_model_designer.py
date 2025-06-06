# crews/backend_dev_crew/backend_agents/database_model_designer.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class DatabaseModelDesigner(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="database_model_designer", role="DatabaseModelDesigner - Design the core domain models/tables for primary entities.", logger=logger, db=db, model_name_override=model_name_override)
