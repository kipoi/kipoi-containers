import os
from pathlib import Path

import click

from kipoi_containers.singularityhandler import SingularityHandler
from kipoi_containers.updateoradd import (
    MODEL_GROUP_TO_SINGULARITY_JSON,
    DOCKER_TO_MODEL_JSON,
)
from kipoi_containers.helper import populate_json, write_json


@click.command()
@click.argument("docker_image", required=True, type=str)
def run_update(docker_image: str) -> None:
    model_group_to_singularity_dict = populate_json(
        MODEL_GROUP_TO_SINGULARITY_JSON
    )
    model_group_to_singularity_dict_ci = {
        k.lower(): v for k, v in model_group_to_singularity_dict.items()
    }
    model_group = docker_image.split(":")[-1]
    model_or_model_group = model_group.replace("-", "/")
    singularity_pull_folder = os.environ.get(
        "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
    )
    singularity_handler = SingularityHandler(
        model_group=model_or_model_group,
        docker_image_name=docker_image,
        singularity_image_folder=singularity_pull_folder,
        model_group_to_singularity_dict=model_group_to_singularity_dict_ci,
    )
    docker_to_model_dict = populate_json(DOCKER_TO_MODEL_JSON)
    models_to_test = docker_to_model_dict[docker_image]
    singularity_handler.update(models_to_test)
    model_group_to_singularity_dict = {
        k: model_group_to_singularity_dict_ci[k.lower()]
        for k, _ in model_group_to_singularity_dict_ci.items()
    }
    write_json(
        model_group_to_singularity_dict, MODEL_GROUP_TO_SINGULARITY_JSON
    )


if __name__ == "__main__":
    run_update()
