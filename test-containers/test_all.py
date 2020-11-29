import json
from pathlib import Path

import docker
import pytest

def test_containers_and_models():
    with open(Path.cwd()/ "test-containers" / "image-name-to-model.json", "r") as infile:
        image_to_model_dict = json.load(infile)

    for image_name, model_group in image_to_model_dict.items():
        for model in model_group:
            print(f"image name = {image_name}, model_name={model}")
            if model == "Basenji":
                test_cmd = f'kipoi test {model} --source=kipoi --batch_size=2'
            else:
                test_cmd = f'kipoi test {model} --source=kipoi'
            client = docker.from_env()
            try:
                container_log = client.containers.run(image=image_name, command=test_cmd)
            except docker.errors.ImageNotFound:
                raise(f"Image {image_name} is not found")
            except docker.errors.ContainerError as e:
                raise(e)
            except docker.errors.APIError as e:
                raise(e)
            print(container_log.decode("utf-8"))
            client.images.prune(filters={'dangling': False})