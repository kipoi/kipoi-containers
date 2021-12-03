from collections import Counter
import json


def populate_info(json_file):
    with open(json_file, "r") as file_handle:
        return json.load(file_handle)


def write_info(container_model_dict, container_json):
    with open(container_json, "w") as file_handle:
        json.dump(container_model_dict, file_handle, indent=4)


def total_number_of_unique_containers(
    list_of_containers,
):
    unique_container_counter = Counter([sc for sc in list_of_containers])
    return len(unique_container_counter.keys())
