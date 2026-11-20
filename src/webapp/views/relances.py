"""
Onglet Relances : trois listes de clients à recontacter.

- Devis en attente : relancer les devis récents, classer sans suite les vieux.
- Commandes à retirer : prévenir les clients dont la commande est prête.
- Anciens clients : recontacter ceux venus une seule fois il y a 6 à 24 mois.

Chaque relance (SMS ou appel) est enregistrée dans FollowUp : un client relancé
récemment passe en bas de liste, grisé, jusqu'à ce qu'il soit temps de le relancer.
"""
from datetime import timedelta

from django.db.models import Count, Max, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from ..models import Customer, FollowUp, Order
from .home_stats import EXCLUDED_STATUSES, _age_label, _money, fr_number

# Délai avant qu'un client relancé réapparaisse en haut de liste.
REMIND_AGAIN_DAYS = {"devis": 14, "retrait": 14, "reactivation": 180}
RECENT_QUOTE_DAYS = 90
# Anciens clients : une seule commande, passée il y a 6 à 24 mois.
DORMANT_MIN_DAYS, DORMANT_MAX_DAYS = 180, 730

SMS_TEMPLATES = {
    "devis": (
        "{hello}, suite à votre devis \"{label}\" à la Galerie Libre Cours, "
        "avez-vous pu y réfléchir ? Nous restons à votre disposition. À bientôt !"
    ),
    "retrait": (
        "{hello}, votre commande \"{label}\" est prête et vous attend "
        "à la Galerie Libre Cours. À bientôt !"
    ),
    "reactivation": (
        "{hello}, merci encore pour votre confiance. Une oeuvre, une photo, "
        "un souvenir à encadrer ? Toute l'équipe de la Galerie Libre Cours serait "
        "ravie de vous revoir !"
    ),
}


def _last_follow_ups(kind):
    """{(customer_id, order_id): dernière relance} pour un type de relance."""
    last = {}
    for f in FollowUp.objects.filter(kind=kind).order_by("created_at"):
        last[(f.customer_id, f.order_id)] = f
        last[(f.customer_id, None)] = f
    return last


def _since(now, when):
    days = (now - when).days
    return "aujourd'hui" if days == 0 else ("hier" if days == 1 else f"il y a {_age_label(days)}")


def _row(kind, customer, now, order=None, amount=None, last=None, extra=None):
    # « Bonjour Camille, » si le prénom est connu ; sinon « Bonjour, » (pas « Bonjour Dupont »).
    first = (customer.first_name or "").strip()
    hello = f"Bonjour {first}" if first else "Bonjour"
    row = {
        "kind": kind,
        "customer": customer,
        "customer_name": f"{customer.first_name} {customer.last_name}".strip(),
        "phone": customer.formatted_phone_number(),
        "order": order,
        "amount_display": fr_number(_money(amount), "€") if amount else "",
        "sms": SMS_TEMPLATES[kind].format(hello=hello, label=order.label if order else ""),
        "last": last,
        "last_label": _since(now, last.created_at) if last else "",
        "snoozed": bool(last and (now - last.created_at).days < REMIND_AGAIN_DAYS[kind]),
    }
    if order:
        row["date"] = timezone.localtime(order.created_at).strftime("%d/%m/%Y")
        row["age_label"] = _age_label((now - order.created_at).days)
    row.update(extra or {})
    return row


def _sorted(rows, key):
    """À relancer d'abord (selon `key`), les clients relancés récemment à la fin."""
    todo = sorted((r for r in rows if not r["snoozed"]), key=key)
    done = sorted((r for r in rows if r["snoozed"]), key=lambda r: r["last"].created_at, reverse=True)
    return todo, done


