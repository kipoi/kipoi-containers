import os
import requests


def test_zenodo_access():
    ACCESS_TOKEN = os.environ.get("ZENODO_ACCESS_TOKEN", "")
    assert ACCESS_TOKEN != ""
    r = requests.get(
        "https://zenodo.org/api/deposit/depositions",
        params={"access_token": ACCESS_TOKEN},
    )
    assert r.status_code == 200
