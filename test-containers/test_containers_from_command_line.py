from kipoi_containers.dockerhelper import test_docker_image


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
                    test_docker_image(
                        model_name=model, image_name=self.image_name
                    )
        elif self.image_name not in [None, "kipoi-base-env"]:
            models = self.image_to_model_dict.get(self.image_name)
            for model in models:
                print(f"Testing {model} with {self.image_name}")
                test_docker_image(model_name=model, image_name=self.image_name)
