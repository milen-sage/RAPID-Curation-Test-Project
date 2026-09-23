"""
Create a new Synapse Project with two folders:

    Project
    ├── Inputs
    └── TargetRecordSet

Install:
    pip install --upgrade synapseclient

Authentication:
    export SYNAPSE_AUTH_TOKEN="<your Synapse personal access token>"
"""

import os

from synapseclient import Synapse
from synapseclient.models import Project, Folder


# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

# IMPORTANT:
# Synapse project names must be globally unique.
PROJECT_NAME = "My Unique Synapse Project Name"

PROJECT_DESCRIPTION = (
    "Project created for document processing and RecordSet curation."
)


# ---------------------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------------------

def login():
    """
    Authenticate to Synapse.

    Recommended:
        export SYNAPSE_AUTH_TOKEN="<your PAT>"
    """

    if not os.environ.get("SYNAPSE_AUTH_TOKEN"):
        print(
            "SYNAPSE_AUTH_TOKEN is not set. "
            "Synapse will attempt to use credentials "
            "from ~/.synapseConfig."
        )

    syn = Synapse()
    syn.login()

    return syn


# ---------------------------------------------------------------------
# CREATE PROJECT
# ---------------------------------------------------------------------

def create_project(syn):

    project = Project(
        name=PROJECT_NAME,
        description=PROJECT_DESCRIPTION,
    )

    project = project.store(
        synapse_client=syn
    )

    print(
        f"Created Project: "
        f"{project.name} ({project.id})"
    )

    return project


# ---------------------------------------------------------------------
# CREATE FOLDERS
# ---------------------------------------------------------------------

def create_folders(project, syn):

    inputs_folder = Folder(
        name="Inputs",
        parent_id=project.id,
    ).store(
        synapse_client=syn
    )

    print(
        f"Created Inputs folder: "
        f"{inputs_folder.id}"
    )

    target_recordset_folder = Folder(
        name="TargetRecordSet",
        parent_id=project.id,
    ).store(
        synapse_client=syn
    )

    print(
        f"Created TargetRecordSet folder: "
        f"{target_recordset_folder.id}"
    )

    return (
        inputs_folder,
        target_recordset_folder,
    )


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    # 1. Authenticate
    syn = login()

    # 2. Create new Synapse project
    project = create_project(syn)

    # 3. Create Inputs and TargetRecordSet folders
    (
        inputs_folder,
        target_recordset_folder,
    ) = create_folders(
        project,
        syn,
    )

    print("\nSuccess")
    print("----------------------------------------")
    print(f"Project:                {project.id}")
    print(f"Inputs folder:          {inputs_folder.id}")
    print(
        f"TargetRecordSet folder: "
        f"{target_recordset_folder.id}"
    )

    print(
        "\nProject URL:\n"
        f"https://www.synapse.org/Synapse:{project.id}"
    )

    return (
        project,
        inputs_folder,
        target_recordset_folder,
    )


if __name__ == "__main__":
    main()
