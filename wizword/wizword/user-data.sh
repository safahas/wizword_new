#!/bin/bash
set -ex

# Update system
yum update -y
yum install -y python3-pip git

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
yum install -y unzip
unzip awscliv2.zip
./aws/install

# Clone repository
cd /home/ec2-user
git clone https://github.com/CICD-Student/cursor-ai-agent.git
cd cursor-ai-agent/game_guess

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Get API key
OPENROUTER_API_KEY=$(aws ssm get-parameter --name "/word-guess/openrouter-api-key" --with-decryption --query "Parameter.Value" --output text)
echo "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" > .env

# Start application
nohup streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &

# Print logs for debugging
sleep 10
cat streamlit.log 