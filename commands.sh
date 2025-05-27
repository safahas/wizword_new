#!/bin/bash
export PATH=/usr/local/bin:$PATH
cd /home/ec2-user/word-guess || exit 1
aws ssm get-parameter --name /word-guess/openrouter-api-key --with-decryption --query Parameter.Value --output text > .env || exit 1
echo USE_CLOUD_STORAGE=true >> .env
echo AWS_REGION=us-east-1 >> .env
docker-compose down || exit 1
docker-compose up -d || exit 1 