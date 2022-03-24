import json
import os
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
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
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_content(self, url: str, **kwargs) -> Dict:
        """Performs GET request to an url and returns the
        response body"""
        response = self.session.get(url, params=self.params | kwargs)
        response.raise_for_status()
        return response.json()

    def put_content(self, url: str, data: Union[Path, Dict], **kwargs) -> Dict:
        """Performs PUT request to an url with either a file
        or a dict and returns the response body"""
        if isinstance(data, Path):
            with open(data, "rb") as file_handle:
                response = self.session.put(
                    url, data=file_handle, params=(self.params | kwargs)
                )
        else:
            response = self.session.put(
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
        response = self.session.delete(
            url,
            params=(self.params | kwargs),
        )
        response.raise_for_status()
