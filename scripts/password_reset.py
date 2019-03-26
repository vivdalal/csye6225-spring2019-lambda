import json
import os
import boto3

from botocore.exceptions import ClientError


def password_reset(event, context):
    # what_to_print = os.environ.get("what_to_print")
    print("Hello World")
