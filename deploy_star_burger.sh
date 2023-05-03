#!/bin/bash

set -e

git pull

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
