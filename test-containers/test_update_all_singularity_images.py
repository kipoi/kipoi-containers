from click.testing import CliRunner
import pytest

from kipoi_containers import update_all_singularity_images


@pytest.fixture
def runner():
    runner = CliRunner()
    yield runner


def test_cli_correct_use(runner, monkeypatch):
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

    def mock_write_json(*args, **kwargs):
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
        "kipoi_containers.update_all_singularity_images.write_json",
        mock_write_json,
    )

    result = runner.invoke(
        update_all_singularity_images.run_update,
        ["kipoi/kipoi-docker:mmsplice-mtsplice"],
    )
    assert result.exit_code == 0
