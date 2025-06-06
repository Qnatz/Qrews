# crews/backend_dev_crew/backend_agents/security_and_hardening.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class SecurityAndHardening(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="security_and_hardening", role="SecurityAndHardening - Enforce security best practices.", logger=logger, db=db, model_name_override=model_name_override)
