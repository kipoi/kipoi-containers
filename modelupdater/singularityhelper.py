import os
from pathlib import Path
from spython.main import Client


def cleanup(images=False):
    """
    Cleans up unused singularity containers, volumes and networks
    """
    pass


def build_singularity_image(name_of_docker_image, name_of_singularity_image):
    """
    This function builds a singularity image from an existing singularity image
    Parameters
    ----------
    name_of_singularity_image : str
        Name of the singularity image to build
    """
    singularity_image_folder = os.environ.get(
        "SINGULARITY_PULL_FOLDER", Path(__file__).parent.resolve()
    )
    singualrity_image = Client.pull(
        image=f"docker://{name_of_docker_image}",
        pull_folder=singularity_image_folder,
        force=True,
        name=f"{name_of_singularity_image}.sif",
    )
    return singualrity_image


def test_singularity_image(singularity_image_name, model_name):
    """
    Tests a container for a given singularity image and run
    kipoi test <model_name> --source=kipoi inside
    the container, followed by a cleanup

    Parameters
    ----------
    image_name : str
        Name of the singularity image
    model_name : str
        Name of the model to test
    """
    result = Client.execute(
        singularity_image_name,
        f"kipoi test {model_name} --source=kipoi",
        return_result=True,
    )
    # TODO: cleanup
    return result


def push_singularity_image(tag):
    """
    This function pushes a singularity image to zenodo
    Parameters
    ----------
    tag : str
       Tag of the singularity image to push
    """
    pass
