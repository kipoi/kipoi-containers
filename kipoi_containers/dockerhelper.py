from io import BytesIO
import os
from pathlib import Path
from typing import Union, Dict
import docker

from kipoi_containers.logger import bot


def cleanup(images: bool = False) -> None:
    """
    Cleans up unused docker containers, volumes and networks.
    If images is true cleanup the images as well.
    """
    client = docker.from_env()
    client.containers.prune()
    client.networks.prune()
    client.volumes.prune()
    if images:
        client.images.prune(filters={"dangling": True})


def build_docker_image(
    dockerfile_path: Union[str, Path], name_of_docker_image: str
) -> None:
    """
    This function builds a docker image from scratch using dockerfile_path

    Raises:
      docker.errors.BuildError: If the docker image cannot be build
      docker.errors.APIError: If there is an issue connecting to the docker api
    """
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


def test_docker_image(image_name: str, model_name: str) -> None:
    """
    Runs a container for a given docker image and run
    kipoi test <model_name> --source=kipoi inside
    the container, followed by a cleanup

    Raises:
        docker.errors.ImageNotFound: if <image_name> cannot be found
        docker.errors.ContainerError: If errors are raised during execution of the container
        docker.errors.APIError: If there is an issue connecting to the docker api
    """
    if model_name == "Basenji":
        test_cmd = f"kipoi test {model_name} --source=kipoi --batch_size=2"
    else:
        test_cmd = f"kipoi test {model_name} --source=kipoi"
    client = docker.from_env()
    try:
        container_log = client.containers.run(
            image=image_name,
            command=test_cmd,
        )
    except docker.errors.ImageNotFound:
        raise (f"Image {image_name} is not found")
    except docker.errors.ContainerError as e:
        raise (e)
    except docker.errors.APIError as e:
        raise (e)
    cleanup()
    bot.info(container_log.decode("utf-8"))


def test_docker_image_without_exception(
    image_name: str, model_name: str
) -> None:
    """
    Runs a container for a given docker image and run
    kipoi test <model_name> --source=kipoi inside
    the container, followed by a cleanup, without raising an exception
    """
    client = docker.from_env()
    try:
        container_log = client.containers.run(
            image=image_name,
            command=f"kipoi test {model_name} --source=kipoi",
        )
    except docker.errors.ImageNotFound:
        cleanup()
        return False
    except docker.errors.ContainerError:
        cleanup()
        return False
    except docker.errors.APIError:
        cleanup()
        return False
    cleanup()
    bot.info(container_log.decode("utf-8"))
    return True


def push_docker_image(tag: str) -> None:
    """
    This function pushes kipoi/kipoi-docker:<tag> to dockerhub

    Raises:
      docker.errors.APIError: If there is an issue connecting to the docker api
    """
    client = docker.from_env()
    auth_config = {
        "username": os.environ["DOCKER_USERNAME"],
        "password": os.environ["DOCKER_PASSWORD"],
    }
    try:
        client.images.push(
            repository="kipoi/kipoi-docker",
            tag=tag,
            auth_config=auth_config,
        )
    except docker.errors.APIError as e:
        raise (e)
