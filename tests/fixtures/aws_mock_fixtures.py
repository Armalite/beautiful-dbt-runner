#!/usr/bin/env python3

"""
Fixtures to mock AWS resources needed for DBT Runner testing
"""

import os

import boto3
import pytest
from moto import mock_s3, mock_secretsmanager


@pytest.fixture(scope='session', name='test_aws_credentials')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'


@pytest.fixture(scope='session', name='test_s3_bucket')
def s3(test_aws_credentials):
    with mock_s3():
        yield boto3.client('s3', region_name='us-east-1')


@pytest.fixture(scope='session', name='test_secretsmanager_client')
def secret_client(test_aws_credentials):
    with mock_secretsmanager():
        yield boto3.client('secretsmanager', region_name='us-east-1')


@pytest.fixture(scope='session', name='test_secret')
def create_test_secret(test_secretsmanager_client):

    secretname = "test_secret"
    kmskeyid = "someKMSkeyID"
    secretstring = "PrivateKeyLocatedInsideYourMockSecret"
    mock_secret = test_secretsmanager_client.create_secret(
        Name=secretname,
        Description='Test Mock Secret',
        KmsKeyId=kmskeyid,
        SecretString=secretstring,
        Tags=[
            {
                'Key': 'uuid',
                'Value': 'PotatoesPotatoesPotatoesPotatoes'
            },
        ],
    )
    test_secret_response = {
        "secret": mock_secret,
        "expected_arn": mock_secret["ARN"],
        "expected_secretstring": secretstring
    }
    yield test_secret_response
