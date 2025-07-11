"""
Configuration management for the unified discovery system.
"""

from .manager import ConfigurationManager
from .schema import (
    CastingMethodEnum,
    ContentType,
    RetryPolicy,
    HealthCheckConfig,
    ScheduleConfig,
    ContentConfig,
    DeviceConfig,
    GlobalConfig,
    ConfigurationFile,
    validate_device_config,
    validate_global_config,
    validate_configuration_file,
    EXAMPLE_CONFIG
)

__all__ = [
    'ConfigurationManager',
    'CastingMethodEnum',
    'ContentType',
    'RetryPolicy',
    'HealthCheckConfig',
    'ScheduleConfig',
    'ContentConfig',
    'DeviceConfig',
    'GlobalConfig',
    'ConfigurationFile',
    'validate_device_config',
    'validate_global_config',
    'validate_configuration_file',
    'EXAMPLE_CONFIG'
]