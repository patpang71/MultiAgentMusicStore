import json
import os
import boto3


def get_secrets() -> dict:
    secret_arn = os.environ["DB_SECRET_ARN"]
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response["SecretString"])


def get_openai_api_key() -> str:
    return get_secrets()["openai_api_key"]
