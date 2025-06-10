#!/bin/bash
set -e

# Install nginx
sudo yum install -y nginx

# Create nginx configuration
sudo tee /etc/nginx/conf.d/streamlit.conf << 'EOL'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOL

# Start nginx
sudo systemctl start nginx

# Start Streamlit
cd /home/ec2-user/cursor-ai-agent/game_guess
source venv/bin/activate
nohup streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 & 