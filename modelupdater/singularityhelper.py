import os
import requests
from pathlib import Path
import json

from spython.main import Client


ZENODO_API_URL = "https://zenodo.org/api"


def cleanup(images=False):
    """
    Cleans up unused singularity containers, volumes and networks
    """
    pass


def build_singularity_image(name_of_docker_image, singularity_image_name):
    """
    This function builds a singularity image from an existing singularity image
    Parameters
    ----------
    singularity_image_name : str
        Name of the singularity image to build
    """
    singularity_image_folder = os.environ.get(
        "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
    )
    singualrity_image = Client.pull(
        image=f"docker://{name_of_docker_image}",
        pull_folder=singularity_image_folder,
        force=True,
        name=f"{singularity_image_name}.sif",
    )
    return singualrity_image


def test_singularity_image(singularity_image_name, model_name):
    """
    Tests a container for a given singularity image and run
    kipoi test <model_name> --source=kipoi inside
    the container, followed by a cleanup

    Parameters
    ----------
    image_name : str
        Name of the singularity image
    model_name : str
        Name of the model to test
    """
    result = Client.execute(
        singularity_image_name,
        f"kipoi test {model_name} --source=kipoi",
        return_result=True,
    )
    # TODO: cleanup
    return result


def push_new_singularity_image(singularity_image_name, model_group):
    """
    This function pushes a singularity image to zenodo
    Parameters
    ----------
    tag : str
       Tag of the singularity image to push
    """
    ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
    params = {"access_token": ACCESS_TOKEN}
    try:
        response = requests.post(
            f"{ZENODO_API_URL}/deposit/depositions",
            params=params,
            json={},
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    deposition_id = response.json()["id"]
    bucket_url = response.json()["links"]["bucket"]
    filename = singularity_image_name
    path = Path(__file__).resolve().parent / filename

    with open(path, "rb") as fp:
        try:
            response = requests.put(
                f"{bucket_url}/{filename}",
                data=fp,
                params=params,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)

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
    url = f"{ZENODO_API_URL}/deposit/depositions/{deposition_id}?access_token={ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.put(url, data=json.dumps(data), headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    try:
        response = requests.post(
            f"{ZENODO_API_URL}/deposit/depositions/{deposition_id}/actions/publish",
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    try:
        response = requests.get(
            f"{ZENODO_API_URL}/deposit/depositions/{deposition_id}",
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    fileobj = response.json()["files"][0]
    md5 = fileobj["checksum"]
    name = fileobj["filename"]
    url = f'https://zenodo.org/record/{response.json()["metadata"]["prereserve_doi"]["recid"]}/files/{name}?download=1'

    return {model_group: {"url": url, "name": name, "md5": md5}}


def update_existing_singularity_container(sngularity_dict, model_group):
    ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
    url = sngularity_dict["url"]
    deposition_id = url.split("/")[4]
    params = {"access_token": ACCESS_TOKEN}
    # Create a new version of an existing deposition
    try:
        response = requests.post(
            f"https://zenodo.org/api/deposit/depositions/{deposition_id}/actions/newversion",
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    new_deposition_id = response.json()["links"]["latest_draft"].split("/")[-1]
    assert new_deposition_id != deposition_id

    # Delete existing file from this new version
    try:
        response = requests.get(
            f"https://zenodo.org/api/deposit/depositions/{new_deposition_id}",
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    bucket_url = response.json()["links"]["bucket"]
    file_id = response.json()["files"][0]["id"]
    try:
        response = requests.delete(
            f"https://zenodo.org/api/deposit/depositions/{new_deposition_id}/files/{file_id}",
            # Assuming there will always be one file associated with each version
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    assert response.status_code == 204
    # Add a new file to this new version
    filename = sngularity_dict["name"]
    path = Path(__file__).resolve().parent / filename
    assert path.exists()

    with open(path, "rb") as fp:
        try:
            response = requests.put(
                f"{bucket_url}/{filename}",
                data=fp,
                params=params,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
    assert (
        response.json()["links"]["self"] == f"{bucket_url}/{filename}"
    )  # This is same as
    assert response.status_code == 200

    try:
        response = requests.post(
            f"{ZENODO_API_URL}/deposit/depositions/{new_deposition_id}/actions/publish",
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    try:
        response = requests.get(
            f"{ZENODO_API_URL}/deposit/depositions/{new_deposition_id}",
            params=params,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    fileobj = response.json()["files"][0]
    md5 = fileobj["checksum"]
    name = fileobj["filename"]
    url = f'https://zenodo.org/record/{response.json()["metadata"]["prereserve_doi"]["recid"]}/files/{name}?download=1'

    return {model_group: {"url": url, "name": name, "md5": md5}}


def populate_singularity_container_info():
    with open(
        Path.cwd() / "test-containers" / "model-group-to-singularity.json", "r"
    ) as singularity_container_json_filehandle:
        return json.load(singularity_container_json_filehandle)


def write_singularity_container_info(model_group_to_singularity_image_dict):
    with open(
        Path.cwd() / "test-containers" / "model-group-to-singularity.json", "w"
    ) as fp:
        json.dump(model_group_to_singularity_image_dict, fp, indent=2)
