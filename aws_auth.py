
import boto3
import re
from botocore.exceptions import ClientError, BotoCoreError


def connect_aws_account(role_arn, external_id, region="us-east-1"):
    """
    Connect to another AWS account securely
    using STS AssumeRole.
    """

    # Validate IAM Role ARN
    if not re.fullmatch(
        r"arn:[^:]+:iam::\d{12}:role/.+",
        role_arn.strip()
    ):
        raise ValueError("Please enter a valid IAM Role ARN.")

    # Validate External ID
    if not external_id or len(external_id) < 2:
        raise ValueError("A valid External ID is required.")

    try:
        # Use the application's AWS identity
        base_session = boto3.Session(region_name=region)

        sts = base_session.client("sts")

        # Request temporary credentials
        response = sts.assume_role(
            RoleArn=role_arn.strip(),
            RoleSessionName="CloudFailureLabSession",
            ExternalId=external_id
        )

        credentials = response["Credentials"]

        # Create a temporary AWS session
        user_session = boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            region_name=region
        )

        return user_session

    except (ClientError, BotoCoreError) as error:
        raise Exception(
            f"AWS connection failed: {error}"
        ) from error
