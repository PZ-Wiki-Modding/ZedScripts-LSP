import enum
from typing import TypedDict

class ZedNotification(enum.StrEnum):
    SET_ZEDSCRIPTS = "zedscripts/setZedScripts"

class NotificationParams(TypedDict):
    pass

class SetZedScriptsNotificationParams(NotificationParams):
    uri: str
