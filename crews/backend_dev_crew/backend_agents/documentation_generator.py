# crews/backend_dev_crew/backend_agents/documentation_generator.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class DocumentationGenerator(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="documentation_generator", role="DocumentationGenerator - Auto-generate API documentation.", logger=logger, db=db, model_name_override=model_name_override)
