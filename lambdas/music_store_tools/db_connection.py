import json
import os
import boto3
import pymysql
import pymysql.cursors


def get_connection() -> pymysql.connections.Connection:
    secret_arn = os.environ["DB_SECRET_ARN"]
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_arn)
    creds = json.loads(response["SecretString"])
    return pymysql.connect(
        host=creds["host"],
        user=creds["username"],
        password=creds["password"],
        database="Chinook_AutoIncrement",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
    )
