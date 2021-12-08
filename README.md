# kipoi-containers

This repository contains necessary infrastructure elements for adding and updating docker and singularity images for models and model groups in [Kipoi model zoo](https://kipoi.org/). These images are pre-activated with a compatible conda environment where all the model (group) specific dependencies have been installed.

## Docker and singularity image hosting

- Docker images are hosted in [dockerhub](https://hub.docker.com/repository/docker/kipoi/kipoi-docker).

- Singularity images are hosted in [zenodo](https://zenodo.org/).

- Model specific docker and singularity image information and example usage are located under `docker` and `singularity` tab in each model's webpage at [kipoi website](http://kipoi.org) such as [here](http://kipoi.org/models/DeepMEL/DeepMEL/).

## Installation

- python>=3.9

- Install [docker](https://docs.docker.com/get-docker/)

- Install [singularity](https://sylabs.io/guides/3.0/user-guide/installation.html)
 
- Install kipoi_containers using ```pip install -e .```

## Required environment variables

1. `DOCKER_USERNAME`, `DOCKER_PASSWORD`  
    - Only required for pushing the image to kipoi/kipoi-docker
    - Get it [here](https://hub.docker.com/signup)

2. `ZENODO_ACCESS_TOKEN`  
    - Required for updating and pushing singularity images to zenodo using its rest api
    - Get it [here](https://zenodo.org/account/settings/applications/tokens/new/). Make sure to check deposit:actions and deposit:write

3. `GITHUB_PAT`
    - Required for syncing with [Kipoi model zoo](https://kipoi.org/)
    - Get it [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token). Make sure to add both read and write access

## [Map between models (groups) and docker and singularity images](#dockermap)

- Docker: [here](https://github.com/kipoi/models/blob/master/shared/containers/model-to-docker.json)

  - This maps models (groups) to a docker images. Each value here refers to a dockerhub image which can be pulled using docker cli/api.

- Singularity: [here](https://github.com/kipoi/models/blob/master/shared/containers/model-to-singularity.json)

  - Each entry here has three keys  
    - url: A globally accessible url for the image
    - name: Name of the image without any extension
    - md5: A md5 checksum used to ensure integrity during download

## Sync with Kipoi model zoo

As models get added and updated in the [model zoo](https://github.com/kipoi/models), the respective docker and singularity containers should also be added and updated  along with various json files in `kipoi_contaners/container-info` and github workflows in `.github/workflows`. Execute this as follows -

```bash
python kipoi_containers/updateoradd.py
```

If everything is succesfull `kipoi_containers/kipoi-model-repo-hash` will be updated to the most recent commit on the master branch of the [model zoo](https://github.com/kipoi/models).

**Note:** This **does not** update the jsons residing at the [model repo](https://github.com/kipoi/models/tree/master/shared/containers). For now, only the local jsons at `kipoi_contaners/container-info` gets updated. An automated feature to update the maps at the [model repo](https://github.com/kipoi/models/tree/master/shared/containers) followed by a pr will be added in future.

## Tests

### Testing the package

```bash
docker pull kipoi/kipoi-docker:mmsplice

pytest test-docker test-singularity test-containers/test_update_all_singularity_images.py
```

### Testing the containers manually

Currently, there are two ways to test the docker and singularity images along with the models.

1. Test model(s) at a time or model group(s) if it contains only one model within their respective docker and singularity containers

    ```bash
    pytest test-containers/test_models_from_command_line.py --model=KipoiSplice/4,Basenji
    ```

2. Test any docker image which tests all compatible models or with a specific model group.

- ```bash
  pytest test-containers/test_containers_from_command_line.py --image=kipoi/kipoi-docker:sharedpy3keras2
  ```

- ```bash
  pytest test-containers/test_containers_from_command_line.py --image=kipoi/kipoi-docker:sharedpy3keras2 --modelgroup=HAL
  ```
  
[This workflow](https://github.com/kipoi/kipoi-containers/blob/main/.github/workflows/sync-with-model-repo.yml) keep this repo in sync with [kipoi model repo](https://github.com/kipoi/models). 
This workflow gets triggered on the 1st of every month and can also be trigerred manually.
  
```.github/workflows/release-workflow.yml``` can be manually triggered if all the docker images need to be updated in dockerhub. One reason can be Kipoi package update on pypi. Your dockerhub username and access token must be saved as github encrypoted secrets named DOCKERUSERNAME and DOCKERPASSWORD respectively. For a quick howto look [here](https://docs.github.com/en/actions/reference/encrypted-secrets) 

## Mapping between model and docker images

To know which model group/model is represented by which docker image pleae take a look at https://github.com/kipoi/kipoi-containers/blob/main/test-containers/model-group-to-docker.json.

Due to conflicting package requirements, all models in group MMSplice could not be represented by a single docker image. MMSplice/mtsplice has its own docker image named kipoi/kipoi-docker:mmsplice-mtsplice and the rest can be tested with kipoi/kipoi-docker:mmsplice

## Singularity support

Native support for singularity has been added to kipoi_containers.updateoradd. This utilizes ```singularity pull``` from a dockerhub repo feature which converts the docker container to a singularity container.


## Adding new containers

If new models are added to kipoi repository it is prudent to add all the necessary files in this repo and build, test and push a container to kipoi-docker dockerhub repo. For this purpose, I have provided ```kipoi_containers/updateoradd.py```. Run it as - 

 ```bash
 pip install -e .
 python kipoi_containers/updateoradd.py
 ```
 
 A Personal Access Token is required since we will read from and write to github repos using PyGithub. Please add it as an environment variable named ```GITHUB_PAT```. Docker username and access token is also required for pushing the container to [the docker hub](https://index.docker.io/v1/kipoi/kipoi-docker/). Please add them as environment variables named ```DOCKER_USERNAME``` and ```DOCKER_PASSWORD```. ZENODO access token must also be added as an environment variable named ```ZENODO_ACCESS_TOKEN```. Create it [here](https://zenodo.org/account/settings/applications/tokens/new/) and make sure to click deposit:actions, deposit:write and user:email. This script will update existing images and rerun the tests. If a new model group needs to be updated, add a new dockerfile for model group which has not been containerized yet, build the docker  image, run tests to ensure all corresponding models in the group are compatible with this image, update the json files, update github workflow files, repeat these steps for the singularity containers and finally update ```kipoi_containers/kipoi-model-repo-hash```.  If everything goes well, at this point feel free to push the image and create a PR on github.

