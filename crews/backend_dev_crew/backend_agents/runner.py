# crews/backend_dev_crew/backend_agents/runner.py
from utils.general_utils import Logger
from utils.database import Database
from utils.context_handler import ProjectContext

# Import all 20 backend sub-agent classes
from .config_manager import ConfigManager
from .database_model_designer import DatabaseModelDesigner
from .migration_generator import MigrationGenerator
from .data_access_layer_builder import DataAccessLayerBuilder
from .service_layer_builder import ServiceLayerBuilder
from .api_endpoint_controller_generator import ApiEndpointControllerGenerator
from .auth_and_authorization_manager import AuthAndAuthorizationManager
from .caching_layer_manager import CachingLayerManager
from .background_jobs_manager import BackgroundJobsManager
from .message_queue_integrator import MessageQueueIntegrator
from .storage_service_manager import StorageServiceManager
from .email_notification_service import EmailNotificationService
from .error_handling_and_logging import ErrorHandlingAndLogging
from .monitoring_and_metrics_integrator import MonitoringAndMetricsIntegrator
from .security_and_hardening import SecurityAndHardening
from .performance_optimizer import PerformanceOptimizer
from .documentation_generator import DocumentationGenerator
from .testing_suite_generator import TestingSuiteGenerator
from .deployment_descriptor_generator import DeploymentDescriptorGenerator
from .maintenance_and_migration_scheduler import MaintenanceAndMigrationScheduler

