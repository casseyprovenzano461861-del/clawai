@echo off
cd /d "e:\ClawAI"

set DEBUG=True
set API_AUTH_ENABLED=false
set SECRET_KEY=clawai_secret_key_2024_change_this_in_production
set API_SECRET_KEY=clawai_api_secret_key_2024_change_this_in_production
set JWT_SECRET=clawai_jwt_secret_key_2024_change_this_in_production
set SESSION_SECRET=clawai_session_secret_key_2024_change_this_in_production
set DEFAULT_ADMIN_USERNAME=admin
set DEFAULT_ADMIN_PASSWORD=admin123
set NMAP_PATH=nmap
set WHATWEB_PATH=whatweb
set NUCLEI_PATH=nuclei
set API_VERSION=v1

echo Starting ClawAI New Architecture API Server...
python run_new_api.py