from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Union, List, Type
import os


from kipoi_containers.singularityhelper import (
    build_singularity_image,
    update_existing_singularity_container,
    push_new_singularity_image,
    test_singularity_image,
    cleanup,
)
from kipoi_containers import zenodoclient

from kipoi_utils.external.torchvision.dataset_utils import check_integrity


@dataclass
class SingularityHandler:
    """This is a dataclass to be instantiated in order to update and
    adding singularity images"""

    model_group: str
    docker_image_name: str
    model_group_to_singularity_dict: Dict
    singularity_image_folder: Union[str, Path] = None
    zenodo_client: zenodoclient.Client = zenodoclient.Client()

    def __post_init__(self):
        """If a location has not been specified for saving the downloaded
        singularity containers to, a value is populated from
        SINGULARITY_PULL_FOLDER environment variable. If there is no
        such variable, the current directory is served as default."""
        if self.singularity_image_folder is None:
            self.singularity_image_folder = os.environ.get(
                "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
            )

    def update_container_info(self, updated_singularity_dict: Dict) -> None:
        """Update url, md5 and name keys of the model group's singularity
        container dict with the correspondong values from updated_singularity_dict"""
        self.model_group_to_singularity_dict[self.model_group] = {
            k: v
            for k, v in updated_singularity_dict.items()
            if k in ["url", "name", "md5"]
        }

    def add(self, models_to_test: List, push: bool = False) -> None:
        """Adds a new singularity image. The steps are as follows -
        1. First, the new image is built and saved in
        singularity_image_folder from the docker image
        2. This new singularity image is tested with the models in
         <models_to_test>
        3. If everything is fine, push the image to zenodo and return
        the modified url, name and md5 as a dict
        4. Update <model_group_to_singularity_dict> with the new model
        group as key and the dictionary with url, md5, key as values"""
        self.singularity_image_name = (
            f"kipoi-docker_{self.model_group.lower()}.sif"
        )
        self.singularity_dict = {
            "url": "",
            "name": self.singularity_image_name.replace(".sif", ""),
            "md5": "",
        }
        build_singularity_image(
            name_of_docker_image=self.docker_image_name,
            singularity_image_name=self.singularity_image_name,
            singularity_image_folder=self.singularity_image_folder,
        )
        for model in models_to_test:
            test_singularity_image(
                singularity_image_folder=self.singularity_image_folder,
                singularity_image_name=self.singularity_image_name,
                model=model,
            )

        new_singularity_dict = push_new_singularity_image(
            zenodo_client=self.zenodo_client,
            singularity_image_folder=self.singularity_image_folder,
            singularity_dict=self.singularity_dict,
            model_group=self.model_group,
            push=push,
        )
        self.update_container_info(new_singularity_dict)

    def update(self, models_to_test: List, push: bool = False) -> None:
        """Updates an existing singularity image. The steps are as follows -
        1. First, a singularity image is built and saved in
        singularity_image_folder from the docker image
        2. A checksum is computed and compared against the existing md5 key
        3. If the new image is identical to the existing one,
        a cleanup is performed followed by an exit.
        2. Otherwise, This new singularity image is tested with the models in
         <models_to_test>
        3. If everything is fine, push the new image to zenodo as a new version
        and return the modified url, name and md5 as a dict
        4. Update <model_group_to_singularity_dict> with the new model
        group as key and the dictionary with url, md5, key as values"""
        self.singularity_dict = self.model_group_to_singularity_dict[
            self.model_group
        ]
        self.singularity_image_name = f'{self.singularity_dict["name"]}.sif'
        singularity_image_path = build_singularity_image(
            name_of_docker_image=self.docker_image_name,
            singularity_image_name=self.singularity_image_name,
            singularity_image_folder=self.singularity_image_folder,
        )
        checksum_match = check_integrity(
            singularity_image_path, self.singularity_dict["md5"]
        )
        if checksum_match:
            print(
                f"No need to update the existing singularity container for {self.model_group}"
            )
            cleanup(singularity_image_path)
        else:
            for model in models_to_test:
                test_singularity_image(
                    singularity_image_folder=self.singularity_image_folder,
                    singularity_image_name=self.singularity_image_name,
                    model=model,
                )
            updated_singularity_dict = update_existing_singularity_container(
                zenodo_client=self.zenodo_client,
                singularity_dict=self.singularity_dict,
                singularity_image_folder=self.singularity_image_folder,
                model_group=self.model_group,
                push=push,
            )
            cleanup(singularity_image_path)
            self.update_container_info(updated_singularity_dict)
