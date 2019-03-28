#!/bin/bash

set -e
## Checking whether the stack-name is passed as an arguement
if [ $# -lt 1 ]; then
  echo "Kindly provide stack name! Script execution stopped."
  exit 1
fi
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo "Creating cloud stack with name: $1"
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"

# stackList=$(aws cloudformation list-stack-resources --stack-name $1)
#
# if [ ! -z "$stackList" ]; then
#   echo "Stack already exists. Please use a different name for the stack"
#   echo "Stack creation failed. Exiting..."
#   echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
#   exit 1
# fi

stackList=$(aws cloudformation list-stacks --query 'StackSummaries[?StackStatus != `DELETE_COMPLETE`].{StackName:StackName}')
#echo "stacklist is $stackList"


if [  `echo $stackList | grep -w -c $1 ` -gt 0 ]
then
  echo "Stack with name: $1  exists"
  echo "Stack creation failed"
  echo "Exiting.."
  exit 1
fi

echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
#Listing the buckets in the AWS account and allowing the user to pick the codeDeploy bucket
echo "Displaying all buckets in the AWS Account"
aws s3 ls --human-readable
echo "Select the S3 bucket to store lambda artifacts via CircleCI"
read s3BucketName

if [ -z s3BucketName ]
    then
    echo "Bucket name not provided, exiting code"
    exit 1
fi

echo "Selected bucket : $s3BucketName"
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"

domain=$(aws route53 list-hosted-zones --query 'HostedZones[0].{Name:Name}' --output text)
domain=${domain: 0:-1}

##Creating Stack
#echo "Creating Cloud Stack $1"
response=$(aws cloudformation create-stack --stack-name "$1" --template-body file://csye6225-aws-cf-serverless.json --capabilities CAPABILITY_NAMED_IAM --parameters ParameterKey="S3BUCKETLAMBDA",ParameterValue=$s3BucketName ParameterKey="DOMAINIDNAME",ParameterValue=$domain)
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo "Waiting for Stack $1 to be created"
echo "$response"

aws cloudformation wait stack-create-complete --stack-name $1
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo "stack $1 created successfully"
