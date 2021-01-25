from pathlib import Path
import json


def pytest_generate_tests(metafunc):
    metafunc.cls.model_group_to_update = "AttentiveChrome"
    metafunc.cls.image_name_to_update = (
        "haimasree/kipoi-docker:attentivechrome"
    )
