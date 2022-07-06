from collections import Counter
import json
import logging
import logging.config
from pathlib import Path
from typing import Dict, List, Union, TYPE_CHECKING

from ruamel.yaml import round_trip_load, round_trip_dump
import kipoi

if TYPE_CHECKING:
    from github.Repository import Repository

FileType = Union[str, Path]
CONTAINER_PREFIX = "shared/containers"

logging.config.fileConfig(Path(__file__).resolve().parent / "logging_conf.ini")
logger = logging.getLogger("kipoi_containers")


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
    if branch_exists(kipoi_model_repo):
        json_content = kipoi_model_repo.get_contents(
            f"{CONTAINER_PREFIX}/{json_file}", ref="update-json"
        ).decoded_content.decode()
    else:
        json_content = kipoi_model_repo.get_contents(
            f"{CONTAINER_PREFIX}/{json_file}"
        ).decoded_content.decode()

    return json.loads(json_content)


def write_json(container_model_dict: Dict, container_json: FileType) -> None:
    """
    Write the given dict to the given json file
    """
    with open(container_json, "w") as file_handle:
        json.dump(container_model_dict, file_handle, indent=4)


def branch_exists(kipoi_model_repo: "Repository") -> bool:
    """
    Check if update-json branch exists in kipoi model repo

    Returns:
        bool: True if update-json branch exists, False otherwise
    """
    return any(
        [
            b.name == "update-json"
            for b in list(kipoi_model_repo.get_branches())
        ]
    )


def write_json_to_kipoi(
    container_model_dict: Dict,
    container_json: FileType,
    kipoi_model_repo: "Repository",
) -> bool:
    """
    Create a new branch in kipoi models repo called update-json
    if not present. Write the given dict to the given json file
     in that branch. It returns true if update-json branch has
     been updated, returns false otherwise.
    """
    target_branch = "update-json"
    main_branch = kipoi_model_repo.get_branch("master")
    if not branch_exists(kipoi_model_repo):
        existing_content = kipoi_model_repo.get_contents(
            f"{CONTAINER_PREFIX}/{container_json}"
        )
        existing_container_dict = json.loads(
            existing_content.decoded_content.decode()
        )
        if existing_container_dict != container_model_dict:
            kipoi_model_repo.create_git_ref(
                ref=f"refs/heads/{target_branch}",
                sha=main_branch.commit.sha,
            )
            kipoi_model_repo.update_file(
                existing_content.path,
                f"Updating {container_json}",
                json.dumps(container_model_dict, indent=4),
                existing_content.sha,
                branch=target_branch,
            )
            return True
    else:
        existing_content = kipoi_model_repo.get_contents(
            f"{CONTAINER_PREFIX}/{container_json}", ref=target_branch
        )
        existing_container_dict = json.loads(
            existing_content.decoded_content.decode()
        )
        if existing_container_dict != container_model_dict:
            kipoi_model_repo.update_file(
                existing_content.path,
                f"Updating {container_json}",
                json.dumps(container_model_dict, indent=4),
                existing_content.sha,
                branch=target_branch,
            )
            return True
    return False


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


def create_pr(kipoi_model_repo: "Repository") -> None:
    "Create a pr from update-json to master in kipoi models repo"
    body = "Automatic pr created from kipoi-containers"
    kipoi_model_repo.create_pull(
        title="Update container jsons",
        body=body,
        head="update-json",
        base="master",
    )


def one_model_per_modelgroup(all_models):
    model_list = []
    for model in all_models:
        if not any(model.split("/")[0] in s for s in model_list):
            model_list.append(model)
    return model_list
