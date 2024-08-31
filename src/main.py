import requests
from requests import Response
import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import (APIGatewayRestResolver, Response)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

# Get all the environment variables
env = os.environ

logging_level = env.get("LOGGING_LEVEL", "INFO")

# Logger
logger = Logger(level=logging_level)

print(f"Logging level: {logging_level}")

# API Gateway Resolver
app = APIGatewayRestResolver()

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
    logger.info("Catching all GET methods")
    logger.info(f"Environment variables: {env}")
    logger.info(app.current_event)
    return Response(
        status_code=302,
        body="",
        headers={"Location": "https://www.google.com"},
    )

@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)