# crews/backend_dev_crew/backend_agents/deployment_descriptor_generator.py
from . import BackendSubAgent
from utils.general_utils import Logger
from utils.database import Database
class DeploymentDescriptorGenerator(BackendSubAgent):
    def __init__(self, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name="deployment_descriptor_generator", role="DeploymentDescriptorGenerator - Produce Dockerfiles, K8s manifests, CI/CD config.", logger=logger, db=db, model_name_override=model_name_override)
