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
            "size": 30,
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
    bucket_url = r.json()["links"]["bucket"]
    print(bucket_url)
    filename = "tiny-container_latest.sif"
    path = Path(__file__).resolve().parent / filename

    with open(path, "rb") as fp:
        r = requests.put(
            "%s/%s" % (bucket_url, filename),
            data=fp,
            params=params,
        )
    assert r.status_code == 200
