# crews/backend_dev_crew/backend_agents/testing_suite_generator.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class TestingSuiteGenerator(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="testing_suite_generator", role="TestingSuiteGenerator - Create unit, integration, and smoke tests.", logger=logger, db=db, model_name_override=model_name_override)
