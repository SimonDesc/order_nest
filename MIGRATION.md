# Migration PythonAnywhere → VPS Hostinger (Coolify)

But : `app.galerielibrecours.fr` servi par Coolify sur le VPS (92.113.26.165), déployé
automatiquement à chaque push sur `main`, base PostgreSQL. Les photos restent sur S3.

L'app PythonAnywhere continue de tourner jusqu'à l'étape 5 : aucune coupure avant la bascule DNS.

## 1. Coolify : la base PostgreSQL

1. Projet → **+ New** → **Database** → **PostgreSQL** (version 16).
2. Nom : `order-nest-db`. Démarrer.
3. Noter dans l'onglet de la base : *Postgres User*, *Password*, *Database*, et l'URL
   **interne** (hôte du type `xxxxxxxx` sur le port 5432). Ne pas l'exposer publiquement.

## 2. Coolify : l'application

1. **+ New** → **Application** → dépôt GitHub `SimonDesc/order_nest`, branche `main`.
2. **Build Pack : Dockerfile**. Port exposé : `8000`.
3. Domaine provisoire pour tester, par ex. `https://order-nest-test.galerielibrecours.fr`
   (ajouter d'abord chez Hostinger un enregistrement A `order-nest-test` → 92.113.26.165),
   ou le domaine `sslip.io` proposé par Coolify.
4. Variables d'environnement (reprendre les valeurs du `.env` PythonAnywhere) :

   | Variable | Valeur |
   |---|---|
   | `SECRET_KEY` | celle de PythonAnywhere |
   | `DEBUG` | `False` |
   | `CSRF_TRUSTED_ORIGINS` | `https://app.galerielibrecours.fr,https://<domaine-de-test>` |
   | `DB_ENGINE` | `django.db.backends.postgresql` |
   | `DB_NAME` / `DB_USER` / `DB_PASSWORD` | ceux de l'étape 1 |
   | `DB_HOST` | hôte interne de l'étape 1 |
   | `DB_PORT` | `5432` |
   | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME` | ceux de PythonAnywhere |
   | `SMS_API`, `WEB_HOOK` | ceux de PythonAnywhere |

5. **Deploy**. Au démarrage, le conteneur applique les migrations (base vide) et
   `collectstatic`. Le domaine de test doit afficher la page de connexion
   (il n'y a pas encore de compte : c'est normal).

## 3. Exporter les données depuis PythonAnywhere

Dans une console Bash PythonAnywhere, dans le dossier `src` du projet, avec le virtualenv actif :

```bash
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission -e admin.logentry -e sessions \
  --indent 2 -o dump.json
```

Puis onglet **Files** → télécharger `dump.json`.
Ce fichier contient les clients et leurs numéros : ne pas le commiter, le supprimer après.

## 4. Importer sur le VPS

Depuis ton PC :

```bash
scp dump.json root@92.113.26.165:/root/dump.json
```

Puis sur le VPS (SSH, ou terminal Coolify du serveur) :

```bash
docker ps --format '{{.Names}}' | grep -i order    # nom du conteneur de l'app
docker cp /root/dump.json <conteneur>:/tmp/dump.json
docker exec <conteneur> python manage.py loaddata /tmp/dump.json
rm /root/dump.json
```

Vérifier sur le domaine de test : connexion avec le compte habituel, commandes, clients,
photos (elles viennent de S3), impression d'un ticket, envoi d'un SMS de test.

## 5. Bascule

1. Refaire l'export / import (étapes 3 et 4) juste avant la bascule pour avoir les dernières
   commandes : vider d'abord la base Coolify (`docker exec <conteneur> python manage.py flush --noinput`).
2. Coolify : ajouter le domaine `https://app.galerielibrecours.fr` à l'application.
3. Hostinger → DNS : remplacer le CNAME `app` (→ `webapp-1927665.pythonanywhere.com`)
   par un enregistrement **A** `app` → `92.113.26.165`.
4. Attendre que Let's Encrypt délivre le certificat (quelques minutes), tester.
5. Garder PythonAnywhere quelques jours, puis résilier.

## Déploiements suivants

Un push sur `main` suffit : Coolify reconstruit l'image et applique les migrations au démarrage.

## En local (Docker)

```bash
docker build -t order-nest .
docker run --rm -p 8000:8000 --env-file src/order_nest/.env order-nest
```
