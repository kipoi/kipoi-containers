# kipoi-containers

[![Python >=3.9](https://img.shields.io/badge/python-%3E=3.9-cyan.svg)](https://www.python.org/downloads/)
![](https://github.com/kipoi/kipoi-containers/actions/workflows/test-images.yml/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/kipoi/kipoi-containers/badge.svg)](https://coveralls.io/github/kipoi/kipoi-containers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


> [!WARNING]
> ### **Kipoi Project - Sunset Announcement**
> 
> After several impactful years, we have made the decision to **archive the Kipoi repositories and end active maintenance** of the project.
> 
> This is a bittersweet moment. While it’s always a little sad to sunset a project, the field of machine learning in genomics has evolved rapidly, with new technologies and platforms emerging that better meet current needs. Kipoi played an important role in its time, helping researchers **share, reuse, and benchmark trained models** in regulatory genomics. We’re proud of what it accomplished and grateful for the strong community support that made it possible.
> 
> Kipoi’s impact continues, however:
> 
> *   [The Kipoi webinar series](seminar.html) will carry on, supporting discussions around model reuse and interpretability.
> *   [Kipoiseq](https://github.com/kipoi/kipoiseq), our standard set of data-loaders for sequence-based modeling, also remains active and relevant.
> 
> Thanks to everyone who contributed, used, or supported Kipoi. It’s been a fantastic journey, and we're glad the project helped shape how models are shared in the field.
> 
> \- The Kipoi Team

![alt text](misc/kipoicontainers.png?raw=true "kipoi-containers")
This repository contains necessary infrastructure elements for adding and updating docker and singularity images for models and model groups in [Kipoi model zoo](https://kipoi.org/). These images are pre-activated with a compatible conda environment where all the model (group) specific dependencies have been installed.

## Motivation

### Example usage of [kipoi](https://pypi.org/project/kipoi/)

```bash
kipoi env create Basset
source activate kipoi-Basset

kipoi predict Basset \
--dataloader_args='{"intervals_file": "example/intervals_file", "fasta_file": "example/fasta_file"}' \
-o 'Basset.example_pred.tsv'
```

### Main bottleneck

Kipoi uses conda for creating model specific environments.

- It is impossible to gurantee that ```kipoi env create Basset``` resolves in every operating system since conda is not operating system agnostic.
- It is cumbersome, labor intensive and error prone to pin all model dependencies across 31 and counting model groups in kipoi.
- There is no gurantee that even if the dependencies are getting resolved now, they will continue to be resolved in future since the universe of python dependencies are ever changing.

### Solution

Software containers were invented to handle exactly these problems  by making a snapshot of a working system. We use both docker and singularity to make the containers as generalized as possible all the while remaining high performance computing cluster friendly.

### Example usage of kipoi with singularity

```bash
kipoi predict Basset \
--dataloader_args='{"intervals_file": "example/intervals_file", "fasta_file": "example/fasta_file"}' \
-o 'Basset.example_pred.tsv' \
--singularity
```

**Note**: There is no need to create a separate environment as the container comes pre-installed with the model specific conda environment.

### Example usage of kipoi with docker

```bash
docker run -v $PWD/app/ kipoi/kipoi-docker:sharedpy3keras2tf2 
kipoi predict Basset \
--dataloader_args='{'intervals_file': '/app/intervals.bed',
                    'fasta_file': '/app/ref.fa'}' \
-o '/app/Basset.example_pred.tsv'
```

## Docker and singularity image hosting

- Docker images are hosted in [dockerhub](https://hub.docker.com/repository/docker/kipoi/kipoi-docker).

- Singularity images are hosted in [zenodo](https://zenodo.org/).

- Model specific docker and singularity image information and example usage are located under `docker` and `singularity` tab in each model's webpage at [kipoi website](http://kipoi.org) such as [here](http://kipoi.org/models/DeepMEL/DeepMEL/).

## Installation

- python>=3.9

- Install [docker](https://docs.docker.com/get-docker/)

- Install singularity
  - Singularity has been renamed to [Apptainer](https://apptainer.org/). However, it is also possible to use SingularityCE from [Sylabs](https://sylabs.io/). Current versions of kipoi containers are compatible with the latest version of Apptainer (1.0.2) and SingularityCE 3.9. Install Apptainer from [here](https://apptainer.org/docs/user/main/quick_start.html#quick-installation-steps) or SingularityCE from [here](https://sylabs.io/guides/3.9/admin-guide/installation.html).

- Install kipoi_containers using ```pip install -e .```

## Environment variables

1. `DOCKER_USERNAME`, `DOCKER_PASSWORD`  
    - Only required for pushing the image to kipoi/kipoi-docker
    - Get it [here](https://hub.docker.com/signup)

2. `ZENODO_ACCESS_TOKEN`  
    - Required for updating and pushing singularity images to zenodo using its rest api
    - Get it [here](https://zenodo.org/account/settings/applications/tokens/new/). Make sure to check deposit:actions and deposit:write

3. `GITHUB_TOKEN`
    - Required for syncing with [Kipoi model zoo](https://kipoi.org/)
    - Get it [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token). Make sure to add both read and write access

4. `SINGULARITY_PULL_FOLDER` (Optional)
    - If specified, singularity images will be downloaded, built into and pushed from this folder. Otherwise, the current working directory is chosen as default.

## Map between models (groups) and docker and singularity images

- Docker: [here](https://github.com/kipoi/models/blob/master/shared/containers/model-to-docker.json)

  - This maps models (groups) to a docker images. Each value here refers to a dockerhub image which can be pulled using docker cli/api.

- Singularity: [here](https://github.com/kipoi/models/blob/master/shared/containers/model-to-singularity.json)

  - Each entry here has three keys  
    - url: A globally accessible url for the image
    - name: Name of the image without any extension
    - md5: A md5 checksum used to ensure integrity during download

## Sync with Kipoi model repo

As models get added and updated in the [model repo](https://github.com/kipoi/models), the respective docker and singularity containers should also be added and updated  along with various json files in `kipoi_contaners/container-info` and github workflows in `.github/workflows`. Execute this as follows -

```bash
python kipoi_containers/updateoradd.py
```

If everything is succesfull `kipoi_containers/kipoi-model-repo-hash` will be updated to the most recent commit on the master branch of the [model repo](https://github.com/kipoi/models).


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
  pytest test-containers/test_containers_from_command_line.py --image=kipoi/kipoi-docker:sharedpy3keras2tf1
  ```

- ```bash
  pytest test-containers/test_containers_from_command_line.py --image=kipoi/kipoi-docker:sharedpy3keras2tf2 --modelgroup=HAL
  ```
  
## Github action workflows

There are three different workflows at .github/workflow, each of which serves a different purpose. The necessary secrets and workflows are described below.

### Github secrets

  For a quick howto look [here](https://docs.github.com/en/actions/reference/encrypted-secrets)

  1. `DOCKERUSERNAME` and `DOCKERPASSWORD`
      - Correspond to values of env variables `DOCKER_USERNAME` and `DOCKER_PASSWORD` respectively
  2. `ZENODOACCESSTOKEN`
      - Corresponds to value of env variable `ZENODO_ACCESS_TOKEN`
  3. `GITHUBPAT`
      - Corresponds to value of env variable `GITHUB_TOKEN`

### Workflows

1. Continuous integration
    - Which
      - `.github/workflows/test-images.yml`
    - When
      - Push to any branch and pr to main branch in this repo
    - Why
      - `kipoi_containers` package is tested by this workflow
    - How
      - The package is built from scratch and tests specified in `Tests` section get executed. Additionally, one model from every model group gets tested within its docker and singularity containers.

2. Sync with [Kipoi model repo](https://github.com/kipoi/models)
    - Which
      - `.github/workflows/sync-with-model-repo.yml`
    - When
      - On demand and when a pull request is merged to master branch of [model repo](https://github.com/kipoi/models) from [here](https://github.com/kipoi/models/blob/master/.circleci/config.yml#L243-#L253)
    - Why
      - Keep the docker and singularity images up to date with the model definition in the [model repo](https://github.com/kipoi/models)

    - How
      - Update existing images on dockerhub and zenodo if the model definiton has been updated
      - Add new images if new model has been added to the [model repo](https://github.com/kipoi/models)
      - Create a new branch in [model repo](https://github.com/kipoi/models) named  `target-json` if it already does not exist
      - Update `shared/containers/model-to-singularity.json` in branch `target-json` of [model repo](https://github.com/kipoi/models) if a 
        singularity image has been updated in zenodo.
      - Update jsons in `kipoi_containers/container-info/` and ```shared/containers/``` in branch `target-json` 
        of [model repo](https://github.com/kipoi/models) in case a new model has been added
      - Update workflows in `.github/workflow` in case a new model has been added
      - Update `kipoi_containers/kipoi-model-repo-hash`
      - A pr is created automatically which then needs to be reviewed and merged.

3. Build, test and push all docker and singularity images
    - Which
      - `.github/workflows/release-workflow.yml`
    - When
      - On demand and when a new package of kipoi is released to pypi from [here](https://github.com/kipoi/kipoi/blob/master/.circleci/config.yml#L380-#L418)
    - Why
      - Re-build, test and push the docker and singularity images. Some example scenarios -
        - kipoi pypi package has been updated
        - A new version has been released for `continuumio/miniconda3:latest`

    - How
      - Re-build, test and push the dockerhub images. Docker cli is used for this purpose.
      - A new version of the singularity image will be built based on the new docker image. A new version of the existing deposition on zenodo will be created and this modified image will be uploaded there. Finally, this new deposition will be pushed an url will be returned.
      - New url will be updated in `shared/containers/model-to-singularity.json` in branch `target-json` of [model repo](https://github.com/kipoi/models)
