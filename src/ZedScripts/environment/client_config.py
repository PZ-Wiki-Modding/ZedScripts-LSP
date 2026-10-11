import logging
from typing import Annotated, Optional
from pydantic import BaseModel, Field

from lsprotocol import types

class LoggingConfig(BaseModel):
    level: int = Field(
        description="Logging level for the server.",
        default=logging.INFO,
    )

class InitializationOptions(BaseModel):
    logging: LoggingConfig = Field(
        description="Logging configuration for the server.",
        default_factory=LoggingConfig,
    )

def get_initialization_options(options: types.LSPAny) -> InitializationOptions:
    if not isinstance(options, dict):
        logging.warning("Initialization options are not a dictionary. Using default options.")
        return InitializationOptions()
    try:
        return InitializationOptions(**options)
    except Exception as e:
        logging.warning("Failed to validate initialization options: %s. Using default options.", e)
        return InitializationOptions()
