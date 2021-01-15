import subprocess


def get_kipoi_model_head():
    process = subprocess.Popen(
        ["git", "ls-remote", "https://github.com/kipoi/models", "HEAD"],
        stdout=subprocess.PIPE,
    )
    output = process.communicate()[0].decode("utf-8")
    return output.split("\t")[0]


if __name__ == "__main__":
    print(get_kipoi_model_head())
