"""python manage.py sync_brevo : envoie les clients vers Brevo (à planifier chaque nuit)."""
from django.core.management.base import BaseCommand, CommandError

from webapp.brevo import is_configured, run_sync


class Command(BaseCommand):
    help = "Synchronise les clients (e-mail, consentement, historique d'achat) vers Brevo."

    def handle(self, *args, **options):
        if not is_configured():
            raise CommandError("BREVO_API_KEY n'est pas définie : synchronisation impossible.")
        sync = run_sync(trigger="automatique")
        if not sync.success:
            raise CommandError(f"Échec : {sync.message}")
        self.stdout.write(self.style.SUCCESS(
            f"{sync.contacts} contacts envoyés à Brevo ({sync.unsubscribed} désinscrits). {sync.message}"
        ))
