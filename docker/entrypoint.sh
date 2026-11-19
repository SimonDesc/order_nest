#!/bin/sh
# Au démarrage du conteneur : migrations, fichiers statiques, puis gunicorn.
# (collectstatic ici et pas au build : settings.py exige les variables AWS_*.)
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput --verbosity 0

exec "$@"
