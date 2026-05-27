import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn = boto3.client("stepfunctions")

STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def _error(status: int, message: str) -> dict:
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps({"error": message}),
    }


def lambda_handler(event: dict, context) -> dict:
    logger.info("Received event: %s", json.dumps(event))

    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    # Parse body
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _error(400, "Invalid JSON in request body")

    # Validate typeOfSending
    type_of_sending = body.get("typeOfSending")
    if type_of_sending not in ("email", "sms"):
        return _error(400, "typeOfSending must be 'email' or 'sms'")

    # Validate required message
    if not body.get("message"):
        return _error(400, "message is required")

    # Validate type-specific fields
    if type_of_sending == "email" and not body.get("destinationEmail"):
        return _error(400, "destinationEmail is required for email sending")

    if type_of_sending == "sms" and not body.get("phoneNumber"):
        return _error(400, "phoneNumber is required for SMS sending")

    # Start Step Functions execution
    try:
        sfn.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(body),
        )
        logger.info("Started Step Functions execution for type: %s", type_of_sending)
    except ClientError as exc:
        logger.error("Failed to start Step Functions execution: %s", exc)
        return _error(500, "Failed to initiate sending workflow")

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps({"status": "Message queued successfully"}),
    }
