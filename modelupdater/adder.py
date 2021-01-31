import json
from pathlib import Path
import subprocess

from helper import build_docker_image, run_docker_image
from ruamel.yaml import round_trip_load, round_trip_dump
from ruamel.yaml.scalarstring import DoubleQuotedScalarString


class ModelAdder:
    def __init__(self, model_group, kipoi_model_repo, kipoi_container_repo):
        self.kipoi_model_repo = kipoi_model_repo
        self.kipoi_container_repo = kipoi_container_repo
        self.model_group = model_group
        self.image_name = f"haimasree/kipoi-docker:{self.model_group.lower()}"
        self.list_of_models = []

    def update_github_workflow_files(self):
        with open(
            ".github/workflows/build-and-test-images.yml",
            "r",
        ) as f:
            data = round_trip_load(f, preserve_quotes=True)
        data["jobs"]["buildandtest"]["strategy"]["matrix"]["image"].append(
            DoubleQuotedScalarString(self.image_name.split(":")[1])
        )
        with open(".github/workflows/build-and-test-images.yml", "w") as f:
            round_trip_dump(data, f)

        with open(
            ".github/workflows/test-images.yml",
            "r",
        ) as f:
            data = round_trip_load(f, preserve_quotes=True)
        if self.list_of_models:
            data["jobs"]["test"]["strategy"]["matrix"]["model"].append(
                DoubleQuotedScalarString(self.list_of_models[0])
            )
        else:
            data["jobs"]["test"]["strategy"]["matrix"]["model"].append(
                DoubleQuotedScalarString(self.model_group)
            )
        with open(".github/workflows/test-images.yml", "w") as f:
            round_trip_dump(data, f)

    def get_list_of_models_from_repo(self):
        contents = self.kipoi_model_repo.get_contents(self.model_group)
        self.list_of_models = [
            f"{self.model_group}/{content_file.name}"
            for content_file in contents
            if content_file.type == "dir"
        ]

    def update_test_and_json_files(self):
        with open(
            Path.cwd() / "test-containers" / "model-group-to-image-name.json",
            "r",
        ) as infile:
            model_group_to_image_dict = json.load(infile)
        model_group_to_image_dict.update(
            {f"{self.model_group}": f"{self.image_name}"}
        )
        with open(
            Path.cwd() / "test-containers" / "model-group-to-image-name.json",
            "w",
        ) as fp:
            json.dump(model_group_to_image_dict, fp, indent=2)

        with open(
            Path.cwd() / "test-containers" / "image-name-to-model.json", "r"
        ) as infile:
            image_name_to_model_dict = json.load(infile)
        image_name_to_model_dict.update(
            {self.image_name: self.list_of_models}
            if self.list_of_models
            else {self.image_name: [self.model_group]}
        )
        with open(
            Path.cwd() / "test-containers" / "image-name-to-model.json", "w"
        ) as fp:
            json.dump(image_name_to_model_dict, fp, indent=2)

    def add(self):
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
        dockerfile_path = f"dockerfiles/Dockerfile.{self.model_group.lower()}"
        build_docker_image(
            dockerfile_path=dockerfile_path,
            name_of_docker_image=self.image_name,
        )

        # Test the newly created container
        self.get_list_of_models_from_repo()

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

        self.update_test_and_json_files()
        self.update_github_workflow_files()
