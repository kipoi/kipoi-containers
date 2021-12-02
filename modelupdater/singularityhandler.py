from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Union, List, Type
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

from kipoi_utils.external.torchvision.dataset_utils import check_integrity


@dataclass
class SingularityHandler:
    model_group: str
    docker_image_name: str
    container_info: Union[str, Path] = (
        Path.cwd() / "test-containers" / "model-group-to-singularity.json"
    )
    singularity_image_folder: Union[str, Path] = os.environ.get(
        "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
    )
    zenodo_client = zenodoclient.Client()

    def __post_init__(self):
        self.model_group_to_image_dict = populate_singularity_container_info(
            self.container_info
        )

    def update_container_info(self, updated_singularity_dict: Dict) -> None:
        self.model_group_to_image_dict[self.model_group] = {
            k: v
            for k, v in updated_singularity_dict.items()
            if k in ["url", "md5", "name"]
        }
        write_singularity_container_info(
            self.model_group_to_image_dict, self.container_info
        )

    def add(self, models_to_test: List) -> None:
        self.singularity_image_name = (
            f"kipoi-docker_{self.model_group.lower()}.sif"
        )
        self.singularity_dict = {
            "url": "",
            "md5": "",
            "name": self.singularity_image_name,
        }

        build_singularity_image(
            name_of_docker_image=self.docker_image_name,
            singularity_image_name=self.singularity_image_name,
            singularity_image_folder=self.singularity_image_folder,
        )
        test_singularity_image(
            singularity_image_folder=self.singularity_image_folder,
            singularity_image_name=self.singularity_image_name,
            models=models_to_test,
        )
        new_singularity_dict = push_new_singularity_image(
            zenodo_client=self.zenodo_client,
            singularity_image_folder=self.singularity_image_folder,
            singularity_dict=self.singularity_dict,
            model_group=self.model_group,
        )
        self.update_container_info(new_singularity_dict)

    def update(self, models_to_test: List) -> None:
        self.singularity_image_name = f'{self.singularity_dict["name"]}.sif'
        self.singularity_dict = self.model_group_to_image_dict.get(
            self.model_group
        )
        singularity_image_path = build_singularity_image(
            name_of_docker_image=self.docker_image_name,
            singularity_image_name=self.singularity_image_name,
            singularity_image_folder=self.singularity_image_folder,
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
                singularity_image_folder=self.singularity_image_folder,
                singularity_image_name=self.singularity_image_name,
                models=models_to_test,
            )
            updated_singularity_dict = update_existing_singularity_container(
                zenodo_client=self.zenodo_client,
                singularity_dict=self.singularity_dict,
                singularity_image_folder=self.singularity_image_folder,
                model_group=self.model_group,
            )
        self.update_container_info(updated_singularity_dict)
