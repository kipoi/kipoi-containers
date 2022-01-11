from collections import Counter
import json
from pathlib import Path
from typing import Dict, List, Union, TYPE_CHECKING

from github import GithubException
from ruamel.yaml import round_trip_load, round_trip_dump
import kipoi

if TYPE_CHECKING:
    from github.Repository import Repository

FileType = Union[str, Path]
CONTAINER_PREFIX = "shared/containers"


def populate_json(json_file: FileType) -> Dict:
    """
    Populate and returns a dict using the given json file
    """
    with open(json_file, "r") as file_handle:
        return json.load(file_handle)


def populate_json_from_kipoi(
    json_file: FileType, kipoi_model_repo: "Repository"
) -> Dict:
    """
    Populate and returns a dict using the given json file from Kipoi
    """
    json_content = kipoi_model_repo.get_contents(
        f"{CONTAINER_PREFIX}/{json_file}"
    ).decoded_content.decode()
    return json_content


def write_json(container_model_dict: Dict, container_json: FileType) -> None:
    """
    Write the given dict to the given json file
    """
    with open(container_json, "w") as file_handle:
        json.dump(container_model_dict, file_handle, indent=4)


def write_json_to_kipoi(
    container_model_dict: Dict,
    container_json: FileType,
    kipoi_model_repo: "Repository",
) -> Dict:
    """
    Create a new branch in kipoi models repo. Write the given dict
    to the given json file in that branch.
    """
    # TODO: Create a new branch
    main_branch = kipoi_model_repo.get_branch("master")
    existing_content = kipoi_model_repo.get_contents(
        f"{CONTAINER_PREFIX}/{container_json}"
    ).decoded_content.decode()
    if existing_content != container_model_dict:
        target_branch = "update-json"
        try:
            kipoi_model_repo.create_git_ref(
                ref=f"refs/heads/{target_branch}", sha=main_branch.commit.sha
            )
        except GithubException as err:
            print(err)
        try:
            kipoi_model_repo.update_file(
                existing_content.path,
                f"Updating {container_json}",
                container_model_dict,
                existing_content.sha,
                branch=target_branch,
            )
        except GithubException as err:
            print(err)


def total_number_of_unique_containers(
    list_of_containers: List,
) -> int:
    """Returns the total number of unique names in a list of container names"""
    unique_container_counter = Counter([sc for sc in list_of_containers])
    return len(unique_container_counter.keys())


def populate_yaml(yaml_file: FileType) -> Dict:
    """
    Populate and returns a dict using the given yaml file
    """
    with open(yaml_file, "r") as f:
        return round_trip_load(f, preserve_quotes=True)


def write_yaml(data: Dict, yaml_file: FileType) -> None:
    """
    Write the given dict to the given yaml file
    """
    with open(yaml_file, "w") as f:
        round_trip_dump(data, f)
