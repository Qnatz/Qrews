# crews/backend_dev_crew/backend_agents/migration_generator.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class MigrationGenerator(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="migration_generator", role="MigrationGenerator - Create and version-control database migrations.", logger=logger, db=db, model_name_override=model_name_override)
