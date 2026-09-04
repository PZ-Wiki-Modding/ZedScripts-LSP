import json
import logging
from pathlib import Path
from typing import Any
from importlib.resources import files

from .diagnostics import DiagnosticType


class Locale:
    def __init__(self, code: str, strings: dict[str, str] | None = None) -> None:
        if strings is None:
            strings = {}
        self.code: str = code
        self.strings: dict[str, str] = strings


class Localizer:
    def __init__(self) -> None:
        self.locales: dict[str, Locale] = {}
        self.default_locale: str = "en"
        self.current_locale: str = self.default_locale

    def localize_string(self, identifier: DiagnosticType, locale: str | None = None, args: dict[str, Any] | None = None) -> str:
        if locale is None:
            locale = self.current_locale
        assert locale in self.locales, "Locale not loaded or invalid: {}".format(locale)

        string = self.locales[locale].strings.get(identifier.name)
        if string is None:
            logging.warning("Missing string: %s (%s).", identifier.name, locale)
            return identifier.name

        if args is not None:
            return string.format(**args)

        return string

    def load_locale_file(self) -> None:
        for locale in files("ZedScripts.locale").iterdir():
            # safeguards, probably not needed tbh
            if not locale.is_file():
                continue
            if not locale.name.endswith(".json"):
                continue

            # access the locale data
            with locale.open('r') as file:
                raw: dict[str, Any] = json.load(file)

            assert "code" in raw, "Locale file missing 'code'"
            assert "strings" in raw, "Locale file missing 'strings'"

            self.locales[raw["code"]] = Locale(raw["code"], raw["strings"])
