# Get the OpenRouter API key from SSM
$OPENROUTER_API_KEY = aws ssm get-parameter --name /word-guess/openrouter-api-key --with-decryption --query 'Parameter.Value' --output text

# Create .env file content
@"
OPENROUTER_API_KEY=$OPENROUTER_API_KEY
USE_CLOUD_STORAGE=true
AWS_REGION=us-east-1
"@ | Out-File -FilePath .env -Encoding UTF8

# Copy .env file to both instances
$INSTANCES = @("i-01b74c517cdca9fd9", "i-0f97c19fbb2dd503c")

foreach ($instance in $INSTANCES) {
    # Get instance's public IP
    $PUBLIC_IP = aws ec2 describe-instances --instance-ids $instance --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
    
    Write-Host "Updating environment variables on instance $instance ($PUBLIC_IP)..."
    
    # Copy .env file to instance using AWS Systems Manager
    aws ssm send-command `
        --instance-ids $instance `
        --document-name "AWS-RunShellScript" `
        --parameters commands=@(
            "mkdir -p /home/ec2-user/word-guess",
            "aws s3 cp s3://word-guess-config/.env /home/ec2-user/word-guess/.env",
            "cd /home/ec2-user/word-guess",
            "docker-compose down",
            "docker-compose up -d"
        )
}

# Clean up local .env file
Remove-Item .env

Write-Host "Environment variables updated on all instances." 