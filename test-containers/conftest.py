from pathlib import Path
import json

from kipoi_containers.updateoradd import (
    MODEL_GROUP_TO_DOCKER_JSON,
    DOCKER_TO_MODEL_JSON,
)
from kipoi_containers.helper import populate_json


def pytest_addoption(parser):
    """attaches optional cmd-line args to the pytest machinery"""
    parser.addoption(
        "--model", action="append", default=[], help="Model name(s)"
    )
    parser.addoption(
        "--modelgroup", action="append", default=[], help="Model group name(s)"
    )
    parser.addoption("--image", action="append", default=[], help="Image name")


def pytest_generate_tests(metafunc):
    metafunc.cls.model_group_to_docker_dict = populate_json(
        MODEL_GROUP_TO_DOCKER_JSON
    )
    metafunc.cls.image_to_model_dict = populate_json(DOCKER_TO_MODEL_JSON)

    if metafunc.config.getoption("image"):
        image_from_cmd_line = metafunc.config.getoption("image")
        if image_from_cmd_line and hasattr(metafunc.cls, "image_name"):
            metafunc.cls.image_name = image_from_cmd_line[0]
    if metafunc.config.getoption("modelgroup"):
        modelgroup_from_cmd_line = metafunc.config.getoption("modelgroup")
        if modelgroup_from_cmd_line and hasattr(
            metafunc.cls, "modelgroup_name"
        ):
            modelgroups_to_test = modelgroup_from_cmd_line[0].split(",")
            print(modelgroups_to_test)
            metafunc.cls.modelgroup_name = modelgroups_to_test
    elif metafunc.config.getoption("model"):
        model_from_cmd_line = metafunc.config.getoption("model")
        if model_from_cmd_line and hasattr(metafunc.cls, "model_name"):
            models_to_test = model_from_cmd_line[0].split(",")
            metafunc.cls.model_name = models_to_test
