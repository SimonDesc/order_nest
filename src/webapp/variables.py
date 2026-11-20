"""
Variables utilisables dans une campagne : {prenom}, {derniere_commande}…

Chaque variable a une valeur par client (SMS : remplacée par OrderNest) et un attribut
Brevo du même contenu (e-mail : remplacée par Brevo à l'envoi). Les clients doivent être
annotés avec nb_orders, first_order, last_order et last_label (voir with_variables).
"""
from django.db.models import Count, Max, Min, OuterRef, Q, Subquery

from .models import Order

COUNTED = ~Q(order__status__in=["Devis", "Annulée"])
MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
          "septembre", "octobre", "novembre", "décembre"]


def _month(date):
    return f"{MONTHS[date.month - 1]} {date.year}" if date else ""


VARIABLES = {
    "prenom": {
        "label": "Prénom", "brevo": "FIRSTNAME", "sample": "Camille",
        "value": lambda c: c.first_name,
    },
    "nom": {
        "label": "Nom", "brevo": "LASTNAME", "sample": "Martin",
        "value": lambda c: c.last_name,
    },
    "derniere_commande": {
        "label": "Dernière commande", "brevo": "DERNIER_ACHAT", "sample": "Aquarelle de Venise",
        "hint": "le nom de sa dernière commande",
        "value": lambda c: getattr(c, "last_label", "") or "",
    },
    "date_derniere_commande": {
        "label": "Mois dernière commande", "brevo": "DERNIERE_VISITE", "sample": "mars 2025",
        "hint": "le mois de sa dernière commande",
        "value": lambda c: _month(getattr(c, "last_order", None)),
    },
    "nb_commandes": {
        "label": "Nb de commandes", "brevo": "NB_COMMANDES_TEXTE", "sample": "3",
        "hint": "son nombre de commandes",
        "value": lambda c: str(getattr(c, "nb_orders", 0) or "") if getattr(c, "nb_orders", 0) else "",
    },
    "client_depuis": {
        "label": "Client depuis", "brevo": "CLIENT_DEPUIS", "sample": "2024",
        "hint": "l'année de sa première commande",
        "value": lambda c: str(c.first_order.year) if getattr(c, "first_order", None) else "",
    },
}

# Attributs Brevo texte à créer (FIRSTNAME / LASTNAME existent déjà).
BREVO_TEXT_ATTRIBUTES = [v["brevo"] for v in VARIABLES.values() if v["brevo"] not in ("FIRSTNAME", "LASTNAME")]
SAMPLE = {key: var["sample"] for key, var in VARIABLES.items()}


def with_variables(queryset):
    """Ajoute aux clients ce qu'il faut pour calculer les variables."""
    last_label = (
        Order.objects.filter(customer=OuterRef("pk")).exclude(status__in=["Devis", "Annulée"])
        .order_by("-created_at").values("label")[:1]
    )
    return queryset.annotate(
        nb_orders=Count("order", filter=COUNTED, distinct=True),
        first_order=Min("order__created_at", filter=COUNTED),
        last_order=Max("order__created_at", filter=COUNTED),
        last_label=Subquery(last_label),
    )


def values_of(customer):
    return {key: (var["value"](customer) or "").strip() for key, var in VARIABLES.items()}


def public_list():
    """Pour la page : clé, libellé, exemple et explication de chaque variable."""
    return [
        {"key": key, "label": v["label"], "sample": v["sample"], "hint": v.get("hint", f"le {v['label'].lower()} du client")}
        for key, v in VARIABLES.items()
    ]
