from pathlib import Path
import pytest

from helper import build_docker_image


class ModelUpdater:
    def __init__(self, kipoi_model_repo, kipoi_container_repo):
        self.kipoi_model_repo = kipoi_model_repo
        self.kipoi_container_repo = kipoi_container_repo
        self.list_of_models = []

    def update(self, model, name_of_docker_image):
        print(f"Updating {model} and {name_of_docker_image}")
        dockerfile_path = (
            Path.cwd() / "dockerfiles" / f"Dockerfile.{model.lower()}"
        )
        if dockerfile_path.exists():
            build_docker_image(
                dockerfile_path=dockerfile_path,
                name_of_docker_image=name_of_docker_image,
            )
            exitcode = pytest.main(
                [
                    "-s",
                    "test-containers/test_containers_from_command_line.py",
                    f"--image={name_of_docker_image}",
                ]
            )
            if exitcode != 0:
                raise ValueError(
                    f"Updated docker image {name_of_docker_image} for {model} did not pass relevant tests"
                )
        else:
            print(f"{model} needs to be containerized first")
