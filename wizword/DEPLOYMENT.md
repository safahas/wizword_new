# Word Guess Game - ECS Deployment Guide

This guide explains how to deploy the Word Guess Game to Amazon ECS using Fargate.

## Prerequisites

1. AWS CLI installed and configured
2. Docker installed locally
3. Access to an AWS account with necessary permissions
4. Required environment variables:
   - `OPENROUTER_API_KEY`
   - `ADMIN_EMAIL`
   - `SMTP_USER`
   - `SMTP_PASS`

## Local Development

1. Build and run locally using Docker Compose:
   ```bash
   # Create .env file with required variables
   cp .env.example .env
   # Edit .env with your values
   
   # Build and run
   docker-compose up --build
   ```

2. Access the application at http://localhost:8501

## AWS Setup

### 1. Create Required IAM Roles

1. ECS Task Execution Role:
   ```bash
   aws iam create-role \
     --role-name ecsTaskExecutionRole \
     --assume-role-policy-document file://iam/task-execution-assume-role.json

   aws iam attach-role-policy \
     --role-name ecsTaskExecutionRole \
     --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
   ```

2. Task Role for application permissions:
   ```bash
   aws iam create-role \
     --role-name word-guess-game-task-role \
     --assume-role-policy-document file://iam/task-assume-role.json

   # Attach required policies (SSM, CloudWatch, etc.)
   aws iam attach-role-policy \
     --role-name word-guess-game-task-role \
     --policy-arn arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess

   aws iam attach-role-policy \
     --role-name word-guess-game-task-role \
     --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
   ```

### 2. Store Secrets in AWS Systems Manager Parameter Store

```bash
# Store secrets (use SecureString for sensitive data)
aws ssm put-parameter \
  --name "/word-guess-game/openrouter-api-key" \
  --value "your-api-key" \
  --type SecureString

aws ssm put-parameter \
  --name "/word-guess-game/admin-email" \
  --value "admin@example.com" \
  --type SecureString

aws ssm put-parameter \
  --name "/word-guess-game/smtp-user" \
  --value "smtp-user" \
  --type SecureString

aws ssm put-parameter \
  --name "/word-guess-game/smtp-pass" \
  --value "smtp-password" \
  --type SecureString
```

### 3. Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name word-guess-game \
  --image-scanning-configuration scanOnPush=true
```

### 4. Build and Push Docker Image

```bash
# Get ECR login token
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build image
docker build -t word-guess-game .

# Tag image
docker tag word-guess-game:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/word-guess-game:latest

# Push to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/word-guess-game:latest
```

### 5. Create ECS Cluster

```bash
aws ecs create-cluster \
  --cluster-name word-guess-game-cluster \
  --capacity-providers FARGATE
```

### 6. Create Task Definition

1. Replace placeholders in task-definition.json:
   ```bash
   # Set environment variables
   export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
   export AWS_REGION=$(aws configure get region)
   export ECR_REPOSITORY_URI=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/word-guess-game

   # Replace placeholders
   envsubst < task-definition.json > task-definition-resolved.json
   ```

2. Register task definition:
   ```bash
   aws ecs register-task-definition \
     --cli-input-json file://task-definition-resolved.json
   ```

### 7. Create Application Load Balancer

1. Create ALB:
   ```bash
   aws elbv2 create-load-balancer \
     --name word-guess-game-alb \
     --subnets subnet-xxxxx subnet-yyyyy \
     --security-groups sg-zzzzz
   ```

2. Create target group:
   ```bash
   aws elbv2 create-target-group \
     --name word-guess-game-tg \
     --protocol HTTP \
     --port 8501 \
     --vpc-id vpc-xxxxx \
     --target-type ip \
     --health-check-path /_stcore/health
   ```

3. Create listener:
   ```bash
   aws elbv2 create-listener \
     --load-balancer-arn ${ALB_ARN} \
     --protocol HTTP \
     --port 80 \
     --default-actions Type=forward,TargetGroupArn=${TARGET_GROUP_ARN}
   ```

### 8. Create ECS Service

```bash
aws ecs create-service \
  --cluster word-guess-game-cluster \
  --service-name word-guess-game-service \
  --task-definition word-guess-game:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[sg-zzzzz],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=${TARGET_GROUP_ARN},containerName=word-guess-game,containerPort=8501"
```

## Monitoring and Maintenance

### CloudWatch Logs

Access application logs:
```bash
aws logs get-log-events \
  --log-group-name /ecs/word-guess-game \
  --log-stream-name ecs/word-guess-game/{TASK_ID}
```

### Updating the Application

1. Build and push new image version
2. Update ECS service:
   ```bash
   aws ecs update-service \
     --cluster word-guess-game-cluster \
     --service word-guess-game-service \
     --force-new-deployment
   ```

### Scaling

Adjust desired count for manual scaling:
```bash
aws ecs update-service \
  --cluster word-guess-game-cluster \
  --service word-guess-game-service \
  --desired-count 3
```

## Cleanup

To remove all resources:
```bash
# Delete ECS service
aws ecs update-service \
  --cluster word-guess-game-cluster \
  --service word-guess-game-service \
  --desired-count 0

aws ecs delete-service \
  --cluster word-guess-game-cluster \
  --service word-guess-game-service

# Delete cluster
aws ecs delete-cluster \
  --cluster word-guess-game-cluster

# Delete ALB and target group
aws elbv2 delete-load-balancer \
  --load-balancer-arn ${ALB_ARN}

aws elbv2 delete-target-group \
  --target-group-arn ${TARGET_GROUP_ARN}

# Delete ECR repository
aws ecr delete-repository \
  --repository-name word-guess-game \
  --force

# Delete SSM parameters
aws ssm delete-parameters \
  --names \
    "/word-guess-game/openrouter-api-key" \
    "/word-guess-game/admin-email" \
    "/word-guess-game/smtp-user" \
    "/word-guess-game/smtp-pass"

# Delete IAM roles (remove attached policies first)
aws iam delete-role --role-name word-guess-game-task-role
``` 