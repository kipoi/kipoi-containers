import os
from pathlib import Path

import pytest

from kipoi_containers.singularityhelper import build_singularity_image


@pytest.fixture
def test_singularity_image():
    from kipoi_containers.singularityhelper import test_singularity_image

    return test_singularity_image


def test_singularity_buildandtest(test_singularity_image):
    singularity_image_folder = os.environ.get(
        "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
    )
    singularity_image = "kipoi-docker_aparent-veff-slim.sif"
    build_singularity_image(
        name_of_docker_image="kipoi/kipoi-docker:aparent-veff-slim",
        singularity_image_name=singularity_image,
        singularity_image_folder=singularity_image_folder,
    )
    test_singularity_image(
        singularity_image_folder=singularity_image_folder,
        singularity_image_name=singularity_image,
        model="APARENT/veff",
    )
