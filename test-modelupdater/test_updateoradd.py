import docker
import json
from pathlib import Path
import pytest
import shutil

from ruamel.yaml import round_trip_load, round_trip_dump
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from modelupdater.updater import ModelUpdater
from modelupdater.adder import ModelAdder
from modelupdater.helper import populate_json


@pytest.fixture
def parent_path():
    return Path(__file__).resolve().parent


# @pytest.mark.parametrize(
#     "model_group_to_update,image_to_update",
#     [
#         ("MMSplice/deltaLogitPSI", "kipoi/kipoi-docker:mmsplice"),
#     ],
# )
# def test_update(model_group_to_update, image_to_update, monkeypatch):
#     def mock_push_docker_image(*args, **kwargs):
#         return True

#     monkeypatch.setattr(
#         "modelupdater.updater.push_docker_image",
#         mock_push_docker_image,
#     )
#     client = docker.from_env()
#     original_shortid = client.images.get(image_to_update).short_id
#     ModelUpdater().update(
#         model_group=model_group_to_update,
#         name_of_docker_image=image_to_update,
#     )
#     assert client.images.get(image_to_update).short_id != original_shortid


def test_add(monkeypatch, parent_path, tmpdir):
    model_group_to_add = "CleTimer"

    def mock_get_list_of_models_from_repo(*args, **kwargs):
        return ["CleTimer/customBP", "CleTimer/default"]

    def mock_is_compatible_with_existing_image(*args, **kwargs):
        return False

    def mock_push_docker_image(*args, **kwargs):
        return True

    monkeypatch.setattr(
        "modelupdater.adder.ModelAdder.get_list_of_models_from_repo",
        staticmethod(mock_get_list_of_models_from_repo),
    )
    monkeypatch.setattr(
        "modelupdater.adder.ModelAdder.is_compatible_with_existing_image",
        staticmethod(mock_is_compatible_with_existing_image),
    )
    monkeypatch.setattr(
        "modelupdater.adder.push_docker_image",
        mock_push_docker_image,
    )
    # p = tmpdir.mkdir("copies").join("hello.txt")
    docker_to_model_file_path = (
        parent_path / "../container-info" / "docker-to-model.json"
    )
    model_group_to_docker_file_path = (
        parent_path / "../container-info" / "model-group-to-docker.json"
    )
    model_group_to_docker_dict = populate_json(model_group_to_docker_file_path)
    docker_to_model_dict = populate_json(docker_to_model_file_path)

    workflow_test_images_file_path = (
        parent_path / "../.github/workflows/test-images.yml"
    )

    shutil.copy(
        workflow_test_images_file_path,
        parent_path / "tmp-test-images.yml",
    )

    assert model_group_to_add

    model_adder = ModelAdder(
        model_group=model_group_to_add,
        kipoi_model_repo=None,
        kipoi_container_repo=None,
    )
    model_adder.add(model_group_to_docker_dict, docker_to_model_dict)

    # Revert the change
    dockerfile_path = (
        parent_path / f"../dockerfiles/Dockerfile.{model_group_to_add.lower()}"
    )
    assert dockerfile_path.exists()
    dockerfile_path.unlink()

    assert "kipoi/kipoi-docker:cletimer" in model_group_to_docker_dict
    assert docker_to_model_dict["kipoi/kipoi-docker:cletimer"] == [
        "CleTimer/customBP",
        "CleTimer/default",
    ]

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
        parent_path / "tmp-test-images.yml",
        workflow_test_images_file_path,
    )

    (parent_path / "tmp-test-images.yml").unlink()


# def test_add_is_compatible_with_existing_image(monkeypatch):
#     model_group_to_add = "Basset"
#     docker_image = "kipoi/kipoi-docker:sharedpy3keras2"

#     def mock_get_list_of_models_from_repo(*args, **kwargs):
#         return []

#     def mock_is_compatible_with_existing_image(*args, **kwargs):
#         return True

#     def mock_push_docker_image(*args, **kwargs):
#         return True

