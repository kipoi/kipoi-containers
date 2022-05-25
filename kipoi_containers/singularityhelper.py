from collections import Counter
from datetime import datetime
import os
import requests
from pathlib import Path
import json
from typing import Dict, Union, TYPE_CHECKING

from kipoi_utils.external.torchvision.dataset_utils import download_url
from spython.main import Client

if TYPE_CHECKING:
    import zenodoclient


ZENODO_BASE = "https://zenodo.org"
ZENODO_DEPOSITION = f"{ZENODO_BASE}/api/deposit/depositions"

PathType = Union[str, Path]


def cleanup(singularity_file_path: PathType) -> None:
    """
    Deletes the singularity image that was created by build_singularity_image
    """
    if isinstance(singularity_file_path, str):
        singularity_file_path = Path(singularity_file_path)
    if singularity_file_path.exists():
        singularity_file_path.unlink()


def build_singularity_image(
    name_of_docker_image: str,
    singularity_image_name: str,
    singularity_image_folder: PathType,
) -> PathType:
    """
    This function builds a singularity image from a dockerhub image
    using singularity pull. The resulting .sif is stored in <singularity_image_folder> and
    the filepath is returned.
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
    singularity_image_folder: PathType, singularity_image_name: str, model: str
) -> None:
    """Tests a singularity image residing in singularity_image_folder
    with kipoi test <model> --source=kipoi

    Raises:
        ValueError: Raise valueerror if the test is not successful"""
    print(
        f"Testing {model} with {singularity_image_folder}/{singularity_image_name}"
    )
    if model == "Basenji":
        test_cmd = f"kipoi test {model} --source=kipoi --batch_size=2"
    else:
        test_cmd = f"kipoi test {model} --source=kipoi"
    if isinstance(singularity_image_folder, str):
        singularity_image_folder = Path(singularity_image_folder)
    if isinstance(singularity_image_name, str):
        singularity_image_name = Path(singularity_image_name)
    result = Client.execute(
        singularity_image_folder / singularity_image_name,
        test_cmd,
        return_result=True,
    )
    if result["return_code"] != 0:
        print(result["message"])
        raise ValueError(
            f"Singularity image {singularity_image_name} for {model} did not pass relevant tests"
        )


def create_new_deposition(
    zenodo_client: "zenodoclient.Client", deposition_id: str
) -> str:
    """Creates a new version of an existing depsosition on zenodo and returns the
    corresponding id"""
    status_code, response = zenodo_client.post_content(
        f"{ZENODO_DEPOSITION}/{deposition_id}/actions/newversion"
    )
    return response["links"]["latest_draft"].split("/")[-1]


def get_deposit(
    zenodo_client: "zenodoclient.Client", deposition_id: str
) -> Dict:
    """Returns the response body of a get request for an existing deposition"""
    response = zenodo_client.get_content(
        f"{ZENODO_DEPOSITION}/{deposition_id}"
    )
    return response


def upload_file(
    zenodo_client: "zenodoclient.Client",
    url: str,
    singularity_image_folder: PathType,
    filename: str,
) -> None:
    """Upload singularity_image_folder/filename to a url"""
    path = Path(singularity_image_folder) / Path(filename)
    zenodo_client.put_content(url, data=path)


def upload_metadata(
    zenodo_client: "zenodoclient.Client", url: str, model_group: str
) -> None:
    """Upload metadata for a model group to a given url"""
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


def push_deposition(
    zenodo_client: "zenodoclient.Client", deposition_id: str
) -> Dict:
    """Pushes a deposition to zenodo. An additional get request is made to the newy pushed
    deposition and a response body is returned"""
    status_code, response = zenodo_client.post_content(
        f"{ZENODO_DEPOSITION}/{deposition_id}/actions/publish"
    )
    response = get_deposit(zenodo_client, deposition_id)
    return response


def update_existing_singularity_container(
    zenodo_client: "zenodoclient.Client",
    singularity_dict: Dict,
    singularity_image_folder: PathType,
    model_group: str,
    file_to_upload: str = "",
    push: bool = True,
) -> None:
    """This function creates a new draft version of an existing image's zenodo entry with updated
    metadata and file after deleting the old file. If push is True, the draft version is finalized
    and the url, name and md5 fields are updated and the new deposition id and file id is added to
    singularity dict which contains information about the existing image. Otherwise, only
    the new deposotion id and file id is added to the dictionary. This modified dictionary is
    returned"""
    # Create a new version of an existing deposition
    deposition_id = singularity_dict["url"].split("/")[4]
    new_deposition_id = create_new_deposition(zenodo_client, deposition_id)
    response = get_deposit(zenodo_client, new_deposition_id)
    bucket_url = response["links"]["bucket"]
    filename = (
        file_to_upload if file_to_upload else f"{singularity_dict['name']}.sif"
    )
    file_id = ""
    for fileobj in response["files"]:
        if fileobj["filename"] == filename:
            file_id = fileobj["id"]  # Assuming only 1 version is added
    # Delete existing file from this new version
    if file_id:
        zenodo_client.delete_content(
            f"{ZENODO_DEPOSITION}/{new_deposition_id}/files/{file_id}"
        )

    # Add a new file to this new version
    upload_file(
        zenodo_client,
        f"{bucket_url}/{filename}",
        singularity_image_folder,
        filename,
    )

    url = f"{ZENODO_DEPOSITION}/{new_deposition_id}"
    upload_metadata(zenodo_client, url, model_group)

    # publish the newly created revision
    if push:
        response = push_deposition(zenodo_client, new_deposition_id)
        record_id = response["metadata"]["prereserve_doi"]["recid"]
        print(response["files"])
        file_id, file_name, file_md5 = "", "", ""
        for fileobj in response["files"]:
            if fileobj["filename"] == filename:
                file_id = fileobj["id"]  # Assuming only 1 version is added
                file_name = fileobj["filename"].replace(".sif", "")
                file_md5 = fileobj["checksum"]
        return {
            "new_deposition_id": new_deposition_id,
            "file_id": file_id,
            "url": f"{ZENODO_BASE}/record/{record_id}/files/{filename}?download=1",
            "name": file_name,
            "md5": file_md5,
        }
    else:
        return singularity_dict | {
            "new_deposition_id": new_deposition_id,
            "file_id": "",
        }


def push_new_singularity_image(
    zenodo_client: "zenodoclient.Client",
    singularity_image_folder: PathType,
    singularity_dict: Dict,
    model_group: str,
    file_to_upload: str = "",
    path: str = "",
    push: bool = True,
) -> None:
    """This function creates a draft version of a new zenodo entry with the
    metadata and singularity image. If push is True, the draft version is finalized
    and the url, name and md5 fields are updated and the new deposition id and file id is added to
    singularity dict which contains empty strings as url and md5. Otherwise, only
    the new deposotion id and file id is added to the dictionary. This modified dictionary is
    returned"""
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
        response = get_deposit(zenodo_client, deposition_id)
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
    singularity_image_folder: PathType,
    singularity_image_dict: Dict,
    model_or_model_group: str,
) -> PathType:
    """This function downloads the singularity image corresponding to the given model or
    model group from zenodo to singularity_image_folder and returns the name of the image"""
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
