"""
Onglet Campagnes : écrire un message, choisir un public, s'envoyer un test, envoyer.

La page appelle campaign_action en JSON (test, envoi, programmation) ; une campagne
reste modifiable tant qu'elle est en brouillon.
"""
import json
import re
from datetime import datetime, timedelta

import requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from .. import brevo, campaign_suggestions, campaigns
from ..models import Campaign, CampaignTemplate
from ..variables import public_list

EXAMPLES = {
    "email": {
        "subject": "Noël à la Galerie Libre Cours",
        "message": (
            "Bonjour {prenom},\n\n"
            "Les fêtes approchent : c'est le moment de faire encadrer une photo, une affiche "
            "ou une oeuvre à offrir. Pour être prêt à temps, déposez vos encadrements avant le 10 décembre.\n\n"
            "À très bientôt à la galerie !"
        ),
    },
    "sms": {
        "message": (
            "Bonjour {prenom}, pensez à vos cadeaux de fin d'année : déposez vos "
            "encadrements avant le 10/12 pour les avoir à temps. Galerie Libre Cours"
        ),
    },
}


class CampagnesView(TemplateView):
    template_name = "webapp/campagnes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        counts = campaigns.audience_counts()
        context.update({
            "audiences": [
                {"key": key, "label": label, "hint": hint, "email": counts[key]["email"], "sms": counts[key]["sms"]}
                for key, label, hint in campaigns.AUDIENCES
            ],
            "campaigns": Campaign.objects.all()[:30],
            "brevo_configured": brevo.is_configured(),
            "sender": campaigns.sender(),
            "sms_window_open": campaigns.sms_window_open(),
            "examples": EXAMPLES,
            "audience_labels": campaigns.AUDIENCE_LABELS,
            "templates": [t.as_dict() for t in CampaignTemplate.objects.all()],
            "variables": public_list(),
            "suggestions": campaign_suggestions.as_list(),
        })
        return context


def _clean_url(value):
    """« galerielibrecours.fr » → « https://galerielibrecours.fr » ; refuse ce qui n'est pas un lien."""
    url = (value or "").strip()
    if not url:
        return ""
    if not re.match(r"https?://", url):
        url = "https://" + url
    if not re.match(r"https?://[^\s/]+\.[^\s/]+", url):
        raise campaigns.CampaignError("Le lien du bouton n'est pas une adresse web (ex. galerielibrecours.fr).")
    return url


def _error(message, status=400):
    return JsonResponse({"ok": False, "error": message}, status=status)


def _campaign_from(data):
    """La campagne décrite par le formulaire : la reprend si c'est un brouillon, sinon en crée une."""
    channel = data.get("channel")
    if channel not in ("email", "sms"):
        raise campaigns.CampaignError("Choisir e-mail ou SMS.")
    if data.get("audience") not in campaigns.AUDIENCE_LABELS:
        raise campaigns.CampaignError("Choisir un public.")
    message = (data.get("message") or "").strip()
    subject = (data.get("subject") or "").strip()
    if not message:
        raise campaigns.CampaignError("Le message est vide.")
    if channel == "email" and not subject:
        raise campaigns.CampaignError("Il manque l'objet de l'e-mail.")
    button_url = _clean_url(data.get("button_url"))

    campaign = None
    if data.get("id"):
        campaign = Campaign.objects.filter(pk=data["id"], status="brouillon", channel=channel).first()
    campaign = campaign or Campaign(channel=channel)
    campaign.audience = data["audience"]
    campaign.subject = subject[:200] if channel == "email" else ""
    campaign.preheader = (data.get("preheader") or "").strip()[:200] if channel == "email" else ""
    campaign.message = message
    campaign.button_label = (data.get("button_label") or "").strip()[:60] if channel == "email" else ""
    campaign.button_url = button_url if channel == "email" else ""
    unknown = campaigns.unknown_variables(subject, message, data.get("preheader"))
    if unknown:
        raise campaigns.CampaignError(
            f"Variable inconnue : {', '.join(unknown)}. Variables possibles : "
            + ", ".join("{" + key + "}" for key in campaigns.VARIABLES) + "."
        )
    campaign.name = (subject or campaigns.personalize(message, {}).strip())[:60] or "Campagne"
    try:
        campaign.excluded = sorted({int(pk) for pk in data.get("exclude") or []})
    except (TypeError, ValueError):
        raise campaigns.CampaignError("Liste d'exclusion illisible.")
    campaign.save()
    return campaign


def _parse_schedule(value):
    try:
        when = timezone.make_aware(datetime.fromisoformat(value))
    except (TypeError, ValueError):
        raise campaigns.CampaignError("Date d'envoi invalide.")
    if when <= timezone.now() + timedelta(minutes=5):
        raise campaigns.CampaignError("Programmer au moins 5 minutes à l'avance.")
    return when