class RelancesView(TemplateView):
    template_name = "webapp/relances.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        # --- Devis en attente ---------------------------------------------------------
        last = _last_follow_ups("devis")
        quotes = (
            Order.objects.filter(status="Devis").exclude(customer=None)
            .select_related("customer")
            .annotate(amount=Sum("products__selling_price_unit"))
        )
        recent, old = [], []
        for q in quotes:
            row = _row("devis", q.customer, now, q, q.amount, last.get((q.customer_id, q.pk)))
            (recent if (now - q.created_at).days <= RECENT_QUOTE_DAYS else old).append(row)
        quote_todo, quote_done = _sorted(recent, key=lambda r: r["order"].created_at)
        old.sort(key=lambda r: r["order"].created_at, reverse=True)

        # --- Commandes prêtes, pas encore retirées --------------------------------------
        last = _last_follow_ups("retrait")
        ready = (
            Order.objects.filter(status="Terminée").exclude(customer=None)
            .select_related("customer")
            .annotate(amount=Sum("products__selling_price_unit"))
        )
        pickup_rows = []
        for o in ready:
            due = max((o.amount or 0) - (o.deposit or 0), 0) if o.payment == "En attente" else 0
            pickup_rows.append(_row(
                "retrait", o.customer, now, o, None, last.get((o.customer_id, o.pk)),
                {"due_display": fr_number(_money(due), "€") if due else "", "paid": o.payment != "En attente"},
            ))
        pickup_todo, pickup_done = _sorted(pickup_rows, key=lambda r: r["order"].created_at)

        # --- Anciens clients : une seule commande, il y a 6 à 24 mois -------------------
        last = _last_follow_ups("reactivation")
        counted = Q(order__status__in=["En cours", "Urgent", "Terminée", "Archivée", "Facturée"])
        dormant = (
            Customer.objects.filter(active=True)
            .annotate(n=Count("order", filter=counted), last_order=Max("order__created_at", filter=counted))
            .filter(
                n=1,
                last_order__lte=now - timedelta(days=DORMANT_MIN_DAYS),
                last_order__gte=now - timedelta(days=DORMANT_MAX_DAYS),
            )
        )
        # Pas de relance d'un client qui a un devis ou une commande en cours.
        busy = set(
            Order.objects.filter(status__in=["Devis", "En cours", "Urgent", "Terminée"])
            .values_list("customer_id", flat=True)
        )
        orders = {
            o.customer_id: o
            for o in Order.objects.filter(customer__in=dormant).exclude(status__in=EXCLUDED_STATUSES)
            .annotate(amount=Sum("products__selling_price_unit"))
        }
        dormant_rows = [
            _row("reactivation", c, now, orders.get(c.pk), getattr(orders.get(c.pk), "amount", None),
                 last.get((c.pk, None)))
            for c in dormant if c.pk not in busy and c.phone_number
        ]
        # Les plus gros paniers d'abord : ce sont les clients qui valent le plus d'être revus.
        dormant_todo, dormant_done = _sorted(
            dormant_rows, key=lambda r: -float(getattr(r["order"], "amount", 0) or 0)
        )

        context.update({
            "quote_todo": quote_todo,
            "quote_done": quote_done,
            "quote_old": old,
            "pickup_todo": pickup_todo,
            "pickup_done": pickup_done,
            "dormant_todo": dormant_todo,
            "dormant_done": dormant_done,
            "remind_again": REMIND_AGAIN_DAYS,
        })
        return context


@require_POST
def follow_up_create(request):
    """Enregistre une relance (appelé après un SMS envoyé ou un appel passé)."""
    kind = request.POST.get("kind")
    channel = request.POST.get("channel", "appel")
    if kind not in dict(FollowUp.KIND) or channel not in dict(FollowUp.CHANNEL):
        return JsonResponse({"success": False, "error": "Type de relance inconnu."}, status=400)
    customer = get_object_or_404(Customer, pk=request.POST.get("customer"))
    order = None
    if request.POST.get("order"):
        order = get_object_or_404(Order, pk=request.POST.get("order"), customer=customer)
    follow_up = FollowUp.objects.create(
        kind=kind, channel=channel, customer=customer, order=order,
        note=request.POST.get("note", "")[:300],
    )
    return JsonResponse({"success": True, "id": follow_up.pk})


@require_POST
def follow_up_delete(request, pk):
    """Annule une relance enregistrée par erreur (le SMS éventuel, lui, est parti)."""
    get_object_or_404(FollowUp, pk=pk).delete()
    return JsonResponse({"success": True})


@require_POST
def quote_close(request, pk):
    """Classe un devis sans suite (statut Annulée)."""
    order = get_object_or_404(Order, pk=pk, status="Devis")
    order.status = "Annulée"
    order.save(update_fields=["status"])
    return JsonResponse({"success": True})
