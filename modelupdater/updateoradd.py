from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys

import docker
from github import Github
import pytest
from ruamel.yaml import round_trip_load, round_trip_dump
from ruamel.yaml.scalarstring import DoubleQuotedScalarString


def get_list_of_updated_models(
    source_commit_hash, target_commit_hash, kipoi_model_repo
):
    comparison_obj = kipoi_model_repo.compare(
        base=source_commit_hash, head=target_commit_hash
    )
    return list(
        dict.fromkeys([f.filename.split("/")[0] for f in comparison_obj.files])
    )


def build_docker_image(dockerfile_path, name_of_docker_image):
    client = docker.from_env()
    with open(dockerfile_path, "r") as dockerfile:
        dockerfile_obj = BytesIO(dockerfile.read().encode("utf-8"))
    try:
        client.images.build(
            fileobj=dockerfile_obj, tag=name_of_docker_image, nocache=True
        )
    except docker.errors.BuildError as e:
        raise (e)
    except docker.errors.APIError as e:
        raise (e)


def update(model, name_of_docker_image):
    # TODO: Add provision for mmsplice and mmsplice/mtsplice
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
        # TODO: Edge cases


def run_docker_image(image_name, model_name):
    client = docker.from_env()
    try:
        container_log = client.containers.run(
            image=image_name,
            command=f"kipoi test {model_name} --source=kipoi",
        )
    except docker.errors.ImageNotFound:
        raise (f"Image {image_name} is not found")
    except docker.errors.ContainerError as e:
        raise (e)
    except docker.errors.APIError as e:
        raise (e)
    client.containers.prune()
    client.networks.prune()
    client.volumes.prune()
    print(container_log.decode("utf-8"))


def update_github_workflow_files(image_name, list_of_models, model_group):
    with open(
        ".github/workflows/build-and-test-images.yml",
        "r",
    ) as f:
        data = round_trip_load(f, preserve_quotes=True)
    data["jobs"]["buildandtest"]["strategy"]["matrix"]["image"].append(
        DoubleQuotedScalarString(image_name.split(":")[1])
    )
    with open(".github/workflows/build-and-test-images.yml", "w") as f:
        round_trip_dump(data, f)

    with open(
        ".github/workflows/test-images.yml",
        "r",
    ) as f:
        data = round_trip_load(f, preserve_quotes=True)
    if list_of_models:
        data["jobs"]["test"]["strategy"]["matrix"]["model"].append(
            DoubleQuotedScalarString(list_of_models[0])
        )
    else:
        data["jobs"]["test"]["strategy"]["matrix"]["model"].append(
            DoubleQuotedScalarString(model_group)
        )
    with open(".github/workflows/test-images.yml", "w") as f:
        round_trip_dump(data, f)


def add(model_group, kipoi_model_repo, kipoi_container_repo):
    print(f"Adding {model_group}")

    dockerfile_generator_path = (
        Path(__file__).resolve().parent / "dockerfiles/dockerfile-generator.sh"
    )
    # Create a new dockerfile
    subprocess.call(
        [
            "sh",
            dockerfile_generator_path,
            f"{model_group}",
        ],
    )

    # Build a docker image
    dockerfile_path = (
        Path(__file__).resolve().parent
        / f"dockerfiles/Dockerfile.{model_group.lower()}"
    )
    image_name = f"haimasree/kipoi-docker:{model_group.lower()}"
    build_docker_image(
        dockerfile_path=dockerfile_path, name_of_docker_image=image_name
    )

    # Test the newly created container
    list_of_models = get_list_of_models_from_repo(
        model_group=model_group, kipoi_model_repo=kipoi_model_repo
    )
    if list_of_models:
        for model_name in list_of_models:
            # Run the newly created container
            run_docker_image(image_name=image_name, model_name=model_name)
    else:
        run_docker_image(image_name=image_name, model_name=model_group)

    # TODO: Push the newly created container

    # Update tests and json files
    with open(
        Path.cwd() / "test-containers" / "model-group-to-image-name.json", "r"
    ) as infile:
        model_group_to_image_dict = json.load(infile)
    model_group_to_image_dict.update({f"{model_group}": f"{image_name}"})
    with open(
        Path.cwd() / "test-containers" / "model-group-to-image-name.json", "w"
    ) as fp:
        json.dump(model_group_to_image_dict, fp, indent=2)

    with open(
        Path.cwd() / "test-containers" / "image-name-to-model.json", "r"
    ) as infile:
        image_name_to_model_dict = json.load(infile)
    image_name_to_model_dict.update(
        {image_name: list_of_models}
        if list_of_models
        else {image_name: [model_group]}
    )
    with open(
        Path.cwd() / "test-containers" / "image-name-to-model.json", "w"
    ) as fp:
        json.dump(image_name_to_model_dict, fp, indent=2)

    # Update github workflow files
    update_github_workflow_files(
        image_name=image_name,
        list_of_models=list_of_models,
        model_group=model_group,
    )


def update_or_add_model_container(
    model, kipoi_model_repo, kipoi_container_repo
):
    with open(
        Path.cwd() / "test-containers" / "model-group-to-image-name.json", "r"
    ) as infile:
        model_group_to_image_dict = json.load(infile)
    if model in model_group_to_image_dict:
        update(model, model_group_to_image_dict[model])
        # TODO: Strategy for updating kipoi-model-repo-hash
    else:
        add(
            model=model,
            kipoi_model_repo=kipoi_model_repo,
            kipoi_container_repo=kipoi_container_repo,
        )


def get_list_of_models_from_repo(model_group, kipoi_model_repo):
    contents = kipoi_model_repo.get_contents(model_group)
    list_of_models = [
        f"{model_group}/{content_file.name}"
        for content_file in contents
        if content_file.type == "dir"
    ]
    return list_of_models


if __name__ == "__main__":
    g = Github(os.environ["GITHUB_PAT"])
    kipoi_container_repo = g.get_user().get_repo("kipoi-containers")
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
                update_or_add_model_container(
                    model=model,
                    kipoi_model_repo=kipoi_model_repo,
                    kipoi_container_repo=kipoi_container_repo,
                )
    else:
        print("No need to update the repo")

    # If everything has gone well so far update kipoi-model-hash
    with open(
        "./model-updater/kipoi-model-repo-hash", "w"
    ) as kipoimodelrepohash:
        kipoimodelrepohash.write(target_commit_hash)
