import json
import subprocess
import sys

from ZedScripts.environment.config import ConfigurationModel


def test_default_config_cli():
    result = subprocess.run(
        [sys.executable, "-m", "ZedScripts.environment.config", "default"],
        capture_output=True,
        text=True,
        check=True,
    )

    output = json.loads(result.stdout)
    assert output["libraries"] == []
    assert isinstance(output["ignored"], list)
    assert ConfigurationModel.model_validate_json(result.stdout) == ConfigurationModel()
    assert '\n    "dataset": {' in result.stdout


def test_config_schema_cli():
    result = subprocess.run(
        [sys.executable, "-m", "ZedScripts.environment.config", "schema"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert json.loads(result.stdout) == ConfigurationModel.model_json_schema()
