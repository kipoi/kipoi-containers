from click.testing import CliRunner
import json
import pytest

from kipoi_containers import update_all_singularity_images


@pytest.fixture
def runner():
    runner = CliRunner()
    yield runner


def test_cli_incorrect_use(runner):
    result = runner.invoke(
        update_all_singularity_images.run_update,
        [],
    )
    assert "Error: Missing argument 'DOCKER_IMAGE'" in result.output
    assert result.exit_code == 2


def test_cli_correct_use(runner, monkeypatch, tmp_path):
    demo_dir = tmp_path / "demo"
    demo_dir.mkdir()
    scrap_singularity_json = demo_dir / "scrap.json"

    def mock_build(*args, **kwargs):
        return ""

    def mock_test(*args, **kwargs):
        return

    def mock_update_existing_singularity_container(*args, **kwargs):
        return {
            "url": "https://dummy.url",
            "name": "wrong_name",
            "md5": "78758738",
        }

    def mock_check_integrity(*args, **kwargs):
        return False

    def mock_cleanup(*args, **kwargs):
        return

    monkeypatch.setattr(
        "kipoi_containers.update_all_singularity_images.singularityhandler.build_singularity_image",
        mock_build,
    )
    monkeypatch.setattr(
        "kipoi_containers.update_all_singularity_images.singularityhandler.test_singularity_image",
        mock_test,
    )
    monkeypatch.setattr(
        "kipoi_containers.update_all_singularity_images.singularityhandler.update_existing_singularity_container",
        mock_update_existing_singularity_container,
    )
    monkeypatch.setattr(
        "kipoi_containers.update_all_singularity_images.singularityhandler.check_integrity",
        mock_check_integrity,
    )
    monkeypatch.setattr(
        "kipoi_containers.update_all_singularity_images.singularityhandler.cleanup",
        mock_cleanup,
    )
    monkeypatch.setattr(
        "kipoi_containers.update_all_singularity_images.MODEL_GROUP_TO_SINGULARITY_JSON",
        scrap_singularity_json,
    )
    singularity_content = {
        "MMSplice/modularPredictions": {
            "url": "https://zenodo.org/record/5643976/files/kipoi-docker_mmsplice.sif?download=1",
            "name": "kipoi-docker_mmsplice",
            "md5": "29438b52fafdde5f48658fdcd7a61c6c",
        },
        "MMSplice/mtsplice": {
            "url": "https://zenodo.org/record/5643967/files/kipoi-docker_mmsplice-mtsplice.sif?download=1",
            "name": "kipoi-docker_mmsplice-mtsplice",
            "md5": "1b8dab773ad7b8d2299fb294b0e3216e",
        },
        "DeepMEL": {
            "url": "https://zenodo.org/record/5643863/files/kipoi-docker_deepmel.sif?download=1",
            "name": "kipoi-docker_deepmel",
            "md5": "c1f7204b834bba9728c67e561952f8e8",
        },
    }
    with open(scrap_singularity_json, "w") as file_handle:
        json.dump(singularity_content, file_handle)
    result = runner.invoke(
        update_all_singularity_images.run_update,
        ["kipoi/kipoi-docker:mmsplice-mtsplice"],
    )
    assert result.exit_code == 0
    with open(scrap_singularity_json, "r") as file_handle:
        result_content = json.load(file_handle)

    assert result_content.keys() == singularity_content.keys()
    assert result_content["DeepMEL"] == singularity_content["DeepMEL"]
    assert (
        result_content["MMSplice/modularPredictions"]
        == singularity_content["MMSplice/modularPredictions"]
    )
    assert result_content["MMSplice/mtsplice"] == {
        "url": "https://dummy.url",
        "name": "wrong_name",
        "md5": "78758738",
    }
