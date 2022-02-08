from typing import Optional, Union

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from vanadium.app.resource import Resources
from vanadium.model import (
    Error,
    RequestAcknowledgement,     # VoterRecordsResponse sub-class
    RequestError,
    RequestRejection,           # VoterRecordsResponse sub-class
    RequestSuccess,             # VoterRecordsResponse sub-class
    SuccessAction,
    VoterRecordsRequest,
)
from vanadium.utils import UniqueIds


# --- Routes

_router = APIRouter(prefix = "/voter/registration")

@_router.post(
    "/",
    response_model = Union[RequestSuccess, RequestRejection],
    response_model_exclude_unset = True,
    # response_model_exclude_none = True,
    response_description = "Voter registration response",
    summary = "Initiate a new voter registration request",
)
def voter_registration_request(
    item: VoterRecordsRequest,
    http_response: Response
):
    """Create a new voter registration request.

    It is an error if no record exists.
    """
    # If a transaction ID was provided use it as the unique ID.
    # Otherwise generate one from the current time.
    # (Note: not robust just good enough for testing.)
    storage = Resources.get_storage()
    registration_id = storage.insert(item.transaction_id, item)
    if registration_id:
        response = RequestSuccess(
            Action = [
                SuccessAction.REGISTRATION_CREATED,
            ],
            TransactionId = registration_id
        )
    else:
        response = RequestRejection(
            AdditionalDetails = [
                "Voter registration request already exists. "
                "The transaction ID is already associated to a pending request."
            ],
            Error = [
                Error(Name = RequestError.IDENTITY_LOOKUP_FAILED),
            ],
            TransactionId = registration_id
        )
        # TODO: Look into this.
        # This isn't right. The request was valid, it's that the action requested
        # doesn't need to be taken.
        http_response.status_code = status.HTTP_400_BAD_REQUEST
    return response


@_router.get(
    "/{transaction_id}",
    response_model = Union[RequestAcknowledgement, RequestRejection],
    response_model_exclude_unset = True,
    response_description = "Voter registration response",
    summary = "Check on the status of a pending voter registration request"
)
def voter_registration_status(
    transaction_id,
    http_response: Response
):
    """Status of pending voter registration request.

    It is an error if no record is found.

    Parameters:
        `transaction_id`: The transaction ID as returned in the initial transaction.

    Returns:
        `RequestAcknowledgement` on success
            Note that this type doesn't allow returning any details about the status.
        `RequestRejection` on failure.

        Note: the `response` field has the official response.
        The `status` and `summary` provide additional information.

    Limitations:

    - Only updates an existing *request*. It does not update a registration
      that has been accepted or rejected, only one that is pending.
      This isn't the correct behavior but it describes the current semantics.
      (The reason is that there isn't yet any long-term storage.)
    - Lookup is only done through the transaction ID, not through other identifiers.
    """
    storage = Resources.get_storage()
    value = storage.lookup(transaction_id)
    if value:
        response = RequestAcknowledgement(
            # There's no way to pass a descriptive message with an Acknowledgement
            # "Transaction request is in process"
            TransactionId = transaction_id
        )
    else:
        response = RequestRejection(
            AdditionalDetails = [
                "Voter registration request not found. "
                "The transaction ID isn't associated with any pending requests."
            ],
            Error = [
                Error(Name = RequestError.IDENTITY_LOOKUP_FAILED)
            ],
            TransactionId = transaction_id
        )
        http_response.status_code = status.HTTP_404_NOT_FOUND
    return response


@_router.put(
    "/{transaction_id}",
    response_model = Union[RequestSuccess, RequestRejection],
    response_model_exclude_unset = True,
    response_description = "Voter registration response",
    summary = "Update a pending voter registration request"
)
def voter_registration_update(
    transaction_id,
    item: VoterRecordsRequest,
    http_response: Response
):
    """Update an existing voter registration request.

    It is an error if there is no record to update.

    Parameters:
        `transaction_id`: The transaction ID as returned

    Limitations:

    - Currently only updates existing *request*. It does not update a registration
      that has been accepted or rejected, only one that is pending.
    - Lookup is only done through the transaction ID, not through other identifiers.
    """
    storage = Resources.get_storage()
    value = storage.update(transaction_id, item)
    if value:
        response = RequestSuccess(
            Action = [
                SuccessAction.REGISTRATION_UPDATED,
            ],
            TransactionId = transaction_id
        )
    else:
        response = RequestRejection(
            AdditionalDetails = [
                "Voter registration request not found. "
                "The transaction ID isn't associated with any pending requests."
            ],
            Error = [
                Error(Name = RequestError.IDENTITY_LOOKUP_FAILED)
            ],
            TransactionId = transaction_id
        )
        http_response.status_code = status.HTTP_404_NOT_FOUND
    return response


@_router.delete(
    "/{transaction_id}",
    response_model = Union[RequestSuccess, RequestRejection],
    response_model_exclude_unset = True,
    response_description = "Voter registration response",
    summary = "Cancel a pending voter registration request"
)
def voter_registration_cancel(
    transaction_id,
    http_response: Response
):
    """Delete an existing request.

    It is an error if there is no record to delete.
    """
    storage = Resources.get_storage()
    value = storage.remove(transaction_id)
    if value:
        response = RequestSuccess(
            Action = [
                SuccessAction.REGISTRATION_CANCELLED,
            ],
            TransactionId = transaction_id
        )
    else:
        response = RequestRejection(
            AdditionalDetails = [
                "Voter registration request not found. "
                "The transaction ID isn't associated with any pending requests."
            ],
            Error = [
                Error(Name = RequestError.IDENTITY_LOOKUP_FAILED)
            ],
            TransactionId = transaction_id
        )
        http_response.status_code = status.HTTP_404_NOT_FOUND
    return response


# --- Router

_routers = [
    _router
]

def router():
    return _router
