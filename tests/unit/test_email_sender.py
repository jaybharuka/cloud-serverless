import os
import sys
from unittest.mock import patch

import pytest

os.environ["SOURCE_EMAIL"] = "noreply@example.com"
os.environ["EMAIL_SUBJECT"] = "Test Subject"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from functions.email_sender.app import lambda_handler


# ── Validation ────────────────────────────────────────────────────────────────

def test_missing_both_fields_raises_value_error():
    with pytest.raises(ValueError, match="required"):
        lambda_handler({}, None)


def test_missing_message_raises_value_error():
    with pytest.raises(ValueError):
        lambda_handler({"destinationEmail": "a@b.com"}, None)


def test_missing_destination_email_raises_value_error():
    with pytest.raises(ValueError):
        lambda_handler({"message": "hello"}, None)


# ── Happy path ────────────────────────────────────────────────────────────────

@patch("functions.email_sender.app.ses")
def test_valid_event_returns_sent_message(mock_ses):
    mock_ses.send_email.return_value = {"MessageId": "msg-001"}
    result = lambda_handler(
        {"destinationEmail": "user@example.com", "message": "Hello!"}, None
    )
    assert result == "Email sent!"
    mock_ses.send_email.assert_called_once()


@patch("functions.email_sender.app.ses")
def test_ses_called_with_correct_source(mock_ses):
    mock_ses.send_email.return_value = {"MessageId": "msg-001"}
    lambda_handler({"destinationEmail": "user@example.com", "message": "Hi"}, None)
    call_kwargs = mock_ses.send_email.call_args[1]
    assert call_kwargs["Source"] == "noreply@example.com"


# ── Error handling ────────────────────────────────────────────────────────────

@patch("functions.email_sender.app.ses")
def test_ses_client_error_raises_runtime_error(mock_ses):
    from botocore.exceptions import ClientError

    mock_ses.send_email.side_effect = ClientError(
        {"Error": {"Code": "MessageRejected", "Message": "Email address not verified"}},
        "SendEmail",
    )
    with pytest.raises(RuntimeError, match="Failed to send email"):
        lambda_handler(
            {"destinationEmail": "user@example.com", "message": "Hello!"}, None
        )
