# crews/backend_dev_crew/backend_agents/monitoring_and_metrics_integrator.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class MonitoringAndMetricsIntegrator(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="monitoring_and_metrics_integrator", role="MonitoringAndMetricsIntegrator - Instrument app for metrics and health checks.", logger=logger, db=db, model_name_override=model_name_override)
