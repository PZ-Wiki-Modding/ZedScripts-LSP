import enum
from typing import Any, TypedDict


class ConfigurationType(enum.IntEnum):
    DATA_SOURCE = enum.auto()

# TODO: implement fixed configuration values


default_configuration: dict[ConfigurationType, Any] = {
    ConfigurationType.DATA_SOURCE: "latest"
}



class Configuration:
    def __init__(self):
        self.settings: dict[ConfigurationType, Any] = {}

    def get(self, key: ConfigurationType, default=None):
        return self.settings.get(key, default)

    def set(self, key: ConfigurationType, value):
        self.settings[key] = value

