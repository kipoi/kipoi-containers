import pytest

from kipoi_containers.singularityhelper import (
    build_singularity_image,
    test_singularity_image,
)


def test_singularity_buildandtest(tmp_path):
    singularity_dir = tmp_path / "singularity"
    singularity_dir.mkdir()
    singularity_image = "kipoi-docker_aparent-veff-slim.sif"
    build_singularity_image(
        name_of_docker_image="kipoi/kipoi-docker:aparent-veff-slim",
        singularity_image_name=singularity_image,
        singularity_image_folder=singularity_dir,
    )
    test_singularity_image(
        singularity_image_folder=singularity_dir,
        singularity_image_name=singularity_image,
        model="APARENT/veff",
    )
