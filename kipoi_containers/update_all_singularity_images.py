import os
from pathlib import Path

import click

from kipoi_containers import singularityhandler
from kipoi_containers.updateoradd import (
    MODEL_GROUP_TO_SINGULARITY_JSON,
    DOCKER_TO_MODEL_JSON,
    MODEL_GROUP_TO_DOCKER_JSON,
)
from kipoi_containers.helper import populate_json, write_json


@click.command()
@click.argument("docker_image", required=True, type=str)
def run_update(docker_image: str) -> None:
    """Update the singularity image corresponding to the docker image.
    By default, it does not push the image to zenodo but creates a new
    version of an existing deposition and updates the metadata and file
    after deleting the existing file. Obviously, this does not update
    content of model_group_to_singularity_dict. However, if push is
    enabled in SingularityHandler.udpate, the draft entry will be
    pushed to zenodo, the image specific entry in model_group_to_singularity_dict
    will be updated with url and md5 values of the new deposition and
    kipoi_containers/container-info/model-group-to-singularity.json will be
    updated.
    """
    click.echo(f"Updating {docker_image}")
    model_group_to_singularity_dict = populate_json(
        MODEL_GROUP_TO_SINGULARITY_JSON
    )
    model_group_to_docker = populate_json(MODEL_GROUP_TO_DOCKER_JSON)
    docker_to_model_group_dict_ci = {}
    for model_group, docker_image in model_group_to_docker.json():
        if docker_image in docker_to_model_group_dict_ci:
            docker_to_model_group_dict_ci[docker_image].append(model_group)
        else:
            docker_to_model_group_dict_ci[docker_image] = [model_group]
    model_group_to_singularity_dict_ci = {
        k.lower(): v for k, v in model_group_to_singularity_dict.items()
    }
    model_or_model_group_list = docker_to_model_group_dict_ci[docker_image]
    singularity_pull_folder = os.environ.get(
        "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
    )
    docker_to_model_dict = populate_json(DOCKER_TO_MODEL_JSON)
    for model_or_model_group in model_or_model_group_list:
        singularity_handler = singularityhandler.SingularityHandler(
            model_group=model_or_model_group,
            docker_image_name=docker_image,
            singularity_image_folder=singularity_pull_folder,
            model_group_to_singularity_dict=model_group_to_singularity_dict_ci,
        )
        models_to_test = docker_to_model_dict[docker_image]
        singularity_handler.update(models_to_test)
        model_group_to_singularity_dict = {
            k: model_group_to_singularity_dict_ci[k.lower()]
            for k in model_group_to_singularity_dict.keys()
        }
        write_json(
            model_group_to_singularity_dict, MODEL_GROUP_TO_SINGULARITY_JSON
        )


if __name__ == "__main__":
    run_update()
