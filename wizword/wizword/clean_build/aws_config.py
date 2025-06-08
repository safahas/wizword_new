"""AWS Configuration Module

This module handles AWS configuration and credentials for the word guessing game.
"""
import os
from typing import Dict, Optional
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# DynamoDB Table Names
LEADERBOARD_TABLE = os.getenv('AWS_DYNAMODB_LEADERBOARD_TABLE', 'word_guess_leaderboard')
GAME_STATE_TABLE = os.getenv('AWS_DYNAMODB_GAME_STATE_TABLE', 'word_guess_game_states')

# S3 Bucket Names
SHARE_CARDS_BUCKET = os.getenv('AWS_S3_SHARE_CARDS_BUCKET', 'word-guess-share-cards')

# URL expiration time for share cards (in seconds)
SHARE_URL_EXPIRATION = 7 * 24 * 60 * 60  # 7 days

def get_aws_session() -> Optional[boto3.Session]:
    """
    Create and return an AWS session using environment credentials.
    Returns None if credentials are not configured.
    """
    try:
        if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
            print("AWS credentials not found in environment variables.")
            return None

        session = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        return session
    except Exception as e:
        print(f"Error creating AWS session: {str(e)}")
        return None

def get_dynamodb_client():
    """Get DynamoDB client using the AWS session."""
    session = get_aws_session()
    if session:
        return session.client('dynamodb')
    return None

def get_s3_client():
    """Get S3 client using the AWS session."""
    session = get_aws_session()
    if session:
        return session.client('s3')
    return None

def generate_share_card_url(object_key: str) -> Optional[str]:
    """
    Generate a pre-signed URL for accessing a share card.
    
    Args:
        object_key: The S3 object key (filename) of the share card
        
    Returns:
        Pre-signed URL string or None if generation fails
    """
    try:
        s3_client = get_s3_client()
        if not s3_client:
            return None
            
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': SHARE_CARDS_BUCKET,
                'Key': object_key
            },
            ExpiresIn=SHARE_URL_EXPIRATION
        )
        return url
    except ClientError as e:
        print(f"Error generating share card URL: {str(e)}")
        return None

def check_aws_configuration() -> Dict[str, bool]:
    """
    Check if AWS services are properly configured.
    Returns a dictionary with the status of each service.
    """
    status = {
        'session': False,
        'dynamodb': False,
        's3': False
    }
    
    try:
        # Check AWS session
        session = get_aws_session()
        if session:
            status['session'] = True
            
            # Check DynamoDB
            dynamodb = session.client('dynamodb')
            try:
                dynamodb.describe_table(TableName=LEADERBOARD_TABLE)
                dynamodb.describe_table(TableName=GAME_STATE_TABLE)
                status['dynamodb'] = True
            except Exception as e:
                print(f"DynamoDB error: {str(e)}")
            
            # Check S3
            s3 = session.client('s3')
            try:
                s3.head_bucket(Bucket=SHARE_CARDS_BUCKET)
                status['s3'] = True
            except Exception as e:
                print(f"S3 error: {str(e)}")
    except Exception as e:
        print(f"AWS configuration check error: {str(e)}")
    
    return status 