import os
from pathlib import Path

from kipoi_containers.updateoradd import (
    DOCKER_TO_MODEL_JSON,
    MODEL_GROUP_TO_SINGULARITY_JSON,
)
from kipoi_containers.helper import populate_json
from kipoi_containers.singularityhelper import get_singularity_image


class TestContainers:
    image_name = None
    modelgroup_name = None
    docker_to_model_dict = populate_json(DOCKER_TO_MODEL_JSON)
    model_group_to_singularity_dict = populate_json(
        MODEL_GROUP_TO_SINGULARITY_JSON
    )

    def test_parameters(self):
        assert self.image_name not in [None, "kipoi-base-env"]
        assert not self.modelgroup_name or (
            self.modelgroup_name
            and self.image_name not in [None, "kipoi-base-env"]
        )
        assert self.docker_to_model_dict != {}

    def test_images(self, test_docker_image, test_singularity_image):
        singularity_pull_folder = os.environ.get(
            "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
        )
        print(singularity_pull_folder)
        if self.modelgroup_name and self.image_name not in [
            None,
            "kipoi-base-env",
        ]:
            models = self.docker_to_model_dict.get(self.image_name)
            singularity_image = get_singularity_image(
                singularity_pull_folder,
                self.model_group_to_singularity_dict,
                self.modelgroup_name,
            )
            for model in models:
                if model.split("/")[0] in self.modelgroup_name:
                    test_docker_image(
                        model_name=model, image_name=self.image_name
                    )
                    test_singularity_image(
                        singularity_image_folder=singularity_pull_folder,
                        singularity_image_name=singularity_image,
                        model=model,
                    )
        elif self.image_name not in [None, "kipoi-base-env"]:
            models = self.docker_to_model_dict.get(self.image_name)
            singularity_image_names = [
                get_singularity_image(
                    singularity_pull_folder,
                    self.model_group_to_singularity_dict,
                    model,
                )
                for model in models
            ]
            assert len(models) == len(singularity_image_names)
            for model, singularity_image in zip(
                models, singularity_image_names
            ):
                print(f"Testing {model} with {self.image_name}")
                test_docker_image(model_name=model, image_name=self.image_name)
                test_singularity_image(
                    singularity_image_folder=singularity_pull_folder,
                    singularity_image_name=singularity_image,
                    model=model,
                )
