$json = '{
    "commands": [
        "export PATH=/usr/local/bin:$PATH",
        "cd /home/ec2-user/word-guess || exit 1",
        "aws ssm get-parameter --name /word-guess/openrouter-api-key --with-decryption --query Parameter.Value --output text > .env || exit 1",
        "echo USE_CLOUD_STORAGE=true >> .env",
        "echo AWS_REGION=us-east-1 >> .env",
        "docker-compose down || exit 1",
        "docker-compose up -d || exit 1"
    ]
}'

$commandOutput = aws ssm send-command `
    --instance-ids "i-01b74c517cdca9fd9" `
    --document-name "AWS-RunShellScript" `
    --parameters $json

$commandId = ($commandOutput | ConvertFrom-Json).Command.CommandId

Write-Host "Command ID: $commandId"
Start-Sleep -Seconds 5

aws ssm get-command-invocation `
    --command-id $commandId `
    --instance-id "i-01b74c517cdca9fd9" 