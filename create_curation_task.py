import synapseclient

"""
Create a Synapse RecordSet from a CSV and bind a JSON Schema.

Install/update the Synapse Python client:

    pip install --upgrade synapseclient

Authentication:

    export SYNAPSE_AUTH_TOKEN="<your Synapse personal access token>"

Then:

    python create_recordset.py
"""

import os
from pathlib import Path

import synapseclient

from synapseclient.models import (
    RecordSet,
    CurationTask,
    RecordBasedMetadataTaskProperties,
)



# ---------------------------------------------------------------------
# CONFIGURATION -- CHANGE THESE VALUES
# ---------------------------------------------------------------------

# 1. Synapse folder in which the RecordSet should be created
PARENT_FOLDER_ID = "syn77547639"

# 2. Local CSV file containing the initial RecordSet contents
CSV_PATH = "./recordset.csv"

# 3. Name of the RecordSet entity in Synapse
RECORDSET_NAME = "My RecordSet"

# Optional description
DESCRIPTION = "RecordSet created using the Synapse Python client"

# 4. Registered Synapse JSON Schema URI
#
# <-- PROVIDE YOUR SCHEMA URI HERE
#
SCHEMA_URI = "org.synapse.nf-datalandscape-11.2.23"

# Optional:
# One or more columns that uniquely identify a record.
#
# For example:
# UPSERT_KEYS = ["participant_id"]
#
# or:
# UPSERT_KEYS = ["participant_id", "visit_id"]
#
UPSERT_KEYS = ["recordID"]

# Optional:
# Set to True if you want Synapse to generate entity annotations
# from schema-derived annotations.
ENABLE_DERIVED_ANNOTATIONS = False


# Optional:
#
# Principal ID of the user/team that should own the Grid session.
#
# None means the currently authenticated user.
GRID_OWNER_PRINCIPAL_ID = None


# 5. Curation Task configuration
#
# Synapse PROJECT containing the RecordSet
# NOTE: this is not the folder ID
PROJECT_ID = "syn77547443"

# Must be unique within the project
CURATION_TASK_DATA_TYPE = "my_record_metadata"

CURATION_TASK_INSTRUCTIONS = (
    "Review and complete the metadata records. "
    "Ensure all required fields satisfy the associated JSON Schema."
)


# ---------------------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------------------

def login():
    """
    Authenticate with Synapse.

    Recommended:
        export SYNAPSE_AUTH_TOKEN="<your PAT>"

    synapseclient.login() automatically picks up
    SYNAPSE_AUTH_TOKEN from the environment.
    """

    if not os.environ.get("SYNAPSE_AUTH_TOKEN"):
        print(
            "SYNAPSE_AUTH_TOKEN is not set.\n"
            "Synapse will attempt to use credentials from ~/.synapseConfig."
        )

    return synapseclient.login()


# ---------------------------------------------------------------------
# CREATE RECORDSET
# ---------------------------------------------------------------------

def create_recordset(syn):
    """
    Upload the CSV and create a RecordSet entity.

    RecordSet.store() handles:
      - selecting the appropriate Synapse storage location
      - uploading the CSV
      - creating the FileHandle
      - creating the RecordSet entity
    """

    csv_path = Path(CSV_PATH).expanduser().resolve()

    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV file does not exist: {csv_path}"
        )

    if csv_path.suffix.lower() != ".csv":
        raise ValueError(
            f"RecordSet input should be a CSV file: {csv_path}"
        )

    record_set = RecordSet(
        name=RECORDSET_NAME,
        description=DESCRIPTION,

        # <-- DESTINATION SYNAPSE FOLDER
        parent_id=PARENT_FOLDER_ID,

        # <-- LOCAL CSV TO UPLOAD
        path=str(csv_path),

        # Optional identifiers used when records are later upserted
        upsert_keys=UPSERT_KEYS,
    )

    print(f"Creating RecordSet '{RECORDSET_NAME}'...")
    print(f"Parent: {PARENT_FOLDER_ID}")
    print(f"CSV:    {csv_path}")

    stored_record_set = record_set.store(
        synapse_client=syn
    )

    print(
        f"Created RecordSet: "
        f"{stored_record_set.id}"
    )

    return stored_record_set


# ---------------------------------------------------------------------
# BIND JSON SCHEMA
# ---------------------------------------------------------------------

def bind_schema(record_set, syn):
    """
    Bind a registered Synapse JSON Schema to the RecordSet.
    """

    # <-- YOUR SCHEMA URI IS USED HERE
    binding = record_set.bind_schema(
        json_schema_uri=SCHEMA_URI,
        enable_derived_annotations=ENABLE_DERIVED_ANNOTATIONS,
        synapse_client=syn,
    )

    print(
        f"Bound schema '{SCHEMA_URI}' "
        f"to {record_set.id}"
    )

    return binding


# ---------------------------------------------------------------------
# CURATION TASK
# ---------------------------------------------------------------------

def create_curation_task(record_set, syn):

    task_properties = RecordBasedMetadataTaskProperties(
        record_set_id=record_set.id,
    )

    curation_task = CurationTask(
        project_id=PROJECT_ID,
        data_type=CURATION_TASK_DATA_TYPE,
        instructions=CURATION_TASK_INSTRUCTIONS,
        task_properties=task_properties,
    )

    curation_task = curation_task.store(
        synapse_client=syn
    )

    print(
        f"Created CurationTask: "
        f"{curation_task.task_id}"
    )

    return curation_task


# ---------------------------------------------------------------------
# CREATE GRID SESSION
# ---------------------------------------------------------------------

def create_grid_session(curation_task, syn):
    """
    Create a Grid session for the Curation Task.

    Because this is a record-based CurationTask,
    Synapse automatically uses:

        curation_task.task_properties.record_set_id

    as the source for the Grid.

    create_grid_session() also makes this Grid session the
    active Grid session for the CurationTask.
    """

    grid = curation_task.create_grid_session(
        owner_principal_id=GRID_OWNER_PRINCIPAL_ID,
        synapse_client=syn,
    )

    print(
        f"Created Grid session: "
        f"{grid.session_id}"
    )

    return grid


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    # 1. Authenticate
    syn = login()

    # 2. Upload CSV and create RecordSet
    record_set = create_recordset(syn)

    # 3. Bind JSON Schema
    schema_binding = bind_schema(record_set, syn)

    # 4. create CurationTask for this RecordSet
    curation_task = create_curation_task(
        record_set,
        syn,
    )

    # 5. create a grid session for this task
    grid = create_grid_session(
        curation_task,
        syn,
    )

    print("\nSuccess")
    print("----------------------------------------")
    print(f"RecordSet ID:   {record_set.id}")
    print(f"RecordSet name: {record_set.name}")
    print(f"Parent folder:  {record_set.parent_id}")
    print(f"Schema:         {SCHEMA_URI}")

    if UPSERT_KEYS:
        print(f"Upsert keys:    {', '.join(UPSERT_KEYS)}")

    print(
        "\nRecordSet URL:\n"
        f"https://www.synapse.org/Synapse:{record_set.id}"
    )

    print(f"Curation Task ID:   {curation_task.task_id}")
    print(f"Curation data type: {CURATION_TASK_DATA_TYPE}")
    print(f"Grid session ID:    {grid.session_id}")

    return record_set, schema_binding


if __name__ == "__main__":
    main()
