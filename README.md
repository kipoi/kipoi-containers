# kipoi-docker
This is an attempt to reduce  and eventully eliminate complexities related to creating and invoking model specific conda environments. The docker images are hosted 
[here](https://hub.docker.com/repository/docker/haimasree/kipoi-docker).

# Building the docker images

First, we need to build the base image which activates a conda environment made with python 3.6 with kipoi installed in it.
```
docker build -f dockerfiles/Dockerfile.base -t haimasree/kipoi-docker:kipoi-base-env .
```
Note: The model specific Dockefiles are sensitive to the name and tag of the base image right now. 
After the base image is built, build any other image using the following template
```
docker build -f dockerfiles/Dockerfile.<model-group-name-in-lowercase> -t haimasree/kipoi-docker:<image-name> .
```
# Map between model group and docker images

See [here](https://github.com/haimasree/kipoi-containers/blob/main/test-containers/model-group-to-image-name.json)

# Map between docker image and model(s)

See [here](https://github.com/haimasree/kipoi-containers/blob/main/test-containers/image-name-to-model.json)


# Running the images
For an interactive experience, run the following -
```
docker run -it haimasree/kipoi-docker:kipoisplice
```
This will give you an interactive shell with the relevant conda environment kipoi-KipoiSplice.

To run your custom kipoi cli calls directly,
```
docker run haimasree/kipoi-docker:kipoisplice kipoi test KipoiSplice/4 --source=kipoi
```

## Testing the containers

### Manual and CI

We use pytest and docker-py to test the containers.
First in an isolated conda environment or pipenv do the following -
```
pip install -r requirements.txt
```

Currently, there are two ways to test the docker images along with the models.

- Test model(s) at a time or model group(s) if it contains only one model.
  - ```pytest test-containers/test_models_from_command_line.py --model=KipoiSplice/4,Basenji```
  - ```pytest test-containers/test_models_from_command_line.py --model=HAL```

For the corresponding CI (github actions) version, look [here](https://github.com/haimasree/kipoi-containers/blob/main/.github/workflows/test-images.yml).
This workflow gets triggered with every commit to every branch and each pull request to master.
 
 
- Test any docker image which tests all compatible models or with a specific model group
  - ```pytest test-containers/test_containers_from_command_line.py --image=haimasree/kipoi-docker:sharedpy3keras2```
  - ```pytest test-containers/test_containers_from_command_line.py --image=haimasree/kipoi-docker:sharedpy3keras2 --modelgroup=HAL```
  
For the corresponding CI (github actions) version, look [here](https://github.com/haimasree/kipoi-containers/blob/main/.github/workflows/build-and-test-images.yml).
This workflow gets triggered on the 1st of every month. It can also be trigerred manually.
  
  
## Mapping between model and docker images

To know which model group/model is represented by which docker image pleae take a look at https://github.com/haimasree/kipoi-containers/blob/main/test-containers/model-group-to-image-name.json.

Due to conflicting package requirements, all models in group MMSplice could not be represented by a single docker image. MMSplice/mtsplice has its own docker image named haimasree/kipoi-docker:mmsplice-mtsplice and the rest can be tested with haimasree/kipoi-docker:mmsplice

## Singularity support

This feature is meant to support systems where docker is not available due to security reasons or otherwise. There is no need for installing docker. However, singularity must be installed.
The images in [haimasree/kipoi-docker](https://hub.docker.com/repository/docker/haimasree/kipoi-docker) can be easily converted into a local singularity image using ```build-singularity-container.sh```. If no argument is provided, all existing images will be converted and a sample model will be tested against the singularity image as a sanity check. Otherwise, ```./build-singularity-container.sh -i <name of the docker image> -m <compatible model name>``` will convert a docker image in ```haimasree/kipoi-docker``` repo into a singularity image and test the named model. For example,  ```./build-singularity-container.sh -i sharedpy3keras2 -m Basset``` will test Basset with the singularity container made locally from haimasree/kipoi-docker:sharedpy3keras2

## Adding new containers

If new models are added to kipoi repository it is prudent to add all the necessary files in this repo and build, test and push a container to kipoi-docker dockerhub repo. For this purpose, I have provided ```model-updater/update.py```. Run it as ```python model-updater/update.py```. A Personal Access Token is required since we will read from and write to github repos using PyGithub. Please add it as an environment variable named ```GITHUB_PAT```. This script will update existing images and rerun the tests. Also, if necessary, add a new dockerfile for model group which has not been containerized yet, build the docker  image, run tests to ensure all corresponding models in the group are compatible with this image, update the json files, update github workflow files, and finally update ```model-updater/kipoi-model-repo-hash```.  If everything goes well, at this point feel free to push the image and create a PR on github.

### Tests

I have provided some unit tests for testing basic features of this framework. For running these tests, first pull the test image

```bash
docker pull haimasree/kipoi-docker:deepmel
```

Then, install the requirements and run the tests -

```bash
pip install -r requirements.txt
python -m pytest -s test-modelupdater/test_updateoradd.py
```

## Models not working

Following models are missing their respective dataloader.pkl files -
```rbp_eclip/U2AF1, rbp_eclip/U2AF2, rbp_eclip/U2AF2, rbp_eclip/UCHL5, rbp_eclip/UPF1, rbp_eclip/XPO5, rbp_eclip/XRN2, rbp_eclip/YBX3, rbp_eclip/YWHAG, rbp_eclip/ZNF622, rbp_eclip/ZRANB2```
They have been removed from ```test-containers/image-name-to-model.json```.

