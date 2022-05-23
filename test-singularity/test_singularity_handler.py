import os
import requests
import json
from pathlib import Path
import random

import pytest

from github import Github
from kipoi_containers import helper, singularityhandler, singularityhelper
from kipoi_containers import zenodoclient
from kipoi_containers.updateoradd import MODEL_GROUP_TO_SINGULARITY_JSON


@pytest.fixture
def model_group_to_singularity_dict():
    github_obj = Github(os.environ["GITHUB_TOKEN"])
    kipoi_model_repo = github_obj.get_organization("kipoi").get_repo("models")
    return helper.populate_json_from_kipoi(
        MODEL_GROUP_TO_SINGULARITY_JSON, kipoi_model_repo
    )


@pytest.fixture
def cwd():
    return Path.cwd()


def test_pull_folder(monkeypatch, model_group_to_singularity_dict):
    monkeypatch.setenv("SINGULARITY_PULL_FOLDER", "/usr/src/imaginary-folder")
    singularity_handler = singularityhandler.SingularityHandler(
        model_group="Basset",
        docker_image_name="kipoi://kipoi-docker:basset-slim",
        model_group_to_singularity_dict=model_group_to_singularity_dict,
        workflow_release_data={},
    )
    assert Path(singularity_handler.singularity_image_folder) == Path(
        "/usr/src/imaginary-folder"
    )


def test_singularityhandler_init(model_group_to_singularity_dict, cwd):
    singularity_handler = singularityhandler.SingularityHandler(
        model_group="Basset",
        docker_image_name="kipoi://kipoi-docker:basset-slim",
        model_group_to_singularity_dict=model_group_to_singularity_dict,
        singularity_image_folder=cwd,
        workflow_release_data={},
    )
    assert singularity_handler.singularity_image_folder == cwd
    assert (
        "Basset" in singularity_handler.model_group_to_singularity_dict.keys()
    )
    assert all(
        sorted(list(container_dict.keys())) == ["md5", "name", "url"]
        for container_dict in singularity_handler.model_group_to_singularity_dict.values()
    )


def test_singularityhandler_update_container_info(
    model_group_to_singularity_dict, cwd
):
    model_group = "DummyModel"
    singularity_handler = singularityhandler.SingularityHandler(
        model_group=model_group,
        docker_image_name="kipoi://kipoi-docker:dummymodel-slim",
        model_group_to_singularity_dict=model_group_to_singularity_dict,
        singularity_image_folder=cwd,
        workflow_release_data={},
    )
    singularity_json = MODEL_GROUP_TO_SINGULARITY_JSON
    github_obj = Github(os.environ["GITHUB_TOKEN"])
    kipoi_model_repo = github_obj.get_organization("kipoi").get_repo("models")

    original_container_dict = helper.populate_json_from_kipoi(
        singularity_json, kipoi_model_repo
    )

    new_container_dict = {
        "url": "https://www.dummy.url",
        "name": "Dummy_container.sif",
        "md5": f"{random.getrandbits(128)}",
        "new_deposition_id": "dummy",
        "file_id": "123",
    }
    singularity_handler.update_container_info(new_container_dict)

    assert (
        original_container_dict
        != singularity_handler.model_group_to_singularity_dict
    )
    assert "DummyModel" in singularity_handler.model_group_to_singularity_dict
    assert singularity_handler.model_group_to_singularity_dict.get(
        "DummyModel"
    ) == {
        "url": new_container_dict["url"],
        "name": new_container_dict["name"],
        "md5": new_container_dict["md5"],
    }


def test_singularityhandler_noupdate(
    capsys, monkeypatch, model_group_to_singularity_dict, cwd
):
    def mock_build_singularity_image(*args, **kwargs):
        return cwd / "kipoi-docker_deepmel-slim.sif"

    def mock_check_integrity(*args, **kwargs):
        return True

    def mock_cleanup(*args, **kwargs):
        return

    models_to_test = []
    singularity_handler = singularityhandler.SingularityHandler(
        model_group="DeepMEL",
        docker_image_name="kipoi/kipoi-docker:deepmel-slim",
        singularity_image_folder=cwd,
        model_group_to_singularity_dict=model_group_to_singularity_dict,
        workflow_release_data={},
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.cleanup", mock_cleanup
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.build_singularity_image",
        mock_build_singularity_image,
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.check_integrity",
        mock_check_integrity,
    )
    singularity_json = MODEL_GROUP_TO_SINGULARITY_JSON
    github_obj = Github(os.environ["GITHUB_TOKEN"])
    kipoi_model_repo = github_obj.get_organization("kipoi").get_repo("models")

    original_container_dict = helper.populate_json_from_kipoi(
        singularity_json, kipoi_model_repo
    )
    singularity_handler.update(models_to_test, push=False)
    captured = capsys.readouterr()
    assert (
        captured.out.strip()
        == "No need to update the existing singularity container for DeepMEL"
    )
    updated_container_dict = original_container_dict
    assert original_container_dict == updated_container_dict


