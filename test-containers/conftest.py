from pathlib import Path
import json


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
    with open(
        Path.cwd() / "container-info" / "model-group-to-docker.json", "r"
    ) as infile:
        metafunc.cls.model_group_to_docker_dict = json.load(infile)

    with open(
        Path.cwd() / "container-info" / "docker-to-model.json", "r"
    ) as infile:
        metafunc.cls.image_to_model_dict = json.load(infile)
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
