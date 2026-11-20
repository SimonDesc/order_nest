"""
Campagnes d'information : un message envoyé à un groupe de clients.

- E-mail : la campagne est créée dans Brevo (expéditeur contact@…), avec une liste
  Brevo propre à la campagne, puis envoyée tout de suite ou programmée.
- SMS : envoi groupé par SMSPartner (le même compte que les SMS de commande), avec
  la mention STOP obligatoire pour un SMS commercial.

Seuls les clients actifs qui acceptent le canal (case cochée sur la fiche client)
font partie d'un public. Dans le message, {prenom} et {nom} sont remplacés par ceux du client.
"""
import re
import time
from datetime import timedelta

import environ
import requests
from django.db.models import Count, Q, Sum
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import escape

from . import brevo
from .models import Customer
from .variables import SAMPLE, VARIABLES, values_of, with_variables

env = environ.Env()

# Variables du message ({prenom}, {derniere_commande}…) : voir variables.py.
# Pour un e-mail, elles deviennent des attributs Brevo ; pour un SMS, elles sont remplacées ici.
VARIABLE_RE = re.compile(r"([ \t]?)\{(\w+)\}")
SMS_API = "https://api.smspartner.fr/v1"
SMS_SENDER = "LibreCours"
SMS_BATCH = 500
# Les SMS commerciaux : du lundi au samedi, de 8 h à 20 h (hors jours fériés).
SMS_HOURS = (8, 20)

COUNTED = brevo.COUNTED
QUOTES = Q(order__status__in=["Devis", "Annulée"])

AUDIENCES = [
    ("tous", "Tous les clients", "Tous ceux qui acceptent ce canal"),
    ("fideles", "Clients fidèles", "Au moins 2 commandes"),
    ("recents", "Clients de l'année", "Une commande ces 12 derniers mois"),
    ("inactifs", "À reconquérir", "Dernière commande il y a plus d'un an"),
    ("une_fois", "Venus une seule fois", "Une seule commande"),
    ("devis", "Devis sans suite", "Un devis, mais jamais de commande"),
]
AUDIENCE_LABELS = {key: label for key, label, _ in AUDIENCES}


class CampaignError(Exception):
    pass


# --- Publics ------------------------------------------------------------------------

def _customers():
    return with_variables(Customer.objects.filter(active=True)).annotate(
        nb_quotes=Count("order", filter=QUOTES, distinct=True),
        total_spent=Sum("order__products__selling_price_unit", filter=COUNTED),
    )


def _in_audience(customer, key, year_ago):
    n = customer.nb_orders or 0
    if key == "tous":
        return True
    if key == "fideles":
        return n >= 2
    if key == "recents":
        return bool(customer.last_order and customer.last_order >= year_ago)
    if key == "inactifs":
        return bool(customer.last_order and customer.last_order < year_ago)
    if key == "une_fois":
        return n == 1
    if key == "devis":
        return n == 0 and (customer.nb_quotes or 0) > 0
    raise CampaignError(f"Public inconnu : {key}")


def email_of(customer):
    mail = (customer.mail or "").strip().lower()
    return mail if "@" in mail else ""


def mobile_of(customer):
    """Portable français au format +336… / +337…, sinon chaîne vide."""
    phone = str(customer.phone_number or "")
    return phone if re.fullmatch(r"\+33[67]\d{8}", phone) else ""


def _reachable(customer, channel):
    if channel == "email":
        return customer.marketing_email and email_of(customer)
    return customer.marketing_sms and mobile_of(customer)


def audience(key, channel, exclude=()):
    """Clients d'un public joignables sur un canal, sans doublon d'adresse ou de numéro.
    exclude : identifiants des clients retirés à la main de la liste."""
    year_ago = timezone.now() - timedelta(days=365)
    exclude = {int(pk) for pk in exclude}
    result, seen = [], set()
    for customer in _customers().order_by("pk"):
        contact = _reachable(customer, channel)
        if not contact or contact in seen or not _in_audience(customer, key, year_ago):
            continue
        if customer.pk in exclude:
            seen.add(contact)
            continue
        seen.add(contact)
        result.append(customer)
    return result


def audience_counts():
    """{public: {"email": n, "sms": n}} pour afficher la taille de chaque public."""
    year_ago = timezone.now() - timedelta(days=365)
    counts = {key: {"email": 0, "sms": 0} for key, _, _ in AUDIENCES}
    seen = {"email": set(), "sms": set()}
    for customer in _customers().order_by("pk"):
        for channel in ("email", "sms"):
            contact = _reachable(customer, channel)
            if not contact or contact in seen[channel]:
                continue
            seen[channel].add(contact)
            for key in counts:
                if _in_audience(customer, key, year_ago):
                    counts[key][channel] += 1
    return counts


# --- Messages -----------------------------------------------------------------------

def unknown_variables(*texts):
    """Les {mots} qui ne sont pas des variables connues (faute de frappe, ex. {prénom})."""
    found = []
    for text in texts:
        for match in re.finditer(r"\{([^{}\s]{1,30})\}", text or ""):
            if match.group(1) not in VARIABLES and match.group(0) not in found:
                found.append(match.group(0))
    return found


