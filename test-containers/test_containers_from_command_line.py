import docker


def run_test(model_name, image_name, clean=False):
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
    if clean:
        client.containers.prune()
        # client.images.prune(filters={"dangling": False})
    print(container_log.decode("utf-8"))


class TestServerCode(object):
    image_name = None
    image_to_model_dict = {}

    def test_parameters(self):
        assert self.image_name not in [None, "kipoi-base-env"]
        assert self.image_to_model_dict != {}

    def test_images(self):
        if self.image_name not in [None, "kipoi-base-env"]:
            print(self.image_name)
            models = self.image_to_model_dict.get(self.image_name)
            print(f"models are {models}")
            for model in models:
                print(f"Testing {model} with {self.image_name}")
                run_test(
                    model_name=model, image_name=self.image_name, clean=True
                )