class BackendCrewRunner:
    def __init__(self, logger: Logger, db: Database = None, sub_agent_model_config: dict = None):
        self.logger = logger
        self.db = db
        self.model_config = sub_agent_model_config if sub_agent_model_config else {}
        self.logger.log(f"[BackendCrewRunner] Initializing with model config keys: {list(self.model_config.keys())}", "BackendCrewRunner")

        # Instantiate all 20 sub-agents
        self.config_manager = ConfigManager(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("config_manager")
        )
        self.database_model_designer = DatabaseModelDesigner(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("database_model_designer")
        )
        self.migration_generator = MigrationGenerator(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("migration_generator")
        )
        self.data_access_layer_builder = DataAccessLayerBuilder(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("data_access_layer_builder")
        )
        self.service_layer_builder = ServiceLayerBuilder(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("service_layer_builder")
        )
        self.api_endpoint_controller_generator = ApiEndpointControllerGenerator(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("api_endpoint_controller_generator")
        )
        self.auth_and_authorization_manager = AuthAndAuthorizationManager(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("auth_and_authorization_manager")
        )
        self.caching_layer_manager = CachingLayerManager(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("caching_layer_manager")
        )
        self.background_jobs_manager = BackgroundJobsManager(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("background_jobs_manager")
        )
        self.message_queue_integrator = MessageQueueIntegrator(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("message_queue_integrator")
        )
        self.storage_service_manager = StorageServiceManager(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("storage_service_manager")
        )
        self.email_notification_service = EmailNotificationService(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("email_notification_service")
        )
        self.error_handling_and_logging = ErrorHandlingAndLogging(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("error_handling_and_logging")
        )
        self.monitoring_and_metrics_integrator = MonitoringAndMetricsIntegrator(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("monitoring_and_metrics_integrator")
        )
        self.security_and_hardening = SecurityAndHardening(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("security_and_hardening")
        )
        self.performance_optimizer = PerformanceOptimizer(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("performance_optimizer")
        )
        self.documentation_generator = DocumentationGenerator(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("documentation_generator")
        )
        self.testing_suite_generator = TestingSuiteGenerator(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("testing_suite_generator")
        )
        self.deployment_descriptor_generator = DeploymentDescriptorGenerator(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("deployment_descriptor_generator")
        )
        self.maintenance_and_migration_scheduler = MaintenanceAndMigrationScheduler(
            logger=self.logger, db=self.db, model_name_override=self.model_config.get("maintenance_and_migration_scheduler")
        )
        self.logger.log(f"[BackendCrewRunner] All 20 sub-agents initialized.", "BackendCrewRunner")

    def execute(self, project_context: ProjectContext) -> dict:
        self.logger.log(f"[BackendCrewRunner] Starting execution for project: {project_context.project_name}", "BackendCrewRunner")

        artifacts = {}
        overall_status = "complete"
        accumulated_errors = []
        accumulated_warnings = []

        def _process_agent_result(agent_name: str, result: dict, artifact_key: str, critical_step: bool = False) -> bool:
            nonlocal overall_status

            if result is None:
                self.logger.log(f"[{agent_name}] returned None. Treating as error.", "ERROR", "BackendCrewRunner")
                error_message = f"{agent_name} returned None result."
                accumulated_errors.append(error_message)
                overall_status = "error"
                if critical_step:
                    self.logger.log(f"[BackendCrewRunner] Critical step {agent_name} failed. Halting execution.", "ERROR", "BackendCrewRunner")
                    return False
                return True

            structured_output = result.get("structured_output")
            artifacts[artifact_key] = structured_output

            warnings = result.get("warnings")
            if warnings and isinstance(warnings, list):
                accumulated_warnings.extend(warnings)
                for warning in warnings:
                    self.logger.log(f"[{agent_name}] Warning: {warning}", "WARNING", "BackendCrewRunner")
            elif warnings:
                 accumulated_warnings.append(str(warnings))
                 self.logger.log(f"[{agent_name}] Warning: {warnings}", "WARNING", "BackendCrewRunner")

            agent_status = result.get("status", "unknown")
            if agent_status != "complete":
                error_message = result.get("error") or result.get("message", f"{agent_name} failed with unknown error.")
                if not isinstance(error_message, str): error_message = str(error_message)
                accumulated_errors.append(f"{agent_name}: {error_message}")
                self.logger.log(f"[{agent_name}] Failed. Error: {error_message}", "ERROR", "BackendCrewRunner")
                overall_status = "error"
                if critical_step:
                    self.logger.log(f"[BackendCrewRunner] Critical step {agent_name} failed. Halting execution.", "ERROR", "BackendCrewRunner")
                    return False

            summary = result.get("summary", "No summary provided.")
            if not isinstance(summary, str): summary = str(summary)
            self.logger.log(f"[{agent_name}] completed with status: {agent_status}. Summary: {summary[:200]}...", "BackendCrewRunner")
            return True

        # Agents 1-5 (Critical foundational steps)
        config_manager_inputs = {"db_url_example": getattr(project_context, 'db_url_example', "postgresql://user:pass@host:port/dbname"),} # Simplified for brevity
        config_manager_result = self.config_manager.run(project_context, crew_inputs=config_manager_inputs)
        if not _process_agent_result("ConfigManager", config_manager_result, "config_manager_output", critical_step=True): return {"status": "error", "errors": accumulated_errors, "warnings": accumulated_warnings, "backend_artifacts": artifacts}
        project_context.config_module_path = artifacts.get("config_manager_output", {}).get("config_file_path", "") # Example of using artifact

        db_model_designer_inputs = {"key_data_entities_list": getattr(project_context.analysis, 'key_entities_list_str', ""),}
        db_model_designer_result = self.database_model_designer.run(project_context, crew_inputs=db_model_designer_inputs)
        if not _process_agent_result("DatabaseModelDesigner", db_model_designer_result, "database_model_designer_output", critical_step=True): return {"status": "error", "errors": accumulated_errors, "warnings": accumulated_warnings, "backend_artifacts": artifacts}
        project_context.model_definitions_path = artifacts.get("database_model_designer_output", {}).get("model_definitions_path", "")
        project_context.models_dir_path = artifacts.get("database_model_designer_output", {}).get("models_dir_path", "src/models") # Store for later use

        migration_generator_inputs = {"model_definitions_path": project_context.model_definitions_path,}
        migration_generator_result = self.migration_generator.run(project_context, crew_inputs=migration_generator_inputs)
        if not _process_agent_result("MigrationGenerator", migration_generator_result, "migration_generator_output", critical_step=True): return {"status": "error", "errors": accumulated_errors, "warnings": accumulated_warnings, "backend_artifacts": artifacts}
        project_context.migrations_dir_path = artifacts.get("migration_generator_output", {}).get("migrations_dir_path", "src/migrations")

        dal_builder_inputs = {"model_definitions_path": project_context.model_definitions_path,}
        dal_builder_result = self.data_access_layer_builder.run(project_context, crew_inputs=dal_builder_inputs)
        if not _process_agent_result("DataAccessLayerBuilder", dal_builder_result, "data_access_layer_builder_output", critical_step=True): return {"status": "error", "errors": accumulated_errors, "warnings": accumulated_warnings, "backend_artifacts": artifacts}
        project_context.dal_classes_info = artifacts.get("data_access_layer_builder_output", {}).get("dal_summary", "")
        project_context.dal_dir_path = artifacts.get("data_access_layer_builder_output", {}).get("dal_dir_path", "src/dal")

        service_builder_inputs = {"dal_classes_info": project_context.dal_classes_info, "domain_use_cases": getattr(project_context.analysis, 'domain_use_cases_str', ""),}
        service_builder_result = self.service_layer_builder.run(project_context, crew_inputs=service_builder_inputs)
        if not _process_agent_result("ServiceLayerBuilder", service_builder_result, "service_layer_builder_output", critical_step=True): return {"status": "error", "errors": accumulated_errors, "warnings": accumulated_warnings, "backend_artifacts": artifacts}
        project_context.service_layer_info = artifacts.get("service_layer_builder_output", {}).get("service_summary", "")
        project_context.services_dir_path = artifacts.get("service_layer_builder_output", {}).get("services_dir_path", "src/services")

        # Agents 6-10 (Application features and core infrastructure)
        api_controller_inputs = {"service_layer_info": project_context.service_layer_info, "api_route_definitions": getattr(project_context.analysis, 'api_routes_str', ""),}
        api_controller_result = self.api_endpoint_controller_generator.run(project_context, crew_inputs=api_controller_inputs)
        if not _process_agent_result("ApiEndpointControllerGenerator", api_controller_result, "api_endpoint_controller_generator_output", critical_step=False): pass # Decide if critical
        project_context.controllers_dir_path = artifacts.get("api_endpoint_controller_generator_output", {}).get("controllers_dir_path", "src/controllers")

        auth_manager_inputs = {"user_model_path": artifacts.get("database_model_designer_output", {}).get("user_model_file_path", ""), "dal_info": project_context.dal_classes_info,}
        auth_manager_result = self.auth_and_authorization_manager.run(project_context, crew_inputs=auth_manager_inputs)
        if not _process_agent_result("AuthAndAuthorizationManager", auth_manager_result, "auth_and_authorization_manager_output", critical_step=False): pass

        caching_manager_inputs = {"service_methods_to_cache": getattr(project_context.analysis, 'methods_to_cache_str', ""),}
        caching_manager_result = self.caching_layer_manager.run(project_context, crew_inputs=caching_manager_inputs)
        if not _process_agent_result("CachingLayerManager", caching_manager_result, "caching_layer_manager_output", critical_step=False): pass

        background_jobs_inputs = {"example_job_definitions": getattr(project_context.analysis, 'background_jobs_str', ""),}
        background_jobs_result = self.background_jobs_manager.run(project_context, crew_inputs=background_jobs_inputs)
        if not _process_agent_result("BackgroundJobsManager", background_jobs_result, "background_jobs_manager_output", critical_step=False): pass

        message_queue_inputs = {"topics_or_exchanges_to_define": getattr(project_context.analysis, 'message_topics_str', ""),}
        message_queue_result = self.message_queue_integrator.run(project_context, crew_inputs=message_queue_inputs)
        if not _process_agent_result("MessageQueueIntegrator", message_queue_result, "message_queue_integrator_output", critical_step=False): pass

        # Agents 11-15 (Supporting services and operational aspects)
        self.logger.log(f"[BackendCrewRunner] Running StorageServiceManager...", "BackendCrewRunner")
        storage_service_inputs = {"storage_service_type": getattr(project_context.tech_stack, 'storage_service_type', "LocalFileSystem")}
        storage_service_result = self.storage_service_manager.run(project_context, crew_inputs=storage_service_inputs)
        if not _process_agent_result("StorageServiceManager", storage_service_result, "storage_service_output", critical_step=False): pass

        self.logger.log(f"[BackendCrewRunner] Running EmailNotificationService...", "BackendCrewRunner")
        email_service_inputs = {"email_service_provider": getattr(project_context.tech_stack, 'email_service_provider', "SMTP")}
        email_service_result = self.email_notification_service.run(project_context, crew_inputs=email_service_inputs)
        if not _process_agent_result("EmailNotificationService", email_service_result, "email_notification_service_output", critical_step=False): pass

        self.logger.log(f"[BackendCrewRunner] Running ErrorHandlingAndLogging...", "BackendCrewRunner")
        error_logging_inputs = {"logging_library": getattr(project_context.tech_stack, 'logging_library', "logging")}
        error_logging_result = self.error_handling_and_logging.run(project_context, crew_inputs=error_logging_inputs)
        if not _process_agent_result("ErrorHandlingAndLogging", error_logging_result, "error_handling_and_logging_output", critical_step=True): return {"status": "error", "errors": accumulated_errors, "warnings": accumulated_warnings, "backend_artifacts": artifacts}

        self.logger.log(f"[BackendCrewRunner] Running MonitoringAndMetricsIntegrator...", "BackendCrewRunner")
        monitoring_inputs = {"metrics_system": getattr(project_context.tech_stack, 'metrics_system', "Prometheus")}
        monitoring_result = self.monitoring_and_metrics_integrator.run(project_context, crew_inputs=monitoring_inputs)
        if not _process_agent_result("MonitoringAndMetricsIntegrator", monitoring_result, "monitoring_and_metrics_integrator_output", critical_step=False): pass

        self.logger.log(f"[BackendCrewRunner] Running SecurityAndHardening...", "BackendCrewRunner")
        security_inputs = {} # Relies mostly on project_context and default prompt values
        security_result = self.security_and_hardening.run(project_context, crew_inputs=security_inputs)
        if not _process_agent_result("SecurityAndHardening", security_result, "security_and_hardening_output", critical_step=True): return {"status": "error", "errors": accumulated_errors, "warnings": accumulated_warnings, "backend_artifacts": artifacts}

        # Agents 16-20 (Optimization, documentation, testing, deployment, maintenance)
        self.logger.log(f"[BackendCrewRunner] Running PerformanceOptimizer...", "BackendCrewRunner")
        performance_inputs = {"dal_code_path": project_context.dal_dir_path, "service_code_path": project_context.services_dir_path}
        performance_result = self.performance_optimizer.run(project_context, crew_inputs=performance_inputs)
        if not _process_agent_result("PerformanceOptimizer", performance_result, "performance_optimizer_output"): pass

        self.logger.log(f"[BackendCrewRunner] Running DocumentationGenerator...", "BackendCrewRunner")
        doc_gen_inputs = {
            "controller_code_path": project_context.controllers_dir_path,
            "model_definitions_path": project_context.model_definitions_path,
            "service_code_path": project_context.services_dir_path,
        }
        doc_gen_result = self.documentation_generator.run(project_context, crew_inputs=doc_gen_inputs)
        if not _process_agent_result("DocumentationGenerator", doc_gen_result, "documentation_generator_output"): pass
        project_context.openapi_spec_path = artifacts.get("documentation_generator_output", {}).get("openapi_spec_path", "")

        self.logger.log(f"[BackendCrewRunner] Running TestingSuiteGenerator...", "BackendCrewRunner")
        testing_inputs = {
            "controller_code_path": project_context.controllers_dir_path,
            "service_code_path": project_context.services_dir_path,
            "dal_code_path": project_context.dal_dir_path,
            "testing_framework": getattr(project_context.tech_stack, 'testing_framework', "pytest" if "python" in project_context.tech_stack.backend.lower() else "jest"),
        }
        testing_result = self.testing_suite_generator.run(project_context, crew_inputs=testing_inputs)
        if not _process_agent_result("TestingSuiteGenerator", testing_result, "testing_suite_generator_output"): pass
        project_context.tests_dir_path = artifacts.get("testing_suite_generator_output", {}).get("tests_dir_path", "tests")


        self.logger.log(f"[BackendCrewRunner] Running DeploymentDescriptorGenerator...", "BackendCrewRunner")
        deployment_inputs = {
            "application_port_placeholder": artifacts.get("config_manager_output", {}).get("api_port", "8000"), # Example
        }
        deployment_result = self.deployment_descriptor_generator.run(project_context, crew_inputs=deployment_inputs)
        if not _process_agent_result("DeploymentDescriptorGenerator", deployment_result, "deployment_descriptor_generator_output"): pass

        self.logger.log(f"[BackendCrewRunner] Running MaintenanceAndMigrationScheduler...", "BackendCrewRunner")
        maintenance_inputs = {} # Relies on project_context and prompt defaults
        maintenance_result = self.maintenance_and_migration_scheduler.run(project_context, crew_inputs=maintenance_inputs)
        if not _process_agent_result("MaintenanceAndMigrationScheduler", maintenance_result, "maintenance_and_migration_scheduler_output"): pass

        self.logger.log(f"[BackendCrewRunner] Completed all agent executions. Overall status: {overall_status}", "BackendCrewRunner")
        return {
            "status": overall_status,
            "errors": accumulated_errors,
            "warnings": accumulated_warnings,
            "backend_artifacts": artifacts
        }
