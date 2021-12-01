from dataclasses import dataclass
from pathlib import Path
from typing import Union, List
import os

from kipoi_utils.external.torchvision.dataset_utils import check_integrity
from singularityhelper import (
    build_singularity_image,
    populate_singularity_container_info,
    update_existing_singularity_container,
    test_singularity_image,
    write_singularity_container_info,
    cleanup,
)


@dataclass
class SingularityUpdater:
    model_group: str
    docker_image_name: str
    container_info: Union[str, Path] = (
        Path.cwd() / "test-containers" / "model-group-to-image-name.json"
    )
    singularity_image_folder: Union[str, Path] = os.environ.get(
        "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
    )

    def construct_dicts(self) -> None:
        self.model_group_to_image_dict = populate_singularity_container_info(
            self.container_info
        )
        self.singularity_dict = self.model_group_to_image_dict.get(
            self.model_group
        )

    def update(self, models_to_test: List) -> None:
        self.construct_dicts()
        self.singularity_image_name = f'{self.singularity_dict["name"]}.sif'

        singularity_image_path = build_singularity_image(
            self.docker_image_name, self.singularity_image_name
        )
        checksum_match = check_integrity(
            self.singularity_image_path, self.singularity_dict["md5"]
        )
        if checksum_match:
            print(
                f"No need to update the existing singularity container for {self.model_group}"
            )
            cleanup(singularity_image_path)
        else:
            test_singularity_image(
                self.singularity_image_folder, models_to_test
            )
            (
                _,
                _,
                updated_singularity_dict,
            ) = update_existing_singularity_container(
                self.singularity_dict, self.model_group
            )
        self.model_group_image_dict[
            self.model_group
        ] = updated_singularity_dict
        write_singularity_container_info(
            self.model_group_to_image_dict, self.container_json
        )
