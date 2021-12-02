from collections import Counter
import os
import requests
from pathlib import Path
import json

from spython.main import Client

ZENODO_BASE = "https://zenodo.org"
ZENODO_DEPOSITION = f"{ZENODO_BASE}/api/deposit/depositions"


def cleanup(singularity_file_path):
    """
    Cleans up singularity containers that werecreated in build_singularity_image
    """
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
    singularity_image_folder, singularity_image_name, models
):  # TODO: Investigate adding this to test_containers_from_command_line
    """
    Tests a container for a given singularity image and run
    kipoi test <model_name> --source=kipoi inside
    the container, followed by a cleanup

    Parameters
    ----------
    singularity_dict: dict
        Dict containing url, name and md5 checksum of the singularity image
    models : List
        Name of the models to test
    """
    for model in models:
        print(f"Testing {model} with {singularity_image_name}")
        result = Client.execute(
            singularity_image_folder / Path(f"{singularity_image_name}"),
            f"kipoi test {model} --source=kipoi",
            return_result=True,
        )
        if result["return_code"] != 0:
            print(result["message"])
            raise ValueError(
                f"Updated singularity image {singularity_image_name} for {models} did not pass relevant tests"
            )


def create_new_deposition(zenodo_client, deposition_id):
    status_code, response = zenodo_client.post_content(
        f"{ZENODO_DEPOSITION}/{deposition_id}/actions/newversion"
    )
    assert status_code == 201
    return response["links"]["latest_draft"].split("/")[-1]


def get_deposit(zenodo_client, deposition_id):
    response = zenodo_client.get_content(
        f"{ZENODO_DEPOSITION}/{deposition_id}"
    )
    return response


def upload_file(
    zenodo_client, url, singularity_image_folder, filename, cleanup=True
):
    path = singularity_image_folder / filename
    assert path.exists()
    response = zenodo_client.put_content(url, data=path)
    if cleanup:
        cleanup(path)
    assert response["links"]["self"] == url


def upload_metadata(zenodo_client, url, model_group):
    data = {
        "metadata": {
            "title": f"{model_group} singularity container",
            "upload_type": "physicalobject",
            "description": "This is a singularity container for models "
            f"under http://kipoi.org/models/{model_group}/",
            "creators": [
                {"name": "Haimasree, Bhattacharya", "affiliation": "EMBL"}
            ],
        }
    }
    response = zenodo_client.put_content(url, data=data)
    assert response["links"]["self"] == url


def push_deposition(zenodo_client, deposition_id):
    status_code, response = zenodo_client.post_content(
        f"{ZENODO_DEPOSITION}/{deposition_id}/actions/publish"
    )
    assert status_code == 202
    response = get_deposit(f"{ZENODO_DEPOSITION}/{deposition_id}")
    return response


def update_existing_singularity_container(
    zenodo_client,
    singularity_dict,
    singularity_image_folder,
    model_group,
    file_to_upload="",
    push=False,
    cleanup=True,
):
    # Create a new version of an existing deposition
    deposition_id = singularity_dict["url"].split("/")[4]
    new_deposition_id = create_new_deposition(zenodo_client, deposition_id)
    assert new_deposition_id != deposition_id
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
        cleanup,
    )

    # publish the newly created revision
    if push:
        response = push_deposition(zenodo_client, new_deposition_id)
        record_id = response["metadata"]["prereserve_doi"]["recid"]
        return {
            "new_deposition_id": new_deposition_id,
            "file_id": response["files"][0]["id"],
            "url": f"{ZENODO_BASE}/record/{record_id}/files/{filename}?download=1",
            "name": response["files"][0]["filename"],
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
    cleanup=True,
):
    """
    This function pushes a singularity image to zenodo
    Parameters
    ----------
    tag : str
       Tag of the singularity image to push
    """
    status_code, response = zenodo_client.post_content(f"{ZENODO_DEPOSITION}")
    assert status_code == 201

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
        cleanup,
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
            "name": response["files"][0]["filename"],
            "md5": response["files"][0]["checksum"],
        }
    else:
        return singularity_dict | {
            "new_deposition_id": deposition_id,
            "file_id": "",
        }


def populate_singularity_container_info(singularity_json):
    with open(singularity_json, "r") as file_handle:
        return json.load(file_handle)


def write_singularity_container_info(
    model_group_to_singularity_image_dict, container_json
):
    with open(container_json, "w") as file_handle:
        json.dump(model_group_to_singularity_image_dict, file_handle, indent=4)


def total_number_of_singularity_containers(
    available_singularity_containers,
):
    unique_singularity_container_counter = Counter(
        [sc for sc in available_singularity_containers]
    )
    return len(unique_singularity_container_counter.keys())
