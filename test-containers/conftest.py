from pathlib import Path
import json


def pytest_addoption(parser):
    """ attaches optional cmd-line args to the pytest machinery """
    parser.addoption(
        "--model", action="append", default=[], help="Model name(s)"
    )
    parser.addoption(
        "--modelgroup", action="append", default=[], help="Model group name(s)"
    )
    parser.addoption("--image", action="append", default=[], help="Image name")
    parser.addoption(
        "--all",
        action="store_true",
        help="run all model groups with one representative model",
    )


def pytest_generate_tests(metafunc):
    with open(
        Path.cwd() / "test-containers" / "model-group-to-image-name.json", "r"
    ) as infile:
        metafunc.cls.model_group_to_image_dict = json.load(infile)

    with open(
        Path.cwd() / "test-containers" / "image-name-to-model.json", "r"
    ) as infile:
        metafunc.cls.image_to_model_dict = json.load(infile)

    if metafunc.config.getoption("all"):
        metafunc.cls.list_of_models = [
            "DeepCpG_DNA/Hou2016_HepG2_dna",
            "CpGenie/A549_ENCSR000DDI",
            "Divergent421",
            "Basenji",
            "Basset",
            "HAL",
            "DeepSEA/variantEffects",
            "Optimus_5Prime",
            "labranchor",
            "CleTimer/customBP",
            "SiSp",
            "FactorNet/FOXA2/onePeak_Unique35_DGF",
            "MaxEntScan/5prime",
            "pwm_HOCOMOCO/human/AHR",
            "DeepBind/Arabidopsis_thaliana/RBP/D00283.001_RNAcompete_At_0284",
            "lsgkm-SVM/Chip/OpenChrom/Cmyc/K562",
            "rbp_eclip/AARS",
            "MPRA-DragoNN/DeepFactorizedModel",
            "extended_coda",
            "MMSplice/deltaLogitPSI",
            "MMSplice/mtsplice",
            "DeepMEL",
            "Framepool",
            "KipoiSplice/4cons",
            "deepTarget",
            "AttentiveChrome/E003",
            "BPNet-OSKN",
            "SeqVec/structure",
        ]
    elif metafunc.config.getoption("modelgroup"):
        modelgroup_from_cmd_line = metafunc.config.getoption("modelgroup")
        if modelgroup_from_cmd_line and hasattr(
            metafunc.cls, "modelgroup_name"
        ):
            modelgroups_to_test = modelgroup_from_cmd_line[0].split(",")
            print(modelgroups_to_test)
            metafunc.cls.modelgroup_name = modelgroups_to_test
    elif metafunc.config.getoption("model"):
        model_from_cmd_line = metafunc.config.getoption("model")
        if model_from_cmd_line and hasattr(metafunc.cls, "model_name"):
            models_to_test = model_from_cmd_line[0].split(",")
            metafunc.cls.model_name = models_to_test
    if metafunc.config.getoption("image"):
        image_from_cmd_line = metafunc.config.getoption("image")
        if image_from_cmd_line and hasattr(metafunc.cls, "image_name"):
            metafunc.cls.image_name = image_from_cmd_line[0]
