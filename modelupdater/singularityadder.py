from dataclasses import dataclass
from pathlib import Path
from typing import Union, List, Type
import os

from .singularityhelper import (
    build_singularity_image,
    populate_singularity_container_info,
    update_existing_singularity_container,
    push_new_singularity_image,
    test_singularity_image,
    write_singularity_container_info,
    cleanup,
)
from modelupdater import zenodoclient


@dataclass
class SingularityAdder:
    model_group: str
    docker_image_name: str
    container_info: Union[str, Path] = (
        Path.cwd() / "test-containers" / "model-group-to-image-name.json"
    )
    singularity_image_folder: Union[str, Path] = os.environ.get(
        "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
    )
    zenodo_client = zenodoclient.Client()

    def construct_dicts(self) -> None:
        self.model_group_to_image_dict = populate_singularity_container_info(
            self.container_info
        )

    def add(self, models_to_test: List) -> None:
        self.construct_dicts()
        self.singularity_image_name = (
            f"kipoi-docker_{self.model_group.lower()}.sif"
        )
        self.singularity_dict = {
            "url": "",
            "md5": "",
            "name": self.singularity_image_name,
        }

        build_singularity_image(
            self.docker_image_name,
            self.singularity_image_name,
            self.singularity_image_folder,
        )
        test_singularity_image(
            self.singularity_image_folder,
            self.singularity_image_name,
            models_to_test,
        )
        new_singularity_dict = push_new_singularity_image(
            self.zenodo_client,
            self.singularity_image_folder,
            self.singularity_dict,
            self.model_group,
        )
        self.model_group_image_dict[self.model_group] = {
            k: v
            for k, v in new_singularity_dict.items()
            if k in ["url", "md5", "name"]
        }
        write_singularity_container_info(
            self.model_group_to_image_dict, self.container_json
        )
