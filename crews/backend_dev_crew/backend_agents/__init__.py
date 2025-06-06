# crews/backend_dev_crew/backend_agents/__init__.py
"""
Backend Development Sub-Agents package.
Contains individual specialized agents for backend tasks.
"""
from agents.base_agent import Agent
from utils.general_utils import Logger
from utils.database import Database
from prompts.general_prompts import get_agent_prompt
from utils.context_handler import ProjectContext
import json

class BackendSubAgent(Agent):
    def __init__(self, name, role, logger: Logger, db: Database = None, model_name_override: str = None):
        super().__init__(name, role, logger, db=db)
        if model_name_override:
            self.current_model = model_name_override
            self.logger.log(f"BackendSubAgent {self.name} initialized. Model override: {self.current_model}", self.role)
        else:
            self.logger.log(f"BackendSubAgent {self.name} initialized. Using default model selection. Current model: {self.current_model}", self.role)

    def run(self, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
        self.logger.log(f"[{self.name}] Executing BackendSubAgent run method with crew_inputs keys: {list(crew_inputs.keys()) if crew_inputs else 'None'}", self.role)

        analysis_data = project_context.analysis.model_dump() if project_context.analysis else {}
        prompt_render_context = {
            'ROLE': self.role,
            'SPECIALTY': self.role,
            'PROJECT_NAME': project_context.project_name,
            'OBJECTIVE': project_context.objective or "",
            'PROJECT_TYPE': project_context.analysis.project_type_confirmed if project_context.analysis else project_context.project_type,
            'CURRENT_DIR': project_context.current_dir or "/",
            'PROJECT_SUMMARY': project_context.project_summary or "",
            'ARCHITECTURE': project_context.architecture or "", # This will be stringified in _enhance_prompt_context if dict
            'PLAN': project_context.plan or "", # This will be stringified in _enhance_prompt_context if dict
            'MEMORIES': project_context.project_summary or "No specific memories retrieved.",
            'TOOL_NAMES': [tool['name'] for tool in self.tools],
            'TOOLS': self.tools, # List of tool dicts for TOOL_PROMPT_SECTION
            'ANALYSIS': analysis_data, # Dict
            'TECH_STACK': project_context.tech_stack.model_dump() if project_context.tech_stack else {}, # Dict
            # crew_inputs is not directly passed but its content is mapped to context keys
        }
        prompt_render_context = self._enhance_prompt_context(prompt_render_context, project_context, crew_inputs)
        generated_prompt_str = get_agent_prompt(self.name, prompt_render_context)

        if self.tools:
            response_content = self._call_model_with_tools(generated_prompt_str)
        else:
            response_content = self._call_model(generated_prompt_str)

        return self._parse_response(response_content, project_context)

    def _enhance_prompt_context(self, context: dict, project_context: ProjectContext, crew_inputs: dict = None) -> dict:
        if crew_inputs is None:
            crew_inputs = {}

        # General backend related context
        context['TECH_STACK_BACKEND_NAME'] = project_context.tech_stack.backend if project_context.tech_stack and hasattr(project_context.tech_stack, 'backend') else "Not Specified"
        context['TECH_STACK_DATABASE_NAME'] = project_context.tech_stack.database if project_context.tech_stack and hasattr(project_context.tech_stack, 'database') else "Not Specified"
        context['PROJECT_ROOT'] = project_context.current_dir or "/app"

        file_ext = "py" # Default
        backend_name_lower = (context['TECH_STACK_BACKEND_NAME'] or "").lower()
        if "node" in backend_name_lower or "express" in backend_name_lower or "typescript" in backend_name_lower: # Added typescript
            file_ext = "ts" if "typescript" in backend_name_lower else "js"
        elif "java" in backend_name_lower or "spring" in backend_name_lower:
            file_ext = "java"
        elif "go" in backend_name_lower:
            file_ext = "go"
        context['FILE_EXTENSION'] = getattr(project_context.tech_stack, 'file_extension', file_ext) if project_context.tech_stack and hasattr(project_context.tech_stack, 'file_extension') else file_ext

        # Generic placeholders - these might be overridden by specific agent needs or task inputs
        context['DATA_ENTITY_NAME_SINGULAR'] = str(crew_inputs.get('data_entity_name_singular', getattr(project_context, 'generic_data_entity_singular', "Record")))
        context['DATA_ENTITY_NAME_PLURAL'] = str(crew_inputs.get('data_entity_name_plural', getattr(project_context, 'generic_data_entity_plural', "Records")))
        context['ITEM_NAME_SINGULAR'] = str(crew_inputs.get('item_name_singular', getattr(project_context, 'generic_item_name_singular', "Item")))
        context['ITEM_NAME_PLURAL'] = str(crew_inputs.get('item_name_plural', getattr(project_context, 'generic_item_name_plural', "Items"))) # Added based on web dev prompts
        context['METRIC_NAME'] = str(crew_inputs.get('metric_name', getattr(project_context, 'generic_metric_name', "Value")))
        context['BUSINESS_PROCESS_NAME'] = str(crew_inputs.get('business_process_name', getattr(project_context, 'generic_business_process_name', "Process")))
        context['TRANSACTION_SCOPE'] = str(crew_inputs.get('transaction_scope', getattr(project_context, 'transaction_scope', "request"))) # Example for ServiceLayerBuilder
        context['CACHE_TTL'] = str(crew_inputs.get('cache_ttl', getattr(project_context, 'cache_ttl', "3600s"))) # Example for ServiceLayerBuilder
        context['NOTIFICATION_FLAG'] = str(crew_inputs.get('notification_flag', getattr(project_context, 'notification_flag', "true"))) # Example for ServiceLayerBuilder

        # Agent-specific context population
        if self.name == "config_manager":
            context['DB_URL_EXAMPLE'] = str(crew_inputs.get('db_url_example', getattr(project_context, 'db_url_example', "postgresql://user:pass@dbhost:5432/mydb")))
            context['REDIS_URL_EXAMPLE'] = str(crew_inputs.get('redis_url_example', getattr(project_context, 'redis_url_example', "redis://cachehost:6379")))
            context['JWT_SECRET_EXAMPLE'] = str(crew_inputs.get('jwt_secret_example', getattr(project_context, 'jwt_secret_example', "a-very-secure-secret-key-example")))
            context['LOG_LEVEL_EXAMPLE'] = str(crew_inputs.get('log_level_example', getattr(project_context, 'log_level_example', "INFO")))
            context['API_PORT_EXAMPLE'] = str(crew_inputs.get('api_port_example', getattr(project_context, 'api_port_example', "8080")))
            context['ENVIRONMENT_EXAMPLE'] = str(crew_inputs.get('environment_example', getattr(project_context, 'environment_example', "development")))

        elif self.name == "database_model_designer":
            context['DATABASE_NAMING_CONVENTIONS'] = str(crew_inputs.get('database_naming_conventions', getattr(project_context, 'database_naming_conventions', "snake_case_for_tables_and_columns")))
            key_entities = crew_inputs.get('key_data_entities_list', getattr(project_context, 'key_data_entities_list', ["User", "Order", "Product"]))
            context['KEY_DATA_ENTITIES_LIST'] = ", ".join(key_entities) if isinstance(key_entities, list) else str(key_entities)
            context['ENTITY_RELATIONSHIPS_DESCRIPTION'] = str(crew_inputs.get('entity_relationships_description', getattr(project_context, 'entity_relationships_description', "User has many Orders. Order has many OrderItems (linking to Products).")))
            context['MODELS_DIR_PATH'] = str(crew_inputs.get('models_dir_path', getattr(project_context, 'models_dir_path', "src/db/models")))

        elif self.name == "migration_generator":
            context['MODEL_DEFINITIONS_PATH'] = str(crew_inputs.get('model_definitions_path', getattr(project_context, 'model_definitions_path', "src/db/models")))
            context['CURRENT_DB_SCHEMA_INFO'] = str(crew_inputs.get('current_db_schema_info', getattr(project_context, 'current_db_schema_info', "Initial database schema.")))
            context['DESIRED_MODEL_STATE_INFO'] = str(crew_inputs.get('desired_model_state_info', getattr(project_context, 'desired_model_state_info', "Reflect changes from current ORM models.")))
            context['MIGRATIONS_DIR_PATH'] = str(crew_inputs.get('migrations_dir_path', getattr(project_context, 'migrations_dir_path', "src/db/migrations")))

        elif self.name == "data_access_layer_builder":
            context['MODEL_DEFINITIONS_PATH'] = str(crew_inputs.get('model_definitions_path', getattr(project_context, 'model_definitions_path', "src/db/models")))
            context['DAL_DIR_PATH'] = str(crew_inputs.get('dal_dir_path', getattr(project_context, 'dal_dir_path', "src/dal"))) # Or src/repositories
            db_errors = crew_inputs.get('database_error_types', getattr(project_context, 'database_error_types', ["sqlalchemy.exc.NoResultFound", "sqlalchemy.exc.IntegrityError"]))
            context['DATABASE_ERROR_TYPES'] = ", ".join(db_errors) if isinstance(db_errors, list) else str(db_errors)
            # DATA_ENTITY_NAME_SINGULAR is set from generic placeholders

        elif self.name == "service_layer_builder":
            context['DAL_CLASSES_INFO'] = str(crew_inputs.get('dal_classes_info', getattr(project_context, 'dal_classes_info', '{"UserRepository": "Available with CRUD", "ProductRepository": "Available with CRUD"}')))
            use_cases = crew_inputs.get('domain_use_cases', getattr(project_context, 'domain_use_cases', ["Register a new user with data validation.", "Create a new product ensuring unique name."]))
            context['DOMAIN_USE_CASES'] = "\n".join(use_cases) if isinstance(use_cases, list) else str(use_cases)
            context['INPUT_SCHEMA_DEFINITIONS_PATH'] = str(crew_inputs.get('input_schema_definitions_path', getattr(project_context, 'input_schema_definitions_path', "src/schemas")))
            context['SERVICES_DIR_PATH'] = str(crew_inputs.get('services_dir_path', getattr(project_context, 'services_dir_path', "src/services")))
            # DATA_ENTITY_NAME_SINGULAR, BUSINESS_PROCESS_NAME, ITEM_NAME_SINGULAR, METRIC_NAME, TRANSACTION_SCOPE, CACHE_TTL, NOTIFICATION_FLAG are set from generic placeholders

        elif self.name == "api_endpoint_controller_generator":
            context['SERVICE_LAYER_INFO'] = str(crew_inputs.get('service_layer_info', getattr(project_context, 'service_layer_info', '{"UserService": "register_user, get_user", "ProductService": "create_product"}')))
            routes = crew_inputs.get('api_route_definitions', getattr(project_context, 'api_route_definitions', ["POST /users/register", "GET /users/{user_id}", "POST /products"]))
            context['API_ROUTE_DEFINITIONS'] = "\n".join(routes) if isinstance(routes, list) else str(routes)
            context['CONTROLLERS_DIR_PATH'] = str(crew_inputs.get('controllers_dir_path', getattr(project_context, 'controllers_dir_path', "src/controllers")))
            context['REQUEST_DTO_PATH'] = str(crew_inputs.get('request_dto_path', getattr(project_context, 'request_dto_path', "src/dtos/request")))
            context['RESPONSE_DTO_PATH'] = str(crew_inputs.get('response_dto_path', getattr(project_context, 'response_dto_path', "src/dtos/response")))
            context['SHARED_ERROR_SCHEMAS_INFO'] = str(crew_inputs.get('shared_error_schemas_info', getattr(project_context, 'shared_error_schemas_info', "Standard error DTOs available in src/dtos/errors")))

        elif self.name == "auth_and_authorization_manager":
            context['AUTH_STRATEGY'] = str(crew_inputs.get('auth_strategy', getattr(project_context, 'auth_strategy', "JWT")))
            context['USER_MODEL_PATH'] = str(crew_inputs.get('user_model_path', getattr(project_context, 'user_model_path', f"src/models/user.{context['FILE_EXTENSION']}")))
            context['DAL_INFO'] = str(crew_inputs.get('dal_info', getattr(project_context, 'dal_info', "User DAL (UserRepository) available for user data access.")))
            context['AUTH_MODULE_PATH'] = str(crew_inputs.get('auth_module_path', getattr(project_context, 'auth_module_path', "src/auth")))
            roles = crew_inputs.get('role_definitions', getattr(project_context, 'role_definitions', ["admin", "user", "guest"]))
            context['ROLE_DEFINITIONS'] = "\n".join(roles) if isinstance(roles, list) else str(roles)
            permissions = crew_inputs.get('permission_definitions', getattr(project_context, 'permission_definitions', ["create:items", "read:items", "update:items", "delete:items"]))
            context['PERMISSION_DEFINITIONS'] = "\n".join(permissions) if isinstance(permissions, list) else str(permissions)
            protected_routes = crew_inputs.get('protected_routes_info', getattr(project_context, 'protected_routes_info', ["/admin/* requires 'admin' role", "/items POST requires 'write:items' permission"]))
            context['PROTECTED_ROUTES_INFO'] = "\n".join(protected_routes) if isinstance(protected_routes, list) else str(protected_routes)
            # JWT_SECRET_EXAMPLE is already in context from ConfigManager section or general defaults if this agent runs standalone.

        elif self.name == "caching_layer_manager":
            context['CACHE_TYPE'] = str(crew_inputs.get('cache_type', getattr(project_context, 'cache_type', "Redis")))
            context['CACHE_CONNECTION_URL_PLACEHOLDER'] = str(crew_inputs.get('cache_connection_url_placeholder', getattr(project_context, 'cache_connection_url_placeholder', "REDIS_URL"))) # Matches .env example
            context['CACHE_CLIENT_MODULE_PATH'] = str(crew_inputs.get('cache_client_module_path', getattr(project_context, 'cache_client_module_path', "src/utils/cache_client")))
            methods_to_cache = crew_inputs.get('service_methods_to_cache', getattr(project_context, 'service_methods_to_cache', ["ProductService.get_product_by_id:300", "UserService.get_all_users:3600"]))
            context['SERVICE_METHODS_TO_CACHE'] = "\n".join(methods_to_cache) if isinstance(methods_to_cache, list) else str(methods_to_cache)
            context['CACHE_KEY_PREFIX'] = str(crew_inputs.get('cache_key_prefix', getattr(project_context, 'cache_key_prefix', f"{project_context.project_name or 'app'}:cache")))

        elif self.name == "background_jobs_manager":
            context['JOB_QUEUE_SYSTEM'] = str(crew_inputs.get('job_queue_system', getattr(project_context, 'job_queue_system', "Celery")))
            context['QUEUE_CONNECTION_URL_PLACEHOLDER'] = str(crew_inputs.get('queue_connection_url_placeholder', getattr(project_context, 'queue_connection_url_placeholder', "CELERY_BROKER_URL"))) # Example
            context['WORKERS_DIR_PATH'] = str(crew_inputs.get('workers_dir_path', getattr(project_context, 'workers_dir_path', "src/workers")))
            context['JOBS_DIR_PATH'] = str(crew_inputs.get('jobs_dir_path', getattr(project_context, 'jobs_dir_path', "src/jobs")))
            job_defs = crew_inputs.get('example_job_definitions', getattr(project_context, 'example_job_definitions', ["send_welcome_email(user_id: int)", "generate_monthly_report(month: str, year: int)"]))
            context['EXAMPLE_JOB_DEFINITIONS'] = "\n".join(job_defs) if isinstance(job_defs, list) else str(job_defs)
            context['DEFAULT_QUEUE_NAME'] = str(crew_inputs.get('default_queue_name', getattr(project_context, 'default_queue_name', "default")))
            context['DEFAULT_CONCURRENCY'] = str(crew_inputs.get('default_concurrency', getattr(project_context, 'default_concurrency', "4")))
            context['DEFAULT_RETRY_COUNT'] = str(crew_inputs.get('default_retry_count', getattr(project_context, 'default_retry_count', "3")))

        elif self.name == "message_queue_integrator":
            context['MESSAGE_BROKER_SYSTEM'] = str(crew_inputs.get('message_broker_system', getattr(project_context, 'message_broker_system', "RabbitMQ")))
            context['BROKER_CONNECTION_URL_PLACEHOLDER'] = str(crew_inputs.get('broker_connection_url_placeholder', getattr(project_context, 'broker_connection_url_placeholder', "RABBITMQ_AMQP_URL"))) # Example
            context['MESSAGING_MODULE_PATH'] = str(crew_inputs.get('messaging_module_path', getattr(project_context, 'messaging_module_path', "src/messaging")))
            topics = crew_inputs.get('topics_or_exchanges_to_define', getattr(project_context, 'topics_or_exchanges_to_define', ["user_events:user.created", "order_service:order.processed"]))
            context['TOPICS_OR_EXCHANGES_TO_DEFINE'] = "\n".join(topics) if isinstance(topics, list) else str(topics)
            context['SERIALIZATION_FORMAT'] = str(crew_inputs.get('serialization_format', getattr(project_context, 'serialization_format', "JSON")))
            context['CONSUMER_GROUP_ID_EXAMPLE'] = str(crew_inputs.get('consumer_group_id_example', getattr(project_context, 'consumer_group_id_example', f"{project_context.project_name or 'app'}-workers")))

        elif self.name == "storage_service_manager":
            context['STORAGE_SERVICE_TYPE'] = str(crew_inputs.get('storage_service_type', getattr(project_context, 'storage_service_type', "AWS_S3")))
            context['BUCKET_NAME_PLACEHOLDER'] = str(crew_inputs.get('bucket_name_placeholder', getattr(project_context, 'bucket_name_placeholder', "S3_BUCKET_NAME"))) # Example
            config_placeholders = crew_inputs.get('storage_config_placeholders', getattr(project_context, 'storage_config_placeholders', ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_S3_REGION"]))
            context['STORAGE_CONFIG_PLACEHOLDERS'] = ", ".join(config_placeholders) if isinstance(config_placeholders, list) else str(config_placeholders)
            context['STORAGE_MODULE_PATH'] = str(crew_inputs.get('storage_module_path', getattr(project_context, 'storage_module_path', "src/utils/storage")))
            context['EXAMPLE_USE_CASE'] = str(crew_inputs.get('example_use_case', getattr(project_context, 'example_use_case', "Storing user profile pictures and generated documents.")))

        elif self.name == "email_notification_service":
            context['EMAIL_SERVICE_PROVIDER'] = str(crew_inputs.get('email_service_provider', getattr(project_context, 'email_service_provider', "SendGrid")))
            config_placeholders = crew_inputs.get('email_config_placeholders', getattr(project_context, 'email_config_placeholders', ["SENDGRID_API_KEY", "DEFAULT_FROM_EMAIL"]))
            context['EMAIL_CONFIG_PLACEHOLDERS'] = ", ".join(config_placeholders) if isinstance(config_placeholders, list) else str(config_placeholders)
            context['EMAIL_SERVICE_MODULE_PATH'] = str(crew_inputs.get('email_service_module_path', getattr(project_context, 'email_service_module_path', "src/services/notification_service")))
            context['TEMPLATES_DIR_PATH'] = str(crew_inputs.get('templates_dir_path', getattr(project_context, 'templates_dir_path', "src/templates/emails")))
            templates = crew_inputs.get('example_email_templates', getattr(project_context, 'example_email_templates', ["welcome_email:USER_NAME,VERIFICATION_URL", "order_confirmation:ORDER_ID,TOTAL_AMOUNT"]))
            context['EXAMPLE_EMAIL_TEMPLATES'] = "\n".join(templates) if isinstance(templates, list) else str(templates)

        elif self.name == "error_handling_and_logging":
            context['LOGGING_LIBRARY'] = str(crew_inputs.get('logging_library', getattr(project_context, 'logging_library', "Python's standard logging module")))
            context['ERROR_CLASSES_MODULE_PATH'] = str(crew_inputs.get('error_classes_module_path', getattr(project_context, 'error_classes_module_path', "src/utils/exceptions")))
            context['LOGGER_CONFIG_MODULE_PATH'] = str(crew_inputs.get('logger_config_module_path', getattr(project_context, 'logger_config_module_path', "src/config/logging_config")))
            context['LOG_LEVEL_PLACEHOLDER'] = str(crew_inputs.get('log_level_placeholder', getattr(project_context, 'log_level_placeholder', "LOG_LEVEL"))) # From .env
            context['LOG_FORMAT'] = str(crew_inputs.get('log_format', getattr(project_context, 'log_format', "JSON")))
            log_dests = crew_inputs.get('log_destinations', getattr(project_context, 'log_destinations', ["stdout", f"file:{context['PROJECT_ROOT']}/logs/app.log"]))
            context['LOG_DESTINATIONS'] = ",".join(log_dests) if isinstance(log_dests, list) else str(log_dests)

        elif self.name == "monitoring_and_metrics_integrator":
            context['METRICS_SYSTEM'] = str(crew_inputs.get('metrics_system', getattr(project_context, 'metrics_system', "Prometheus")))
            context['HEALTH_CHECK_ENDPOINT_PATH'] = str(crew_inputs.get('health_check_endpoint_path', getattr(project_context, 'health_check_endpoint_path', "/app/health")))
            context['METRICS_ENDPOINT_PATH'] = str(crew_inputs.get('metrics_endpoint_path', getattr(project_context, 'metrics_endpoint_path', "/app/metrics")))
            context['MONITORING_MODULE_PATH'] = str(crew_inputs.get('monitoring_module_path', getattr(project_context, 'monitoring_module_path', "src/monitoring")))
            context['METRIC_PREFIX'] = str(crew_inputs.get('metric_prefix', getattr(project_context, 'metric_prefix', f"{project_context.project_name_slug or 'app'}_")))
            context['SERVICE_NAME_FOR_METRICS'] = str(crew_inputs.get('service_name_for_metrics', getattr(project_context, 'service_name_for_metrics', project_context.project_name_slug or "app_service")))
            # DATA_ENTITY_NAME_SINGULAR is set generically

        elif self.name == "security_and_hardening":
            context['SECURITY_MIDDLEWARE_PATH'] = str(crew_inputs.get('security_middleware_path', getattr(project_context, 'security_middleware_path', "src/middleware/security_headers")))
            context['INPUT_VALIDATION_STRATEGY'] = str(crew_inputs.get('input_validation_strategy', getattr(project_context, 'input_validation_strategy', "DTOs with class-validator/Pydantic")))
            context['CSP_POLICY_EXAMPLE'] = str(crew_inputs.get('csp_policy_example', getattr(project_context, 'csp_policy_example', "default-src 'self'; object-src 'none'; script-src 'self' 'unsafe-inline'"))) # Slightly more permissive example
            context['CORS_ALLOWED_ORIGINS_PLACEHOLDER'] = str(crew_inputs.get('cors_allowed_origins_placeholder', getattr(project_context, 'cors_allowed_origins_placeholder', "CORS_ALLOWED_ORIGINS_FROM_ENV")))
            context['RATE_LIMIT_REQUESTS_PLACEHOLDER'] = str(crew_inputs.get('rate_limit_requests_placeholder', getattr(project_context, 'rate_limit_requests_placeholder', "RATE_LIMIT_MAX_REQUESTS")))
            context['RATE_LIMIT_WINDOW_SECONDS_PLACEHOLDER'] = str(crew_inputs.get('rate_limit_window_seconds_placeholder', getattr(project_context, 'rate_limit_window_seconds_placeholder', "RATE_LIMIT_WINDOW_SEC")))

        elif self.name == "performance_optimizer":
            context['DAL_CODE_PATH'] = str(crew_inputs.get('dal_code_path', getattr(project_context, 'dal_code_path', "src/dal"))) # or repositories
            context['SERVICE_CODE_PATH'] = str(crew_inputs.get('service_code_path', getattr(project_context, 'service_code_path', "src/services")))
            context['SLOW_QUERY_LOGS'] = str(crew_inputs.get('slow_query_logs', getattr(project_context, 'slow_query_logs', "No specific slow query logs provided; analyze general patterns.")))
            context['MAX_QUERY_TIME_MS_THRESHOLD'] = str(crew_inputs.get('max_query_time_ms_threshold', getattr(project_context, 'max_query_time_ms_threshold', "200")))
            context['BATCH_SIZE_EXAMPLE'] = str(crew_inputs.get('batch_size_example', getattr(project_context, 'batch_size_example', "200")))

        elif self.name == "documentation_generator":
            context['CONTROLLER_CODE_PATH'] = str(crew_inputs.get('controller_code_path', getattr(project_context, 'controller_code_path', "src/controllers")))
            context['SERVICE_CODE_PATH'] = str(crew_inputs.get('service_code_path', getattr(project_context, 'service_code_path', "src/services")))
            context['MODEL_DEFINITIONS_PATH'] = str(crew_inputs.get('model_definitions_path', getattr(project_context, 'model_definitions_path', "src/models")))
            context['EXISTING_OPENAPI_SPEC_PATH'] = str(crew_inputs.get('existing_openapi_spec_path', getattr(project_context, 'existing_openapi_spec_path', "docs/openapi.yml")))
            context['DOCS_OUTPUT_PATH'] = str(crew_inputs.get('docs_output_path', getattr(project_context, 'docs_output_path', "docs")))
            context['API_TITLE'] = str(crew_inputs.get('api_title', getattr(project_context, 'api_title', f"{project_context.project_name or 'MyProject'} API Documentation")))
            context['API_VERSION'] = str(crew_inputs.get('api_version', getattr(project_context, 'api_version', "v1.0.0")))
            context['CONTACT_EMAIL_EXAMPLE'] = str(crew_inputs.get('contact_email_example', getattr(project_context, 'contact_email_example', "api.support@example.com")))
            # TECH_STACK_DATABASE_NAME already set

        elif self.name == "testing_suite_generator":
            context['CONTROLLER_CODE_PATH'] = str(crew_inputs.get('controller_code_path', getattr(project_context, 'controller_code_path', "src/controllers")))
            context['SERVICE_CODE_PATH'] = str(crew_inputs.get('service_code_path', getattr(project_context, 'service_code_path', "src/services")))
            context['DAL_CODE_PATH'] = str(crew_inputs.get('dal_code_path', getattr(project_context, 'dal_code_path', "src/dal")))
            context['TESTING_FRAMEWORK'] = str(crew_inputs.get('testing_framework', getattr(project_context, 'testing_framework', "pytest" if "python" in context['TECH_STACK_BACKEND_NAME'].lower() else "jest")))
            context['TESTS_DIR_PATH'] = str(crew_inputs.get('tests_dir_path', getattr(project_context, 'tests_dir_path', "tests")))
            context['TEST_DATA_EXAMPLES'] = json.dumps(crew_inputs.get('test_data_examples', getattr(project_context, 'test_data_examples', {"default_user_id": 123, "sample_payload": {"name": "Test"}})), default=str)
            context['MOCKING_STRATEGY_GUIDANCE'] = str(crew_inputs.get('mocking_strategy_guidance', getattr(project_context, 'mocking_strategy_guidance', "Use unittest.mock for Python, jest.mock for Node.js.")))

        elif self.name == "deployment_descriptor_generator":
            context['BASE_IMAGE_PLACEHOLDER'] = str(crew_inputs.get('base_image_placeholder', getattr(project_context, 'base_image_placeholder', "python:3.11-slim-bullseye" if "python" in context['TECH_STACK_BACKEND_NAME'].lower() else "node:18-alpine")))
            context['APPLICATION_PORT_PLACEHOLDER'] = str(crew_inputs.get('application_port_placeholder', getattr(project_context, 'application_port_placeholder', "APP_PORT_FROM_ENV"))) # Example to use env var
            context['DOCKERFILE_PATH'] = str(crew_inputs.get('dockerfile_path', getattr(project_context, 'dockerfile_path', "Dockerfile")))
            context['K8S_MANIFESTS_PATH'] = str(crew_inputs.get('k8s_manifests_path', getattr(project_context, 'k8s_manifests_path', "deploy/k8s")))
            context['CI_CD_CONFIG_PATH'] = str(crew_inputs.get('ci_cd_config_path', getattr(project_context, 'ci_cd_config_path', ".github/workflows/deploy.yml")))
            context['DEPLOYMENT_NAME_PLACEHOLDER'] = str(crew_inputs.get('deployment_name_placeholder', getattr(project_context, 'deployment_name_placeholder', f"{project_context.project_name_slug or 'app'}-service")))
            context['DOCKER_IMAGE_NAME_PLACEHOLDER'] = str(crew_inputs.get('docker_image_name_placeholder', getattr(project_context, 'docker_image_name_placeholder', f"your-docker-registry/{project_context.project_name_slug or 'app'}")))
            context['IMAGE_TAG_PLACEHOLDER'] = str(crew_inputs.get('image_tag_placeholder', getattr(project_context, 'image_tag_placeholder', "latest")))
            context['K8S_REPLICAS_PLACEHOLDER'] = str(crew_inputs.get('k8s_replicas_placeholder', getattr(project_context, 'k8s_replicas_placeholder', "3")))

        elif self.name == "maintenance_and_migration_scheduler":
            context['BACKUP_SCRIPT_PATH'] = str(crew_inputs.get('backup_script_path', getattr(project_context, 'backup_script_path', "scripts/db_backup.sh")))
            context['CRON_CONFIG_PATH'] = str(crew_inputs.get('cron_config_path', getattr(project_context, 'cron_config_path', "deploy/cron/db-backup-cronjob"))) # Example for k8s cronjob
            context['DB_BACKUP_COMMAND'] = str(crew_inputs.get('db_backup_command', getattr(project_context, 'db_backup_command', "pg_dump -Fc --username={{DB_USER}} --host={{DB_HOST}} --dbname={{DB_NAME}} > /backups/backup_`date +%Y%m%d%H%M%S`.dump")))
            context['BACKUP_STORAGE_INFO'] = str(crew_inputs.get('backup_storage_info', getattr(project_context, 'backup_storage_info', "Store backups in /var/db_backups volume, to be synced to cloud storage by a separate process.")))
            context['LOG_ROTATION_STRATEGY'] = str(crew_inputs.get('log_rotation_strategy', getattr(project_context, 'log_rotation_strategy', "Use system logrotate for files in /var/log/app. Configure application to log to stdout/stderr for containerized environments.")))
            context['CRON_SCHEDULE_BACKUP_EXAMPLE'] = str(crew_inputs.get('cron_schedule_backup_example', getattr(project_context, 'cron_schedule_backup_example', "0 3 * * *"))) # Daily at 3 AM
            context['BACKUP_RETENTION_DAYS_EXAMPLE'] = str(crew_inputs.get('backup_retention_days_example', getattr(project_context, 'backup_retention_days_example', "14")))


        # Ensure all context values are strings for .format()
        # This final loop helps catch any complex types that weren't explicitly stringified above.
        final_context = {}
        for key, value in context.items():
            if isinstance(value, (dict, list)) and key not in ['TOOLS']: # TOOLS is list of dicts for TOOL_PROMPT_SECTION
                try:
                    final_context[key] = json.dumps(value, indent=2, default=str)
                except TypeError:
                    final_context[key] = str(value)
            elif not isinstance(value, (str, list)):
                final_context[key] = str(value)
            else:
                final_context[key] = value

        self.logger.log(f"[{self.name}] Enhanced prompt context for backend agent. Keys: {list(final_context.keys())}", self.role)
        return final_context

    def _parse_response(self, response_text: str, project_context: ProjectContext) -> dict:
        self.logger.log(f"[{self.name}] Parsing response in BackendSubAgent _parse_response", self.role)
        parsed_output = super()._parse_response(response_text, project_context)
        if parsed_output['status'] == 'complete' and 'parsed_json_content' in parsed_output:
            parsed_output['structured_output'] = parsed_output['parsed_json_content']
        elif parsed_output['status'] == 'complete' and 'raw_response' in parsed_output and not parsed_output.get('structured_output'):
            parsed_output['structured_output'] = parsed_output['raw_response']
            self.logger.log(f"[{self.name}] No JSON block found. Using raw response as structured_output.", self.role, level="WARNING")
        return parsed_output

# Import and list all agent classes (will be populated as they are created)
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

__all__ = [
    "BackendSubAgent",
    "ConfigManager",
    "DatabaseModelDesigner",
    "MigrationGenerator",
    "DataAccessLayerBuilder",
    "ServiceLayerBuilder",
    "ApiEndpointControllerGenerator",
    "AuthAndAuthorizationManager",
    "CachingLayerManager",
    "BackgroundJobsManager",
    "MessageQueueIntegrator",
    "StorageServiceManager",
    "EmailNotificationService",
    "ErrorHandlingAndLogging",
    "MonitoringAndMetricsIntegrator",
    "SecurityAndHardening",
    "PerformanceOptimizer",
    "DocumentationGenerator",
    "TestingSuiteGenerator",
    "DeploymentDescriptorGenerator",
    "MaintenanceAndMigrationScheduler",
]