#     monkeypatch.setattr(
#         "modelupdater.adder.ModelAdder.get_list_of_models_from_repo",
#         staticmethod(mock_get_list_of_models_from_repo),
#     )
#     monkeypatch.setattr(
#         "modelupdater.adder.ModelAdder.is_compatible_with_existing_image",
#         staticmethod(mock_is_compatible_with_existing_image),
#     )
#     monkeypatch.setattr(
#         "modelupdater.adder.push_docker_image",
#         mock_push_docker_image,
#     )

#     docker_to_model_file_path = (
#         Path(__file__).resolve().parent
#         / "../container-info"
#         / "docker-to-model.json"
#     )
#     model_group_to_docker_file_path = (
#         Path(__file__).resolve().parent
#         / "../container-info"
#         / "model-group-to-docker.json"
#     )
#     shutil.copy(
#         docker_to_model_file_path,
#         Path(__file__).resolve().parent / "tmp-docker-to-model.json",
#     )
#     shutil.copy(
#         model_group_to_docker_file_path,
#         Path(__file__).resolve().parent / "tmp-model-group-to-docker.json",
#     )
#     with open(
#         model_group_to_docker_file_path,
#         "r",
#     ) as infile:
#         model_group_to_docker_dict = json.load(infile)
#     model_group_to_docker_dict.pop(model_group_to_add)
#     with open(
#         model_group_to_docker_file_path,
#         "w",
#     ) as fp:
#         json.dump(model_group_to_docker_dict, fp, indent=2)

#     with open(
#         docker_to_model_file_path,
#         "r",
#     ) as infile:
#         image_name_to_model_dict = json.load(infile)
#     image_name_to_model_dict[docker_image].remove(model_group_to_add)

#     with open(
#         docker_to_model_file_path,
#         "w",
#     ) as fp:
#         json.dump(image_name_to_model_dict, fp, indent=2)

#     workflow_test_images_file_path = (
#         Path(__file__).resolve().parent
#         / "../.github/workflows/test-images.yml"
#     )

#     shutil.copy(
#         workflow_test_images_file_path,
#         Path(__file__).resolve().parent / "tmp-test-images.yml",
#     )

#     assert model_group_to_add

#     model_adder = ModelAdder(
#         model_group=model_group_to_add,
#         kipoi_model_repo=None,
#         kipoi_container_repo=None,
#     )
#     model_adder.image_name = docker_image
#     model_adder.add()

#     # Revert the change
#     dockerfile_path = (
#         Path(__file__).resolve().parent
#         / f"../dockerfiles/Dockerfile.{model_group_to_add.lower()}"
#     )
#     assert not dockerfile_path.exists()
#     with open(
#         Path(__file__).resolve().parent
#         / "../container-info"
#         / "docker-to-model.json",
#         "r",
#     ) as infile:
#         new_image_name_to_model_dict = json.load(infile)
#     assert model_group_to_add in new_image_name_to_model_dict[docker_image]

#     with open(
#         Path(__file__).resolve().parent
#         / "../container-info"
#         / "model-group-to-docker.json",
#         "r",
#     ) as infile:
#         new_model_group_to_image_dict = json.load(infile)
#     assert "CleTimer" in new_model_group_to_image_dict
#     assert new_model_group_to_image_dict[model_group_to_add] == docker_image
#     shutil.copy(
#         Path(__file__).resolve().parent / "tmp-docker-to-model.json",
#         docker_to_model_file_path,
#     )
#     shutil.copy(
#         Path(__file__).resolve().parent / "tmp-model-group-to-docker.json",
#         model_group_to_docker_file_path,
#     )
#     (Path(__file__).resolve().parent / "tmp-docker-to-model.json").unlink()
#     (
#         Path(__file__).resolve().parent / "tmp-model-group-to-docker.json"
#     ).unlink()

#     with open(
#         workflow_test_images_file_path,
#         "r",
#     ) as f:
#         data = round_trip_load(f, preserve_quotes=True)
#         assert (
#             data["jobs"]["test"]["strategy"]["matrix"]["model"].count(
#                 model_group_to_add
#             )
#             == 1
#         )  # As Basset is part of a group job

#     shutil.copy(
#         Path(__file__).resolve().parent / "tmp-test-images.yml",
#         workflow_test_images_file_path,
#     )

#     (Path(__file__).resolve().parent / "tmp-test-images.yml").unlink()
