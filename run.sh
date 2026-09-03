#!/bin/sh
# starts the project with correct host file-ownership on Linux/macOS.
set -e

HOST_UID=$(id -u)
HOST_GID=$(id -g)

env UID="$HOST_UID" GID="$HOST_GID" docker compose up -d --build

echo ""
echo "Containers starting. Tail logs with: docker compose logs -f api"