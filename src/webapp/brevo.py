"""
Synchronisation des clients vers Brevo (e-mailing et SMS marketing).

Tous les clients qui ont un e-mail sont envoyés dans une liste Brevo, avec des
attributs qui servent à faire des segments dans Brevo (clients récents, fidèles…) :

    PRENOM / NOM          FIRSTNAME, LASTNAME (attributs standard de Brevo)
    SMS                   portable au format +33…, seulement si le client accepte les SMS
    ORDERNEST_ID          identifiant du client dans OrderNest
    NB_COMMANDES          nombre de commandes (hors devis et annulées)
    DERNIERE_COMMANDE     date de la dernière commande
    PREMIERE_COMMANDE     date de la première commande
    TOTAL_DEPENSE         total des commandes, en euros
    CLIENT_FIDELE         au moins deux commandes

Consentement : un client qui refuse les e-mails (case décochée, ou client désactivé)
est marqué « désinscrit » dans Brevo. L'inverse n'est jamais fait : un client qui
s'est désinscrit depuis un lien Brevo n'est pas réinscrit par la synchronisation.

Réglages (variables d'environnement) :
    BREVO_API_KEY     clé d'API Brevo (Paramètres > SMTP & API > Clés API)
    BREVO_LIST_NAME   nom de la liste (par défaut « OrderNest – clients »)
"""
import logging

import environ
import requests
from django.db.models import Q, Sum

from .models import Customer
from .variables import BREVO_TEXT_ATTRIBUTES, VARIABLES, values_of, with_variables

logger = logging.getLogger(__name__)
env = environ.Env()

API = "https://api.brevo.com/v3"
DEFAULT_LIST_NAME = "OrderNest – clients"
BATCH_SIZE = 500
TIMEOUT = 30

ATTRIBUTES = {
    "ORDERNEST_ID": "float",
    "NB_COMMANDES": "float",
    "DERNIERE_COMMANDE": "date",
    "PREMIERE_COMMANDE": "date",
    "TOTAL_DEPENSE": "float",
    "CLIENT_FIDELE": "boolean",
    # Variables des campagnes (texte prêt à afficher : « mars 2025 », « Aquarelle de Venise »…)
    **{name: "text" for name in BREVO_TEXT_ATTRIBUTES},
}

# Commandes qui comptent : ni les devis, ni les commandes annulées.
COUNTED = ~Q(order__status__in=["Devis", "Annulée"])


class BrevoError(Exception):
    pass


def api_key():
    return env("BREVO_API_KEY", default="")


def is_configured():
    return bool(api_key())


class BrevoClient:
    def __init__(self, key=None, session=None):
        self.key = key or api_key()
        if not self.key:
            raise BrevoError("Clé d'API Brevo absente (variable BREVO_API_KEY).")
        self.http = session or requests.Session()

    def request(self, method, path, **kwargs):
        response = self.http.request(
            method, API + path, timeout=TIMEOUT,
            headers={"api-key": self.key, "accept": "application/json", "content-type": "application/json"},
            **kwargs,
        )
        if response.status_code >= 400:
            try:
                message = response.json().get("message", response.text)
            except ValueError:
                message = response.text
            raise BrevoError(f"Brevo {method} {path} : {response.status_code} {message}")
        return response.json() if response.content else {}

    # --- Liste et attributs : créés au premier passage, retrouvés ensuite ---------------

    def ensure_list(self, name):
        offset = 0
        while True:
            page = self.request("GET", f"/contacts/lists?limit=50&offset={offset}")
            for item in page.get("lists", []):
                if item["name"] == name:
                    return item["id"]
            if len(page.get("lists", [])) < 50:
                break
            offset += 50
        folders = self.request("GET", "/contacts/folders?limit=50&offset=0").get("folders", [])
        folder = next((f["id"] for f in folders if f["name"] == "OrderNest"), None)
        if folder is None:
            folder = self.request("POST", "/contacts/folders", json={"name": "OrderNest"})["id"]
        return self.request("POST", "/contacts/lists", json={"name": name, "folderId": folder})["id"]

    def ensure_attributes(self):
        existing = {
            a["name"] for a in self.request("GET", "/contacts/attributes").get("attributes", [])
        }
        for name, kind in ATTRIBUTES.items():
            if name not in existing:
                self.request("POST", f"/contacts/attributes/normal/{name}", json={"type": kind})

    def import_contacts(self, list_id, contacts):
        """Import asynchrone côté Brevo : renvoie l'identifiant du traitement."""
        return self.request("POST", "/contacts/import", json={
            "jsonBody": contacts,
            "listIds": [list_id],
            "updateExistingContacts": True,
            "emptyContactsAttributes": False,
        }).get("processId")


