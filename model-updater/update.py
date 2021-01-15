import subprocess
import sys

from github import Github

def get_kipoi_model_head():
    process = subprocess.Popen(
        ["git", "ls-remote", "https://github.com/kipoi/models", "HEAD"],
        stdout=subprocess.PIPE,
    )
    output = process.communicate()[0].decode("utf-8").split("\t")[0]
    return output
            
def get_list_of_updated_models(source_commit_hash, target_commit_hash, access_token):
    g = Github(access_token)
    kipoi_model_repo = g.get_organization("kipoi").get_repo("models")
    comparison_obj = kipoi_model_repo.compare(base=source_commit_hash, head=target_commit_hash)
    return list(dict.fromkeys([f.filename.split('/')[0] for f in comparison_obj.files]))

def update_or_add_model_container(model):
    print(model)


if __name__ == "__main__":
    with open('./model-updater/kipoi-model-repo-hash', 'r') as kipoimodelrepohash:
        source_commit_hash = kipoimodelrepohash.readline()
        target_commit_hash = get_kipoi_model_head()
    if source_commit_hash != target_commit_hash:
        list_of_updated_models = get_list_of_updated_models(source_commit_hash=source_commit_hash, target_commit_hash=target_commit_hash, access_token=sys.argv[1])
        for model in list_of_updated_models:
            update_or_add_model_container(model=model)
    else:
        print("No need to update the repo")
        
