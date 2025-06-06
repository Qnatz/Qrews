# crews/backend_dev_crew/backend_agents/email_notification_service.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class EmailNotificationService(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="email_notification_service", role="EmailNotificationService - Configure transactional email sending.", logger=logger, db=db, model_name_override=model_name_override)
