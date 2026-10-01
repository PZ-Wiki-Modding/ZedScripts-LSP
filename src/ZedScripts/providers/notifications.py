import enum
from typing import TypedDict
from pathlib import Path

from ..utils import path_to_uri

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..environment import WorkspaceType


class ZedNotification(enum.StrEnum):
    SET_ZEDSCRIPTS = "zedscripts/setZedScripts"

    LOADING_DOCUMENTS = "zedscripts/loadingDocuments"
    LOADING_DOCUMENTS_DONE = "zedscripts/loadingDocumentsDone"



class NotificationParams(TypedDict): ...

class SetZedScriptsNotificationParams(NotificationParams):
    uri: str

class LoadingDocumentsNotificationParams(NotificationParams):
    uri: str
    progress: float
    workspace_type: 'WorkspaceType'




def send_progress_notification(type: ZedNotification, folder: Path, progress: float, workspace_type: 'WorkspaceType'):
    from ..server import ZedServer
    server = ZedServer.instance
    if server is None:
        return
    server.send_notification(
        type,
        LoadingDocumentsNotificationParams(
            uri=path_to_uri(folder),
            progress=progress,
            workspace_type=workspace_type
        )
    )