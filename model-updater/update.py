import subprocess


def get_kipoi_model_head():
    process = subprocess.Popen(
        ["git", "ls-remote", "https://github.com/kipoi/models", "HEAD"],
        stdout=subprocess.PIPE,
    )
    output = process.communicate()[0].decode("utf-8").split("\t")[0]
    return output
            
if __name__ == "__main__":
    with open('./model-updater/kipoi-model-repo-hash', 'r') as kipoimodelrepohash:
        if kipoimodelrepohash.readline() != get_kipoi_model_head():
            print("No need to update the repo")
        else:
            print("The repo must be updated")