import os
import shutil
import stat
from git import Repo



# Handles Windows read-only git files
def remove_readonly(func, path, excinfo):

    os.chmod(
        path,
        stat.S_IWRITE
    )

    func(path)




def clone_repository(repo_url):

    """
    Clone GitHub repository into temp_repos folder.

    If the repo was already cloned previously, pull the latest
    changes instead of deleting and re-cloning from scratch. This
    avoids paying the full clone cost every time the same repo is
    analyzed again.
    """


    repo_name = (
        repo_url
        .split("/")[-1]
        .replace(".git", "")
    )


    repo_path = os.path.join(
        "temp_repos",
        repo_name
    )


    if os.path.exists(repo_path):

        try:

            print(
                "Repository already cloned, pulling latest changes..."
            )

            existing_repo = Repo(repo_path)

            existing_repo.remotes.origin.pull()

            print(
                "Pull Complete"
            )

            return repo_path

        except Exception:

            print(
                "Existing clone looks stale or corrupted, re-cloning..."
            )

            shutil.rmtree(
                repo_path,
                onerror=remove_readonly
            )


    print(
        "Downloading Repository..."
    )


    Repo.clone_from(
        repo_url,
        repo_path
    )


    print(
        "Download Complete"
    )


    return repo_path



def get_commit_hash(repo_path):

    """
    Return the current commit hash of the cloned repo. Used as part
    of the cache key so a new commit invalidates the old cache while
    re-analyzing the same commit can reuse it.
    """

    repo = Repo(repo_path)

    return repo.head.commit.hexsha





def get_python_files(repo_path):

    """
    Extract supported programming files
    """


    code_files = []


    supported_extensions = (

        ".py",

        ".js",
        ".jsx",

        ".ts",
        ".tsx",

        ".java",

        ".cpp",
        ".c",
        ".h"

    )


    ignored_folders = (

        ".git",

        "node_modules",

        "__pycache__",

        "venv",

        ".venv",

        "dist",

        "build"

    )



    for root, dirs, files in os.walk(repo_path):


        # remove ignored folders while walking
        dirs[:] = [

            d for d in dirs

            if d not in ignored_folders

        ]



        for file in files:


            if file.endswith(
                supported_extensions
            ):


                path = os.path.join(
                    root,
                    file
                )


                try:


                    with open(
                        path,
                        "r",
                        encoding="utf-8",
                        errors="ignore"
                    ) as f:


                        code_files.append(
                            {

                                "file_path": path,

                                "code": f.read()

                            }
                        )


                except Exception as e:


                    print(
                        "Skipping file:",
                        path
                    )



    return code_files