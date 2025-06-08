"""AWS Setup Script

This script helps users configure their AWS settings for the word guessing game.
It creates necessary DynamoDB tables and S3 buckets if they don't exist.
"""
import os
import sys
import json
import boto3
from botocore.exceptions import ClientError
from config.aws_config import (
    AWS_REGION,
    LEADERBOARD_TABLE,
    GAME_STATE_TABLE,
    SHARE_CARDS_BUCKET,
    get_aws_session
)

def create_dynamodb_tables(dynamodb):
    """Create required DynamoDB tables if they don't exist."""
    
    # Leaderboard table
    try:
        dynamodb.create_table(
            TableName=LEADERBOARD_TABLE,
            KeySchema=[
                {'AttributeName': 'nickname', 'KeyType': 'HASH'},
                {'AttributeName': 'game_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'nickname', 'AttributeType': 'S'},
                {'AttributeName': 'game_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print(f"Created table: {LEADERBOARD_TABLE}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table already exists: {LEADERBOARD_TABLE}")
        else:
            print(f"Error creating table {LEADERBOARD_TABLE}: {str(e)}")
            return False

    # Game state table
    try:
        dynamodb.create_table(
            TableName=GAME_STATE_TABLE,
            KeySchema=[
                {'AttributeName': 'game_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'game_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print(f"Created table: {GAME_STATE_TABLE}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table already exists: {GAME_STATE_TABLE}")
        else:
            print(f"Error creating table {GAME_STATE_TABLE}: {str(e)}")
            return False

    return True

def create_s3_bucket(s3):
    """Create S3 bucket for share cards if it doesn't exist."""
    try:
        # For us-east-1, we don't specify LocationConstraint
        if AWS_REGION == 'us-east-1':
            s3.create_bucket(Bucket=SHARE_CARDS_BUCKET)
        else:
            s3.create_bucket(
                Bucket=SHARE_CARDS_BUCKET,
                CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
            )
        print(f"Created bucket: {SHARE_CARDS_BUCKET}")
        
        # Block all public access for security
        s3.put_public_access_block(
            Bucket=SHARE_CARDS_BUCKET,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        print(f"Configured private access for bucket: {SHARE_CARDS_BUCKET}")
        
        # Enable versioning for data protection
        s3.put_bucket_versioning(
            Bucket=SHARE_CARDS_BUCKET,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print(f"Enabled versioning for bucket: {SHARE_CARDS_BUCKET}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print(f"Bucket already exists: {SHARE_CARDS_BUCKET}")
        else:
            print(f"Error creating bucket {SHARE_CARDS_BUCKET}: {str(e)}")
            return False
    return True

def main():
    """Main setup function."""
    print("Setting up AWS resources for Word Guessing Game...")
    
    # Get AWS session
    session = get_aws_session()
    if not session:
        print("Failed to create AWS session. Please check your credentials.")
        sys.exit(1)
    
    # Create DynamoDB tables
    print("\nSetting up DynamoDB tables...")
    dynamodb = session.client('dynamodb')
    if not create_dynamodb_tables(dynamodb):
        print("Failed to set up DynamoDB tables.")
        sys.exit(1)
    
    # Create S3 bucket
    print("\nSetting up S3 bucket...")
    s3 = session.client('s3')
    if not create_s3_bucket(s3):
        print("Failed to set up S3 bucket.")
        sys.exit(1)
    
    print("\nAWS setup completed successfully!")
    print(f"Region: {AWS_REGION}")
    print(f"DynamoDB Tables: {LEADERBOARD_TABLE}, {GAME_STATE_TABLE}")
    print(f"S3 Bucket: {SHARE_CARDS_BUCKET}")

if __name__ == "__main__":
    main() 