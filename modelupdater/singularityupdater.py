from dataclasses import dataclass
from pathlib import Path
from typing import Union, List, Type
import os

from kipoi_utils.external.torchvision.dataset_utils import check_integrity
from .singularityhelper import (
    build_singularity_image,
    populate_singularity_container_info,
    update_existing_singularity_container,
    test_singularity_image,
    write_singularity_container_info,
    cleanup,
)
from modelupdater import zenodoclient


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
    zenodo_client: Type(zenodoclient) = zenodoclient.Client()

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
            self.docker_image_name,
            self.singularity_image_name,
            self.singularity_image_folder,
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
                self.singularity_image_folder,
                self.singularity_image_name,
                models_to_test,
            )
            updated_singularity_dict = update_existing_singularity_container(
                self.zenodo_client,
                self.singularity_dict,
                self.singularity_image_folder,
                self.model_group,
            )
        self.model_group_image_dict[self.model_group] = {
            k: v
            for k, v in updated_singularity_dict.items()
            if k in ["url", "md5", "name"]
        }
        write_singularity_container_info(
            self.model_group_to_image_dict, self.container_json
        )
