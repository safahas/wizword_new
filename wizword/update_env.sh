#!/bin/bash

# Get the OpenRouter API key from SSM
OPENROUTER_API_KEY=$(aws ssm get-parameter --name /word-guess/openrouter-api-key --with-decryption --query 'Parameter.Value' --output text)

# Create .env file content
cat > .env << EOL
OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
USE_CLOUD_STORAGE=true
AWS_REGION=us-east-1
EOL

# Copy .env file to both instances
INSTANCES=(i-01b74c517cdca9fd9 i-0f97c19fbb2dd503c)

for instance in "${INSTANCES[@]}"; do
    # Get instance's public IP
    PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $instance --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
    
    echo "Updating environment variables on instance $instance ($PUBLIC_IP)..."
    
    # Copy .env file to instance
    scp -i ~/.ssh/word-guess-key.pem .env ec2-user@$PUBLIC_IP:/home/ec2-user/word-guess/
    
    # Restart the application
    ssh -i ~/.ssh/word-guess-key.pem ec2-user@$PUBLIC_IP "cd /home/ec2-user/word-guess && docker-compose down && docker-compose up -d"
done

# Clean up local .env file
rm .env

echo "Environment variables updated on all instances." 