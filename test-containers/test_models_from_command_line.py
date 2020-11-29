from pathlib import Path
import json

import docker


def run_test(model_name, image_name):
    if model_name == "Basenji":
        test_cmd = f'kipoi test {model_name} --source=kipoi --batch_size=2'
    else:
        test_cmd = f'kipoi test {model_name} --source=kipoi'
    client = docker.from_env()
    try:
        container_log = client.containers.run(
            image=image_name, command=test_cmd)
    except docker.errors.ImageNotFound:
        raise(f"Image {image_name} is not found")
    except docker.errors.ContainerError as e:
        raise(e)
    except docker.errors.APIError as e:
        raise(e)

    print(container_log.decode("utf-8"))


def pytest_generate_tests(metafunc):
    ''' just to attach the cmd-line args to a test-class that needs them '''
    model_from_cmd_line = metafunc.config.getoption("model")

    if model_from_cmd_line and hasattr(metafunc.cls, 'model_name'):
        metafunc.cls.model_name = model_from_cmd_line[0]
        with open(Path.cwd() / "test-containers" / "model-group-to-image-name.json", "r") as infile:
            metafunc.cls.model_group_to_image_dict = json.load(infile)


class TestServerCode(object):
    model_name = None
    model_group_to_image_dict = {}

    def test_parameters(self):
        assert self.model_name != None
        assert self.model_group_to_image_dict != {}

    def test_other(self):
        if self.model_name != None:
            assert self.model_name in self.model_group_to_image_dict or self.model_name.split(
                '/')[0] in self.model_group_to_image_dict

            if self.model_name in self.model_group_to_image_dict:  # For MMSplice/mtsplice
                image_name = self.model_group_to_image_dict.get(self.model_name)
                print(f"model_name={self.model_name}, image_name={image_name}")
                run_test(model_name=self.model_name, image_name=image_name)

            # Extract the model group
            elif self.model_name.split('/')[0] in self.model_group_to_image_dict:
                image_name = self.model_group_to_image_dict.get(
                    self.model_name.splite('/')[0])
                print(f"model_name={self.model_name}, image_name={image_name}")
                run_test(model_name=self.model_name, image_name=image_name)
