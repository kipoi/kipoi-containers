import docker
from pathlib import Path
from modelupdater.updateoradd import update


class TestServerCode(object):
    model_group_to_update = ""
    image_to_update = ""

    def test_update(self):
        assert self.model_group_to_update
        assert self.image_to_update
        client = docker.from_env()
        original_shortid = client.images.get(self.image_to_update).short_id
        update(
            model=self.model_group_to_update,
            name_of_docker_image=self.image_to_update,
        )
        assert (
            client.images.get(self.image_to_update).short_id
            != original_shortid
        )
