import boto3
import requests
import csv
import logging
import os

# Get all the environment variables
env = os.environ

logging

logger = logging.getLogger()

def lambda_handler(event, context):
    logging.info('Received event: %s' % event)
    logging.info('Received context: %s' % context)
