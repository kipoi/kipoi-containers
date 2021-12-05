from kipoi_containers.dockerhelper import test_docker_image


class TestServerCode:
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
                test_docker_image(model_name=model, image_name=image_name)
        elif self.model_name is not None:
            for model in self.model_name:
                image_name = self.get_image_name(model=model)
                test_docker_image(model_name=model, image_name=image_name)
