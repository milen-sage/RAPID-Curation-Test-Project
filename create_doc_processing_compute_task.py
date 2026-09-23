"""
Create a document-processing Compute Task for an existing
record-based Synapse Curation Task.

Uses the Synapse REST API through the stable synapseclient.

Requirements:
    pip install --upgrade synapseclient

Authentication:
    export SYNAPSE_AUTH_TOKEN="<your PAT>"
"""

import json
import os

from synapseclient import Synapse


# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

# Project containing both the existing destination Curation Task
# and the new Compute Task.
PROJECT_ID = "syn77547443"


# Existing record-based Curation Task.
#
# IMPORTANT:
# This is the numeric Curation Task ID, NOT the RecordSet synID.
#
# Example:
# DESTINATION_CURATION_TASK_ID = 12345
#
DESTINATION_CURATION_TASK_ID = 7926


# Folder containing documents to process.
#
# The compute task reads the DIRECT CHILD files of this folder.
SOURCE_DOCUMENT_FOLDER_ID = "syn77547933"


# Must be unique within the project.
#
# This identifies the new Compute Task in the project's task list.
COMPUTE_TASK_DATA_TYPE = "clinical_landscape_document_processing"


# Human-facing description of the compute task.
COMPUTE_TASK_INSTRUCTIONS = (
    "Extract structured metadata from the source documents "
    "and populate the associated RecordSet."
)


# These are the actual instructions sent to the document-processing
# computation.
#
# <-- CUSTOMIZE THIS FOR YOUR DATA
DOCUMENT_PROCESSING_INSTRUCTIONS = """
Extract the metadata described by the JSON Schema associated with
the destination RecordSet.

Produce one row per logical record.

Use the source documents to populate all fields that can be
determined from the documents. Do not invent values that are
not supported by the source material.
""".strip()


# ---------------------------------------------------------------------
# REST CONCRETE TYPES
# ---------------------------------------------------------------------

RECORD_BASED_TASK_PROPERTIES = (
    "org.sagebionetworks.repo.model.curation.metadata."
    "RecordBasedMetadataTaskProperties"
)

RECORD_SET_GENERATION_PROPERTIES = (
    "org.sagebionetworks.repo.model.curation.execution."
    "RecordSetGenerationExecutionProperties"
)

RECORD_SET_GENERATION_DETAILS = (
    "org.sagebionetworks.repo.model.curation.execution."
    "RecordSetGenerationExecutionDetails"
)


# ---------------------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------------------

def login():

    if not os.environ.get("SYNAPSE_AUTH_TOKEN"):
        print(
            "SYNAPSE_AUTH_TOKEN is not set. "
            "Synapse will attempt to use ~/.synapseConfig."
        )

    syn = Synapse()
    syn.login()

    return syn


# ---------------------------------------------------------------------
# VERIFY EXISTING DESTINATION TASK
# ---------------------------------------------------------------------

def get_and_validate_destination_task(syn):
    """
    Retrieve the existing destination Curation Task and confirm
    that it is a record-based task.
    """

    task = syn.restGET(
        f"/curation/task/{DESTINATION_CURATION_TASK_ID}"
    )

    print(
        f"Destination task: {task['taskId']} "
        f"({task['dataType']})"
    )

    if task.get("projectId") != PROJECT_ID:
        raise ValueError(
            "The destination Curation Task does not belong to "
            f"PROJECT_ID={PROJECT_ID}. "
            f"Task project is {task.get('projectId')}."
        )

    task_properties = task.get("taskProperties", {})

    concrete_type = task_properties.get("concreteType")

    if concrete_type != RECORD_BASED_TASK_PROPERTIES:
        raise ValueError(
            "Destination task must be a record-based Curation Task.\n"
            f"Found taskProperties.concreteType:\n{concrete_type}"
        )

    record_set_id = task_properties.get("recordSetId")

    if not record_set_id:
        raise ValueError(
            "Destination Curation Task does not have a recordSetId."
        )

    print(f"Destination RecordSet: {record_set_id}")

    return task


# ---------------------------------------------------------------------
# CREATE DOCUMENT-PROCESSING COMPUTE TASK
# ---------------------------------------------------------------------

def create_document_compute_task(syn):
    """
    Create a RecordSet-generation Compute Task.

    This task:
        SOURCE_DOCUMENT_FOLDER_ID
                  |
                  v
          document processing
                  |
                  v
        DESTINATION_CURATION_TASK_ID
                  |
                  v
              RecordSet
    """

    payload = {
        "projectId": PROJECT_ID,

        # Must be unique within this Synapse project.
        "dataType": COMPUTE_TASK_DATA_TYPE,

        # Human-facing instructions.
        "instructions": COMPUTE_TASK_INSTRUCTIONS,

        "taskProperties": {

            "concreteType": RECORD_SET_GENERATION_PROPERTIES,

            # Folder containing PDF / CSV / TXT / JSON source docs
            "folderId": SOURCE_DOCUMENT_FOLDER_ID,

            # Instructions used by the document-processing computation
            "instructions": DOCUMENT_PROCESSING_INSTRUCTIONS,

            # Existing RECORD-BASED Curation Task
            # whose RecordSet receives the output.
            "destinationTaskId": DESTINATION_CURATION_TASK_ID,
        },
    }

    compute_task = syn.restPOST(
        "/curation/task",
        body=json.dumps(payload),
    )

    print(
        f"Created Compute Task: "
        f"{compute_task['taskId']}"
    )

    return compute_task


# ---------------------------------------------------------------------
# MAKE COMPUTE TASK EXECUTABLE
# ---------------------------------------------------------------------

def initialize_compute_task_execution(syn, compute_task):
    """
    Newly created compute tasks do not initially have executable
    executionDetails.

    Add RecordSetGenerationExecutionDetails so Synapse knows which
    execution worker should handle this task.
    """

    task_id = compute_task["taskId"]

    # Get current TaskStatus so we preserve state + current etag.
    status = syn.restGET(
        f"/curation/task/{task_id}/status"
    )

    if status.get("state") != "NOT_STARTED":
        raise ValueError(
            f"Expected new Compute Task to be NOT_STARTED, "
            f"but state is {status.get('state')}"
        )

    status["executionDetails"] = {
        "concreteType": RECORD_SET_GENERATION_DETAILS
    }

    updated_status = syn.restPUT(
        f"/curation/task/{task_id}/status",
        body=json.dumps(status),
    )

    print(
        f"Compute Task {task_id} is ready for execution."
    )

    return updated_status


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    syn = login()

    # Confirm that the destination is the expected record-based task.
    destination_task = get_and_validate_destination_task(syn)

    # Create document-processing Compute Task.
    compute_task = create_document_compute_task(syn)

    # Add execution details so the task can subsequently be run.
    compute_status = initialize_compute_task_execution(
        syn,
        compute_task,
    )

    print("\nSuccess")
    print("-------------------------------------------")
    print(f"Project:              {PROJECT_ID}")
    print(
        f"Destination Task:     "
        f"{DESTINATION_CURATION_TASK_ID}"
    )
    print(
        f"Destination RecordSet:"
        f" {destination_task['taskProperties']['recordSetId']}"
    )
    print(
        f"Source Folder:        "
        f"{SOURCE_DOCUMENT_FOLDER_ID}"
    )
    print(
        f"Compute Task ID:      "
        f"{compute_task['taskId']}"
    )
    print(
        f"Compute data type:    "
        f"{COMPUTE_TASK_DATA_TYPE}"
    )
    print(
        f"Compute Task state:   "
        f"{compute_status['state']}"
    )

    return compute_task, compute_status


if __name__ == "__main__":
    main()
