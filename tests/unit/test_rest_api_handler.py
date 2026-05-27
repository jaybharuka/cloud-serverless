import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Set required env var before importing the module
os.environ["STATE_MACHINE_ARN"] = "arn:aws:states:us-east-1:123456789012:stateMachine:test"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from functions.rest_api_handler.app import lambda_handler


def _event(body: dict, method: str = "POST") -> dict:
    return {"httpMethod": method, "body": json.dumps(body)}


# ── CORS preflight ────────────────────────────────────────────────────────────

def test_options_request_returns_200():
    result = lambda_handler({"httpMethod": "OPTIONS"}, None)
    assert result["statusCode"] == 200


# ── Input validation ──────────────────────────────────────────────────────────

def test_invalid_json_returns_400():
    result = lambda_handler({"httpMethod": "POST", "body": "not-json"}, None)
    assert result["statusCode"] == 400
    assert "Invalid JSON" in json.loads(result["body"])["error"]


def test_invalid_type_of_sending_returns_400():
    result = lambda_handler(_event({"typeOfSending": "fax", "message": "hi"}), None)
    assert result["statusCode"] == 400


def test_missing_message_returns_400():
    result = lambda_handler(
        _event({"typeOfSending": "email", "destinationEmail": "a@b.com"}), None
    )
    assert result["statusCode"] == 400
    assert "message" in json.loads(result["body"])["error"]


def test_missing_destination_email_returns_400():
    result = lambda_handler(
        _event({"typeOfSending": "email", "message": "hello"}), None
    )
    assert result["statusCode"] == 400
    assert "destinationEmail" in json.loads(result["body"])["error"]


def test_missing_phone_number_returns_400():
    result = lambda_handler(
        _event({"typeOfSending": "sms", "message": "hello"}), None
    )
    assert result["statusCode"] == 400
    assert "phoneNumber" in json.loads(result["body"])["error"]


# ── Happy paths ───────────────────────────────────────────────────────────────

@patch("functions.rest_api_handler.app.sfn")
def test_valid_email_returns_200_and_starts_execution(mock_sfn):
    mock_sfn.start_execution.return_value = {"executionArn": "arn:test"}
    result = lambda_handler(
        _event({
            "typeOfSending": "email",
            "destinationEmail": "user@example.com",
            "message": "Hello!",
        }),
        None,
    )
    assert result["statusCode"] == 200
    assert json.loads(result["body"])["status"] == "Message queued successfully"
    mock_sfn.start_execution.assert_called_once()


@patch("functions.rest_api_handler.app.sfn")
def test_valid_sms_returns_200_and_starts_execution(mock_sfn):
    mock_sfn.start_execution.return_value = {"executionArn": "arn:test"}
    result = lambda_handler(
        _event({
            "typeOfSending": "sms",
            "phoneNumber": "+1234567890",
            "message": "Hello!",
        }),
        None,
    )
    assert result["statusCode"] == 200
    mock_sfn.start_execution.assert_called_once()


# ── Error handling ────────────────────────────────────────────────────────────

@patch("functions.rest_api_handler.app.sfn")
def test_stepfunctions_client_error_returns_500(mock_sfn):
    from botocore.exceptions import ClientError

    mock_sfn.start_execution.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "Denied"}},
        "StartExecution",
    )
    result = lambda_handler(
        _event({
            "typeOfSending": "email",
            "destinationEmail": "user@example.com",
            "message": "Hello!",
        }),
        None,
    )
    assert result["statusCode"] == 500


# ── CORS headers present on all responses ─────────────────────────────────────

@patch("functions.rest_api_handler.app.sfn")
def test_cors_headers_present(mock_sfn):
    mock_sfn.start_execution.return_value = {"executionArn": "arn:test"}
    result = lambda_handler(
        _event({
            "typeOfSending": "email",
            "destinationEmail": "user@example.com",
            "message": "Hello!",
        }),
        None,
    )
    assert "Access-Control-Allow-Origin" in result["headers"]
