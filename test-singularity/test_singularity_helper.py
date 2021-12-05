import os
import requests
import json
from pathlib import Path

import pytest

from kipoi_containers import (
    helper,
    singularityhelper,
    singularityhandler,
    zenodoclient,
)
from kipoi_containers.updateoradd import MODEL_GROUP_TO_SINGULARITY_JSON


@pytest.fixture(scope="module")
def zenodo_client():
    return zenodoclient.Client()


@pytest.fixture(scope="module")
def test_singularity_dict():
    return {
        "url": f"{singularityhelper.ZENODO_BASE}/record/5725936/files/tiny-container_latest.sif?download=1",
        "name": "tiny-container_latest",
        "md5": "0a85bfc85e749894210d1e53b4add11d",
    }


def test_zenodo_get_access(zenodo_client):
    response_json = zenodo_client.get_content(
        f"{singularityhelper.ZENODO_DEPOSITION}"
    )
    assert len(response_json) == 10  # By default zenodo page size is 10


def test_get_available_sc_depositions(zenodo_client):
    singularity_handler = singularityhandler.SingularityHandler(
        "Basset",
        "Dummy",
        helper.populate_json(MODEL_GROUP_TO_SINGULARITY_JSON),
    )
    available_singularity_containers = [
        container["name"]
        for container in singularity_handler.model_group_to_singularity_dict.values()
    ]
    singularity_container_number = helper.total_number_of_unique_containers(
        available_singularity_containers
    )

    extra_kwargs = {
        "status": "published",
        "q": "singularity container",
        "size": singularity_container_number,
    }

    response_json = zenodo_client.get_content(
        singularityhelper.ZENODO_DEPOSITION, **extra_kwargs
    )

    assert len(response_json) == singularity_container_number
    for index, item in enumerate(response_json):
        for file_obj in item["files"]:
            assert (
                "kipoi-docker" in file_obj["filename"]
                or "busybox_latest" in file_obj["filename"]
            )


def test_get_existing_sc_by_recordid(zenodo_client):
    response_json = zenodo_client.get_content(
        f"{singularityhelper.ZENODO_DEPOSITION}/5643929"
    )
    assert (
        response_json["files"][0]["filename"] == "kipoi-docker_deeptarget.sif"
    )


def test_update_existing_singularity_container(
    zenodo_client, test_singularity_dict
):
    new_test_singularity_dict = (
        singularityhelper.update_existing_singularity_container(
            zenodo_client=zenodo_client,
            singularity_dict=test_singularity_dict,
            singularity_image_folder=Path(__file__).parent.resolve(),
            model_group="Test",
            file_to_upload="busybox_1.34.1.sif",
        )
    )
    for key in ["url", "md5", "name"]:
        assert new_test_singularity_dict.get(key) == test_singularity_dict.get(
            key
        )  # If push=True this will be different
    assert new_test_singularity_dict["file_id"] == ""
    zenodo_client.delete_content(
        f"{singularityhelper.ZENODO_DEPOSITION}/{new_test_singularity_dict.get('new_deposition_id')}"
    )


def test_push_new_singularity_image(zenodo_client, test_singularity_dict):
    new_singularity_dict = singularityhelper.push_new_singularity_image(
        zenodo_client=zenodo_client,
        singularity_image_folder=Path(__file__).parent.resolve(),
        singularity_dict=test_singularity_dict,
        model_group="Dummy",
        file_to_upload="busybox_1.34.1.sif",
    )
    for key in ["url", "md5", "name"]:
        assert test_singularity_dict.get(key) == new_singularity_dict.get(key)
    zenodo_client.delete_content(
        f"{singularityhelper.ZENODO_DEPOSITION}/{new_singularity_dict.get('new_deposition_id')}"
    )
