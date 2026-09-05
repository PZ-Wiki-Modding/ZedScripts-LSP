r"""
Provides client and server capabilities tools
"""

import logging

from lsprotocol import types

_client_init: types.InitializeParams | None

def register_client_capabilities(params: types.InitializeParams):
    global _client_init
    _client_init = params

    logging.info("Registering client capabilities")

    client_info = params.client_info
    if client_info is not None:
        logging.info("Client info: %s %s", client_info.name, client_info.version)
    else:
        logging.info("Client info is not available")




## CLIENT CAPABILITIES

def get_diagnostics_capabilities() -> types.DiagnosticClientCapabilities | None:
    """
    
    """
    assert _client_init is not None, "Client has not been initialized"

    client_init = _client_init
    client_capabilities = client_init.capabilities
    text_document = client_capabilities.text_document

    if text_document is None:
        return None

    return text_document.diagnostic

def is_support_pull_diagnostics() -> bool:
    """
    Whenever pull mode for diagnostics is possible. It was added in 
    LSP 3.17 and VSCode's language server node package as of 09-2026
    is at LSP 3.18.3 so some clients may not support it, simply for
    other IDEs that don't get too many updates.
    """
    return get_diagnostics_capabilities() is not None




## SERVER CAPABILITIES

def get_server_capabilities() -> types.ServerCapabilities:
    """
    Below are the explanation for diagnostics

    ### Diagnostics
    Our diagnostics depend on other files so we prefer to diagnostic 
    the whole workspace. 
    They could take a while for large workspaces (i.e. the game files) 
    so we want to provide feedback when it takes a while.
    Diagnostics in pull mode (diagnostic_provider != None) was only
    introduced in LSP 3.17 and may not be supported by all clients.
    """
    # diagnostic support in pull mode
    if is_support_pull_diagnostics():
        diagnostic_provider = types.DiagnosticOptions(
            inter_file_dependencies=True,
            workspace_diagnostics=True,
            identifier="zedscripts",
            work_done_progress=True,
        )
    else:
        diagnostic_provider = None

    return types.ServerCapabilities(
        diagnostic_provider=diagnostic_provider
    )