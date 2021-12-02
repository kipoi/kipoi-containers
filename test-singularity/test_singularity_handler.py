import os
import requests
import json
from pathlib import Path
import random

import pytest

from modelupdater import singularityhandler, singularityhelper
from modelupdater import zenodoclient


def test_pull_folder():
    os.environ["SINGULARITY_PULL_FOLDER"] = "/usr/src/imaginary-folder"
    singularity_handler = singularityhandler.SingularityHandler(
        model_group="Basset",
        docker_image_name="kipoi://kipoi-docker:basset",
    )
    os.environ.pop("SINGULARITY_PULL_FOLDER", None)
    assert (
        singularity_handler.container_info
        == Path.cwd() / "test-containers" / "model-group-to-singularity.json"
    )
    print(singularity_handler.singularity_image_folder)
    assert (
        singularity_handler.singularity_image_folder
        == "/usr/src/imaginary-folder"
    )


def test_singularityhandler_init():
    singularity_handler = singularityhandler.SingularityHandler(
        model_group="Basset",
        docker_image_name="kipoi://kipoi-docker:basset",
        singularity_image_folder=Path(__file__).parent.resolve(),
    )
    assert (
        singularity_handler.container_info
        == Path.cwd() / "test-containers" / "model-group-to-singularity.json"
    )
    assert (
        singularity_handler.singularity_image_folder
        == Path(__file__).parent.resolve()
    )
    assert "Basset" in singularity_handler.model_group_to_image_dict.keys()
    assert all(
        sorted(list(container_dict.keys())) == ["md5", "name", "url"]
        for container_dict in singularity_handler.model_group_to_image_dict.values()
    )


def test_singularityhandler_update_container_info():
    model_group = "DummyModel"
    singularity_handler = singularityhandler.SingularityHandler(
        model_group=model_group,
        docker_image_name="kipoi://kipoi-docker:dummymodel",
        singularity_image_folder=Path(__file__).parent.resolve(),
    )
    with open(singularity_handler.container_info, "r") as file_handle:
        original_container_dict = json.load(file_handle)
    new_container_dict = {
        "url": "https://www.dummy.url",
        "name": "Dummy_container.sif",
        "md5": f"{random.getrandbits(128)}",
        "new_deposition_id": "dummy",
        "file_id": "123",
    }
    singularity_handler.update_container_info(new_container_dict)
    with open(singularity_handler.container_info, "r") as file_handle:
        updated_container_dict = json.load(file_handle)

    assert "DummyModel" in updated_container_dict
    assert updated_container_dict.get("DummyModel") == {
        "url": new_container_dict["url"],
        "name": new_container_dict["name"],
        "md5": new_container_dict["md5"],
    }
    singularityhelper.write_singularity_container_info(
        original_container_dict, singularity_handler.container_info
    )
