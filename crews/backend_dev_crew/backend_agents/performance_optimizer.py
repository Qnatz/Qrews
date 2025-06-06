# crews/backend_dev_crew/backend_agents/performance_optimizer.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class PerformanceOptimizer(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="performance_optimizer", role="PerformanceOptimizer - Identify and implement basic performance improvements.", logger=logger, db=db, model_name_override=model_name_override)
