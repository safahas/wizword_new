#!/bin/bash
set -e

# Clean up existing files
cd /home/ec2-user
rm -rf cursor-ai-agent

# Clone repository
git clone https://github.com/CICD-Student/cursor-ai-agent.git
cd cursor-ai-agent/game_guess

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Get API key and create .env file
OPENROUTER_API_KEY=$(aws ssm get-parameter --name "/word-guess/openrouter-api-key" --with-decryption --query "Parameter.Value" --output text)
echo "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" > .env

# Start application
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 