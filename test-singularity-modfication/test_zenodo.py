import os
import requests
import json

# TODO: Move access token to a pytest fixture and add base url https://zenodo.org/api/


def test_zenodo_access():
    ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
    assert ACCESS_TOKEN != ""
    r = requests.get(
        "https://zenodo.org/api/deposit/depositions",
        params={"access_token": ACCESS_TOKEN},
    )
    assert r.status_code == 200


# def test_upload_new_file():
#     ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
#     assert ACCESS_TOKEN != ""
#     r = requests.get(
#         "https://zenodo.org/api/deposit/depositions",
#         params={"access_token": ACCESS_TOKEN},
#     )


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
