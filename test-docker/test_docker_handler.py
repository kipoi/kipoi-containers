import docker
import json
from pathlib import Path
import pytest
import os
import shutil

from github import Github
from ruamel.yaml import round_trip_load, round_trip_dump
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from kipoi_containers.dockerupdater import DockerUpdater
from kipoi_containers.dockeradder import DockerAdder
from kipoi_containers.helper import (
    populate_json,
    populate_json_from_kipoi,
    populate_yaml,
)
from kipoi_containers.updateoradd import (
    DOCKER_TO_MODEL_JSON,
    MODEL_GROUP_TO_DOCKER_JSON,
    TEST_IMAGES_WORKFLOW,
    RELEASE_WORKFLOW,
)


@pytest.fixture
def parent_path():
    return Path(__file__).resolve().parent


@pytest.mark.parametrize(
    "model_group_to_update,image_to_update",
    [
        ("MMSplice/deltaLogitPSI", "kipoi/kipoi-docker:mmsplice"),
        ("MMSplice/deltaLogitPSI", "kipoi/kipoi-docker:mmsplice-slim"),
    ],
)
def test_update(model_group_to_update, image_to_update, monkeypatch):
    def mock_push_docker_image(*args, **kwargs):
        return True

    monkeypatch.setattr(
        "kipoi_containers.dockerupdater.push_docker_image",
        mock_push_docker_image,
    )
    client = docker.from_env()
    original_shortid = client.images.get(image_to_update).short_id
    DockerUpdater(
        model_group=model_group_to_update, name_of_docker_image=image_to_update
    ).update(models_to_test=["MMSplice/modularPredictions"])
    assert client.images.get(image_to_update).short_id != original_shortid


def test_add(monkeypatch, parent_path):
    model_group_to_add = "CleTimer"

    def mock_get_list_of_models_from_repo(*args, **kwargs):
        return ["CleTimer/customBP", "CleTimer/default"]

    def mock_is_compatible_with_existing_image(*args, **kwargs):
        return False

    def mock_push_docker_image(*args, **kwargs):
        return True

    monkeypatch.setattr(
        "kipoi_containers.dockeradder.DockerAdder.get_list_of_models_from_repo",
        staticmethod(mock_get_list_of_models_from_repo),
    )
    monkeypatch.setattr(
        "kipoi_containers.dockeradder.DockerAdder.is_compatible_with_existing_image",
        staticmethod(mock_is_compatible_with_existing_image),
    )
    monkeypatch.setattr(
        "kipoi_containers.dockeradder.push_docker_image",
        mock_push_docker_image,
    )
    github_obj = Github(os.environ["GITHUB_TOKEN"])
    kipoi_model_repo = github_obj.get_organization("kipoi").get_repo("models")

    model_group_to_docker_dict = populate_json_from_kipoi(
        MODEL_GROUP_TO_DOCKER_JSON, kipoi_model_repo
    )
    docker_to_model_dict = populate_json(DOCKER_TO_MODEL_JSON)
    workflow_test_data = populate_yaml(TEST_IMAGES_WORKFLOW)
    workflow_release_data = populate_yaml(RELEASE_WORKFLOW)

    model_adder = DockerAdder(
        model_group=model_group_to_add,
        kipoi_model_repo=None,
        kipoi_container_repo=None,
    )
    model_adder.add(
        model_group_to_docker_dict,
        docker_to_model_dict,
        workflow_test_data,
        workflow_release_data,
    )

    # Revert the changes
    dockerfile_path = (
        parent_path / f"../dockerfiles/Dockerfile.{model_group_to_add.lower()}"
    )
    assert dockerfile_path.exists()
    dockerfile_path.unlink()

    slim_dockerfile_path = Path(f"{dockerfile_path}-slim")
    assert slim_dockerfile_path.exists()
    slim_dockerfile_path.unlink()

    assert (
        model_group_to_docker_dict["CleTimer"] == "kipoi/kipoi-docker:cletimer"
    )
    assert docker_to_model_dict["kipoi/kipoi-docker:cletimer"] == [
        "CleTimer/customBP",
        "CleTimer/default",
    ]
    assert (
        model_group_to_add
        in workflow_test_data["jobs"]["test"]["strategy"]["matrix"]["model"][
            -1
        ]
    )
    assert (
        workflow_release_data["jobs"]["buildtestandpush"]["strategy"][
            "matrix"
        ]["image"][-1]
        == "cletimer"
    )


def test_add_is_compatible_with_existing_image(monkeypatch):
    model_group_to_add = "Basset"
    docker_image = "kipoi/kipoi-docker:sharedpy3keras2tf2"

    def mock_get_list_of_models_from_repo(*args, **kwargs):
        return []

    def mock_is_compatible_with_existing_image(*args, **kwargs):
        return True

    def mock_push_docker_image(*args, **kwargs):
        return True

    monkeypatch.setattr(
        "kipoi_containers.dockeradder.DockerAdder.get_list_of_models_from_repo",
        staticmethod(mock_get_list_of_models_from_repo),
    )
    monkeypatch.setattr(
        "kipoi_containers.dockeradder.DockerAdder.is_compatible_with_existing_image",
        staticmethod(mock_is_compatible_with_existing_image),
    )
    monkeypatch.setattr(
        "kipoi_containers.dockeradder.push_docker_image",
        mock_push_docker_image,
    )
    github_obj = Github(os.environ["GITHUB_TOKEN"])
    kipoi_model_repo = github_obj.get_organization("kipoi").get_repo("models")
    model_group_to_docker_dict = populate_json_from_kipoi(
        MODEL_GROUP_TO_DOCKER_JSON, kipoi_model_repo
    )
    docker_to_model_dict = populate_json(DOCKER_TO_MODEL_JSON)
    workflow_test_data = populate_yaml(TEST_IMAGES_WORKFLOW)
    workflow_release_data = populate_yaml(RELEASE_WORKFLOW)

    model_group_to_docker_dict.pop(model_group_to_add)
    docker_to_model_dict[docker_image].remove(model_group_to_add)

    model_adder = DockerAdder(
        model_group=model_group_to_add,
        kipoi_model_repo=None,
        kipoi_container_repo=None,
    )
    model_adder.image_name = docker_image
    model_adder.slim_image = f"{docker_image}-slim"

    model_adder.add(
        model_group_to_docker_dict,
        docker_to_model_dict,
        workflow_test_data,
        workflow_release_data,
    )

    # Revert the changes
    dockerfile_path = (
        Path(__file__).resolve().parent
        / f"../dockerfiles/Dockerfile.{model_group_to_add.lower()}"
    )
    assert not dockerfile_path.exists()

    slim_dockerfile_path = (
        Path(__file__).resolve().parent
        / f"../dockerfiles/Dockerfile.{model_group_to_add.lower()}-slim"
    )
    assert not slim_dockerfile_path.exists()

    assert model_group_to_add in docker_to_model_dict[docker_image]

    assert model_group_to_docker_dict[model_group_to_add] == docker_image

    assert (
        workflow_test_data["jobs"]["test"]["strategy"]["matrix"][
            "model"
        ].count(model_group_to_add)
        == 1
    )
