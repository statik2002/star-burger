#!/bin/bash

set -e

git stash
git pull

git rev-parse HEAD

curl -H "X-Rollbar-Access-Token: 133ebaa4f3a34cebb5030d9b7e84a169" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "dev", "revision": "dc1f74dee5", "rollbar_name": "statik2002", "local_username": "statik2002", "comment": "Tuesday deployment", "status": "succeeded"}'

source env/bin/activate

pip install -r requirements.txt

sudo apt update

sudo apt install nodejs

npm ci --dev

./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

python manage.py collectstatic --noinput

python manage.py migrate

sudo systemctl restart unit

echo "All done!"
