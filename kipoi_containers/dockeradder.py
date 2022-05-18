import csv
import json
from pathlib import Path
import subprocess
from typing import Dict, List, TYPE_CHECKING

import pandas as pd
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from kipoi_containers.dockerhelper import (
    build_docker_image,
    cleanup,
    test_docker_image,
    test_docker_image_without_exception,
    push_docker_image,
)
from kipoi_containers.helper import populate_yaml, write_yaml

if TYPE_CHECKING:
    from github.Repository import Repository


class DockerAdder:
    def __init__(
        self,
        model_group: str,
        kipoi_model_repo: "Repository",
        kipoi_container_repo: "Repository",
    ) -> None:
        """
        This function instantiates DockerAdder class with model group to
        add, kipoi model repo and this repository
        """
        self.kipoi_model_repo = kipoi_model_repo
        self.kipoi_container_repo = kipoi_container_repo
        self.model_group = model_group
        self.image_name = f"kipoi/kipoi-docker:{self.model_group.lower()}"
        self.list_of_models = []

    def update_content(
        self,
        model_group_to_docker_dict: Dict,
        docker_to_model_dict: Dict,
        workflow_test_data: Dict,
        workflow_release_data: Dict,
    ) -> None:
        """
        Update various dictionaries from the json and github
         workflow files with the newly added model and the
         corresponding docker image
        """
        model_group_to_docker_dict.update(
            {f"{self.model_group}": f"{self.image_name}"}
        )
        if self.image_name in docker_to_model_dict:
            if self.list_of_models:
                docker_to_model_dict[self.image_name].extend(
                    self.list_of_models
                )
            else:
                docker_to_model_dict[self.image_name].append(self.model_group)
        else:
            docker_to_model_dict.update(
                {self.image_name: self.list_of_models}
                if self.list_of_models
                else {self.image_name: [self.model_group]}
            )

        update_test_list = workflow_test_data["jobs"]["test"]["strategy"][
            "matrix"
        ]["model"]
        if self.list_of_models:
            update_test_list.append(
                DoubleQuotedScalarString(self.list_of_models[0])
            )
        else:
            update_test_list.append(DoubleQuotedScalarString(self.model_group))

        if "sharedpy3keras2" in self.image_name:
            workflow_release_data["jobs"]["buildandtestsharedpy3keras2"][
                "strategy"
            ]["matrix"]["modelgroup"].append(
                DoubleQuotedScalarString(self.model_group)
            )
        else:
            workflow_release_data["jobs"]["buildtestandpush"]["strategy"][
                "matrix"
            ]["image"].append(
                DoubleQuotedScalarString(self.image_name.split(":")[1])
            )

    def get_list_of_models_from_repo(self) -> List:
        """
        This model returns a list of models listed under a model group
        at https://github.com/kipoi/models

        Returns
        -------
        list
        List of models under a model group
        """
        contents = self.kipoi_model_repo.get_contents(self.model_group)
        for content_file in contents:
            if content_file.name == "models.tsv":
                model_tsv = pd.read_csv(
                    content_file.download_url, delimiter="\t"
                )
                return [f"{self.model_group}/{m}" for m in model_tsv["model"]]

    def is_compatible_with_existing_image(self) -> bool:
        """
        This function tests if the new model group is compatible
        with existng shared images -
        "kipoi/kipoi-docker:sharedpy3keras2tf1",
        "kipoi/kipoi-docker:sharedpy3keras2tf2"
        and "kipoi/kipoi-docker:sharedpy3keras1.2". If it is found
        to be compatible, it updates class variable image_name
        to the compatible image name and returns True. It will
        return False otherwise.
        """
        for image_name in [
            "kipoi/kipoi-docker:sharedpy3keras2tf1",
            "kipoi/kipoi-docker:sharedpy3keras2tf2",
            "kipoi/kipoi-docker:sharedpy3keras1.2",
        ]:
            if self.list_of_models:
                for model_name in self.list_of_models:
                    # Run the newly created container
                    if test_docker_image_without_exception(
                        image_name=image_name, model_name=model_name
                    ):
                        self.image_name = image_name
                        return True
            else:
                if test_docker_image_without_exception(
                    image_name=image_name, model_name=self.model_group
                ):
                    self.image_name = image_name
                    return True
        return False

    def add(
        self,
        model_group_to_docker_dict: Dict,
        docker_to_model_dict: Dict,
        workflow_test_data: Dict,
        workflow_release_data: Dict,
    ) -> None:
        """
        This function adds a newly added model group to this repo. The steps are -
        1. Test the model group with three available docker images for shared
           environments - kipoi/kipoi-docker:sharedpy3keras2tf1,
           kipoi/kipoi-docker:sharedpy3keras2tf2 and
           kipoi/kipoi-docker:sharedpy3keras1.2. If the tests pass go to step
           6. Otherwise folow step 2-5
        2. Create the appropriate dockerfile using a generator
        3. Build the image
        4. Test the image with all models from this newly added model group
        5. Push the image and cleanup
        6. Update model group to docker image dict and docker image to model name dict
        7. Update github workflow files with this newly added model group
        """
        self.list_of_models = self.get_list_of_models_from_repo()
        if self.is_compatible_with_existing_image():
            self.update_content(
                model_group_to_docker_dict,
                docker_to_model_dict,
                workflow_test_data,
                workflow_release_data,
            )
        else:
            dockerfile_generator_path = "dockerfiles/dockerfile-generator.sh"
            # Create a new dockerfile
            subprocess.call(
                [
                    "bash",
                    dockerfile_generator_path,
                    f"{self.model_group}",
                ],
            )

            # Build a docker image
            dockerfile_path = (
                f"dockerfiles/Dockerfile.{self.model_group.lower()}"
            )
            build_docker_image(
                dockerfile_path=dockerfile_path,
                name_of_docker_image=self.image_name,
            )

            # Test the newly created container
            if self.list_of_models:
                for model_name in self.list_of_models:
                    # Run the newly created container
                    test_docker_image(
                        image_name=self.image_name, model_name=model_name
                    )
            else:
                test_docker_image(
                    image_name=self.image_name, model_name=self.model_group
                )

            # Push the container
            push_docker_image(tag=self.image_name.split(":")[1])
            cleanup(images=True)

            self.update_content(
                model_group_to_docker_dict,
                docker_to_model_dict,
                workflow_test_data,
                workflow_release_data,
            )
