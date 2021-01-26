import docker
from pathlib import Path
import pytest

from modelupdater.updateoradd import update, add


class TestServerCode(object):
    model_group_to_update = ""
    image_to_update = ""
    model_group_to_add = ""

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

    def test_add(self, monkeypatch):
        def mockreturn(*args, **kwargs):
            return ["CleTimer/customBP", "CleTimer/default"]

        monkeypatch.setattr(
            "modelupdater.updateoradd.get_list_of_models_from_repo",
            mockreturn,
        )

        assert self.model_group_to_add
        add(
            model_group=self.model_group_to_add,
            kipoi_model_repo=None,
            kipoi_container_repo=None,
        )
