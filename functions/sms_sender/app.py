import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client("sns")


def lambda_handler(event: dict, context) -> str:
    phone_number: str | None = event.get("phoneNumber")
    message: str | None = event.get("message")

    if not phone_number or not message:
        raise ValueError("phoneNumber and message are required")

    # Log only a partial number to avoid leaking PII
    logger.info("Sending SMS to: %s****", phone_number[:4])

    try:
        sns.publish(
            PhoneNumber=phone_number,
            Message=message,
        )
    except ClientError as exc:
        logger.error("Failed to send SMS: %s", exc)
        raise RuntimeError(
            f"Failed to send SMS: {exc.response['Error']['Message']}"
        ) from exc

    logger.info("SMS sent successfully")
    return "SMS sent!"
