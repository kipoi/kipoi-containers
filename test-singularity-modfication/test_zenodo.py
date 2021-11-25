import os
import requests
import json
from pathlib import Path

# TODO: Move access token to a pytest fixture and add base url https://zenodo.org/api/


def test_zenodo_access():
    ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
    assert ACCESS_TOKEN != ""
    r = requests.get(
        "https://zenodo.org/api/deposit/depositions",
        params={"access_token": ACCESS_TOKEN},
    )
    assert r.status_code == 200


def test_get_available_sc_depositions():
    ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
    assert ACCESS_TOKEN != ""

    r = requests.get(
        "https://zenodo.org/api/deposit/depositions",
        params={
            "access_token": ACCESS_TOKEN,
            "status": "published",
            "q": "singularity container",
            "size": 16,  # TODO: Make this same number as available entries in model-to-singularity-container.json
        },
    )
    assert len(r.json()) == 16
    for index, item in enumerate(r.json()):
        for file_obj in item["files"]:
            assert "kipoi-docker" in file_obj["filename"]


def test_get_existing_sc_by_recordid():
    ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
    assert ACCESS_TOKEN != ""
    # deposition id are same as r.json()[0]["metadata"]["prereserve_doi"]["recid"]
    # This is same in "https://zenodo.org/record/{id}/files/{container_name}
    r = requests.get(
        "https://zenodo.org/api/deposit/depositions/5643929",
        params={
            "access_token": ACCESS_TOKEN,
        },
    )
    assert r.json()["files"][0]["filename"] == "kipoi-docker_deeptarget.sif"


def test_add_new_sc():
    ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
    assert ACCESS_TOKEN != ""
    params = {"access_token": ACCESS_TOKEN}
    r = requests.post(
        "https://zenodo.org/api/deposit/depositions",
        params=params,
        json={},
    )
    assert r.status_code == 201
    deposition_id = r.json()["id"]
    bucket_url = r.json()["links"]["bucket"]
    filename = "tiny-container_latest.sif"
    path = Path(__file__).resolve().parent / filename

    with open(path, "rb") as fp:
        r = requests.put(
            "%s/%s" % (bucket_url, filename),
            data=fp,
            params=params,
        )
    assert r.json()["links"]["self"] == f"{bucket_url}/{filename}"
    assert r.status_code == 200

    data = {
        "metadata": {
            "title": "Tiny test container upload and delete",
            "upload_type": "physicalobject",
            "description": "Tine test container upload and delete",
            "creators": [
                {"name": "Haimasree, Bhattacharya", "affiliation": "EMBL"}
            ],
        }
    }
    url = f"https://zenodo.org/api/deposit/depositions/{deposition_id}?access_token={ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}

    r = requests.put(url, data=json.dumps(data), headers=headers)
    assert r.status_code == 200
    assert r.json()["metadata"]["upload_type"] == "physicalobject"

    # r = requests.get(
    #     f"https://zenodo.org/api/deposit/depositions/{deposition_id}",
    #     params={
    #         "access_token": ACCESS_TOKEN,
    #     },
    # )
    # fileobj = r.json()['files'][0]
    # md5 = fileobj['checksum']
    # name = fileobj['filename']
    # url = f'https://zenodo.org/record/{r.json()["metadata"]["prereserve_doi"]["recid"]}/files/{name}' # This is only valid after publishing
    r = requests.delete(
        f"https://zenodo.org/api/deposit/depositions/{deposition_id}",
        params={"access_token": ACCESS_TOKEN},
    )
    assert r.status_code == 204


def test_update_existing_sc():
    ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
    assert ACCESS_TOKEN != ""
    # Create a new version of an existing deposition
    r = requests.post(
        "https://zenodo.org/api/deposit/depositions/5725937/actions/newversion",
        params={"access_token": ACCESS_TOKEN},
    )
    assert r.status_code == 201
    bucket_url = r.json()["links"]["bucket"]
    print(bucket_url)
    new_deposition_id = r.json()["links"]["latest_draft"].split("/")[-1]
    assert new_deposition_id != 5725937
    # Delete existing file from this new version
    r = requests.get(
        f"https://zenodo.org/api/deposit/depositions/{new_deposition_id}/files",
        params={"access_token": ACCESS_TOKEN},
    )
    assert r.status_code == 200
    print(r.json())
    r = requests.delete(
        f'https://zenodo.org/api/deposit/depositions/{new_deposition_id}/files/{r.json()[0]["id"]}',
        # Assuming there will always be one file associated with each version
        params={"access_token": ACCESS_TOKEN},
    )
    assert r.status_code == 204
    # Add a new file to this new version
    filename = "busybox_1.34.1.sif"
    path = Path(__file__).resolve().parent / filename

    with open(path, "rb") as fp:
        r = requests.put(
            f"{bucket_url}/{filename}",
            data=fp,
            params={"access_token": ACCESS_TOKEN},
        )
    assert r.json()["links"]["self"] == f"{bucket_url}/{filename}"
    assert r.status_code == 200

    # r = requests.post(f'https://zenodo.org/api/deposit/depositions/{deposition_id}/actions/discard',
    #               params={'access_token': ACCESS_TOKEN})
    # assert r.status_code == 201


# def test_get_all_versions_of_anexisting_deposition():
#     pass
