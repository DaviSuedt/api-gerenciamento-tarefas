#!/bin/bash
set -euo pipefail

curl --fail --silent --show-error --location \
  https://raw.githubusercontent.com/DaviSuedt/api-gerenciamento-tarefas/main/deploy/cloud-init-aws.sh \
  | bash
