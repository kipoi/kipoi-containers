import json
import os
from pathlib import Path
import requests
from typing import Dict, Tuple, Union


class Client:
    """This class establishes a client which performs GET, POST,
    PUT and DELETE on zenodo rest api"""

    def __init__(self) -> None:
        """This initializes a dict with the value of environment
        variable ZENODO_ACCESS_TOKEN"""
        self.params = {
            "access_token": os.environ.get("ZENODO_ACCESS_TOKEN", "")
        }

    def get_content(self, url: str, **kwargs) -> Dict:
        """Performs GET request to an url and returns the
        response body"""
        response = requests.get(url, params=self.params | kwargs)
        response.raise_for_status()
        return response.json()

    def put_content(self, url: str, data: Union[Path, Dict], **kwargs) -> Dict:
        """Performs PUT request to an url with either a file
        or a dict and returns the response body"""
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
        return response.json()

    def post_content(self, url: str, **kwargs) -> Tuple[int, Dict]:
        """Performs POST request to an url and returns the response status
        and body"""
        response = requests.post(url, params=(self.params | kwargs), json={})
        response.raise_for_status()
        return response.status_code, response.json()

    def delete_content(self, url: str, **kwargs) -> None:
        # Assumption: There will always be one file associated with each version
        """Performs DELETE request to an url"""
        response = requests.delete(
            url,
            params=(self.params | kwargs),
        )
        response.raise_for_status()
