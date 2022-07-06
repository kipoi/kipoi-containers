from pathlib import Path
import pytest
from typing import List

from kipoi_containers.dockerhelper import (
    build_docker_image,
    cleanup,
    push_docker_image,
    test_docker_image,
)

from kipoi_containers.logger import bot


class DockerUpdater:
    def __init__(self, model_group: str, name_of_docker_image: str) -> None:
        """
        This function instantiates the DockerUpdater class with model group and
        a docker image to update
        """
        self.model_group = model_group
        self.name_of_docker_image = name_of_docker_image

    def update(self, models_to_test: List) -> None:
        """
        This functions rebuilds the given docker image for the given modelgroup and
        tests all models specified by <models_to_test> with this new image. If all
        tests pass the new image is pushed to dockerhub followed by a cleanup.
        The steps are -
        1. Rebuild the image
        2. Rerun the tests for this image specified to <models_to_test>
        3. Push the docker image
        4. Cleanup

        Raises
        ------
        ValueError
            If the dockerfile path for the given model group does not exist
        """
        bot.info(
            f"Updating {self.model_group} and {self.name_of_docker_image}"
        )
        if self.model_group in [
            "MMSplice/mtsplice",
            "APARENT/veff",
            "APARENT/site_probabilities",
        ]:
            dockerfile_name = (
                f"Dockerfile.{self.model_group.replace('/', '-').lower()}"
            )
        elif self.model_group in [
            "MMSplice/pathogenicity",
            "MMSplice/splicingEfficiency",
            "MMSplice/deltaLogitPSI",
            "MMSplice/modularPredictions",
        ]:
            dockerfile_name = "Dockerfile.mmsplice"
        else:
            dockerfile_name = (
                f"Dockerfile.{self.model_group.split('/')[0].lower()}"
            )
        dockerfile_path = Path.cwd() / "dockerfiles" / dockerfile_name
        if "slim" in self.name_of_docker_image:
            dockerfile_path = Path(f"{dockerfile_path}-slim")
        if dockerfile_path.exists():
            bot.info(
                f"Building {self.name_of_docker_image} with {dockerfile_path}"
            )
            build_docker_image(
                dockerfile_path=dockerfile_path,
                name_of_docker_image=self.name_of_docker_image,
            )
            for model in models_to_test:
                test_docker_image(
                    image_name=self.name_of_docker_image, model_name=model
                )
            push_docker_image(tag=self.name_of_docker_image.split(":")[1])
            cleanup(images=True)
        else:
            raise ValueError(
                f"{self.model_group} needs to be containerized first"
            )
