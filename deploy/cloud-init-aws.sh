#!/bin/bash
set -euo pipefail

exec > >(tee /var/log/api-tarefas-install.log) 2>&1
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y python3-venv python3-pip nginx git openssl

id api-tarefas >/dev/null 2>&1 || \
  useradd --system --home /opt/api-tarefas --shell /usr/sbin/nologin api-tarefas

rm -rf /opt/api-tarefas
git clone --depth 1 https://github.com/DaviSuedt/api-gerenciamento-tarefas.git /opt/api-tarefas
python3 -m venv /opt/api-tarefas/.venv
/opt/api-tarefas/.venv/bin/pip install --no-cache-dir -r /opt/api-tarefas/requirements.txt

install -d -o api-tarefas -g api-tarefas -m 750 /opt/api-tarefas/data
chown -R api-tarefas:api-tarefas /opt/api-tarefas

API_KEY="$(openssl rand -hex 24)"
printf 'API_KEY=%s\nDATABASE_PATH=/opt/api-tarefas/data/tarefas.db\n' "$API_KEY" \
  > /etc/api-tarefas.env
chown root:api-tarefas /etc/api-tarefas.env
chmod 640 /etc/api-tarefas.env

printf '%s\n' "$API_KEY" > /home/ubuntu/api-key.txt
chown ubuntu:ubuntu /home/ubuntu/api-key.txt
chmod 600 /home/ubuntu/api-key.txt

cp /opt/api-tarefas/deploy/api-tarefas.service /etc/systemd/system/api-tarefas.service
cp /opt/api-tarefas/deploy/nginx.conf /etc/nginx/sites-available/default

nginx -t
systemctl daemon-reload
systemctl enable --now api-tarefas
systemctl enable --now nginx

curl --fail --retry 10 --retry-delay 3 http://127.0.0.1/health

