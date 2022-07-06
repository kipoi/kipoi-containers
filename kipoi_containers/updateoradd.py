import os
import json
from pathlib import Path
import logging
import logging.config

from github import Github

from kipoi_containers.dockeradder import DockerAdder
from kipoi_containers.dockerupdater import DockerUpdater
from kipoi_containers.singularityhandler import SingularityHandler
from kipoi_containers.helper import (
    populate_json,
    populate_json_from_kipoi,
    write_json,
    write_json_to_kipoi,
    populate_yaml,
    write_yaml,
    create_pr,
)
from kipoi_containers.logger import bot

CONTAINER_PREFIX = Path.cwd() / "container-info"
WORKFLOW_PREFIX = Path.cwd() / ".github/workflows"
MODEL_GROUP_TO_DOCKER_JSON = "model-to-docker.json"
DOCKER_TO_MODEL_JSON = CONTAINER_PREFIX / "docker-to-model.json"
MODEL_GROUP_TO_SINGULARITY_JSON = "model-to-singularity.json"
TEST_IMAGES_WORKFLOW = WORKFLOW_PREFIX / "test-images.yml"
RELEASE_WORKFLOW = WORKFLOW_PREFIX / "release-workflow.yml"


class ModelSyncer:
    def __init__(self, github_obj: Github) -> None:
        """
        This function initializes several class variables with the
        logged in github instance, kipoi_containers/kipoi-model-repo-hash,
        MODEL_GROUP_TO_DOCKER_JSON, DOCKER_TO_MODEL_JSON,
        MODEL_GROUP_TO_SINGULARITY_JSON, TEST_IMAGES_WORKFLOW,
        RELEASE_WORKFLOW
        """
        self.github_obj = github_obj
        self.kipoi_container_repo = self.github_obj.get_user().get_repo(
            "kipoi-containers"
        )
        self.kipoi_model_repo = self.github_obj.get_organization(
            "kipoi"
        ).get_repo("models")
        self.target_commit_hash = self.kipoi_model_repo.get_branch(
            "master"
        ).commit.sha
        with open(
            "kipoi_containers/kipoi-model-repo-hash", "r"
        ) as kipoimodelrepohash:
            self.source_commit_hash = kipoimodelrepohash.readline()
        self.model_group_to_docker_dict = populate_json_from_kipoi(
            MODEL_GROUP_TO_DOCKER_JSON, self.kipoi_model_repo
        )
        self.docker_to_model_dict = populate_json(DOCKER_TO_MODEL_JSON)
        self.model_group_to_singularity_dict = populate_json_from_kipoi(
            MODEL_GROUP_TO_SINGULARITY_JSON, self.kipoi_model_repo
        )
        self.workflow_test_data = populate_yaml(TEST_IMAGES_WORKFLOW)
        self.workflow_release_data = populate_yaml(RELEASE_WORKFLOW)
        self.list_of_updated_model_groups = []

    def get_list_of_updated_model_groups(self) -> None:
        """
        Figures out which model groups have been updated or added between
        the commit hash stored in ./kipoi-model-repo-hash and current
        commit hash of kipoi model repo.
        """
        comparison_obj = self.kipoi_model_repo.compare(
            base=self.source_commit_hash, head=self.target_commit_hash
        )

        self.list_of_updated_model_groups = list(
            dict.fromkeys(
                [
                    f"{f.filename.split('/')[0]}/{f.filename.split('/')[1]}"
                    if any(
                        special_model_group in f.filename
                        for special_model_group in ["MMSplice", "APARENT"]
                    )
                    else f.filename.split("/")[0]
                    for f in comparison_obj.files
                ]
            )
        )
        invalid_options = [
            "shared",
            ".circleci",
            "APARENT",
            "APARENT/README.md",
        ]
        self.list_of_updated_model_groups = [
            mg
            for mg in self.list_of_updated_model_groups
            if mg not in invalid_options
        ]
        # Keep only one MMSPlice model which share image kipoi/kipoi-docker:mmsplice
        mmsplice_models = [
            "MMSplice/deltaLogitPSI",
            "MMSplice/modularPredictions",
            "MMSplice/pathogenicity",
            "MMSplice/splicingEfficiency",
        ]
        for model in mmsplice_models:
            if model in self.list_of_updated_model_groups:
                mmsplice_models_to_remove = [
                    mg for mg in mmsplice_models if mg != model
                ]
                self.list_of_updated_model_groups = [
                    mg
                    for mg in self.list_of_updated_model_groups
                    if mg not in mmsplice_models_to_remove
                ]

        bot.info(
            f"Images need to be updated/added are - {self.list_of_updated_model_groups}"
        )

    def update_or_add_model_container(self, model_group: str) -> None:
        """
        Calls appropariate functions based on whether a model group has
        been updated or added.
        """
        if model_group in self.model_group_to_docker_dict:
            name_of_docker_image = self.model_group_to_docker_dict[model_group]
            slim_docker_image = f"{name_of_docker_image}-slim"
            models_to_test = self.docker_to_model_dict[name_of_docker_image]
            singularity_handler = SingularityHandler(
                model_group=model_group,
                docker_image_name=slim_docker_image,
                model_group_to_singularity_dict=self.model_group_to_singularity_dict,
                workflow_release_data=self.workflow_release_data,
            )
            if "shared" not in name_of_docker_image:
                docker_updater = DockerUpdater(
                    model_group=model_group,
                    name_of_docker_image=name_of_docker_image,
                )
                docker_updater.update(models_to_test)
                slim_docker_updater = DockerUpdater(
                    model_group=model_group,
                    name_of_docker_image=slim_docker_image,
                )
                slim_docker_updater.update(models_to_test)
                singularity_handler.update(models_to_test)
            else:
                bot.info(
                    f"We will not be updating {name_of_docker_image} and {slim_docker_image}"
                )
        else:
            model_adder = DockerAdder(
                model_group=model_group,
                kipoi_model_repo=self.kipoi_model_repo,
                kipoi_container_repo=self.kipoi_container_repo,
            )
            model_adder.add(
                model_group_to_docker_dict=self.model_group_to_docker_dict,
                docker_to_model_dict=self.docker_to_model_dict,
                workflow_test_data=self.workflow_test_data,
                workflow_release_data=self.workflow_release_data,
            )
            singularity_handler = SingularityHandler(
                model_group=model_group,
                docker_image_name=f"{model_adder.image_name}-slim",
                model_group_to_singularity_dict=self.model_group_to_singularity_dict,
                workflow_release_data=self.workflow_release_data,
            )
            singularity_handler.add(
                model_adder.list_of_models
                if model_adder.list_of_models
                else [model_adder.model_group],
                self.docker_to_model_dict,
            )

    def sync(self) -> None:
        """
        Sync this repository with https://github.com/kipoi/models and update the
        commit hash in kipoi-model-repo-hash if everything is fine
        """
        if self.source_commit_hash != self.target_commit_hash:
            self.get_list_of_updated_model_groups()
            for model_group in self.list_of_updated_model_groups:
                self.update_or_add_model_container(model_group=model_group)
            write_json(self.docker_to_model_dict, DOCKER_TO_MODEL_JSON)
            update_docker_json = write_json_to_kipoi(
                self.model_group_to_docker_dict,
                MODEL_GROUP_TO_DOCKER_JSON,
                self.kipoi_model_repo,
            )
            update_singularity_json = write_json_to_kipoi(
                self.model_group_to_singularity_dict,
                MODEL_GROUP_TO_SINGULARITY_JSON,
                self.kipoi_model_repo,
            )
            write_yaml(self.workflow_test_data, TEST_IMAGES_WORKFLOW)
            write_yaml(self.workflow_release_data, RELEASE_WORKFLOW)
            if update_docker_json or update_singularity_json:
                create_pr(self.kipoi_model_repo)
        else:
            bot.info("No need to update the repo")

        # If everything has gone well so far update kipoi-model-hash
        with open(
            "kipoi_containers/kipoi-model-repo-hash", "w"
        ) as kipoimodelrepohash:
            kipoimodelrepohash.write(self.target_commit_hash)


if __name__ == "__main__":
    """
    Main function which logs in to github with a PAT that is stored in
    an environmental variable called "GITHUB_TOKEN"
    """
    model_syncer = ModelSyncer(github_obj=Github(os.environ["GITHUB_TOKEN"]))
    model_syncer.sync()
