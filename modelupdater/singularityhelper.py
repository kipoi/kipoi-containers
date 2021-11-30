import os
import requests
from pathlib import Path
import json

from spython.main import Client


ZENODO_BASE_URL = "https://zenodo.org"


def cleanup(images=False):
    """
    Cleans up unused singularity containers, volumes and networks
    """
    pass


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
    url, params, data, headers={"Content-Type": "application/json"}
):
    try:
        response = requests.put(url, data=data, params=params, header=headers)
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
    return response.json()


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
    return singualrity_image  # TODO: Investigate what does it return?


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
    status_code, response = post_content(
        f"{ZENODO_BASE_URL}/deposit/depositions", params=params
    )
    # TODO: Add status check

    deposition_id = response["id"]
    bucket_url = response["links"]["bucket"]
    filename = singularity_image_name
    path = Path(__file__).resolve().parent / filename

    with open(path, "rb") as fp:
        response = put_content(
            url=f"{bucket_url}/{filename}", params=params, data=fp
        )

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
    url = f"{ZENODO_BASE_URL}/api/deposit/depositions/{deposition_id}?access_token={ACCESS_TOKEN}"
    response = put_content(url=url, params=params, data=json.dumps(data))

    response = post_content(
        f"{ZENODO_BASE_URL}/api/deposit/depositions/{deposition_id}/actions/publish",
        params=params,
    )
    # TODO: Add status check

    response = get_content(
        f"{ZENODO_BASE_URL}/api/deposit/depositions/{deposition_id}", params
    )
    fileobj = response["files"][0]
    url = f'ZENODO_BASE_URL/record/{response["metadata"]["prereserve_doi"]["recid"]}/files/{filename}?download=1'

    return {
        "url": url,
        "name": fileobj["filename"],
        "md5": fileobj["checksum"],
    }


def update_existing_singularity_container(
    singularity_dict, model_group, push=False
):
    ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
    params = {"access_token": ACCESS_TOKEN}
    singularity_image_folder = os.environ.get(
        "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
    )

    # Create a new version of an existing deposition
    deposition_id = singularity_dict["url"].split("/")[4]
    status_code, response = post_content(
        f"ZENODO_BASE_URL/api/deposit/depositions/{deposition_id}/actions/newversion",
        params=params,
    )
    assert status_code == 201

    new_deposition_id = response["links"]["latest_draft"].split("/")[-1]
    assert new_deposition_id != deposition_id

    # Delete existing file from this new version
    response = get_content(
        f"ZENODO_BASE_URL/api/deposit/depositions/{new_deposition_id}", params
    )
    bucket_url = response["links"]["bucket"]
    file_id = response["files"][0]["id"]
    response = delete_content(
        f"ZENODO_BASE_URL/api/deposit/depositions/{new_deposition_id}/files/{file_id}",
        params=params,
    )

    # Add a new file to this new version
    filename = f"{singularity_dict['name']}.sif"
    path = singularity_image_folder / filename
    assert path.exists()

    with open(path, "rb") as fp:
        response = put_content(
            f"{bucket_url}/{filename}", params=params, data=fp
        )
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
        return {
            "url": url,
            "name": fileobj["filename"],
            "md5": fileobj["checksum"],
        }
    else:
        return singularity_dict


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
