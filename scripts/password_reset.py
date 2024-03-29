import json
import os
import boto3
import uuid
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
from botocore.exceptions import ClientError
import time


def password_reset(event, context):

    sender_id_domain = os.environ.get("DOMAIN_NAME")

    message = event['Records'][0]['Sns']['Message']
    print(message)
    reset_req = json.loads(message)
    print(reset_req["emailId"])

    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    recipient = reset_req["emailId"]

    #Check the emailId in DynamoDB
    #Insert record in DynamoDB if it does not exist. Check the TTL of the existing record.
    #Should be less than 20 minutes for it to be considered valid

    # The token returned from DynamoDB
    token = insert_to_dynamodb(recipient)

    #Preparing and Sending
    if token:
        prepare_and_send_email(recipient, token, sender_id_domain)
    else:
        print('no email sent')
def insert_to_dynamodb(recipient):
    dynamo_table = os.environ.get("DYNAMO_TABLE")
    dynamodb = boto3.resource('dynamodb',region_name=os.environ.get("AWS_REGION"))
    table = dynamodb.Table(dynamo_table)
    ud = uuid.uuid4()
    id = str(ud)
    dynamo_row = table.query(
        KeyConditionExpression=Key('Email').eq(recipient)
    )
    items = dynamo_row['Items']

    if not items:
        response = table.put_item(
        Item={
            'UniqueToken': id,
            'Email': recipient,
            'CreationTime' : str(time.time()),
            'ExpirationTime' : str(time.time() + 1200)
            }
        )
        print("New record inserted successfully")
        return id
    elif items:
        dt = float(items[0]['CreationTime'])
        currentTime = float(time.time())
        time_diff_minutes = (currentTime - dt)/60
        if time_diff_minutes<=20.0:
            print("Requested token within TTL")
        else:
            uid = uuid.uuid4()
            id = str(uid)
            table.update_item(
            Key={
                'Email' : recipient
            },
            UpdateExpression="set UniqueToken = :t, CreationTime = :c, ExpirationTime = :e",
            ExpressionAttributeValues={
            ':t': id,
            ':c': str(time.time()),
            ':e': str(time.time() + 1200)
        },
            ReturnValues="UPDATED_NEW"
        )
            return id

def prepare_and_send_email(recipient, token, sender_id_domain):
    # Sender Email ID. Dummy email which will be used to send emails.
    SENDER = "noreply@" + sender_id_domain

    password_reset_link = "http://" + sender_id_domain + "/reset?email=" + recipient +"&token=" + token

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = (
                    password_reset_link + "\r\n"
                )

    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
      <h1>Password Reset link for Note Taking Application</h1>
      <p>
        <br><br>
        """ + password_reset_link + """
        <br><br>
        This link will be active for 20 minutes only.
      </p>
    </body>
    </html>
                """

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # The subject line for the email.
    SUBJECT = "Password reset request for Note Taking App"

    #Sending the mail
    trigger_email(recipient, BODY_HTML, BODY_TEXT, SUBJECT, CHARSET, SENDER)



def trigger_email(recipient, BODY_HTML, BODY_TEXT, SUBJECT, CHARSET, SENDER):

    AWS_REGION = os.environ.get("AWS_REGION")
    print(AWS_REGION)

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)
    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    recipient,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent!"),
        print(response['MessageId'])
