import csv
import json
from pathlib import Path
import subprocess

import pandas as pd
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from .dockerhelper import (
    build_docker_image,
    cleanup,
    run_docker_image,
    run_docker_image_without_exception,
    push_docker_image,
)
from .helper import populate_yaml, write_yaml


class ModelAdder:
    def __init__(self, model_group, kipoi_model_repo, kipoi_container_repo):
        """
        This function instantiates ModelAdder class with the model_group to
        add, kipoi model repo and this repository

        Parameters
        ----------
        model_group : str
            Model group to add
        kipoi_model_repo : github.Repository.Repository
            github.Repository.Repository instance of
            https://github.com/kipoi/models
        kipoi_container_repo : github.Repository.Repository
            github.Repository.Repository instance of this repository
        """
        self.kipoi_model_repo = kipoi_model_repo
        self.kipoi_container_repo = kipoi_container_repo
        self.model_group = model_group
        self.image_name = f"kipoi/kipoi-docker:{self.model_group.lower()}"
        self.list_of_models = []

    def update_github_workflow_files(
        self, test_image_yaml, release_workflow_yaml
    ):
        """
        Update github actions CI workflow files with the newly added model
        """
        data = populate_yaml(test_image_yaml)
        update_list = data["jobs"]["test"]["strategy"]["matrix"]["model"]
        if self.list_of_models:
            update_list.append(
                DoubleQuotedScalarString(self.list_of_models[0])
            )
        else:
            update_list.append(DoubleQuotedScalarString(self.model_group))
        write_yaml(test_image_yaml, data)

        data = populate_yaml(release_workflow_yaml)
        if "sharedpy3keras2" in self.image_name:
            data["jobs"]["buildandtestsharedpy3keras2"]["strategy"]["matrix"][
                "modelgroup"
            ].append(DoubleQuotedScalarString(self.model_group))
        else:
            data["jobs"]["buildtestandpush"]["strategy"]["matrix"][
                "image"
            ].append(DoubleQuotedScalarString(self.image_name.split(":")[1]))
        write_yaml(release_workflow_yaml, data)

    def update_test_and_json_files(
        self, model_group_to_docker_dict, docker_to_model_dict
    ):
        """
        Update docker-to-model.json and model-group-to-docker.json
        with the newly added model and the corresponding docker image
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

    def get_list_of_models_from_repo(self):

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

    def is_compatible_with_existing_image(self):
        """
        This function tests if the new model group is compatible
        with existng shared images -
        "kipoi/kipoi-docker:sharedpy3keras2" and
        "kipoi/kipoi-docker:sharedpy3keras1.2",

        Returns
        -------
        bool
            If the new model group is found to be compatible with
            one of the above mentioned shared image,  it updates
            class variable image_name to the compatible image name
            and returns True. It will return False otherwise.

        """
        for image_name in [
            "kipoi/kipoi-docker:sharedpy3keras2",
            "kipoi/kipoi-docker:sharedpy3keras1.2",
        ]:
            if self.list_of_models:
                for model_name in self.list_of_models:
                    # Run the newly created container
                    if run_docker_image_without_exception(
                        image_name=image_name, model_name=model_name
                    ):
                        self.image_name = image_name
                        return True
            else:
                if run_docker_image_without_exception(
                    image_name=image_name, model_name=self.model_group
                ):
                    self.image_name = image_name
                    return True
        return False

    def add(self, model_group_to_docker_dict, docker_to_model_dict):
        """
        This function adds a newly added model group to this repo. The steps are -
        1. Test the model group with two available docker images for shared
           environments - kipoi/kipoi-docker:sharedpy3keras2 and
           kipoi/kipoi-docker:sharedpy3keras1.2. If the tests pass go to step
           5. Otherwise folow step 2-4
        2. Create the appropriate dockerfile using a generator
        3. Build the image
        4. Test the image with all models from this newly added model group
        5. Update model group to image name map and image name to model name map
        6. Update github workflow files with this newly added model group
        """
        self.list_of_models = self.get_list_of_models_from_repo()
        if self.is_compatible_with_existing_image():
            self.update_test_and_json_files(
                model_group_to_docker_dict, docker_to_model_dict
            )
            self.update_github_workflow_files()
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
                    run_docker_image(
                        image_name=self.image_name, model_name=model_name
                    )
            else:
                run_docker_image(
                    image_name=self.image_name, model_name=self.model_group
                )

            # Push the container
            push_docker_image(tag=self.image_name.split(":")[1])
            cleanup(images=True)

            test_image_yaml = ".github/workflows/test-images.yml"
            release_workflow_yaml = ".github/workflows/release-workflow.yml"

            self.update_test_and_json_files(
                model_group_to_docker_dict, docker_to_model_dict
            )
            self.update_github_workflow_files(
                test_image_yaml, release_workflow_yaml
            )
