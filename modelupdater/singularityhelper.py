import os

from spython.main import Client

def cleanup(images=False):
    """
    Cleans up unused singularity containers, volumes and networks
    """
    pass


def build_singularity_image(name_of_docker_image):
    """
    This function builds a singularity image from an existing singularity image
    Parameters
    ----------
    name_of_singularity_image : str
        Name of the singularity image to build
    """

    singualrity_image = Client.pull(
                        image='docker://{name_of_docker_image}', 
                        pull_folder=os.environ["SINGULARITY_PULL_FOLDER"],
                        force=True)
    
def run_singularity_image(singularity_image_name, model_name):
    """
    Runs a container for a given singularity image and run
    kipoi test <model_name> --source=kipoi inside
    the container, followed by a cleanup

    Parameters
    ----------
    image_name : str
        Name of the singularity image
    model_name : str
        Name of the model to test
    """
    result = Client.execute(singularity_image_name, f"kipoi test {model_name} --source=kipoi", return_result=True)

    
def push_singularity_image(tag):
    """
    This function pushes a singularity image to zenodo
    Parameters
    ----------
    tag : str
       Tag of the singularity image to push
    """
    pass
