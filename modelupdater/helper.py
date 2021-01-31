from io import BytesIO

import docker


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
