import os
from pathlib import Path

from kipoi_containers.updateoradd import DOCKER_TO_MODEL_JSON
from kipoi_containers.helper import populate_json, one_model_per_modelgroup


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

    def test_images(self, test_docker_image, test_singularity_image):
        if self.modelgroup_name and self.image_name not in [
            None,
            "kipoi-base-env",
        ]:
            models = self.docker_to_model_dict.get(self.image_name)
            if not models:
                raise ValueError("Each model group must have one model")

            for model in models:
                if model.split("/")[0] in self.modelgroup_name:
                    test_docker_image(
                        model_name=model, image_name=self.image_name
                    )
                    singularity_image_name = (
                        f"kipoi-docker_{self.image_name.split(':')[1]}.sif"
                    )
                    singularity_image_folder = os.environ.get(
                        "SINGULARITY_PULL_FOLDER",
                        Path(__file__).parent.resolve(),
                    )
                    test_singularity_image(
                        singularity_image_folder=singularity_image_folder,
                        singularity_image_name=singularity_image_name,
                        model=model,
                    )
                    # if self.modelgroup_name != "DeepSEA":
                    #     break
        elif self.image_name not in [None, "kipoi-base-env"]:
            models = self.docker_to_model_dict.get(self.image_name)
            # if "shared" in self.image_name:
            #     models = one_model_per_modelgroup(models)
            for model in models:
                print(f"Testing {model} with {self.image_name}")
                test_docker_image(model_name=model, image_name=self.image_name)
                singularity_image_name = (
                    f"kipoi-docker_{self.image_name.split(':')[1]}.sif"
                )
                singularity_image_folder = os.environ.get(
                    "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
                )
                test_singularity_image(
                    singularity_image_folder=singularity_image_folder,
                    singularity_image_name=singularity_image_name,
                    model=model,
                )
