import docker
import json
from pathlib import Path
import pytest
import shutil

from modelupdater.updateoradd import update, add
from ruamel.yaml import round_trip_load, round_trip_dump
from ruamel.yaml.scalarstring import DoubleQuotedScalarString


class TestServerCode(object):
    model_group_to_update = ""
    image_to_update = ""
    model_group_to_add = ""

    # def test_update(self):
    #     assert self.model_group_to_update
    #     assert self.image_to_update
    #     client = docker.from_env()
    #     original_shortid = client.images.get(self.image_to_update).short_id
    #     update(
    #         model=self.model_group_to_update,
    #         name_of_docker_image=self.image_to_update,
    #     )
    #     assert (
    #         client.images.get(self.image_to_update).short_id
    #         != original_shortid
    #     )

    def test_add(self, monkeypatch):
        def mock_get_list_of_models_from_repo(*args, **kwargs):
            return ["CleTimer/customBP", "CleTimer/default"]

        monkeypatch.setattr(
            "modelupdater.updateoradd.get_list_of_models_from_repo",
            mock_get_list_of_models_from_repo,
        )

        with open(
            Path(__file__).resolve().parent
            / "../test-containers"
            / "image-name-to-model.json",
            "r",
        ) as infile:
            image_name_to_model_dict = json.load(infile)

        with open(
            Path(__file__).resolve().parent
            / "../test-containers"
            / "model-group-to-image-name.json",
            "r",
        ) as infile:
            model_group_to_image_dict = json.load(infile)

        workflow_test_images_file_path = (
            Path(__file__).resolve().parent
            / "../.github/workflows/test-images.yml"
        )
        workflow_build_and_test_images_file_path = (
            Path(__file__).resolve().parent
            / "../.github/workflows/build-and-test-images.yml"
        )

        shutil.copy(
            workflow_test_images_file_path,
            Path(__file__).resolve().parent / "tmp-test-images.yml",
        )
        shutil.copy(
            workflow_build_and_test_images_file_path,
            Path(__file__).resolve().parent / "tmp-build-and-test-images.yml",
        )

        assert self.model_group_to_add

        add(
            model_group=self.model_group_to_add,
            kipoi_model_repo=None,
            kipoi_container_repo=None,
        )

        # Revert the change
        dockerfile_path = (
            Path(__file__).resolve().parent
            / f"../dockerfiles/Dockerfile.{self.model_group_to_add.lower()}"
        )
        assert dockerfile_path.exists()
        dockerfile_path.unlink()

        with open(
            Path(__file__).resolve().parent
            / "../test-containers"
            / "image-name-to-model.json",
            "r",
        ) as infile:
            new_image_name_to_model_dict = json.load(infile)
        assert (
            "haimasree/kipoi-docker:cletimer" in new_image_name_to_model_dict
        )
        assert new_image_name_to_model_dict[
            "haimasree/kipoi-docker:cletimer"
        ] == ["CleTimer/customBP", "CleTimer/default"]

        with open(
            Path(__file__).resolve().parent
            / "../test-containers"
            / "model-group-to-image-name.json",
            "r",
        ) as infile:
            new_model_group_to_image_dict = json.load(infile)
        assert "CleTimer" in new_model_group_to_image_dict
        assert (
            new_model_group_to_image_dict["CleTimer"]
            == "haimasree/kipoi-docker:cletimer"
        )

        with open(
            Path(__file__).resolve().parent
            / "../test-containers"
            / "model-group-to-image-name.json",
            "w",
        ) as fp:
            json.dump(model_group_to_image_dict, fp, indent=2)

        with open(
            Path(__file__).resolve().parent
            / "../test-containers"
            / "image-name-to-model.json",
            "w",
        ) as fp:
            json.dump(image_name_to_model_dict, fp, indent=2)

        with open(workflow_build_and_test_images_file_path, "r") as f:
            data = round_trip_load(f, preserve_quotes=True)
            assert (
                self.model_group_to_add.lower()
                in data["jobs"]["buildandtest"]["strategy"]["matrix"]["image"]
            )

        with open(
            workflow_test_images_file_path,
            "r",
        ) as f:
            data = round_trip_load(f, preserve_quotes=True)
            assert (
                "CleTimer/customBP"
                in data["jobs"]["test"]["strategy"]["matrix"]["model"]
            )

        shutil.copy(
            Path(__file__).resolve().parent / "tmp-test-images.yml",
            workflow_test_images_file_path,
        )
        shutil.copy(
            Path(__file__).resolve().parent / "tmp-build-and-test-images.yml",
            workflow_build_and_test_images_file_path,
        )

        (Path(__file__).resolve().parent / "tmp-test-images.yml").unlink()
        (
            Path(__file__).resolve().parent / "tmp-build-and-test-images.yml"
        ).unlink()