@require_POST
def campaign_action(request):
    try:
        data = json.loads(request.body or "{}")
    except ValueError:
        return _error("Requête illisible.")
    action = data.get("action")
    if action not in ("test", "send", "schedule"):
        return _error("Action inconnue.")

    try:
        todo = campaigns.unfilled(data.get("subject"), data.get("preheader"), data.get("message"), data.get("button_label"))
        if todo and action != "test":
            raise campaigns.CampaignError(f"À compléter avant l'envoi : {', '.join(todo)}.")
        campaign = _campaign_from(data)
        if campaign.channel == "email":
            if action == "test":
                to = [e.strip() for e in re.split(r"[,;\s]+", data.get("test_to") or "") if "@" in e]
                if not to:
                    raise campaigns.CampaignError("Indiquer l'adresse qui reçoit le test.")
                campaigns.send_email_test(campaign, to)
                return JsonResponse({"ok": True, "id": campaign.pk, "message": f"Test envoyé à {', '.join(to)}."})
            when = _parse_schedule(data.get("scheduled_at")) if action == "schedule" else None
            campaigns.send_email(campaign, scheduled_at=when)
        else:
            if action == "test":
                phone = re.sub(r"[^\d+]", "", data.get("test_to") or "")
                if len(phone) < 10:
                    raise campaigns.CampaignError("Indiquer le portable qui reçoit le test.")
                campaigns.send_sms_test(campaign, phone)
                return JsonResponse({"ok": True, "id": campaign.pk, "message": f"Test envoyé au {data['test_to']}."})
            if action == "schedule":
                raise campaigns.CampaignError("Les SMS partent tout de suite : pas de programmation.")
            campaigns.send_sms(campaign)
    except (campaigns.CampaignError, brevo.BrevoError, requests.RequestException) as error:
        if "campaign" in locals() and action != "test":
            campaign.error = str(error)[:500]
            campaign.save(update_fields=["error"])
        return _error(str(error))

    if campaign.status == "programmee":
        when = timezone.localtime(campaign.scheduled_at).strftime("%d/%m/%Y à %H:%M")
        text = f"Campagne programmée le {when} pour {campaign.recipients} clients."
    else:
        text = f"Campagne envoyée à {campaign.recipients} clients."
    return JsonResponse({"ok": True, "id": campaign.pk, "status": campaign.status, "message": text})


@require_POST
def campaign_preview(request):
    """Aperçu de l'e-mail tel que le client le recevra (prénom d'exemple)."""
    data = json.loads(request.body or "{}")
    campaign = Campaign(
        channel="email",
        subject=data.get("subject") or "",
        preheader=data.get("preheader") or "",
        message=data.get("message") or "",
        button_label=data.get("button_label") or "",
        button_url=data.get("button_url") or "",
    )
    html = campaigns.email_html(campaign, sample=True).replace('href="{{ unsubscribe }}"', 'href="#"')
    return HttpResponse(html)


@require_GET
def campaign_stats(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, channel="email")
    if not campaign.brevo_id:
        return _error("Campagne jamais envoyée à Brevo.", 404)
    try:
        return JsonResponse({"ok": True, **campaigns.email_stats(campaign)})
    except (brevo.BrevoError, requests.RequestException) as error:
        return _error(str(error), 502)


@require_GET
def campaign_credits(request):
    """Crédits restants : e-mails Brevo et SMS SMSPartner."""
    result = {"ok": True, "email": None, "sms": None}
    if brevo.is_configured():
        try:
            result["email"] = campaigns.email_credits()
        except Exception:  # crédits : information secondaire, jamais bloquante
            pass
    try:
        result["sms"] = campaigns.sms_credits()
    except Exception:
        pass
    return JsonResponse(result)


@require_POST
def template_save(request):
    """Enregistre le message en cours comme modèle (même nom et même canal : remplacé)."""
    try:
        data = json.loads(request.body or "{}")
    except ValueError:
        return _error("Requête illisible.")
    name = (data.get("name") or "").strip()[:80]
    channel = data.get("channel")
    message = (data.get("message") or "").strip()
    if channel not in ("email", "sms"):
        return _error("Canal inconnu.")
    if not name:
        return _error("Donner un nom au modèle.")
    if not message:
        return _error("Le message est vide.")
    try:
        button_url = _clean_url(data.get("button_url"))
    except campaigns.CampaignError as error:
        return _error(str(error))
    template, created = CampaignTemplate.objects.update_or_create(
        channel=channel, name=name,
        defaults={
            "subject": (data.get("subject") or "").strip()[:200] if channel == "email" else "",
            "preheader": (data.get("preheader") or "").strip()[:200] if channel == "email" else "",
            "message": message,
            "button_label": (data.get("button_label") or "").strip()[:60] if channel == "email" else "",
            "button_url": button_url if channel == "email" else "",
        },
    )
    return JsonResponse({
        "ok": True, "created": created, "template": template.as_dict(),
        "message": f"Modèle « {name} » {'enregistré' if created else 'mis à jour'}.",
    })


@require_POST
def template_delete(request, pk):
    template = get_object_or_404(CampaignTemplate, pk=pk)
    template.delete()
    return JsonResponse({"ok": True, "message": f"Modèle « {template.name} » supprimé."})


@require_GET
def campaign_recipients(request):
    """Les clients d'un public, pour vérifier à qui part la campagne."""
    key, channel = request.GET.get("audience"), request.GET.get("channel")
    if key not in campaigns.AUDIENCE_LABELS or channel not in ("email", "sms"):
        return _error("Public ou canal inconnu.")
    rows = []
    for c in campaigns.audience(key, channel):
        rows.append({
            "id": c.pk,
            "name": f"{c.first_name} {c.last_name}".strip(),
            "contact": campaigns.email_of(c) if channel == "email" else c.formatted_phone_number(),
            "orders": c.nb_orders or 0,
            "last_order": timezone.localtime(c.last_order).strftime("%d/%m/%Y") if c.last_order else "",
            "last_order_sort": c.last_order.isoformat() if c.last_order else "",
            "spent": round(float(c.total_spent or 0)),
            "url": reverse("webapp:customer-edit", args=[c.pk]),
        })
    return JsonResponse({"ok": True, "label": campaigns.AUDIENCE_LABELS[key], "rows": rows})
