import enum

from typing import TYPE_CHECKING, Literal, overload
if TYPE_CHECKING:
    from ..environment import WorkspaceType


class ZedNotification(enum.StrEnum):
    SET_ZEDSCRIPTS = "zedscripts/setZedScripts"

    SET_PROGRESS = "zedscripts/setProgress"
    SET_WORKSPACE_COUNT = "zedscripts/setWorkspaceCount"
    SET_LIBRARIES_COUNT = "zedscripts/setLibrariesCount"

    LOADING_DOCUMENTS = "zedscripts/loadingDocuments"
    LOADING_DOCUMENTS_DONE = "zedscripts/loadingDocumentsDone"


@overload
def send_notification(
    notification: Literal[ZedNotification.SET_ZEDSCRIPTS],
    *, uri: str) -> None: ...


@overload
def send_notification(
    notification: Literal[ZedNotification.SET_PROGRESS],
    *, progress: float) -> None: ...
@overload
def send_notification(
    notification: Literal[ZedNotification.SET_WORKSPACE_COUNT],
    *, count: int) -> None: ...
@overload
def send_notification(
    notification: Literal[ZedNotification.SET_LIBRARIES_COUNT],
    *, count: int) -> None: ...


@overload
def send_notification(
    notification: Literal[ZedNotification.LOADING_DOCUMENTS],
    *, uri: str, workspace_type: 'WorkspaceType', index: int) -> None: ...


def send_notification(notification: ZedNotification, **kargs) -> None:
    """
    Sends a notification to the Zed server.

    Args:
        notification (ZedNotification): The type of notification to send.
        **kargs: Additional keyword arguments specific to the notification type.
    """
    from ..server import ZedServer
    server = ZedServer.instance
    if server is None:
        return
    server.send_notification(notification, kargs)