def unfilled(*texts):
    """Les passages [à compléter] d'un modèle qui n'ont pas été remplacés."""
    found = []
    for text in texts:
        for match in re.finditer(r"\[[^\[\]\n]{2,80}\]", text or ""):
            if match.group(0) not in found:
                found.append(match.group(0))
    return found


def personalize(text, values):
    """« Bonjour {prenom}, » → « Bonjour Camille, », ou « Bonjour, » si le prénom est inconnu."""
    def replace(match):
        key = match.group(2)
        if key not in VARIABLES:
            return match.group(0)
        value = str(values.get(key) or "").strip()
        return match.group(1) + value if value else ""
    return VARIABLE_RE.sub(replace, text or "")


def brevo_tags(text):
    """Pour un e-mail : {prenom} → balise Brevo, qui disparaît (espace compris) si le champ est vide."""
    def replace(match):
        key = match.group(2)
        if key not in VARIABLES:
            return match.group(0)
        attr = VARIABLES[key]["brevo"]
        return f"{{% if contact.{attr} %}}{match.group(1)}{{{{ contact.{attr} }}}}{{% endif %}}"
    return VARIABLE_RE.sub(replace, text or "")


GREETING = re.compile(r"^\s*(bonjour|bonsoir|cher|chère|chers|hello|salut)\b", re.IGNORECASE)


def preheader_of(campaign):
    """Le texte d'aperçu affiché après l'objet dans la boîte de réception.
    S'il n'est pas rempli : le début du message, sans la formule « Bonjour {prenom}, »."""
    if campaign.preheader.strip():
        return campaign.preheader.strip()
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", campaign.message or "") if p.strip()]
    if paragraphs and GREETING.match(paragraphs[0]) and len(paragraphs[0]) < 40:
        paragraphs = paragraphs[1:]
    text = re.sub(r"\s+", " ", " ".join(paragraphs))
    return text if len(text) <= 140 else text[:140].rsplit(" ", 1)[0] + "…"


def email_html(campaign, sample=False):
    """Le corps HTML de l'e-mail : balises Brevo, ou valeurs d'exemple pour l'aperçu."""
    fill = (lambda text: personalize(text, SAMPLE)) if sample else brevo_tags
    paragraphs = [
        fill(escape(p)).replace("\n", "<br>")
        for p in re.split(r"\n\s*\n", campaign.message.strip()) if p.strip()
    ]
    return render_to_string("webapp/campagnes/email.html", {
        "campaign": campaign,
        "preheader": fill(escape(preheader_of(campaign))),
        "paragraphs": paragraphs,
        "sender_name": sender()["name"],
    })


def sender():
    return {
        "name": env("BREVO_SENDER_NAME", default="Galerie Libre Cours"),
        "email": env("BREVO_SENDER_EMAIL", default="contact@galerielibrecours.fr"),
    }


def sms_window_open(now=None):
    now = timezone.localtime(now or timezone.now())
    return now.weekday() < 6 and SMS_HOURS[0] <= now.hour < SMS_HOURS[1]


# --- E-mail : Brevo -----------------------------------------------------------------

def _email_payload(campaign):
    return {
        "name": f"OrderNest · {campaign.name}",
        "subject": brevo_tags(campaign.subject),
        "previewText": brevo_tags(preheader_of(campaign)),
        "sender": sender(),
        "htmlContent": email_html(campaign),
        "inlineImageActivation": False,
    }


def save_email_draft(campaign, client=None):
    """Crée ou met à jour la campagne dans Brevo (sans destinataires)."""
    client = client or brevo.BrevoClient()
    payload = _email_payload(campaign)
    if campaign.brevo_id:
        client.request("PUT", f"/emailCampaigns/{campaign.brevo_id}", json=payload)
    else:
        campaign.brevo_id = client.request("POST", "/emailCampaigns", json=payload)["id"]
        campaign.save(update_fields=["brevo_id"])
    return client


def send_email_test(campaign, emails, client=None):
    client = save_email_draft(campaign, client)
    client.request("POST", f"/emailCampaigns/{campaign.brevo_id}/sendTest", json={"emailTo": emails})


def _wait_for_import(client, process_id, timeout=45):
    deadline = time.monotonic() + timeout
    while process_id and time.monotonic() < deadline:
        status = client.request("GET", f"/processes/{process_id}").get("status")
        if status == "completed":
            return
        time.sleep(1.5)
    raise CampaignError("Brevo n'a pas fini d'importer les destinataires : réessayer dans une minute.")


