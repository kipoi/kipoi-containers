import os
import requests
import json
from pathlib import Path

import pytest

from modelupdater import singularityhandler
from modelupdater import zenodoclient


# @pytest.fixture(scope="module")
# def zenodo_client():
#     return zenodoclient.Client()


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
