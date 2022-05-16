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


def test_cli_correct_use(runner, monkeypatch):
    def mock_populate_singularity_json(*args, **kwargs):
        if args[0] == "model-to-docker.json":
            return {
                "MMSplice/modularPredictions": "kipoi/kipoi-docker:mmsplice-slim",
                "MMSplice/mtsplice": "kipoi/kipoi-docker:mmsplice-mtsplice-slim",
                "DeepMEL": "kipoi/kipoi-docker:deepmel-slim",
            }
        elif args[0] == "model-to-singularity.json":
            return {
                "MMSplice/modularPredictions": {
                    "url": "https://zenodo.org/record/5643976/files/kipoi-docker_mmsplice-slim.sif?download=1",
                    "name": "kipoi-docker_mmsplice-slim",
                    "md5": "29438b52fafdde5f48658fdcd7a61c6c",
                },
                "MMSplice/mtsplice": {
                    "url": "https://zenodo.org/record/5643967/files/kipoi-docker_mmsplice-mtsplice-slim.sif?download=1",
                    "name": "kipoi-docker_mmsplice-mtsplice-slim",
                    "md5": "1b8dab773ad7b8d2299fb294b0e3216e",
                },
                "DeepMEL": {
                    "url": "https://zenodo.org/record/5643863/files/kipoi-docker_deepmel-slim.sif?download=1",
                    "name": "kipoi-docker_deepmel-slim",
                    "md5": "c1f7204b834bba9728c67e561952f8e8",
                },
            }

    def mock_write_singularity_json(*args, **kwargs):
        return

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
        "kipoi_containers.update_all_singularity_images.populate_json_from_kipoi",
        mock_populate_singularity_json,
    )
    monkeypatch.setattr(
        "kipoi_containers.update_all_singularity_images.write_json_to_kipoi",
        mock_write_singularity_json,
    )
    result = runner.invoke(
        update_all_singularity_images.run_update,
        ["kipoi/kipoi-docker:mmsplice-mtsplice-slim"],
    )
    assert result.exit_code == 0