def test_singularityhandler_update(
    monkeypatch, model_group_to_singularity_dict, cwd
):
    def mock_build_singularity_image(*args, **kwargs):
        return cwd / "kipoi-docker_mpra-dragonn-slim.sif"

    def mock_check_integrity(*args, **kwargs):
        return False

    def mock_cleanup(*args, **kwargs):
        return

    def mock_test_singularity_image(*args, **kwargs):
        return

    def mock_update_existing_singularity_container(*args, **kwargs):
        return {
            "new_deposition_id": "123",
            "file_id": "456",
            "url": "https://dummy.url",
            "name": "wrong_name",
            "md5": "78758738",
        }

    models_to_test = [
        "MPRA-DragoNN/ConvModel",
        "MPRA-DragoNN/DeepFactorizedModel",
    ]
    singularity_handler = singularityhandler.SingularityHandler(
        model_group="MPRA-DragoNN",
        docker_image_name="kipoi/kipoi-docker:mpra-dragonn-slim",
        singularity_image_folder=cwd,
        model_group_to_singularity_dict=model_group_to_singularity_dict,
        workflow_release_data={},
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.cleanup", mock_cleanup
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.build_singularity_image",
        mock_build_singularity_image,
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.test_singularity_image",
        mock_test_singularity_image,
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.update_existing_singularity_container",
        mock_update_existing_singularity_container,
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.check_integrity",
        mock_check_integrity,
    )
    singularity_json = MODEL_GROUP_TO_SINGULARITY_JSON
    github_obj = Github(os.environ["GITHUB_TOKEN"])
    kipoi_model_repo = github_obj.get_organization("kipoi").get_repo("models")

    original_container_dict = helper.populate_json_from_kipoi(
        singularity_json, kipoi_model_repo
    )
    singularity_handler.update(models_to_test, push=False)
    updated_container_dict = (
        singularity_handler.model_group_to_singularity_dict
    )

    assert updated_container_dict.get("MPRA-DragoNN") == {
        "url": "https://dummy.url",
        "name": "wrong_name",
        "md5": "78758738",
    }
    assert (
        original_container_dict
        != singularity_handler.model_group_to_singularity_dict
    )


def test_singularityhandler_add(
    monkeypatch, model_group_to_singularity_dict, cwd
):
    def mock_build_singularity_image(*args, **kwargs):
        return cwd / "kipoi-docker_mpra-dragonn-slim.sif"

    def mock_check_integrity(*args, **kwargs):
        return False

    def mock_cleanup(*args, **kwargs):
        return

    def mock_test_singularity_image(*args, **kwargs):
        return

    def mock_push_singularity_container(*args, **kwargs):
        return {
            "new_deposition_id": "123",
            "file_id": "456",
            "url": "https://dummy.url",
            "name": "wrong_name",
            "md5": "78758738",
        }

    models_to_test = [
        "MPRA-DragoNN/ConvModel",
    ]
    singularity_handler = singularityhandler.SingularityHandler(
        model_group="MPRA-DragoNN/ConvModel",
        docker_image_name="kipoi/kipoi-docker:mpra-dragonn",
        singularity_image_folder=cwd,
        model_group_to_singularity_dict=model_group_to_singularity_dict,
        workflow_release_data={},
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.cleanup", mock_cleanup
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.build_singularity_image",
        mock_build_singularity_image,
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.test_singularity_image",
        mock_test_singularity_image,
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.push_new_singularity_image",
        mock_push_singularity_container,
    )
    monkeypatch.setattr(
        "kipoi_containers.singularityhandler.check_integrity",
        mock_check_integrity,
    )
    singularity_json = MODEL_GROUP_TO_SINGULARITY_JSON
    github_obj = Github(os.environ["GITHUB_TOKEN"])
    kipoi_model_repo = github_obj.get_organization("kipoi").get_repo("models")

    original_container_dict = helper.populate_json_from_kipoi(
        singularity_json, kipoi_model_repo
    )
    singularity_handler.add(models_to_test, push=False)
    updated_container_dict = (
        singularity_handler.model_group_to_singularity_dict
    )
    assert updated_container_dict.get("MPRA-DragoNN/ConvModel") == {
        "url": "https://dummy.url",
        "name": "wrong_name",
        "md5": "78758738",
    }
    assert (
        original_container_dict
        != singularity_handler.model_group_to_singularity_dict
    )
