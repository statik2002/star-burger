#!/bin/bash

set -e

COMMIT_HASH=`git rev-parse HEAD`

mkdir -p "frontend_deploy"

cp -f package.json frontend_deploy/package.json
cp -f package-lock.json frontend_deploy/package-lock.json
cp -r bundles-src frontend_deploy/bundles-src

docker compose build
docker compose up -d

docker compose stop web-static
docker compose rm --force web-static
docker compose stop parcel
docker compose rm --force parcel

docker compose exec -it web sh -c "python manage.py collectstatic --noinput"
docker compose exec -it web sh -c "python manage.py migrate"

#sudo systemctl restart unit

#curl -H "X-Rollbar-Access-Token: 133ebaa4f3a34cebb5030d9b7e84a169" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "development", "revision": "'$COMMIT_HASH'", "rollbar_name": "statik2002", "local_username": "'$USER'", "comment": "intermediate deployment", "status": "succeeded"}'

echo "All done!"
