import json
import logging
from pathlib import Path
from typing import Any


class Locale:
    def __init__(self, code: str, strings: dict[str, str] | None = None) -> None:
        if strings is None:
            strings = {}
        self.code: str = code
        self.strings: dict[str, str] = strings


class Localiser:
    def __init__(self) -> None:
        self.locales: dict[str, Locale] = {}
        self.default_locale: str = ""

    def localise_string(self, identifier: str, locale: str | None = None, args: dict[str, Any] | None = None) -> str:
        return identifier

        if locale is None:
            locale = self.default_locale
        assert locale in self.locales

        string = self.locales[locale].strings.get(identifier)
        if string is None:
            logging.warning("Missing string: %s (%s).", identifier, locale)
            return identifier

        if args is not None:
            return string.format(**args)

        return string

    def load_locale_file(self, path: Path) -> None:
        assert path.exists() and path.is_file()

        with path.open('r') as file:
            raw = json.load(file)

        if raw.get("version") != "1.0":
            logging.warning("Locale file %s could not be read.", path)
            return

        self.locales[raw["code"]] = Locale(raw["code"], raw["strings"])
