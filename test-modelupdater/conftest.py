def pytest_generate_tests(metafunc):
    metafunc.cls.model_group_to_update = "DeepMEL"
    metafunc.cls.image_to_update = "haimasree/kipoi-docker:deepmel"
