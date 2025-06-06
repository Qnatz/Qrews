# crews/backend_dev_crew/backend_agents/background_jobs_manager.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class BackgroundJobsManager(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="background_jobs_manager", role="BackgroundJobsManager - Offload tasks to a job queue.", logger=logger, db=db, model_name_override=model_name_override)
