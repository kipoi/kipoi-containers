import os
from pathlib import Path

import docker
from github import Github

from kipoi_containers.updateoradd import (
    MODEL_GROUP_TO_SINGULARITY_JSON,
    MODEL_GROUP_TO_DOCKER_JSON,
)
from kipoi_containers.helper import (
    populate_json,
    populate_json_from_kipoi,
    logger,
)
from kipoi_containers.singularityhelper import get_singularity_image


class TestModels:
    model_name = None
    model_group_to_docker_dict = populate_json_from_kipoi(
        MODEL_GROUP_TO_DOCKER_JSON,
        Github(os.environ["GITHUB_TOKEN"])
        .get_organization("kipoi")
        .get_repo("models"),
    )
    model_group_to_singularity_dict = populate_json_from_kipoi(
        MODEL_GROUP_TO_SINGULARITY_JSON,
        Github(os.environ["GITHUB_TOKEN"])
        .get_organization("kipoi")
        .get_repo("models"),
    )
    list_of_models = []

    def get_image_name(self, model):
        assert (
            model in self.model_group_to_docker_dict
            or model.split("/")[0] in self.model_group_to_docker_dict
        )
        if model in self.model_group_to_docker_dict:  # For MMSplice/mtsplice
            image_name = self.model_group_to_docker_dict.get(model)
        elif model.split("/")[0] in self.model_group_to_docker_dict:
            image_name = self.model_group_to_docker_dict.get(
                model.split("/")[0]
            )
        return image_name

    def test_parameters(self):
        assert self.model_name is not None or self.list_of_models != []
        assert self.model_group_to_docker_dict != {}
        assert self.model_group_to_singularity_dict != {}

    def test_models(self, test_docker_image, test_singularity_image):
        singularity_pull_folder = os.environ.get(
            "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
        )
        if self.list_of_models:
            for model in self.list_of_models:
                image_name = self.get_image_name(model=model)
                test_docker_image(image_name=image_name, model_name=model)
                singularity_image = get_singularity_image(
                    singularity_pull_folder,
                    self.model_group_to_singularity_dict,
                    model,
                )
                image_name = self.get_image_name(model=model)
                slim_image = f"{image_name}-slim"
                logger.info(f"Testing {model} with {image_name}")
                test_docker_image(image_name=image_name, model_name=model)
                logger.info(f"Testing {model} with {slim_image}")
                test_docker_image(image_name=slim_image, model_name=model)
                test_singularity_image(
                    singularity_image_folder=singularity_pull_folder,
                    singularity_image_name=singularity_image,
                    model=model,
                )
        elif self.model_name is not None:
            for model in self.model_name:
                image_name = self.get_image_name(model=model)
                test_docker_image(image_name=image_name, model_name=model)
                singularity_image = get_singularity_image(
                    singularity_pull_folder,
                    self.model_group_to_singularity_dict,
                    model,
                )
                image_name = self.get_image_name(model=model)
                slim_image = f"{image_name}-slim"
                logger.info(f"Testing {model} with {image_name}")
                test_docker_image(image_name=image_name, model_name=model)
                logger.info(f"Testing {model} with {slim_image}")
                test_docker_image(image_name=slim_image, model_name=model)
                test_singularity_image(
                    singularity_image_folder=singularity_pull_folder,
                    singularity_image_name=singularity_image,
                    model=model,
                )
