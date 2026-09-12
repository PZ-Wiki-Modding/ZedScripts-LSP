
from ..providers.diagnostics import DiagnosticCollection


def validate(document) -> DiagnosticCollection:
    diagnostics = document.diagnostics
    diagnostics.clear() # reset previous diagnostics

    # perform validation here

    return diagnostics







