#!/bin/bash

# Change to the word-guess directory
cd /home/ec2-user/word-guess

# Get the OpenRouter API key from SSM and create .env file
echo "OPENROUTER_API_KEY=$(aws ssm get-parameter --name /word-guess/openrouter-api-key --with-decryption --query Parameter.Value --output text)" > .env
echo "USE_CLOUD_STORAGE=true" >> .env
echo "AWS_REGION=us-east-1" >> .env

# Restart the containers
docker-compose down
docker-compose up -d 