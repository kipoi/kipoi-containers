import os
from pathlib import Path

from kipoi_containers.updateoradd import DOCKER_TO_MODEL_JSON
from kipoi_containers.helper import populate_json


class TestContainers:
    image_name = None
    modelgroup_name = None
    docker_to_model_dict = populate_json(DOCKER_TO_MODEL_JSON)

    def test_parameters(self):
        assert self.image_name not in [None, "kipoi-base-env"]
        assert not self.modelgroup_name or (
            self.modelgroup_name
            and self.image_name not in [None, "kipoi-base-env"]
        )
        assert self.docker_to_model_dict != {}

    def test_images(self, test_docker_image):
        if self.modelgroup_name and self.image_name not in [
            None,
            "kipoi-base-env",
        ]:
            models = self.docker_to_model_dict.get(self.image_name)
            if not models:
                raise ValueError("Each model group must have one model")
            if (
                isinstance(self.modelgroup_name, list)
                and len(self.modelgroup_name) == 1
            ):
                self.modelgroup_name = self.modelgroup_name[0]
            for model in models:
                if model.split("/")[0] in self.modelgroup_name:
                    test_docker_image(
                        model_name=model, image_name=self.image_name
                    )
                    if self.modelgroup_name != "DeepSEA":
                        break
                    else:
                        continue
        elif self.image_name not in [None, "kipoi-base-env"]:
            models = self.docker_to_model_dict.get(self.image_name)
            for model in models:
                print(f"Testing {model} with {self.image_name}")
                test_docker_image(model_name=model, image_name=self.image_name)
