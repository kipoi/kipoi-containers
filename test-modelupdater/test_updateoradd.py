import docker
import json
from pathlib import Path
import pytest
import shutil

from modelupdater.updater import ModelUpdater
from modelupdater.adder import ModelAdder
from ruamel.yaml import round_trip_load, round_trip_dump
from ruamel.yaml.scalarstring import DoubleQuotedScalarString


@pytest.mark.parametrize(
    "model_group_to_update,image_to_update",
    [
        ("MMSplice/deltaLogitPSI", "haimasree/kipoi-docker:mmsplice"),
        ("DeepMEL/DeepMEL", "haimasree/kipoi-docker:deepmel"),
    ],
)
def test_update(model_group_to_update, image_to_update):
    client = docker.from_env()
    original_shortid = client.images.get(image_to_update).short_id
    ModelUpdater().update(
        model_group=model_group_to_update,
        name_of_docker_image=image_to_update,
    )
    assert client.images.get(image_to_update).short_id != original_shortid


def test_add(monkeypatch):
    model_group_to_add = "CleTimer"

    def mock_get_list_of_models_from_repo(*args, **kwargs):
        return ["CleTimer/customBP", "CleTimer/default"]

    def mock_is_compatible_with_existing_image(*args, **kwargs):
        return False

    monkeypatch.setattr(
        "modelupdater.adder.ModelAdder.get_list_of_models_from_repo",
        staticmethod(mock_get_list_of_models_from_repo),
    )
    monkeypatch.setattr(
        "modelupdater.adder.ModelAdder.is_compatible_with_existing_image",
        staticmethod(mock_is_compatible_with_existing_image),
    )
    image_name_to_model_file_path = (
        Path(__file__).resolve().parent
        / "../test-containers"
        / "image-name-to-model.json"
    )
    model_group_to_image_name_file_path = (
        Path(__file__).resolve().parent
        / "../test-containers"
        / "model-group-to-image-name.json"
    )

    shutil.copy(
        image_name_to_model_file_path,
        Path(__file__).resolve().parent / "tmp-image-name-to-model.json",
    )
    shutil.copy(
        model_group_to_image_name_file_path,
        Path(__file__).resolve().parent / "tmp-model-group-to-image-name.json",
    )

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

    assert model_group_to_add

    model_adder = ModelAdder(
        model_group=model_group_to_add,
        kipoi_model_repo=None,
        kipoi_container_repo=None,
    )
    model_adder.add()

    # Revert the change
    dockerfile_path = (
        Path(__file__).resolve().parent
        / f"../dockerfiles/Dockerfile.{model_group_to_add.lower()}"
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
    assert "haimasree/kipoi-docker:cletimer" in new_image_name_to_model_dict
    assert new_image_name_to_model_dict["haimasree/kipoi-docker:cletimer"] == [
        "CleTimer/customBP",
        "CleTimer/default",
    ]

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
    shutil.copy(
        Path(__file__).resolve().parent / "tmp-image-name-to-model.json",
        image_name_to_model_file_path,
    )
    shutil.copy(
        Path(__file__).resolve().parent / "tmp-model-group-to-image-name.json",
        model_group_to_image_name_file_path,
    )
    (Path(__file__).resolve().parent / "tmp-image-name-to-model.json").unlink()
    (
        Path(__file__).resolve().parent / "tmp-model-group-to-image-name.json"
    ).unlink()
    with open(workflow_build_and_test_images_file_path, "r") as f:
        data = round_trip_load(f, preserve_quotes=True)
        assert (
            model_group_to_add.lower()
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
