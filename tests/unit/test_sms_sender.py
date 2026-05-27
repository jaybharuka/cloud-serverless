import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from functions.sms_sender.app import lambda_handler


# ── Validation ────────────────────────────────────────────────────────────────

def test_missing_both_fields_raises_value_error():
    with pytest.raises(ValueError, match="required"):
        lambda_handler({}, None)


def test_missing_message_raises_value_error():
    with pytest.raises(ValueError):
        lambda_handler({"phoneNumber": "+1234567890"}, None)


def test_missing_phone_number_raises_value_error():
    with pytest.raises(ValueError):
        lambda_handler({"message": "hello"}, None)


# ── Happy path ────────────────────────────────────────────────────────────────

@patch("functions.sms_sender.app.sns")
def test_valid_event_returns_sent_message(mock_sns):
    mock_sns.publish.return_value = {"MessageId": "msg-001"}
    result = lambda_handler(
        {"phoneNumber": "+1234567890", "message": "Hello!"}, None
    )
    assert result == "SMS sent!"
    mock_sns.publish.assert_called_once()


@patch("functions.sms_sender.app.sns")
def test_sns_called_with_correct_phone(mock_sns):
    mock_sns.publish.return_value = {"MessageId": "msg-001"}
    lambda_handler({"phoneNumber": "+1234567890", "message": "Hi"}, None)
    call_kwargs = mock_sns.publish.call_args[1]
    assert call_kwargs["PhoneNumber"] == "+1234567890"
    assert call_kwargs["Message"] == "Hi"


# ── Error handling ────────────────────────────────────────────────────────────

@patch("functions.sms_sender.app.sns")
def test_sns_client_error_raises_runtime_error(mock_sns):
    from botocore.exceptions import ClientError

    mock_sns.publish.side_effect = ClientError(
        {"Error": {"Code": "InvalidParameter", "Message": "Invalid phone number"}},
        "Publish",
    )
    with pytest.raises(RuntimeError, match="Failed to send SMS"):
        lambda_handler(
            {"phoneNumber": "+1234567890", "message": "Hello!"}, None
        )
