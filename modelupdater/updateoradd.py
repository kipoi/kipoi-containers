import os
import json
from pathlib import Path

from .adder import ModelAdder
from github import Github
from .udpater import ModelUpdater


class ModelSyncer:
    def __init__(self, github_obj):
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
            "./model-updater/kipoi-model-repo-hash", "r"
        ) as kipoimodelrepohash:
            self.source_commit_hash = kipoimodelrepohash.readline()
        self.list_of_updated_models = []
        with open(
            Path.cwd() / "test-containers" / "model-group-to-image-name.json",
            "r",
        ) as infile:
            self.model_group_to_image_dict = json.load(infile)

    def get_list_of_updated_models(self):
        comparison_obj = self.kipoi_model_repo.compare(
            base=self.source_commit_hash, head=self.target_commit_hash
        )
        self.list_of_updated_models = list(
            dict.fromkeys(
                [f.filename.split("/")[0] for f in comparison_obj.files]
            )
        )
        self.list_of_updated_models = self.list_of_updated_models.remove(
            "shared"
        )

    def update_or_add_model_container(self, model):
        if model in self.model_group_to_image_dict:
            model_updater = ModelUpdater()
            model_updater.update(
                model=model,
                name_of_docker_image=self.model_group_to_image_dict[model],
            )
        else:
            model_adder = ModelAdder(
                model_group=model,
                kipoi_model_repo=self.kipoi_model_repo,
                kipoi_container_repo=self.kipoi_container_repo,
            )
            model_adder.add()

    def sync(self):
        if self.source_commit_hash != self.target_commit_hash:
            self.get_list_of_updated_models()
            for model in self.list_of_updated_models:
                self.update_or_add_model_container(model=model)
        else:
            print("No need to update the repo")

        # If everything has gone well so far update kipoi-model-hash
        with open(
            "./model-updater/kipoi-model-repo-hash", "w"
        ) as kipoimodelrepohash:
            kipoimodelrepohash.write(self.target_commit_hash)


if __name__ == "__main__":
    model_syncer = ModelSyncer(github_obj=Github(os.environ["GITHUB_PAT"]))
    model_syncer.sync()
