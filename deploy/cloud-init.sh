#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3-venv python3-pip nginx git openssl

id api-tarefas >/dev/null 2>&1 || useradd --system --home /opt/api-tarefas --shell /usr/sbin/nologin api-tarefas
rm -rf /opt/api-tarefas
git clone https://github.com/DaviSuedt/api-gerenciamento-tarefas.git /opt/api-tarefas
python3 -m venv /opt/api-tarefas/.venv
/opt/api-tarefas/.venv/bin/pip install --no-cache-dir -r /opt/api-tarefas/requirements.txt

mkdir -p /opt/api-tarefas/data
chown -R api-tarefas:api-tarefas /opt/api-tarefas

API_KEY="$(openssl rand -hex 24)"
printf 'API_KEY=%s\nDATABASE_PATH=/opt/api-tarefas/data/tarefas.db\n' "$API_KEY" > /etc/api-tarefas.env
chown root:api-tarefas /etc/api-tarefas.env
chmod 640 /etc/api-tarefas.env
printf '%s\n' "$API_KEY" > /home/azureuser/api-key.txt
chown azureuser:azureuser /home/azureuser/api-key.txt
chmod 600 /home/azureuser/api-key.txt

cp /opt/api-tarefas/deploy/api-tarefas.service /etc/systemd/system/api-tarefas.service
cp /opt/api-tarefas/deploy/nginx.conf /etc/nginx/sites-available/default
nginx -t
systemctl daemon-reload
systemctl enable --now api-tarefas
systemctl enable --now nginx
