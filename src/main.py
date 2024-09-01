import requests
from requests import Response
import os

import boto3
import pandas as pd

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import (APIGatewayRestResolver, Response)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

# Get all the environment variables
env = os.environ

logging_level = env.get("LOGGING_LEVEL", "INFO")
csv_path = env.get("CSV_PATH", None)
table_name = env.get("TABLE_NAME", None)
defaultRedirect = env.get("DEFAULT_REDIRECT", "https://www.google.com")

# Logger
logger = Logger(level=logging_level)

# API Gateway Resolver
app = APIGatewayRestResolver()

if table_name:
    try:
        dynamodb = boto3.client('dynamodb')
    except Exception as e:
        logger.exception(f"Error creating DynamoDB client: {e}")
else:
    dynamodb = None

if csv_path:
    if table_name and dynamodb:
        logger.info("Both CSV and DynamoDB paths are set. Using DynamoDB.")
    else:
        try:
            df = pd.read_csv(csv_path,sep=',',header=0, names=['path', 'redirectDestination'])
        except Exception as e:
            logger.exception(f"Error fetching path from CSV: {e}")


# Find path in DynamoDB
def ddb_fetch_redirect(path):
    if table_name and dynamodb:
        logger.info(f"Fetching DynamoDB value for path: {path}")

        try:
            response = dynamodb.get_item(
                TableName=table_name,
                Key={
                    'path': {
                        'S': path
                    }
                }
            )
        except Exception as e:
            logger.exception(f"Error fetching path from DynamoDB: {e}")
            return defaultRedirect
    else:
        if not table_name:
            logger.exception("DynamoDB table name not set")
            return defaultRedirect
        elif not dynamodb:
            logger.exception("DynamoDB client not set")
            return defaultRedirect
        else:
            logger.exception("Unknown error")
            return defaultRedirect

# Find path in CSV
def csv_fetch_redirect(path):
    if csv_path:
        logger.info(f"Fetching CSV value for path: {path}")
        result = df.loc[df['path'] == path, 'redirectDestination']
        if not result.empty:
            return result.iloc[0]
        else:
            logger.info(f"Path not found in CSV: {path}")
            return defaultRedirect
    else:
        logger.exception("CSV path not set")
        return defaultRedirect

# Catch root path with GET
@app.get("/")
def catch_root_get_method():
    logger.info("Catching root GET method")
    logger.info(f"Environment variables: {env}")
    return Response(
        status_code=200,
        body=f"Hello, World!\n{env}",
    )

# Catch any path with GET
@app.get("/.+")
def catch_any_route_get_method():
    logger.info(f"Redirecting on path: {app.current_event.path}")

    path = app.current_event.path.strip("/")

    if dynamodb:
        logger.info("Fetching redirect from DynamoDB")
        redirect = ddb_fetch_redirect(path)
    elif csv_path:
        logger.info("Fetching redirect from CSV")
        redirect = csv_fetch_redirect(path)
    else:
        logger.info("No fetcher set. Using default redirect")
        redirect = defaultRedirect

    return Response(
        status_code=302,
        body="",
        headers={"Location": redirect},
    )

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)