def contact_payload(customer):
    """Un client OrderNest au format d'import Brevo."""
    attributes = {
        "FIRSTNAME": customer.first_name or "",
        "LASTNAME": customer.last_name or "",
        "ORDERNEST_ID": customer.pk,
        "NB_COMMANDES": customer.nb_orders or 0,
        "TOTAL_DEPENSE": round(float(customer.total_spent or 0), 2),
        "CLIENT_FIDELE": (customer.nb_orders or 0) >= 2,
    }
    if customer.last_order:
        attributes["DERNIERE_COMMANDE"] = customer.last_order.date().isoformat()
    if customer.first_order:
        attributes["PREMIERE_COMMANDE"] = customer.first_order.date().isoformat()
    values = values_of(customer)
    for key, var in VARIABLES.items():
        if var["brevo"] in BREVO_TEXT_ATTRIBUTES:
            attributes[var["brevo"]] = values[key]
    phone = str(customer.phone_number or "")
    if customer.marketing_sms and phone.startswith("+"):
        attributes["SMS"] = phone

    contact = {"email": customer.mail.strip().lower(), "attributes": attributes}
    if not customer.marketing_email or not customer.active:
        contact["emailBlacklisted"] = True
    if not customer.marketing_sms or not customer.active:
        contact["smsBlacklisted"] = True
    return contact


def customers_to_sync():
    return (
        with_variables(Customer.objects.exclude(mail=""))
        .annotate(total_spent=Sum("order__products__selling_price_unit", filter=COUNTED))
        .order_by("pk")
    )


def sync_customers(client=None, list_name=None):
    """Envoie les clients vers Brevo. Renvoie un résumé (dict)."""
    client = client or BrevoClient()
    list_name = list_name or env("BREVO_LIST_NAME", default=DEFAULT_LIST_NAME)
    list_id = client.ensure_list(list_name)
    client.ensure_attributes()

    contacts, seen = [], set()
    for customer in customers_to_sync():
        payload = contact_payload(customer)
        if payload["email"] in seen or "@" not in payload["email"]:
            continue  # doublon d'adresse ou adresse invalide : Brevo refuserait le lot
        seen.add(payload["email"])
        contacts.append(payload)

    processes = []
    for start in range(0, len(contacts), BATCH_SIZE):
        processes.append(client.import_contacts(list_id, contacts[start:start + BATCH_SIZE]))

    summary = {
        "list": list_name,
        "list_id": list_id,
        "contacts": len(contacts),
        "unsubscribed": sum(1 for c in contacts if c.get("emailBlacklisted")),
        "with_sms": sum(1 for c in contacts if "SMS" in c["attributes"]),
        "processes": processes,
    }
    logger.info("Synchronisation Brevo : %s", summary)
    return summary


def run_sync(trigger="manuel", client=None):
    """Lance la synchronisation et en garde la trace (BrevoSync), succès ou échec."""
    from .models import BrevoSync

    try:
        summary = sync_customers(client=client)
    except (BrevoError, requests.RequestException) as error:
        logger.warning("Synchronisation Brevo en échec : %s", error)
        return BrevoSync.objects.create(success=False, trigger=trigger, message=str(error)[:500])
    return BrevoSync.objects.create(
        success=True,
        trigger=trigger,
        contacts=summary["contacts"],
        unsubscribed=summary["unsubscribed"],
        message=f"Liste « {summary['list']} », {summary['with_sms']} avec un portable pour les SMS.",
    )
