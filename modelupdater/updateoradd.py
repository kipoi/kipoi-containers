import os
import json
from pathlib import Path

from .adder import ModelAdder
from github import Github
from .updater import ModelUpdater


class ModelSyncer:
    def __init__(self, github_obj):
        """
        This function initializes several class variables with the
        logged in github instance an from kipoi-model-repo-hash
        and model-group-to-image-name.json.

        Parameters
        ----------
        github_obj : Github instance
            Logged in github instance that is used to get the models
            repo, container repo and current commit hash of kipoi model
            repo.
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
            "./modelupdater/kipoi-model-repo-hash", "r"
        ) as kipoimodelrepohash:
            self.source_commit_hash = kipoimodelrepohash.readline()
        self.list_of_updated_model_groups = []
        with open(
            Path.cwd() / "test-containers" / "model-group-to-image-name.json",
            "r",
        ) as infile:
            self.model_group_to_image_dict = json.load(infile)

    def get_list_of_updated_model_groups(self):
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

        if "shared" in self.list_of_updated_model_groups:
            self.list_of_updated_model_groups.remove("shared")
        if ".circleci" in self.list_of_updated_model_groups:
            self.list_of_updated_model_groups.remove(".circleci")
        if "APARENT" in self.list_of_updated_model_groups:
            self.list_of_updated_model_groups.remove("APARENT")
        if "APARENT/README.md" in self.list_of_updated_model_groups:
            self.list_of_updated_model_groups.remove("APARENT/README.md")

        # TODO: Fix the special case handling for MMSplice
        if "MMSplice/deltaLogitPSI" in self.list_of_updated_model_groups:
            if (
                "MMSplice/modularPredictions"
                in self.list_of_updated_model_groups
            ):
                self.list_of_updated_model_groups.remove(
                    "MMSplice/modularPredictions"
                )
            if "MMSplice/pathogenicity" in self.list_of_updated_model_groups:
                self.list_of_updated_model_groups.remove(
                    "MMSplice/pathogenicity"
                )
            if (
                "MMSplice/splicingEfficiency"
                in self.list_of_updated_model_groups
            ):
                self.list_of_updated_model_groups.remove(
                    "MMSplice/splicingEfficiency"
                )

        print(self.list_of_updated_model_groups)

    def update_or_add_model_container(self, model_group):
        """
        Calls appropariate functions based on whether a model group has
        been updated or added.

        Parameters
        ----------
        model_group : str
            Model group to update or add
        """
        if model_group in self.model_group_to_image_dict:
            model_updater = ModelUpdater()
            name_of_docker_image = self.model_group_to_image_dict[model_group]
            if "shared" not in name_of_docker_image:
                model_updater.update(
                    model_group=model_group,
                    name_of_docker_image=name_of_docker_image,
                )
            else:
                print(f"We will not be updating {name_of_docker_image}")
        else:
            model_adder = ModelAdder(
                model_group=model_group,
                kipoi_model_repo=self.kipoi_model_repo,
                kipoi_container_repo=self.kipoi_container_repo,
            )
            model_adder.add()

    def sync(self):
        """
        Sync this repository with https://github.com/kipoi/models and update the
        commit hash in kipoi-model-repo-hash if everything is fine
        """
        if self.source_commit_hash != self.target_commit_hash:
            self.get_list_of_updated_model_groups()
            for model_group in self.list_of_updated_model_groups:
                self.update_or_add_model_container(model_group=model_group)
        else:
            print("No need to update the repo")

        # If everything has gone well so far update kipoi-model-hash
        with open(
            "./modelupdater/kipoi-model-repo-hash", "w"
        ) as kipoimodelrepohash:
            kipoimodelrepohash.write(self.target_commit_hash)


if __name__ == "__main__":
    """
    Main function which logs in to github with a PAT that is stored in
    an environmental variable called "GITHUB_PAT"
    """
    model_syncer = ModelSyncer(github_obj=Github(os.environ["GITHUB_PAT"]))
    model_syncer.sync()
