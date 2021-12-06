from collections import Counter
from datetime import datetime
import os
import requests
from pathlib import Path
import json

from kipoi_utils.external.torchvision.dataset_utils import download_url
from spython.main import Client

ZENODO_BASE = "https://zenodo.org"
ZENODO_DEPOSITION = f"{ZENODO_BASE}/api/deposit/depositions"


def cleanup(singularity_file_path):
    """
    Cleans up singularity containers that werecreated in build_singularity_image
    """
    if isinstance(singularity_file_path, str):
        singularity_file_path = Path(singularity_file_path)
    singularity_file_path.unlink()


def build_singularity_image(
    name_of_docker_image, singularity_image_name, singularity_image_folder
):
    """
    This function builds a singularity image from an existing singularity image
    Parameters
    ----------
    singularity_image_name : str
        Name of the singularity image to build
    """
    if isinstance(singularity_image_folder, Path):
        singularity_image_folder = str(singularity_image_folder)
    singularity_image_path = Client.pull(
        image=f"docker://{name_of_docker_image}",
        pull_folder=singularity_image_folder,
        force=True,
        name=singularity_image_name,
    )
    return singularity_image_path


def test_singularity_image(
    singularity_image_folder, singularity_image_name, model
):  # TODO: Investigate adding this to test_containers_from_command_line
    """
    Tests a container for a given singularity image and run
    kipoi test <model_name> --source=kipoi inside
    the container

    Parameters
    ----------
    singularity_dict: dict
        Dict containing url, name and md5 checksum of the singularity image
    models : List
        Name of the models to test
    """
    print(f"Testing {model} with {singularity_image_name}")
    if model == "Basenji":
        test_cmd = f"kipoi test {model} --source=kipoi --batch_size=2"
    else:
        test_cmd = f"kipoi test {model} --source=kipoi"

    result = Client.execute(
        singularity_image_folder / Path(f"{singularity_image_name}"),
        test_cmd,
        return_result=True,
    )
    if result["return_code"] != 0:
        print(result["message"])
        raise ValueError(
            f"Updated singularity image {singularity_image_name} for {model} did not pass relevant tests"
        )


def create_new_deposition(zenodo_client, deposition_id):
    status_code, response = zenodo_client.post_content(
        f"{ZENODO_DEPOSITION}/{deposition_id}/actions/newversion"
    )
    return response["links"]["latest_draft"].split("/")[-1]


def get_deposit(zenodo_client, deposition_id):
    response = zenodo_client.get_content(
        f"{ZENODO_DEPOSITION}/{deposition_id}"
    )
    return response


def upload_file(zenodo_client, url, singularity_image_folder, filename):
    path = singularity_image_folder / filename
    zenodo_client.put_content(url, data=path)


def upload_metadata(zenodo_client, url, model_group):
    data = {
        "metadata": {
            "title": f"{model_group} singularity container",
            "upload_type": "physicalobject",
            "description": "This is a singularity container for models "
            f"under https://kipoi.org/models/{model_group}/",
            "creators": [
                {"name": "Haimasree, Bhattacharya", "affiliation": "EMBL"}
            ],
            "publication_date": datetime.today().strftime("%Y-%m-%d"),
            "license": "MIT",
        }
    }
    zenodo_client.put_content(url, data=data)


def push_deposition(zenodo_client, deposition_id):
    status_code, response = zenodo_client.post_content(
        f"{ZENODO_DEPOSITION}/{deposition_id}/actions/publish"
    )
    response = get_deposit(zenodo_client, deposition_id)
    return response


