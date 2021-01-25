import docker


class TestServerCode(object):
    model_group_to_update = ""
    image_name_to_update = ""

    def test_update(self):
        assert self.model_group_to_update
        assert self.image_name_to_update
        client = docker.from_env()
        assert client.images.get(self.image_name_to_update).tags == [
            "haimasree/kipoi-docker:attentivechrome"
        ]
