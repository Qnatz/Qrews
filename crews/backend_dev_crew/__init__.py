# crews/backend_dev_crew/__init__.py
"""
Backend Development Crew package.
This package contains all agents and components related to backend development tasks.
"""
from .lead import BackendLeadAgent
# from .backend_agents.runner import BackendCrewRunner # This line can be removed or kept commented

from .backend_agents import (
    BackendSubAgent,
    ConfigManager,
    DatabaseModelDesigner,
    MigrationGenerator,
    DataAccessLayerBuilder,
    ServiceLayerBuilder,
    ApiEndpointControllerGenerator,
    AuthAndAuthorizationManager,
    CachingLayerManager,
    BackgroundJobsManager,
    MessageQueueIntegrator,
    StorageServiceManager,
    EmailNotificationService,
    ErrorHandlingAndLogging,
    MonitoringAndMetricsIntegrator,
    SecurityAndHardening,
    PerformanceOptimizer,
    DocumentationGenerator,
    TestingSuiteGenerator,
    DeploymentDescriptorGenerator,
    MaintenanceAndMigrationScheduler,
    BackendCrewRunner # Added BackendCrewRunner here
)

__all__ = [
    "BackendLeadAgent",
    # "BackendCrewRunner", # This can be removed if imported above and included below
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
    "BackendCrewRunner", # Added BackendCrewRunner to __all__
]