def update_existing_singularity_container(
    zenodo_client,
    singularity_dict,
    singularity_image_folder,
    model_group,
    file_to_upload="",
    push=False,
):
    # Create a new version of an existing deposition
    deposition_id = singularity_dict["url"].split("/")[4]
    new_deposition_id = create_new_deposition(zenodo_client, deposition_id)
    response = get_deposit(zenodo_client, new_deposition_id)
    bucket_url, file_id = (
        response["links"]["bucket"],
        response["files"][0]["id"],
    )

    # Delete existing file from this new version
    zenodo_client.delete_content(
        f"{ZENODO_DEPOSITION}/{new_deposition_id}/files/{file_id}"
    )

    # Add a new file to this new version
    filename = (
        file_to_upload if file_to_upload else f"{singularity_dict['name']}.sif"
    )
    upload_file(
        zenodo_client,
        f"{bucket_url}/{filename}",
        singularity_image_folder,
        filename,
    )

    # publish the newly created revision
    if push:
        response = push_deposition(zenodo_client, new_deposition_id)
        record_id = response["metadata"]["prereserve_doi"]["recid"]
        return {
            "new_deposition_id": new_deposition_id,
            "file_id": response["files"][0]["id"],
            "url": f"{ZENODO_BASE}/record/{record_id}/files/{filename}?download=1",
            "name": response["files"][0]["filename"].replace(".sif", ""),
            "md5": response["files"][0]["checksum"],
        }
    else:
        return singularity_dict | {
            "new_deposition_id": new_deposition_id,
            "file_id": "",
        }


def push_new_singularity_image(
    zenodo_client,
    singularity_image_folder,
    singularity_dict,
    model_group,
    file_to_upload="",
    path="",
    push=False,
):
    """
    This function pushes a singularity image to zenodo
    Parameters
    ----------
    tag : str
       Tag of the singularity image to push
    """
    status_code, response = zenodo_client.post_content(f"{ZENODO_DEPOSITION}")

    deposition_id = response["id"]
    bucket_url = response["links"]["bucket"]

    filename = (
        file_to_upload if file_to_upload else f"{singularity_dict['name']}.sif"
    )
    upload_file(
        zenodo_client,
        f"{bucket_url}/{filename}",
        singularity_image_folder,
        filename,
    )

    url = f"{ZENODO_DEPOSITION}/{deposition_id}"
    upload_metadata(zenodo_client, url, model_group)
    if push:
        push_deposition(zenodo_client, deposition_id)
        response = get_deposit(
            zenodo_client, deposition_id
        )  # TODO: Is this important here?
        record_id = response["metadata"]["prereserve_doi"]["recid"]
        return {
            "new_deposition_id": deposition_id,
            "file_id": response["files"][0]["id"],
            "url": f"{ZENODO_BASE}/record/{record_id}/files/{filename}?download=1",
            "name": response["files"][0]["filename"].replace(".sif", ""),
            "md5": response["files"][0]["checksum"],
        }
    else:
        return singularity_dict | {
            "new_deposition_id": deposition_id,
            "file_id": "",
        }


def get_singularity_image(
    singularity_image_folder, singularity_image_dict, model_or_model_group
):
    if (
        model_or_model_group in singularity_image_dict
    ):  # Special case for MMSPlice/mtsplice, APARENT/veff
        image_name = (
            f"{singularity_image_dict[model_or_model_group]['name']}.sif"
        )
        image_url = f"{singularity_image_dict[model_or_model_group]['url']}"
        image_md5 = f"{singularity_image_dict[model_or_model_group]['md5']}"
    else:
        model_group = model_or_model_group.split("/")[0]
        image_name = f"{singularity_image_dict[model_group]['name']}.sif"
        image_url = f"{singularity_image_dict[model_group]['url']}"
        image_md5 = f"{singularity_image_dict[model_group]['md5']}"

    if isinstance(singularity_image_folder, str):
        singularity_image_folder = Path(singularity_image_folder)
    if isinstance(image_name, str):
        image_name = Path(image_name)

    if not (singularity_image_folder / image_name).exists():
        download_url(
            url=image_url,
            root=singularity_image_folder,
            filename=image_name,
            md5=image_md5,
        )
    return image_name
