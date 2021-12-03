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
    client.images.prune(filters={"dangling": True})
    client.volumes.prune()
    client.containers.prune()
    print(container_log.decode("utf-8"))


class TestServerCode(object):
    model_name = None
    model_group_to_docker_dict = {}
    list_of_models = []

    def get_image_name(self, model):
        assert (
            model in self.model_group_to_docker_dict
            or model.split("/")[0] in self.model_group_to_docker_dict
        )
        if model in self.model_group_to_docker_dict:  # For MMSplice/mtsplice
            image_name = self.model_group_to_docker_dict.get(model)
        elif model.split("/")[0] in self.model_group_to_docker_dict:
            image_name = self.model_group_to_docker_dict.get(
                model.split("/")[0]
            )
        return image_name

    def test_parameters(self):
        assert self.model_name is not None or self.list_of_models != []
        assert self.model_group_to_docker_dict != {}

    def test_models(self):
        if self.list_of_models:
            for model in self.list_of_models:
                image_name = self.get_image_name(model=model)
                run_test(model_name=model, image_name=image_name)
        elif self.model_name is not None:
            for model in self.model_name:
                image_name = self.get_image_name(model=model)
                run_test(model_name=model, image_name=image_name)
