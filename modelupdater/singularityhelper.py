from collections import Counter
import os
import requests
from pathlib import Path
import json

from spython.main import Client
from kipoi_utils.external.torchvision.dataset_utils import check_integrity


ZENODO_BASE_URL = "https://zenodo.org"


def cleanup(singularity_file_path):
    """
    Cleans up singularity containers that werecreated in build_singularity_image
    """
    singularity_file_path.unlink()


def get_zenodo_access_token():
    ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
    return {"access_token": ACCESS_TOKEN}


def get_content(url, params):
    try:
        response = requests.get(
            url,
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    assert response.status_code == 200
    return response.json()


def put_content(
    url, data, params, headers={"Content-Type": "application/json"}
):
    if isinstance(data, Path):
        with open(data, "rb") as fp:
            try:
                response = requests.put(url, data=fp, params=params)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                raise SystemExit(err)
    else:
        try:
            response = requests.put(
                url, data=json.dumps(data), params=params, headers=headers
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
    assert response.status_code == 200
    return response.json()


def post_content(url, params, json={}):
    try:
        response = requests.post(
            url,
            params=params,
            json=json,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    # TODO: Add appropriate status codes
    return response.status_code, response.json()


def delete_content(url, params):
    try:
        response = requests.delete(
            url,
            # Assuming there will always be one file associated with each version
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    assert response.status_code == 204


def build_singularity_image(name_of_docker_image, singularity_dict):
    """
    This function builds a singularity image from an existing singularity image
    Parameters
    ----------
    singularity_image_name : str
        Name of the singularity image to build
    """
    singularity_image_name = f'{singularity_dict["name"]}.sif'
    singularity_md5 = singularity_dict.get("md5", "")

    singularity_image_folder = os.environ.get(
        "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
    )
    singularity_image_path = Client.pull(
        image=f"docker://{name_of_docker_image}",
        pull_folder=singularity_image_folder,
        force=True,
        name=singularity_image_name,
    )
    checksum_match = check_integrity(singularity_image_path, singularity_md5)
    if checksum_match:
        cleanup(singularity_image_path)
        return False
    else:
        return True


def test_singularity_image(
    singularity_dict, models
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
    singularity_image_folder = os.environ.get(
        "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
    )
    singularity_image_name = f"{singularity_dict['name']}.sif"
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


def push_new_singularity_image(
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
    params = get_zenodo_access_token()
    status_code, response = post_content(
        f"{ZENODO_BASE_URL}/api/deposit/depositions", params=params
    )
    assert status_code == 201

    deposition_id = response["id"]
    bucket_url = response["links"]["bucket"]

    singularity_image_folder = (
        Path(path)
        if path
        else os.environ.get(
            "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
        )
    )
    filename = (
        file_to_upload if file_to_upload else f"{singularity_dict['name']}.sif"
    )
    path = singularity_image_folder / filename
    assert path.exists()

    response = put_content(
        f"{bucket_url}/{filename}", params=params, data=path
    )
    if cleanup:
        cleanup(path)
    assert response["links"]["self"] == f"{bucket_url}/{filename}"

    data = {
        "metadata": {
            "title": f"{model_group} singularity container",
            "upload_type": "physicalobject",
            "description": f"This is a singularity container for models under http://kipoi.org/models/{model_group}/",
            "creators": [
                {"name": "Haimasree, Bhattacharya", "affiliation": "EMBL"}
            ],
        }
    }
    url = f"{ZENODO_BASE_URL}/api/deposit/depositions/{deposition_id}"
    response = put_content(url=url, params=params, data=data)
    if push:
        status_code, response = post_content(
            f"{ZENODO_BASE_URL}/api/deposit/depositions/{deposition_id}/actions/publish",
            params=params,
        )
        assert status_code == 202
        response = get_content(
            f"{ZENODO_BASE_URL}/api/deposit/depositions/{deposition_id}",
            params,
        )
        fileobj = response["files"][0]
        url = f'{ZENODO_BASE_URL}/record/{response["metadata"]["prereserve_doi"]["recid"]}/files/{filename}?download=1'

        return deposition_id, {
            "url": url,
            "name": fileobj["filename"],
            "md5": fileobj["checksum"],
        }
    else:
        return deposition_id, singularity_dict


def update_existing_singularity_container(
    singularity_dict,
    model_group,
    file_to_upload="",
    path="",
    push=False,
    cleanup=True,
):
    params = get_zenodo_access_token()
    singularity_image_folder = (
        Path(path)
        if path
        else os.environ.get(
            "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
        )
    )

    # Create a new version of an existing deposition
    deposition_id = singularity_dict["url"].split("/")[4]
    status_code, response = post_content(
        f"{ZENODO_BASE_URL}/api/deposit/depositions/{deposition_id}/actions/newversion",
        params=params,
    )
    assert status_code == 201

    new_deposition_id = response["links"]["latest_draft"].split("/")[-1]
    assert new_deposition_id != deposition_id

    # Delete existing file from this new version
    response = get_content(
        f"{ZENODO_BASE_URL}/api/deposit/depositions/{new_deposition_id}",
        params,
    )
    bucket_url = response["links"]["bucket"]
    file_id = response["files"][0]["id"]
    delete_content(
        f"{ZENODO_BASE_URL}/api/deposit/depositions/{new_deposition_id}/files/{file_id}",
        params=params,
    )

    # Add a new file to this new version
    filename = (
        file_to_upload if file_to_upload else f"{singularity_dict['name']}.sif"
    )
    path = singularity_image_folder / filename
    assert path.exists()

    response = put_content(
        f"{bucket_url}/{filename}", params=params, data=path
    )
    if cleanup:
        cleanup(path)
    assert response["links"]["self"] == f"{bucket_url}/{filename}"
    # publish the newly created revision
    if push:
        status_code, response = post_content(
            f"{ZENODO_BASE_URL}/api/deposit/depositions/{new_deposition_id}/actions/publish",
            params=params,
        )
        assert status_code == 202
        response = get_content(
            f"{ZENODO_BASE_URL}/api/deposit/depositions/{new_deposition_id}",
            params,
        )
        fileobj = response["files"][0]
        url = f'{ZENODO_BASE_URL}/record/{response["metadata"]["prereserve_doi"]["recid"]}/files/{filename}?download=1'
        return (
            new_deposition_id,
            fileobj["id"],
            {
                "url": url,
                "name": fileobj["filename"],
                "md5": fileobj["checksum"],
            },
        )
    else:
        return new_deposition_id, "", singularity_dict


def populate_singularity_container_info():
    with open(
        Path.cwd() / "test-containers" / "model-group-to-singularity.json", "r"
    ) as singularity_container_json_filehandle:
        return json.load(singularity_container_json_filehandle)


def write_singularity_container_info(model_group_to_singularity_image_dict):
    with open(
        Path.cwd() / "test-containers" / "model-group-to-singularity.json", "w"
    ) as fp:
        json.dump(model_group_to_singularity_image_dict, fp, indent=4)


def total_number_of_singularity_containers(
    available_singularity_container_dict,
):
    list_of_singularity_container_names = Counter(
        [sc["name"] for sc in available_singularity_container_dict]
    )
    return len(list_of_singularity_container_names.keys())
