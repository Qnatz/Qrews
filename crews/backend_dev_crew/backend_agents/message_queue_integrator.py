# crews/backend_dev_crew/backend_agents/message_queue_integrator.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class MessageQueueIntegrator(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="message_queue_integrator", role="MessageQueueIntegrator - Integrate with Pub/Sub or message broker.", logger=logger, db=db, model_name_override=model_name_override)
