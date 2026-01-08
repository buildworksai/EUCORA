# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Integration service factory.

Provides factory method to get appropriate integration service by system type.
"""
from typing import Dict, Type
from .base import IntegrationService
from apps.integrations.models import ExternalSystem

# Import service implementations
from .servicenow import ServiceNowCMDBService
from .servicenow_itsm import ServiceNowITSMService
from .jira import JiraAssetsService
from .jira_itsm import JiraServiceManagementService
from .freshservice import FreshserviceCMDBService
from .freshservice_itsm import FreshserviceITSMService
from .entra_id import EntraIDService
from .active_directory import ActiveDirectoryService
from .abm import AppleBusinessManagerService
from .android_enterprise import AndroidEnterpriseService
from .datadog import DatadogService
from .splunk import SplunkService
from .elastic import ElasticService
from .defender import DefenderForEndpointService
from .vulnerability_scanner import TrivyService, GrypeService, SnykService
# from .jira import JiraAssetsService, JiraServiceManagementService
# from .freshservice import FreshserviceCMDBService, FreshserviceITSMService
# from .entra_id import EntraIDService
# from .active_directory import ActiveDirectoryService
# from .abm import AppleBusinessManagerService
# from .android_enterprise import AndroidEnterpriseService
# from .datadog import DatadogService
# from .splunk import SplunkService
# from .elastic import ElasticService
# from .trivy import TrivyService
# from .grype import GrypeService
# from .snyk import SnykService
# from .defender import DefenderForEndpointService


# Service registry mapping system types to service classes
SERVICE_REGISTRY: Dict[str, Type[IntegrationService]] = {
    # CMDB Services
    ExternalSystem.SystemType.SERVICENOW_CMDB: ServiceNowCMDBService,
    ExternalSystem.SystemType.JIRA_ASSETS: JiraAssetsService,
    ExternalSystem.SystemType.FRESHSERVICE_CMDB: FreshserviceCMDBService,
    
    # ITSM Services
    ExternalSystem.SystemType.SERVICENOW_ITSM: ServiceNowITSMService,
    ExternalSystem.SystemType.JIRA_SERVICE_MANAGEMENT: JiraServiceManagementService,
    ExternalSystem.SystemType.FRESHSERVICE_ITSM: FreshserviceITSMService,
    
    # Identity Services
    ExternalSystem.SystemType.ENTRA_ID: EntraIDService,
    ExternalSystem.SystemType.ACTIVE_DIRECTORY: ActiveDirectoryService,
    
    # MDM Services
    ExternalSystem.SystemType.APPLE_BUSINESS_MANAGER: AppleBusinessManagerService,
    ExternalSystem.SystemType.ANDROID_ENTERPRISE: AndroidEnterpriseService,
    
    # Monitoring Services
    ExternalSystem.SystemType.DATADOG: DatadogService,
    ExternalSystem.SystemType.SPLUNK: SplunkService,
    ExternalSystem.SystemType.ELASTIC: ElasticService,
    
    # Security Services
    ExternalSystem.SystemType.DEFENDER_FOR_ENDPOINT: DefenderForEndpointService,
    ExternalSystem.SystemType.TRIVY: TrivyService,
    ExternalSystem.SystemType.GRYPE: GrypeService,
    ExternalSystem.SystemType.SNYK: SnykService,
    # ExternalSystem.SystemType.JIRA_ASSETS: JiraAssetsService,
    # ExternalSystem.SystemType.FRESHSERVICE_CMDB: FreshserviceCMDBService,
    
    # ITSM Services
    # ExternalSystem.SystemType.SERVICENOW_ITSM: ServiceNowITSMService,
    # ExternalSystem.SystemType.JIRA_SERVICE_MANAGEMENT: JiraServiceManagementService,
    # ExternalSystem.SystemType.FRESHSERVICE_ITSM: FreshserviceITSMService,
    
    # Identity Services
    # ExternalSystem.SystemType.ENTRA_ID: EntraIDService,
    # ExternalSystem.SystemType.ACTIVE_DIRECTORY: ActiveDirectoryService,
    
    # MDM Services
    # ExternalSystem.SystemType.APPLE_BUSINESS_MANAGER: AppleBusinessManagerService,
    # ExternalSystem.SystemType.ANDROID_ENTERPRISE: AndroidEnterpriseService,
    
    # Monitoring Services
    # ExternalSystem.SystemType.DATADOG: DatadogService,
    # ExternalSystem.SystemType.SPLUNK: SplunkService,
    # ExternalSystem.SystemType.ELASTIC: ElasticService,
    
    # Security Services
    # ExternalSystem.SystemType.TRIVY: TrivyService,
    # ExternalSystem.SystemType.GRYPE: GrypeService,
    # ExternalSystem.SystemType.SNYK: SnykService,
    # ExternalSystem.SystemType.DEFENDER_FOR_ENDPOINT: DefenderForEndpointService,
}


def get_integration_service(system_type: str) -> IntegrationService:
    """
    Factory method to get integration service by system type.
    
    Args:
        system_type: System type string (from ExternalSystem.SystemType)
    
    Returns:
        IntegrationService instance
    
    Raises:
        ValueError: If no service is registered for the system type
    """
    service_class = SERVICE_REGISTRY.get(system_type)
    if not service_class:
        raise ValueError(f'No service registered for system type: {system_type}')
    return service_class()

