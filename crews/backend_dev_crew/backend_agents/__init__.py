# crews/backend_dev_crew/backend_agents/__init__.py
"""
Backend Development Sub-Agents package.
Contains individual specialized agents for backend tasks.
"""
import json
from agents.base_agent import Agent
from utils.general_utils import Logger
from utils.database import Database
from prompts.general_prompts import get_agent_prompt
from utils.context_handler import ProjectContext

class BackendSubAgent(Agent):
    def __init__(self, name, role, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name, role, logger, db=db)
        if model_name_override:
            self.current_model = model_name_override
            if hasattr(self, 'gemini_config'): # Check if gemini_config is initialized
                self.generation_config = self.gemini_config.get_generation_config(self.name)
            self.logger.log(f"BackendSubAgent {self.name} initialized. Model override: {self.current_model}", self.role)
        else:
            self.logger.log(f"BackendSubAgent {self.name} initialized. Using default model selection. Current model: {self.current_model}", self.role)

    def run(self, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
        # This run method structure should be preserved
        self.logger.log(f"[{self.name}] Executing BackendSubAgent run method with crew_inputs keys: {list(crew_inputs.keys()) if crew_inputs else 'None'}", self.role)
        analysis_data = project_context.analysis.model_dump() if project_context.analysis else {}
        prompt_render_context = {
            'ROLE': self.role, 'SPECIALTY': self.role,
            'PROJECT_NAME': project_context.project_name, 'OBJECTIVE': project_context.objective or "",
            'PROJECT_TYPE': project_context.analysis.project_type_confirmed if project_context.analysis else project_context.project_type,
            'CURRENT_DIR': project_context.current_dir or "/",
            'PROJECT_SUMMARY': project_context.project_summary or "",
            'ARCHITECTURE': project_context.architecture or "", 'PLAN': project_context.plan or "",
            'MEMORIES': project_context.project_summary or "No specific memories retrieved.",
            'TOOL_NAMES': [tool['name'] for tool in self.tools if 'name' in tool],
            'TOOLS': self.tools, 'ANALYSIS': analysis_data,
            'TECH_STACK': project_context.tech_stack.model_dump() if project_context.tech_stack else {},
            'crew_inputs': crew_inputs if crew_inputs else {}, # Pass along crew_inputs
        }
        prompt_render_context = self._enhance_prompt_context(prompt_render_context, project_context, crew_inputs)
        generated_prompt_str = get_agent_prompt(self.name, prompt_render_context)
        response_content = self._call_model(generated_prompt_str) if not self.tools else self._call_model_with_tools(generated_prompt_str)
        return self._parse_response(response_content, project_context)

    def _enhance_prompt_context(self, context: dict, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
        if crew_inputs is None: crew_inputs = {}

        # General Backend Context from project_context
        context['TECH_STACK_BACKEND_NAME'] = project_context.tech_stack.backend if project_context.tech_stack and project_context.tech_stack.backend else "Not Specified"
        context['TECH_STACK_DATABASE_NAME'] = project_context.tech_stack.database if project_context.tech_stack and project_context.tech_stack.database else "Not Specified"
        context['PROJECT_ROOT'] = context.get('CURRENT_DIR', getattr(project_context, "current_dir", "/app/backend"))

        file_ext = "py" # Default
        if "node" in (context['TECH_STACK_BACKEND_NAME'] or "").lower() or "express" in (context['TECH_STACK_BACKEND_NAME'] or "").lower():
            file_ext = "js"
        elif "java" in (context['TECH_STACK_BACKEND_NAME'] or "").lower() or "spring" in (context['TECH_STACK_BACKEND_NAME'] or "").lower():
            file_ext = "java"
        elif "go" in (context['TECH_STACK_BACKEND_NAME'] or "").lower():
            file_ext = "go"
        context['FILE_EXTENSION'] = getattr(project_context.tech_stack, 'file_extension', file_ext) if project_context.tech_stack and hasattr(project_context.tech_stack, 'file_extension') else file_ext

        # Common generic placeholders (can be overridden by agent-specific logic or crew_inputs)
        context['DATA_ENTITY_NAME_SINGULAR'] = str(crew_inputs.get('data_entity_name_singular', getattr(project_context, 'generic_data_entity_singular', "GenericEntity")))
        context['DATA_ENTITY_NAME_PLURAL'] = str(crew_inputs.get('data_entity_name_plural', getattr(project_context, 'generic_data_entity_plural', "GenericEntities")))
        context['ITEM_NAME_SINGULAR'] = str(crew_inputs.get('item_name_singular', getattr(project_context, 'generic_item_name', "Item")))
        context['BUSINESS_PROCESS_NAME'] = str(crew_inputs.get('business_process_name', getattr(project_context, 'generic_business_process', "Process")))
        context['METRIC_NAME'] = str(crew_inputs.get('metric_name', getattr(project_context, 'generic_metric_name', "Value")))


        # Agent-Specific Context Population
        agent_specific_dispatch = {
            "config_manager": lambda: {
                'DB_URL_EXAMPLE': str(crew_inputs.get('db_url_example', getattr(project_context, 'db_url_example', "postgresql://user:pass@host:port/dbname"))),
                'REDIS_URL_EXAMPLE': str(crew_inputs.get('redis_url_example', getattr(project_context, 'redis_url_example', "redis://host:port"))),
                'JWT_SECRET_EXAMPLE': str(crew_inputs.get('jwt_secret_example', getattr(project_context, 'jwt_secret_example', "your-jwt-secret"))),
                'LOG_LEVEL_EXAMPLE': str(crew_inputs.get('log_level_example', getattr(project_context, 'log_level_example', "info"))),
                'API_PORT_EXAMPLE': str(crew_inputs.get('api_port_example', getattr(project_context, 'api_port_example', "8000"))),
                'ENVIRONMENT_EXAMPLE': str(crew_inputs.get('environment_example', getattr(project_context, 'environment_example', "development"))),
            },
            "database_model_designer": lambda: {
                'DATABASE_NAMING_CONVENTIONS': str(crew_inputs.get('database_naming_conventions', getattr(project_context, 'database_naming_conventions', "snake_case_pluralized"))),
                'KEY_DATA_ENTITIES_LIST': ", ".join(crew_inputs.get('key_data_entities_list', getattr(project_context, 'key_data_entities_list', ["SampleEntity"]))),
                'ENTITY_RELATIONSHIPS_DESCRIPTION': str(crew_inputs.get('entity_relationships_description', getattr(project_context, 'entity_relationships_description', "No specific relationships."))),
                'MODELS_DIR_PATH': str(crew_inputs.get('models_dir_path', getattr(project_context, 'models_dir_path', "src/models"))),
            },
            "migration_generator": lambda: {
                'MODEL_DEFINITIONS_PATH': str(crew_inputs.get('model_definitions_path', getattr(project_context, 'model_definitions_path', 'src/models'))),
                'CURRENT_DB_SCHEMA_INFO': str(crew_inputs.get('current_db_schema_info', getattr(project_context, 'current_db_schema_info', 'No current schema info.'))),
                'DESIRED_MODEL_STATE_INFO': str(crew_inputs.get('desired_model_state_info', getattr(project_context, 'desired_model_state_info', ''))),
                'MIGRATIONS_DIR_PATH': str(crew_inputs.get('migrations_dir_path', getattr(project_context, 'migrations_dir_path', 'src/migrations'))),
            },
            "data_access_layer_builder": lambda: {
                'MODEL_DEFINITIONS_PATH': str(crew_inputs.get('model_definitions_path', getattr(project_context, 'model_definitions_path', 'src/models'))),
                'DAL_DIR_PATH': str(crew_inputs.get('dal_dir_path', getattr(project_context, 'dal_dir_path', 'src/repositories'))),
                'DATABASE_ERROR_TYPES': ", ".join(crew_inputs.get('database_error_types', getattr(project_context, 'database_error_types', ["Example.NotFound"]))),
            },
            "service_layer_builder": lambda: {
                'DAL_CLASSES_INFO': str(crew_inputs.get('dal_classes_info', getattr(project_context, 'dal_classes_info', 'DAL classes info not provided.'))),
                'DOMAIN_USE_CASES': "\n".join(crew_inputs.get('domain_use_cases', getattr(project_context, 'domain_use_cases', ["Process GenericEntity data."]))),
                'INPUT_SCHEMA_DEFINITIONS_PATH': str(crew_inputs.get('input_schema_definitions_path', getattr(project_context, 'input_schema_definitions_path', 'src/schemas/dtos'))),
                'SERVICES_DIR_PATH': str(crew_inputs.get('services_dir_path', getattr(project_context, 'services_dir_path', 'src/services'))),
                'TRANSACTION_SCOPE': str(crew_inputs.get('transaction_scope', "per_request")),
                'CACHE_TTL': str(crew_inputs.get('cache_ttl', "300s")),
                'NOTIFICATION_FLAG': str(crew_inputs.get('notification_flag', "false")),
            },
            "api_endpoint_controller_generator": lambda: {
                'SERVICE_LAYER_INFO': json.dumps(crew_inputs.get('service_layer_info', getattr(project_context, 'service_layer_info', {})), default=str),
                'API_ROUTE_DEFINITIONS': "\n".join(crew_inputs.get('api_route_definitions', getattr(project_context, 'api_route_definitions', ["GET /generic_items/{id}"]))),
                'CONTROLLERS_DIR_PATH': str(crew_inputs.get('controllers_dir_path', getattr(project_context, 'controllers_dir_path', "src/controllers"))),
                'REQUEST_DTO_PATH': str(crew_inputs.get('request_dto_path', getattr(project_context, 'request_dto_path', "src/dtos/request"))),
                'RESPONSE_DTO_PATH': str(crew_inputs.get('response_dto_path', getattr(project_context, 'response_dto_path', "src/dtos/response"))),
                'SHARED_ERROR_SCHEMAS_INFO': str(crew_inputs.get('shared_error_schemas_info', getattr(project_context, 'shared_error_schemas_info', "Use standard error handling."))),
            },
            "auth_and_authorization_manager": lambda: {
                'AUTH_STRATEGY': str(crew_inputs.get('auth_strategy', getattr(project_context, 'auth_strategy', "JWT"))),
                'USER_MODEL_PATH': str(crew_inputs.get('user_model_path', getattr(project_context, 'user_model_path', "src/models/user.py"))),
                'DAL_INFO': str(crew_inputs.get('dal_info', getattr(project_context, 'dal_info', "User DAL available."))),
                'AUTH_MODULE_PATH': str(crew_inputs.get('auth_module_path', getattr(project_context, 'auth_module_path', "src/auth"))),
                'ROLE_DEFINITIONS': "\n".join(crew_inputs.get('role_definitions', getattr(project_context, 'role_definitions', ["ADMIN", "USER"]))),
                'PERMISSION_DEFINITIONS': "\n".join(crew_inputs.get('permission_definitions', getattr(project_context, 'permission_definitions', ["read_data"]))),
                'PROTECTED_ROUTES_INFO': "\n".join(crew_inputs.get('protected_routes_info', getattr(project_context, 'protected_routes_info', ["/admin/* requires ADMIN"]))),
                'JWT_SECRET_EXAMPLE': str(crew_inputs.get('jwt_secret_example', getattr(project_context, 'jwt_secret_example', "config_jwt_secret_placeholder"))),
            },
            "caching_layer_manager": lambda: {
                'CACHE_TYPE': str(crew_inputs.get('cache_type', getattr(project_context, 'cache_type', "Redis"))),
                'CACHE_CONNECTION_URL_PLACEHOLDER': str(crew_inputs.get('cache_connection_url_placeholder', getattr(project_context, 'cache_connection_url_placeholder', "CACHE_URL"))),
                'CACHE_CLIENT_MODULE_PATH': str(crew_inputs.get('cache_client_module_path', getattr(project_context, 'cache_client_module_path', "src/utils/cache_client"))),
                'SERVICE_METHODS_TO_CACHE': "\n".join(crew_inputs.get('service_methods_to_cache', getattr(project_context, 'service_methods_to_cache', ["ExampleService.get_data:60s"]))),
                'CACHE_KEY_PREFIX': str(crew_inputs.get('cache_key_prefix', getattr(project_context, 'cache_key_prefix', "app_cache"))),
            },
            "background_jobs_manager": lambda: {
                'JOB_QUEUE_SYSTEM': str(crew_inputs.get('job_queue_system', getattr(project_context, 'job_queue_system', "Celery"))),
                'QUEUE_CONNECTION_URL_PLACEHOLDER': str(crew_inputs.get('queue_connection_url_placeholder', getattr(project_context, 'queue_connection_url_placeholder', "QUEUE_URL"))),
                'WORKERS_DIR_PATH': str(crew_inputs.get('workers_dir_path', getattr(project_context, 'workers_dir_path', "src/workers"))),
                'JOBS_DIR_PATH': str(crew_inputs.get('jobs_dir_path', getattr(project_context, 'jobs_dir_path', "src/jobs"))),
                'EXAMPLE_JOB_DEFINITIONS': "\n".join(crew_inputs.get('example_job_definitions', getattr(project_context, 'example_job_definitions', ["sendEmail(user_id)"]))),
                'DEFAULT_QUEUE_NAME': str(crew_inputs.get('default_queue_name', getattr(project_context, 'default_queue_name', "default"))),
                'DEFAULT_CONCURRENCY': str(crew_inputs.get('default_concurrency', getattr(project_context, 'default_concurrency', 1))),
                'DEFAULT_RETRY_COUNT': str(crew_inputs.get('default_retry_count', getattr(project_context, 'default_retry_count', 3))),
            },
            "message_queue_integrator": lambda: {
                'MESSAGE_BROKER_SYSTEM': str(crew_inputs.get('message_broker_system', getattr(project_context, 'message_broker_system', "RabbitMQ"))),
                'BROKER_CONNECTION_URL_PLACEHOLDER': str(crew_inputs.get('broker_connection_url_placeholder', getattr(project_context, 'broker_connection_url_placeholder', "BROKER_URL"))),
                'MESSAGING_MODULE_PATH': str(crew_inputs.get('messaging_module_path', getattr(project_context, 'messaging_module_path', "src/messaging"))),
                'TOPICS_OR_EXCHANGES_TO_DEFINE': "\n".join(crew_inputs.get('topics_or_exchanges_to_define', getattr(project_context, 'topics_or_exchanges_to_define', ["entity.event:created"]))),
                'SERIALIZATION_FORMAT': str(crew_inputs.get('serialization_format', getattr(project_context, 'serialization_format', "JSON"))),
                'CONSUMER_GROUP_ID_EXAMPLE': str(crew_inputs.get('consumer_group_id_example', getattr(project_context, 'consumer_group_id_example', "my-app-group"))),
            },
            "storage_service_manager": lambda: {
                'STORAGE_SERVICE_TYPE': str(crew_inputs.get('storage_service_type', getattr(project_context, 'storage_service_type', "LocalFileSystem"))),
                'BUCKET_NAME_PLACEHOLDER': str(crew_inputs.get('bucket_name_placeholder', getattr(project_context, 'bucket_name_placeholder', "MY_BUCKET"))),
                'STORAGE_CONFIG_PLACEHOLDERS': ", ".join(crew_inputs.get('storage_config_placeholders', getattr(project_context, 'storage_config_placeholders', ["LOCAL_STORAGE_ROOT_PATH"]))),
                'STORAGE_MODULE_PATH': str(crew_inputs.get('storage_module_path', getattr(project_context, 'storage_module_path', "src/utils/storage"))),
                'EXAMPLE_USE_CASE': str(crew_inputs.get('example_use_case', getattr(project_context, 'example_use_case', "User file uploads."))),
            },
            "email_notification_service": lambda: {
                'EMAIL_SERVICE_PROVIDER': str(crew_inputs.get('email_service_provider', getattr(project_context, 'email_service_provider', "SMTP"))),
                'EMAIL_CONFIG_PLACEHOLDERS': ", ".join(crew_inputs.get('email_config_placeholders', getattr(project_context, 'email_config_placeholders', ["SMTP_HOST", "SMTP_USER"]))),
                'EMAIL_SERVICE_MODULE_PATH': str(crew_inputs.get('email_service_module_path', getattr(project_context, 'email_service_module_path', "src/services/email"))),
                'TEMPLATES_DIR_PATH': str(crew_inputs.get('templates_dir_path', getattr(project_context, 'templates_dir_path', "src/templates/emails"))),
                'EXAMPLE_EMAIL_TEMPLATES': "\n".join(crew_inputs.get('example_email_templates', getattr(project_context, 'example_email_templates', ["welcome:USER_NAME,VERIFY_LINK"]))),
            },
            "error_handling_and_logging": lambda: {
                'LOGGING_LIBRARY': str(crew_inputs.get('logging_library', getattr(project_context, 'logging_library', "Python logging"))),
                'ERROR_CLASSES_MODULE_PATH': str(crew_inputs.get('error_classes_module_path', getattr(project_context, 'error_classes_module_path', "src/utils/errors"))),
                'LOGGER_CONFIG_MODULE_PATH': str(crew_inputs.get('logger_config_module_path', getattr(project_context, 'logger_config_module_path', "src/config/logging_config"))),
                'LOG_LEVEL_PLACEHOLDER': str(crew_inputs.get('log_level_placeholder', getattr(project_context, 'log_level_placeholder', "LOG_LEVEL_CONFIG"))),
                'LOG_FORMAT': str(crew_inputs.get('log_format', getattr(project_context, 'log_format', "JSON"))),
                'LOG_DESTINATIONS': ", ".join(crew_inputs.get('log_destinations', getattr(project_context, 'log_destinations', ["stdout"]))),
            },
            "monitoring_and_metrics_integrator": lambda: {
                'METRICS_SYSTEM': str(crew_inputs.get('metrics_system', getattr(project_context, 'metrics_system', "Prometheus"))),
                'HEALTH_CHECK_ENDPOINT_PATH': str(crew_inputs.get('health_check_endpoint_path', getattr(project_context, 'health_check_endpoint_path', "/healthz"))),
                'METRICS_ENDPOINT_PATH': str(crew_inputs.get('metrics_endpoint_path', getattr(project_context, 'metrics_endpoint_path', "/metrics"))),
                'MONITORING_MODULE_PATH': str(crew_inputs.get('monitoring_module_path', getattr(project_context, 'monitoring_module_path', "src/monitoring"))),
                'METRIC_PREFIX': str(crew_inputs.get('metric_prefix', getattr(project_context, 'metric_prefix', "app_"))),
                'SERVICE_NAME_FOR_METRICS': str(crew_inputs.get('service_name_for_metrics', getattr(project_context, 'service_name_for_metrics', "my_app_service"))),
            },
            "security_and_hardening": lambda: {
                'SECURITY_MIDDLEWARE_PATH': str(crew_inputs.get('security_middleware_path', getattr(project_context, 'security_middleware_path', "src/middleware/security"))),
                'INPUT_VALIDATION_STRATEGY': str(crew_inputs.get('input_validation_strategy', getattr(project_context, 'input_validation_strategy', "DTOs with validation library"))),
                'CSP_POLICY_EXAMPLE': str(crew_inputs.get('csp_policy_example', getattr(project_context, 'csp_policy_example', "default-src 'self'"))),
                'CORS_ALLOWED_ORIGINS_PLACEHOLDER': str(crew_inputs.get('cors_allowed_origins_placeholder', getattr(project_context, 'cors_allowed_origins_placeholder', "CORS_ORIGINS_CONFIG"))),
                'RATE_LIMIT_REQUESTS_PLACEHOLDER': str(crew_inputs.get('rate_limit_requests_placeholder', getattr(project_context, 'rate_limit_requests_placeholder', 100))),
                'RATE_LIMIT_WINDOW_SECONDS_PLACEHOLDER': str(crew_inputs.get('rate_limit_window_seconds_placeholder', getattr(project_context, 'rate_limit_window_seconds_placeholder', 60))),
            },
            "performance_optimizer": lambda: {
                'DAL_CODE_PATH': str(crew_inputs.get('dal_code_path', getattr(project_context, 'dal_code_path', "src/dal"))),
                'SERVICE_CODE_PATH': str(crew_inputs.get('service_code_path', getattr(project_context, 'service_code_path', "src/services"))),
                'SLOW_QUERY_LOGS': str(crew_inputs.get('slow_query_logs', getattr(project_context, 'slow_query_logs', "No slow query logs available."))),
                'MAX_QUERY_TIME_MS_THRESHOLD': str(crew_inputs.get('max_query_time_ms_threshold', getattr(project_context, 'max_query_time_ms_threshold', 500))),
                'BATCH_SIZE_EXAMPLE': str(crew_inputs.get('batch_size_example', getattr(project_context, 'batch_size_example', 100))),
            },
            "documentation_generator": lambda: {
                'CONTROLLER_CODE_PATH': str(crew_inputs.get('controller_code_path', getattr(project_context, 'controllers_dir_path', "src/controllers"))),
                'SERVICE_CODE_PATH': str(crew_inputs.get('service_code_path', getattr(project_context, 'services_dir_path', "src/services"))),
                'MODEL_DEFINITIONS_PATH': str(crew_inputs.get('model_definitions_path', getattr(project_context, 'models_dir_path', "src/models"))),
                'EXISTING_OPENAPI_SPEC_PATH': str(crew_inputs.get('existing_openapi_spec_path', getattr(project_context, 'openapi_spec_path', ""))),
                'DOCS_OUTPUT_PATH': str(crew_inputs.get('docs_output_path', getattr(project_context, 'docs_output_path', "docs"))),
                'API_TITLE': str(crew_inputs.get('api_title', getattr(project_context, 'project_name', "API")) + " Documentation"),
                'API_VERSION': str(crew_inputs.get('api_version', getattr(project_context, 'api_version', "1.0.0"))),
                'CONTACT_EMAIL_EXAMPLE': str(crew_inputs.get('contact_email_example', getattr(project_context, 'contact_email', "contact@example.com"))),
            },
            "testing_suite_generator": lambda: {
                'CONTROLLER_CODE_PATH': str(crew_inputs.get('controller_code_path', getattr(project_context, 'controllers_dir_path', "src/controllers"))),
                'SERVICE_CODE_PATH': str(crew_inputs.get('service_code_path', getattr(project_context, 'services_dir_path', "src/services"))),
                'DAL_CODE_PATH': str(crew_inputs.get('dal_code_path', getattr(project_context, 'dal_dir_path', "src/dal"))),
                'TESTING_FRAMEWORK': str(crew_inputs.get('testing_framework', getattr(project_context, 'testing_framework', "pytest"))),
                'TESTS_DIR_PATH': str(crew_inputs.get('tests_dir_path', getattr(project_context, 'tests_dir_path', "tests"))),
                'TEST_DATA_EXAMPLES': json.dumps(crew_inputs.get('test_data_examples', getattr(project_context, 'test_data_examples', {})), default=str),
                'MOCKING_STRATEGY_GUIDANCE': str(crew_inputs.get('mocking_strategy_guidance', getattr(project_context, 'mocking_strategy_guidance', "Use unittest.mock or jest.mock."))),
            },
            "deployment_descriptor_generator": lambda: {
                'BASE_IMAGE_PLACEHOLDER': str(crew_inputs.get('base_image_placeholder', getattr(project_context, 'docker_base_image', "python:3.9-slim"))),
                'APPLICATION_PORT_PLACEHOLDER': str(crew_inputs.get('application_port_placeholder', getattr(project_context, 'app_port_placeholder', "APP_PORT"))),
                'DOCKERFILE_PATH': str(crew_inputs.get('dockerfile_path', getattr(project_context, 'dockerfile_path', "Dockerfile"))),
                'K8S_MANIFESTS_PATH': str(crew_inputs.get('k8s_manifests_path', getattr(project_context, 'k8s_manifests_path', "k8s"))),
                'CI_CD_CONFIG_PATH': str(crew_inputs.get('ci_cd_config_path', getattr(project_context, 'ci_cd_config_path', ".github/workflows/main.yml"))),
                'DEPLOYMENT_NAME_PLACEHOLDER': str(crew_inputs.get('deployment_name_placeholder', getattr(project_context, 'project_name_slug', "app") + "-deployment")),
                'DOCKER_IMAGE_NAME_PLACEHOLDER': str(crew_inputs.get('docker_image_name_placeholder', getattr(project_context, 'docker_image_name', "myimage"))),
                'IMAGE_TAG_PLACEHOLDER': str(crew_inputs.get('image_tag_placeholder', getattr(project_context, 'docker_image_tag', "latest"))),
                'K8S_REPLICAS_PLACEHOLDER': str(crew_inputs.get('k8s_replicas_placeholder', getattr(project_context, 'k8s_replicas', 2))),
            },
            "maintenance_and_migration_scheduler": lambda: {
                'BACKUP_SCRIPT_PATH': str(crew_inputs.get('backup_script_path', getattr(project_context, 'backup_script_path', "scripts/backup.sh"))),
                'CRON_CONFIG_PATH': str(crew_inputs.get('cron_config_path', getattr(project_context, 'cron_config_path', "config/cronjobs"))),
                'DB_BACKUP_COMMAND': str(crew_inputs.get('db_backup_command', getattr(project_context, 'db_backup_command', "pg_dump"))),
                'BACKUP_STORAGE_INFO': str(crew_inputs.get('backup_storage_info', getattr(project_context, 'backup_storage_info', "Local path /backups"))),
                'LOG_ROTATION_STRATEGY': str(crew_inputs.get('log_rotation_strategy', getattr(project_context, 'log_rotation_strategy', "logrotate"))),
                'CRON_SCHEDULE_BACKUP_EXAMPLE': str(crew_inputs.get('cron_schedule_backup_example', getattr(project_context, 'cron_schedule_backup_example', "0 2 * * *"))),
                'BACKUP_RETENTION_DAYS_EXAMPLE': str(crew_inputs.get('backup_retention_days_example', getattr(project_context, 'backup_retention_days_example', 7))),
            },
        }

        agent_specific_context = agent_specific_dispatch.get(self.name, lambda: {})()
        context.update(agent_specific_context)

        # Final string conversion for all context items
        for key, value in context.items():
            if isinstance(value, (dict, list)) and key not in ['TOOLS']: # TOOLS is list of dicts
                try:
                    context[key] = json.dumps(value, default=str) # Use default=str for non-serializable
                except TypeError:
                    context[key] = str(value) # Fallback for truly problematic types
            elif not isinstance(value, str) and key not in ['TOOLS']:
                context[key] = str(value)

        self.logger.log(f"[{self.name}] Enhanced prompt context for backend agent. Keys: {list(context.keys())}", self.role)
        return context

    def _parse_response(self, response_text: str, project_context: ProjectContext) -> dict:
        # This method should be preserved as previously defined and verified
        parsed_output = super()._parse_response(response_text, project_context)
        if parsed_output['status'] == 'complete':
            if 'parsed_json_content' in parsed_output:
                parsed_output['structured_output'] = parsed_output['parsed_json_content']
            elif 'raw_response' in parsed_output and not parsed_output.get('structured_output'):
                self.logger.log(f"[{self.name}] WARNING: No JSON block found in response, though one was expected. Raw response will be in 'raw_response' field.", self.role, level="WARNING")
        return parsed_output

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
from .runner import BackendCrewRunner


__all__ = [
    "BackendSubAgent",
    "ConfigManager", "DatabaseModelDesigner", "MigrationGenerator", "DataAccessLayerBuilder",
    "ServiceLayerBuilder", "ApiEndpointControllerGenerator", "AuthAndAuthorizationManager",
    "CachingLayerManager", "BackgroundJobsManager", "MessageQueueIntegrator",
    "StorageServiceManager", "EmailNotificationService", "ErrorHandlingAndLogging",
    "MonitoringAndMetricsIntegrator", "SecurityAndHardening", "PerformanceOptimizer",
    "DocumentationGenerator", "TestingSuiteGenerator", "DeploymentDescriptorGenerator",
    "MaintenanceAndMigrationScheduler",
    "BackendCrewRunner",
]
