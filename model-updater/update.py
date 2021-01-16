from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys

import docker
from github import Github
import pytest


def get_list_of_updated_models(
    source_commit_hash, target_commit_hash, kipoi_model_repo
):
    comparison_obj = kipoi_model_repo.compare(
        base=source_commit_hash, head=target_commit_hash
    )
    return list(
        dict.fromkeys([f.filename.split("/")[0] for f in comparison_obj.files])
    )


def update(model, name_of_docker_image):
    # TODO: Add provision for mmsplice and mmsplice/mtsplice
    print(f"Updating {model} and {name_of_docker_image}")
    client = docker.from_env()
    dockerfile_path = (
        Path.cwd() / "dockerfiles" / f"Dockerfile.{model.lower()}"
    )
    if dockerfile_path.exists():
        with open(dockerfile_path, "r") as dockerfile:
            dockerfile_obj = BytesIO(dockerfile.read().encode("utf-8"))
        try:
            build_log = client.images.build(
                fileobj=dockerfile_obj, tag=name_of_docker_image
            )
            print(build_log)
            exitcode = pytest.main(
                [
                    "-s",
                    "test-containers/test_containers_from_command_line.py",
                    f"--image={name_of_docker_image}",
                ]
            )
            if exitcode != 0:
                print(
                    f"Updated docker image {name_of_docker_image} for {model} did not pass relevant tests"
                )
        except docker.errors.BuildError as e:
            raise (e)
        except docker.errors.APIError as e:
            raise (e)
    else:
        print(f"{model} needs to be containerized first")


def add(model):
    print(f"Adding {model}")


def update_or_add_model_container(model):
    with open(
        Path.cwd() / "test-containers" / "model-group-to-image-name.json", "r"
    ) as infile:
        model_group_to_image_dict = json.load(infile)
    if model in model_group_to_image_dict:
        update(model, model_group_to_image_dict[model])
        # TODO: Strategy for updating kipoi-model-repo-hash
    else:
        add(model)


if __name__ == "__main__":
    g = Github(sys.argv[1])
    kipoi_model_repo = g.get_organization("kipoi").get_repo("models")
    target_commit_hash = kipoi_model_repo.get_branch("master").commit.sha
    with open(
        "./model-updater/kipoi-model-repo-hash", "r"
    ) as kipoimodelrepohash:
        source_commit_hash = kipoimodelrepohash.readline()
    if source_commit_hash != target_commit_hash:
        list_of_updated_models = get_list_of_updated_models(
            source_commit_hash=source_commit_hash,
            target_commit_hash=target_commit_hash,
            kipoi_model_repo=kipoi_model_repo,
        )
        for model in list_of_updated_models:
            if model != "shared":
                update_or_add_model_container(model=model)
    else:
        print("No need to update the repo")
