import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses = boto3.client("ses")

SOURCE_EMAIL: str = os.environ["SOURCE_EMAIL"]
EMAIL_SUBJECT: str = os.environ.get("EMAIL_SUBJECT", "Cloud Messaging Service")


def lambda_handler(event: dict, context) -> str:
    destination_email: str | None = event.get("destinationEmail")
    message: str | None = event.get("message")

    if not destination_email or not message:
        raise ValueError("destinationEmail and message are required")

    logger.info("Sending email to: %s", destination_email)

    try:
        ses.send_email(
            Source=SOURCE_EMAIL,
            Destination={"ToAddresses": [destination_email]},
            Message={
                "Subject": {"Data": EMAIL_SUBJECT},
                "Body": {"Text": {"Data": message}},
            },
        )
    except ClientError as exc:
        logger.error("Failed to send email: %s", exc)
        raise RuntimeError(
            f"Failed to send email: {exc.response['Error']['Message']}"
        ) from exc

    logger.info("Email sent successfully to: %s", destination_email)
    return "Email sent!"
