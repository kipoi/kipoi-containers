import docker


def run_test(model_name, image_name):
    if model_name == "Basenji":
        test_cmd = f"kipoi test {model_name} --source=kipoi --batch_size=2"
    else:
        test_cmd = f"kipoi test {model_name} --source=kipoi"
    client = docker.from_env()
    try:
        container_log = client.containers.run(
            image=image_name, command=test_cmd
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


class TestServerCode(object):
    image_name = None
    modelgroup_name = None
    image_to_model_dict = {}

    def test_parameters(self):
        assert self.image_name not in [None, "kipoi-base-env"]
        assert not self.modelgroup_name or (
            self.modelgroup_name
            and self.image_name not in [None, "kipoi-base-env"]
        )
        assert self.image_to_model_dict != {}

    def test_images(self):
        if self.modelgroup_name and self.image_name not in [
            None,
            "kipoi-base-env",
        ]:
            models = self.image_to_model_dict.get(self.image_name)
            for model in models:
                if model.split("/")[0] in self.modelgroup_name:
                    run_test(model_name=model, image_name=self.image_name)
        elif self.image_name not in [None, "kipoi-base-env"]:
            models = self.image_to_model_dict.get(self.image_name)
            for model in models:
                print(f"Testing {model} with {self.image_name}")
                run_test(model_name=model, image_name=self.image_name)