def send_email(campaign, scheduled_at=None, client=None, wait=_wait_for_import):
    """Envoie (ou programme) la campagne e-mail à son public."""
    customers = audience(campaign.audience, "email", campaign.excluded)
    if not customers:
        raise CampaignError("Aucun client dans ce public.")
    client = save_email_draft(campaign, client)

    # Une liste Brevo par campagne : on sait exactement qui l'a reçue.
    list_name = f"Campagne {campaign.pk} · {campaign.name}"[:100]
    list_id = client.ensure_list(list_name)
    client.ensure_attributes()
    contacts = [brevo.contact_payload(c) for c in brevo.customers_to_sync().filter(pk__in=[c.pk for c in customers])]
    for start in range(0, len(contacts), brevo.BATCH_SIZE):
        wait(client, client.import_contacts(list_id, contacts[start:start + brevo.BATCH_SIZE]))

    payload = {"recipients": {"listIds": [list_id]}}
    if scheduled_at:
        payload["scheduledAt"] = scheduled_at.isoformat()
    client.request("PUT", f"/emailCampaigns/{campaign.brevo_id}", json=payload)
    if not scheduled_at:
        client.request("POST", f"/emailCampaigns/{campaign.brevo_id}/sendNow")

    campaign.recipients = len(contacts)
    campaign.status = "programmee" if scheduled_at else "envoyee"
    campaign.scheduled_at = scheduled_at
    campaign.sent_at = None if scheduled_at else timezone.now()
    campaign.error = ""
    campaign.save()
    return campaign


def email_stats(campaign, client=None):
    """Ouvertures, clics… d'une campagne envoyée (statistiques Brevo)."""
    client = client or brevo.BrevoClient()
    data = client.request("GET", f"/emailCampaigns/{campaign.brevo_id}?statistics=globalStats")
    stats = (data.get("statistics") or {}).get("globalStats") or {}
    delivered = stats.get("delivered") or 0
    opens = stats.get("uniqueViews") or 0
    clicks = stats.get("uniqueClicks") or 0
    return {
        "status": data.get("status"),
        "delivered": delivered,
        "opens": opens,
        "clicks": clicks,
        "unsubscribed": stats.get("unsubscriptions") or 0,
        "open_rate": round(100 * opens / delivered) if delivered else None,
        "click_rate": round(100 * clicks / delivered) if delivered else None,
    }


def email_credits(client=None):
    """E-mails restants sur l'offre Brevo (300 par jour sur l'offre gratuite)."""
    client = client or brevo.BrevoClient()
    for plan in client.request("GET", "/account").get("plan", []):
        if plan.get("creditsType") == "sendLimit":
            return {"credits": plan.get("credits"), "plan": plan.get("type")}
    return None


# --- SMS : SMSPartner ---------------------------------------------------------------

def _sms_post(path, payload, session=None):
    key = env("SMS_API", default="")
    if not key:
        raise CampaignError("Clé SMSPartner absente (variable SMS_API).")
    http = session or requests
    response = http.post(SMS_API + path, json={"apiKey": key, **payload}, timeout=30)
    try:
        data = response.json()
    except ValueError:
        raise CampaignError(f"SMSPartner : réponse illisible ({response.status_code}).")
    if not data.get("success"):
        raise CampaignError(f"SMSPartner : {data.get('message') or data.get('errors') or data}")
    return data


def send_sms_test(campaign, phone, session=None):
    _sms_post("/send", {
        "phoneNumbers": phone,
        "message": personalize(campaign.message, SAMPLE),
        "sender": SMS_SENDER,
        "gamme": 1,
        "isStopSms": 1,
    }, session)


GSM = set("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZ"
          "ÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà")
GSM_EXT = set("^{}\\[~]|€")
STOP_MENTION = " STOP au 36180"
MAX_SMS_PARTS = 2  # au-delà, le client reçoit une rafale de SMS : envoi refusé


def sms_parts(text):
    """Nombre de SMS facturés pour un message, mention STOP comprise (même calcul que la page)."""
    full = text + STOP_MENTION
    if all(ch in GSM or ch in GSM_EXT for ch in full):
        length, single, multi = sum(2 if ch in GSM_EXT else 1 for ch in full), 160, 153
    else:
        length, single, multi = len(full), 70, 67
    return 1 if length <= single else -(-length // multi)


def send_sms(campaign, session=None):
    if not sms_window_open():
        raise CampaignError("Les SMS commerciaux partent du lundi au samedi, entre 8 h et 20 h.")
    customers = audience(campaign.audience, "sms", campaign.excluded)
    if not customers:
        raise CampaignError("Aucun client dans ce public.")
    messages = [{"phoneNumber": mobile_of(c), "message": personalize(campaign.message, values_of(c))}
                for c in customers]
    longest = max(sms_parts(m["message"]) for m in messages)
    if longest > MAX_SMS_PARTS:
        raise CampaignError(f"Message trop long : jusqu'à {longest} SMS par client. Visez un seul SMS (160 caractères).")
    sent = 0
    for start in range(0, len(messages), SMS_BATCH):
        _sms_post("/bulk-send", {
            "SMSList": messages[start:start + SMS_BATCH],
            "sender": SMS_SENDER,
            "gamme": 1,
            "isStopSms": 1,
        }, session)
        sent += len(messages[start:start + SMS_BATCH])
    campaign.recipients = sent
    campaign.status = "envoyee"
    campaign.sent_at = timezone.now()
    campaign.error = ""
    campaign.save()
    return campaign


def sms_credits(session=None):
    http = session or requests
    data = http.get(f"{SMS_API}/me", params={"apiKey": env("SMS_API")}, timeout=15).json()
    return data.get("credits", {}).get("creditSms") if data.get("success") else None
