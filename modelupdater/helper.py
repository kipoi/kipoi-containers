from io import BytesIO

import docker


def cleanup(client):
    """
    Cleans up unused docker containers, volumes and networks

    Parameters
    ----------
    client : DockerClient
        A docker client configured from environment variables
    """
    client.containers.prune()
    client.networks.prune()
    client.volumes.prune()


def build_docker_image(dockerfile_path, name_of_docker_image):
    """
    This function builds a docker image
    Parameters
    ----------
    dockerfile_path : str
        Path to the dockerfile which will be used to build the docker
        image with no-cache option
    name_of_docker_image : str
        Name of the docker image to build
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


def run_docker_image(image_name, model_name):
    """
    Runs a container for a given docker image and run
    kipoi test <model_name> --source=kipoi inside
    the container, followed by a cleanup

    Parameters
    ----------
    image_name : str
        Name of the docker image
    model_name : str
        Name of the model to test
    """
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
    cleanup(client=client)
    print(container_log.decode("utf-8"))


def run_docker_image_without_exception(image_name, model_name):
    """
    Runs a container for a given docker image and run
    kipoi test <model_name> --source=kipoi inside
    the container, followed by a cleanup, without raising an exception

    Parameters
    ----------
    image_name : str
        Name of the docker image
    model_name : str
        Name of the model to test
    """
    client = docker.from_env()
    try:
        container_log = client.containers.run(
            image=image_name,
            command=f"kipoi test {model_name} --source=kipoi",
        )
    except docker.errors.ImageNotFound:
        cleanup(client=client)
        return False
    except docker.errors.ContainerError:
        cleanup(client=client)
        return False
    except docker.errors.APIError:
        cleanup(client=client)
        return False
    cleanup(client=client)
    print(container_log.decode("utf-8"))
    return True
