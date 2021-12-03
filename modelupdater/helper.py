from collections import Counter
import json

from ruamel.yaml import round_trip_load, round_trip_dump


def populate_json(json_file):
    with open(json_file, "r") as file_handle:
        return json.load(file_handle)


def write_json(container_model_dict, container_json):
    with open(container_json, "w") as file_handle:
        json.dump(container_model_dict, file_handle, indent=4)


def total_number_of_unique_containers(
    list_of_containers,
):
    unique_container_counter = Counter([sc for sc in list_of_containers])
    return len(unique_container_counter.keys())


def populate_yaml(yaml_file):
    with open(yaml_file, "r") as f:
        return round_trip_load(f, preserve_quotes=True)


def write_yaml(yaml_file, data):
    with open(yaml_file, "w") as f:
        round_trip_dump(data, f)
