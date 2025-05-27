#!/usr/bin/env python3
"""
Deployment script for Word Guess Game AWS infrastructure.
This script helps deploy and manage the AWS resources using CloudFormation.
"""

import os
import sys
import boto3
import argparse
import time
from botocore.exceptions import ClientError

def parse_args():
    parser = argparse.ArgumentParser(description='Deploy Word Guess Game infrastructure')
    parser.add_argument('--environment', default='Development',
                      choices=['Development', 'Staging', 'Production'],
                      help='Deployment environment')
    parser.add_argument('--domain', required=True,
                      help='Domain name for the application')
    parser.add_argument('--region', default='us-east-1',
                      help='AWS region to deploy to')
    parser.add_argument('--action', required=True,
                      choices=['deploy', 'update', 'delete'],
                      help='Action to perform')
    return parser.parse_args()

def get_certificate_arn(acm_client, domain_name):
    """Get or create SSL certificate for the domain."""
    try:
        # List certificates and find matching one
        paginator = acm_client.get_paginator('list_certificates')
        for page in paginator.paginate():
            for cert in page['CertificateSummaryList']:
                if cert['DomainName'] == f"*.{domain_name}":
                    return cert['CertificateArn']
        
        # If not found, request new certificate
        response = acm_client.request_certificate(
            DomainName=f"*.{domain_name}",
            ValidationMethod='DNS',
            SubjectAlternativeNames=[domain_name]
        )
        print(f"Requested new certificate for {domain_name}")
        print("Please add the DNS validation records and wait for validation")
        return response['CertificateArn']
    except ClientError as e:
        print(f"Error managing certificate: {str(e)}")
        sys.exit(1)

def deploy_stack(cf_client, stack_name, template_path, parameters):
    """Deploy or update CloudFormation stack."""
    try:
        # Read template
        with open(template_path) as f:
            template_body = f.read()
        
        # Check if stack exists
        try:
            cf_client.describe_stacks(StackName=stack_name)
            exists = True
        except ClientError:
            exists = False
        
        # Create or update stack
        if exists:
            print(f"Updating stack {stack_name}...")
            cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
            )
        else:
            print(f"Creating stack {stack_name}...")
            cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
            )
        
        # Wait for completion
        print("Waiting for stack operation to complete...")
        waiter = cf_client.get_waiter('stack_update_complete' if exists else 'stack_create_complete')
        waiter.wait(StackName=stack_name)
        print("Stack operation completed successfully")
        
    except ClientError as e:
        print(f"Error deploying stack: {str(e)}")
        sys.exit(1)

def delete_stack(cf_client, stack_name):
    """Delete CloudFormation stack."""
    try:
        print(f"Deleting stack {stack_name}...")
        cf_client.delete_stack(StackName=stack_name)
        
        # Wait for completion
        print("Waiting for stack deletion to complete...")
        waiter = cf_client.get_waiter('stack_delete_complete')
        waiter.wait(StackName=stack_name)
        print("Stack deleted successfully")
        
    except ClientError as e:
        print(f"Error deleting stack: {str(e)}")
        sys.exit(1)

def main():
    args = parse_args()
    
    # Initialize AWS clients
    session = boto3.Session(region_name=args.region)
    cf_client = session.client('cloudformation')
    acm_client = session.client('acm')
    
    stack_name = f"word-guess-game-{args.environment.lower()}"
    template_path = "cloudformation/word-guess-stack.yaml"
    
    if args.action in ['deploy', 'update']:
        # Get certificate ARN
        cert_arn = get_certificate_arn(acm_client, args.domain)
        
        # Prepare parameters
        parameters = [
            {'ParameterKey': 'Environment', 'ParameterValue': args.environment},
            {'ParameterKey': 'DomainName', 'ParameterValue': args.domain},
            {'ParameterKey': 'CertificateArn', 'ParameterValue': cert_arn}
        ]
        
        # Deploy stack
        deploy_stack(cf_client, stack_name, template_path, parameters)
        
    elif args.action == 'delete':
        # Delete stack
        delete_stack(cf_client, stack_name)

if __name__ == '__main__':
    main() 