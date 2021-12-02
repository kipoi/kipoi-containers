import json
import os
from pathlib import Path
import requests
from typing import Dict, Tuple


class Client:
    def __init__(self):
        self.params = {
            "access_token": os.environ.get("ZENODO_ACCESS_TOKEN", "")
        }

    def get_content(self, url, **kwargs) -> Dict:
        response = requests.get(url, params=self.params | kwargs)
        response.raise_for_status()
        assert response.status_code == 200
        return response.json()

    def put_content(self, url: str, data, **kwargs) -> Dict:
        if isinstance(data, Path):
            with open(data, "rb") as file_handle:
                response = requests.put(
                    url, data=file_handle, params=(self.params | kwargs)
                )
        else:
            response = requests.put(
                url,
                data=json.dumps(data),
                params=(self.params | kwargs),
                headers={"Content-Type": "application/json"},
            )
        response.raise_for_status()
        assert response.status_code == 200
        return response.json()

    def post_content(self, url: str, **kwargs) -> Tuple[int, Dict]:
        response = requests.post(url, params=(self.params | kwargs), json={})
        response.raise_for_status()
        return response.status_code, response.json()

    def delete_content(self, url, **kwargs) -> None:
        # Assumption: There will always be one file associated with each version
        response = requests.delete(
            url,
            params=(self.params | kwargs),
        )
        response.raise_for_status()
        assert response.status_code == 204
