$content = Get-Content -Path "commands.sh" -Raw
$encodedContent = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($content))

$params = @{
    commands = @(
        "echo $encodedContent | base64 -d > /tmp/update.sh",
        "chmod +x /tmp/update.sh",
        "/tmp/update.sh",
        "rm /tmp/update.sh"
    )
}

$jsonString = $params | ConvertTo-Json
$jsonString = $jsonString.Replace('"', '\"')

aws ssm send-command --instance-ids "i-079d801af90793989" --document-name "AWS-RunShellScript" --parameters "{\"commands\":[\"echo $encodedContent | base64 -d > /tmp/update.sh\",\"chmod +x /tmp/update.sh\",\"/tmp/update.sh\",\"rm /tmp/update.sh\"]}" 