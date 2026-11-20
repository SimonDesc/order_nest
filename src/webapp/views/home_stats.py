"""
Statistiques de l'accueil et de la page Statistiques.

Les volumes sont petits (quelques centaines de commandes par an) : on charge toutes
les commandes en une requête et on regroupe en Python, ce qui évite les différences
SQLite / PostgreSQL sur les fonctions de date.

Le prix d'une commande est la somme des prix de vente de ses produits. Il est souvent
saisi après la prise de commande : une commande à 0 € est « pas encore chiffrée », on
l'exclut du panier moyen et le chiffre d'affaires du mois en cours est sous-estimé.
"""
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from ..models import Customer, Order, OrderHasProduct

# Un devis n'est pas encore une commande, une commande annulée ne rapporte rien.
EXCLUDED_STATUSES = ("Devis", "Annulée")
OPEN_STATUSES = ("En cours", "Urgent")
STALE_DAYS = 30

MONTH_LABELS = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
                "juil.", "août", "sept.", "oct.", "nov.", "déc."]

# --- Outils -----------------------------------------------------------------------

def _shift_months(dt, months):
    """Premier jour du mois décalé de `months` (dt doit être un 1er du mois à minuit)."""
    index = dt.year * 12 + dt.month - 1 + months
    return dt.replace(year=index // 12, month=index % 12 + 1)


def _pct(current, previous):
    if not previous:
        return None
    return round((current - previous) * 100 / previous)


def _money(value):
    return float(value or 0)


def fr_number(value, unit=""):
    """1234 -> '1 234', avec l'espace fine insécable du français."""
    text = f"{round(value):,}".replace(",", " ")
    return f"{text} {unit}" if unit else text


def _trend(pct):
    return "flat" if not pct else ("up" if pct > 0 else "down")


def _age_label(days):
    if days < 14:
        return f"{days} j"
    if days < 60:
        return f"{days // 7} sem."
    return f"{days // 30} mois"


def _due(order):
    """Reste à payer : total des produits moins l'acompte."""
    return max((order["amount"] or Decimal(0)) - (order["deposit"] or Decimal(0)), Decimal(0))


class _Periods:
    """Bornes de dates utilisées partout, calculées une fois."""

    def __init__(self):
        self.now = timezone.localtime()
        self.today = self.now.date()
        self.end = self.now + timedelta(seconds=1)
        self.month_start = self.now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.last_month_start = _shift_months(self.month_start, -1)
        self.year_start = self.month_start.replace(month=1)
        self.last_year_start = self.year_start.replace(year=self.year_start.year - 1)
        self.window_start = _shift_months(self.month_start, -11)  # 12 mois glissants
        # Même avancement dans la période précédente : on compare le 1er→20 nov. au
        # 1er→20 oct., pas un mois entamé à un mois complet.
        self.last_month_cutoff = min(
            self.last_month_start + (self.now - self.month_start), self.month_start
        )
        try:
            self.last_year_cutoff = self.now.replace(year=self.now.year - 1)
        except ValueError:  # 29 février
            self.last_year_cutoff = self.now.replace(year=self.now.year - 1, day=28)


def _load_orders():
    return list(
        Order.objects
        .exclude(status__in=EXCLUDED_STATUSES)
        .annotate(amount=Sum("products__selling_price_unit"))
        .values("created_at", "amount", "customer_id")
    )


def _in_range(rows, start, stop, key=lambda r: r["created_at"]):
    return [r for r in rows if start <= key(r) < stop]


def _revenue(rows):
    return sum((r["amount"] or 0 for r in rows), Decimal(0))


def _basket(rows):
    priced = [r for r in rows if r["amount"]]
    return _revenue(priced) / len(priced) if priced else Decimal(0)


def _monthly(orders, customers):
    count, revenue, new_customers = defaultdict(int), defaultdict(Decimal), defaultdict(int)
    for order in orders:
        created = timezone.localtime(order["created_at"])
        count[(created.year, created.month)] += 1
        revenue[(created.year, created.month)] += order["amount"] or 0
    for created in customers:
        created = timezone.localtime(created)
        new_customers[(created.year, created.month)] += 1
    return count, revenue, new_customers


def _first_orders(orders):
    first = {}
    for order in orders:
        cid = order["customer_id"]
        if cid and (cid not in first or order["created_at"] < first[cid]):
            first[cid] = order["created_at"]
    return first


def _returning(rows, first):
    """(commandes de clients déjà venus, commandes de clients connus)."""
    known = [r for r in rows if r["customer_id"] in first]
    back = sum(1 for r in known if first[r["customer_id"]] < r["created_at"] - timedelta(days=1))
    return back, len(known)


def _pending_orders(p):
    """Commandes en cours ou terminées, avec montant, reste dû et ancienneté."""
    rows = list(
        Order.objects
        .filter(status__in=OPEN_STATUSES + ("Terminée",))
        .annotate(amount=Sum("products__selling_price_unit"))
        .values("pk", "label", "status", "payment", "created_at", "amount", "deposit",
                "customer__first_name", "customer__last_name", "customer__phone_number")
    )
    for order in rows:
        order["date"] = timezone.localtime(order["created_at"]).strftime("%d/%m/%Y")
        order["phone"] = _phone(order["customer__phone_number"])
        order["age"] = (p.now - order["created_at"]).days
        order["age_label"] = _age_label(order["age"])
        order["customer"] = f'{order["customer__first_name"]} {order["customer__last_name"]}'.strip()
        order["due"] = _due(order)
        order["due_display"] = fr_number(_money(order["due"]), "€")
    return rows


def _phone(number):
    """+33612345678 -> 06 12 34 56 78 (numéros français), sinon tel quel."""
    text = str(number or "")
    if text.startswith("+33") and len(text) == 12:
        digits = "0" + text[3:]
        return " ".join(digits[i:i + 2] for i in range(0, 10, 2))
    return text


def _actions(pending):
    unpriced = sorted((o for o in pending if not o["amount"]), key=lambda o: -o["age"])
    unpaid = [o for o in pending if o["status"] == "Terminée" and o["payment"] == "En attente"]
    to_collect = sum((o["due"] for o in unpaid), Decimal(0))
    stale_collect = sum((o["due"] for o in unpaid if o["age"] > STALE_DAYS), Decimal(0))
    return {
        "unpriced_count": len(unpriced),
        "unpriced_open": sum(1 for o in unpriced if o["status"] in OPEN_STATUSES),
        "unpriced_done": sum(1 for o in unpriced if o["status"] == "Terminée"),
        "unpriced": unpriced[:8],
        "unpaid_count": len(unpaid),
        "to_collect_display": fr_number(_money(to_collect), "€"),
        "stale_collect_display": fr_number(_money(stale_collect), "€"),
        "has_stale_collect": stale_collect > 0,
    }


# --- Accueil -----------------------------------------------------------------------

def build_home_stats():
    """Les 4 indicateurs du quotidien."""
    p = _Periods()
    orders = _in_range(_load_orders(), p.window_start, p.end)
    customers = list(
        Customer.objects.filter(created_at__gte=p.window_start).values_list("created_at", flat=True)
    )
    count, _, new_customers = _monthly(orders, customers)

    months_12 = [_shift_months(p.window_start, i) for i in range(12)]
    spark = lambda source: [
        {"label": f"{MONTH_LABELS[m.month - 1]} {m.year}", "value": int(source[(m.year, m.month)])}
        for m in months_12
    ]

    def trend_kpi(**kpi):
        pct = _pct(kpi["value"], kpi["previous"])
        kpi.update(
            display=fr_number(kpi["value"]),
            previous_display=fr_number(kpi["previous"]),
            delta_pct=pct,
            delta_abs=abs(pct) if pct is not None else None,
            trend=_trend(pct),
        )
        return kpi

    in_month = lambda rows, key=lambda r: r["created_at"]: len(_in_range(rows, p.month_start, p.end, key))
    in_prev = lambda rows, key=lambda r: r["created_at"]: len(
        _in_range(rows, p.last_month_start, p.last_month_cutoff, key)
    )
    same = lambda r: r

    kpis = [
        trend_kpi(
            id="orders", label="Commandes ce mois",
            value=in_month(orders), previous=in_prev(orders),
            compare="à la même date le mois dernier", spark=spark(count),
        ),
        trend_kpi(
            id="customers", label="Nouveaux clients ce mois",
            value=in_month(customers, same), previous=in_prev(customers, same),
            compare="à la même date le mois dernier", spark=spark(new_customers),
        ),
    ]
    return {"kpis": kpis, "actions": _actions(_pending_orders(p))}


# --- Page Statistiques -------------------------------------------------------------

def build_stats_page():
    p = _Periods()
    orders = _load_orders()
    customers = list(Customer.objects.values_list("created_at", flat=True))
    count, revenue, new_customers = _monthly(orders, customers)
    first = _first_orders(orders)
    pending = _pending_orders(p)
    year, prev_year = p.now.year, p.now.year - 1

    ytd = _in_range(orders, p.year_start, p.end)
    prev_ytd = _in_range(orders, p.last_year_start, p.last_year_cutoff)

    def headline(label, value, previous, unit="", note=""):
        pct = _pct(_money(value), _money(previous))
        return {
            "label": label,
            "display": fr_number(_money(value), unit),
            "previous_display": fr_number(_money(previous), unit),
            "delta_pct": pct,
            "delta_abs": abs(pct) if pct is not None else None,
            "trend": _trend(pct),
            "note": note,
        }

    compare = f"à la même date en {prev_year}"
    headlines = [
        headline(f"Chiffre d'affaires {year}", _revenue(ytd), _revenue(prev_ytd), "€"),
        headline(f"Commandes {year}", len(ytd), len(prev_ytd)),
        headline("Panier moyen", _basket(ytd), _basket(prev_ytd), "€"),
        headline(
            f"Nouveaux clients {year}",
            len(_in_range(customers, p.year_start, p.end, lambda c: c)),
            len(_in_range(customers, p.last_year_start, p.last_year_cutoff, lambda c: c)),
        ),
    ]

    # --- Activité depuis la première commande ------------------------------------
    start = (
        timezone.localtime(min(o["created_at"] for o in orders))
        .replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if orders else p.month_start
    )
    history = []
    m = start
    while m <= p.month_start:
        key = (m.year, m.month)
        history.append({
            "label": f"{MONTH_LABELS[m.month - 1]} {m.year}",
            "short": MONTH_LABELS[m.month - 1],
            "year": m.year,
            "month": m.month,
            "orders": count[key],
            "revenue": round(_money(revenue[key])),
            "customers": new_customers[key],
            "partial": m == p.month_start,
        })
        m = _shift_months(m, 1)

    # --- Tableau mois par mois des dernières années (vue texte du graphique) -------
    shown_years = sorted({h["year"] for h in history})[-3:]
    by_key = {(h["year"], h["month"]): h for h in history}
    years_table = {
        "years": shown_years,
        "rows": [
            {
                "label": MONTH_LABELS[i - 1],
                "cells": [
                    {
                        "orders": by_key[(y, i)]["orders"],
                        "revenue": fr_number(by_key[(y, i)]["revenue"], "€"),
                        "customers": by_key[(y, i)]["customers"],
                        "partial": by_key[(y, i)]["partial"],
                    } if (y, i) in by_key else None
                    for y in shown_years
                ],
            }
            for i in range(1, 13)
        ],
    }

    # --- Bilan par année ------------------------------------------------------------
    years = []
    for y in sorted({h["year"] for h in history}):
        y_start = p.year_start.replace(year=y)
        y_end = p.end if y == year else p.year_start.replace(year=y + 1)
        rows = _in_range(orders, y_start, y_end)
        back, known = _returning(rows, first)
        years.append({
            "year": y,
            "partial": y == year,
            "orders": len(rows),
            "revenue": _revenue(rows),
            "basket": _basket(rows),
            "customers": len(_in_range(customers, y_start, y_end, lambda c: c)),
            "loyalty": round(back * 100 / known) if known else None,
        })
    # La première année ne commence qu'à la première commande : si elle est incomplète,
    # l'évolution de l'année suivante n'aurait pas de sens.
    first_month = history[0]["month"] if history else 1
    for i, row in enumerate(years):
        before = years[i - 1] if i else None
        comparable = before and not (i == 1 and first_month > 1)
        if row["partial"] and before:
            # Année en cours : comparée à la même période de l'année précédente.
            row["orders_pct"] = _pct(row["orders"], len(prev_ytd))
            row["revenue_pct"] = _pct(_money(row["revenue"]), _money(_revenue(prev_ytd)))
        elif comparable:
            row["orders_pct"] = _pct(row["orders"], before["orders"])
            row["revenue_pct"] = _pct(_money(row["revenue"]), _money(before["revenue"]))
        for key in ("orders_pct", "revenue_pct"):
            row.setdefault(key, None)
            row[key.replace("_pct", "_trend")] = _trend(row[key])
        row["revenue_display"] = fr_number(_money(row["revenue"]), "€")
        row["basket_display"] = fr_number(_money(row["basket"]), "€")
    years_note = (
        f"{years[0]['year']} commence en {MONTH_LABELS[first_month - 1]} (première commande)."
        if years and first_month > 1 else ""
    )

    # --- Fidélité -------------------------------------------------------------------
    back, known = _returning(ytd, first)
    prev_back, prev_known = _returning(prev_ytd, first)
    share = round(back * 100 / known) if known else 0
    prev_share = round(prev_back * 100 / prev_known) if prev_known else None
    loyalty = {
        "share": share,
        "returning": back,
        "new": known - back,
        "previous_share": prev_share,
        "delta": share - prev_share if prev_share is not None else None,
        "regulars": Customer.objects.annotate(n=Count("order")).filter(n__gte=2).count(),
    }

    # --- Atelier ----------------------------------------------------------------------
    open_orders = [o for o in pending if o["status"] in OPEN_STATUSES]
    open_qs = Order.objects.filter(status__in=OPEN_STATUSES)
    quotes = list(Order.objects.filter(status="Devis").values_list("created_at", flat=True))
    recent_quotes = sum(1 for c in quotes if (p.now - c).days <= STALE_DAYS)
    workshop = {
        "urgent": sum(1 for o in open_orders if o["status"] == "Urgent"),
        "todo": sum(1 for o in open_orders if o["status"] == "En cours"),
        "done": sum(1 for o in pending if o["status"] == "Terminée"),
        "late": open_qs.filter(estimated_delivery_date__lt=p.today).count(),
        "due_soon": open_qs.filter(
            estimated_delivery_date__gte=p.today,
            estimated_delivery_date__lte=p.today + timedelta(days=7),
        ).count(),
        "stale_open": sum(1 for o in open_orders if o["age"] > STALE_DAYS),
        "recent_quotes": recent_quotes,
        "old_quotes": len(quotes) - recent_quotes,
    }
    workshop["open"] = workshop["urgent"] + workshop["todo"]
    workshop["total"] = workshop["open"] + workshop["done"]

    # --- Retraits en attente ------------------------------------------------------------
    done = sorted((o for o in pending if o["status"] == "Terminée"), key=lambda o: -o["age"])
    to_remind = [o for o in done if o["age"] > STALE_DAYS]
    unpaid_remind = [o for o in to_remind if o["payment"] == "En attente"]
    pickup = {
        "count": len(done),
        "recent": len(done) - len(to_remind),
        "to_remind": to_remind,
        "to_remind_count": len(to_remind),
        "to_remind_due_display": fr_number(
            _money(sum((o["due"] for o in unpaid_remind), Decimal(0))), "€"
        ),
    }

    return {
        "headlines": headlines,
        "headline_compare": compare,
        "actions": _actions(pending),
        "history": history,
        "current_year": year,
        "years_table": years_table,
        "years": years,
        "years_note": years_note,
        "loyalty": loyalty,
        "workshop": workshop,
        "pickup": pickup,
        "trends": _trends(orders, first, p),
    }



# --- Tendances : grandes catégories par période ------------------------------------
#
# Les produits sont saisis en texte libre (descriptif, baguette, passe-partout) : on les
# range en grandes familles par mots-clés. Ce qui ne se classe pas n'apparaît pas dans
# les graphiques de baguettes et de passe-partout plutôt que de les brouiller.

def _norm(text):
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return " " + re.sub(r"[^a-z0-9]+", " ", text.encode("ascii", "ignore").decode()) + " "


def _has(text, words):
    return any(word in text for word in words)


def _service(label, wand):
    if _has(label, (" restauration ", " resto ", " reparation ", " nettoyage ", " vernis ",
                    " dorure ", " retouche ", " recollage ")):
        return "restoration"
    if _has(label, (" collage ", " contrecollage ", " carton plume ", " dibond ")):
        return "mounting"
    if _has(label, (" chassis ", " tension ", " toile ")) and not wand:
        return "stretcher"
    if not wand and _has(label, (" verre ", " sous verre ", " art glass ", " artglass ",
                                 " miroir ", " pmma ", " plexi ")):
        return "glass_only"
    if wand or _finish(label):
        return "framing"
    return "other"


def _finish(label):
    if " noir" in label:
        return "black"
    if _has(label, (" or ", " jonc or", " dore", " doree ", " dorure ")):
        return "gold"
    if _has(label, (" alu ", " metal", " argent", " bronze", " inox", " laiton")):
        return "metal"
    if _has(label, (" blanc", " blanche ")):
        return "white"
    if _has(label, (" nat ", " naturel", " chene", " bois ", " ramin", " noyer", " hetre",
                    " frene", " pin ", " sauterelle nat", " merisier", " acajou", " wenge")):
        return "wood"
    if _has(label, (" bleu", " rouge", " vert", " gris", " rose", " jaune", " marine",
                    " bordeau", " kaki", " orange", " violet", " marron", " brun", " taupe")):
        return "color"
    return None


def _mat(mat):
    if not mat.strip() or _has(mat, (" sans ", " direct ")):
        return None
    if _has(mat, (" blanc", " creme", " ivoire", " beige", " ecru", " papier ")):
        return "light"
    if " noir" in mat:
        return "black"
    return "color"


def _price_band(amount):
    if not amount:
        return "unpriced"
    if amount < 50:
        return "lt50"
    if amount < 150:
        return "lt150"
    if amount < 300:
        return "lt300"
    return "gte300"


# Couleurs : le sens d'abord (noir = noir, doré = or) ; sinon la palette catégorielle
# validée, dans son ordre ; gris pour « non chiffrée ».
TREND_CHARTS = [
    ("sales", "Commandes par montant", [
        ("lt50", "Moins de 50 €", "#b7d3f6"),
        ("lt150", "50 à 150 €", "#6da7ec"),
        ("lt300", "150 à 300 €", "#2a78d6"),
        ("gte300", "300 € et plus", "#184f95"),
        ("unpriced", "Non chiffrée", "#d9d3c7"),
    ]),
    ("customers", "Clientèle", [
        ("returning", "Clients déjà venus", "#1a4562"),
        ("new", "Première commande", "#9fb3c2"),
    ]),
    ("services", "Prestations", [
        ("framing", "Encadrement", "#2a78d6"),
        ("restoration", "Restauration, nettoyage", "#eb6834"),
        ("mounting", "Collage, contrecollage", "#1baf7a"),
        ("glass_only", "Verre seul", "#eda100"),
        ("stretcher", "Châssis, toile", "#e87ba4"),
        ("other", "Autre", "#d9d3c7"),
    ]),
    ("glass", "Verres", [
        ("Artglass", "Artglass", "#2a78d6"),
        ("Anti-reflet", "Anti-reflet", "#6250d6"),
        ("Normal", "Normal", "#1baf7a"),
        ("PMMA", "PMMA", "#eda100"),
    ]),
    ("finish", "Baguettes par finition", [
        ("wood", "Bois naturel", "#a8743f"),
        ("black", "Noir", "#2b2b2b"),
        ("gold", "Doré", "#c9a227"),
        ("color", "Couleur", "#2a78d6"),
        ("white", "Blanc", "#cfc8b8"),
        ("metal", "Alu, métal", "#8d99a6"),
    ]),
    ("mat", "Passe-partout", [
        ("light", "Blanc, crème", "#d8cba8"),
        ("black", "Noir", "#2b2b2b"),
        ("color", "Couleur, référence", "#2a78d6"),
    ]),
]


def _trends(orders, first, p):
    month_key = lambda dt: (lambda d: f"{d.year}-{d.month:02d}")(timezone.localtime(dt))
    counts = {chart: defaultdict(Counter) for chart, _, _ in TREND_CHARTS}
    counts["components"] = defaultdict(Counter)

    for order in orders:
        key = month_key(order["created_at"])
        counts["sales"][_price_band(order["amount"])][key] += 1
        cid = order["customer_id"]
        if cid in first:
            back = first[cid] < order["created_at"] - timedelta(days=1)
            counts["customers"]["returning" if back else "new"][key] += 1

    lines = (
        OrderHasProduct.objects
        .exclude(order=None).exclude(product=None)
        .exclude(order__status__in=EXCLUDED_STATUSES)
        .values("order__created_at", "product__label", "product__wand",
                "product__mat", "product__glass")
    )
    for line in lines:
        key = month_key(line["order__created_at"])
        label = _norm(line["product__label"])
        wand = (line["product__wand"] or "").strip()
        service = _service(label, wand)
        counts["services"][service][key] += 1
        glass = line["product__glass"] if line["product__glass"] != "Sans" else None
        mat = _mat(_norm(line["product__mat"]))
        if glass:
            counts["glass"][glass][key] += 1
        if mat:
            counts["mat"][mat][key] += 1
        if service == "framing":
            # Un encadrement = une baguette ; on compte ceux qui ont aussi un verre,
            # un passe-partout.
            counts["components"]["wand"][key] += 1
            if glass:
                counts["components"]["glass"][key] += 1
            if mat:
                counts["components"]["mat"][key] += 1
            finish = _finish(label)
            if finish:
                counts["finish"][finish][key] += 1

    start = (
        timezone.localtime(min(o["created_at"] for o in orders))
        .replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if orders else p.month_start
    )
    months = []
    m = start
    while m <= p.month_start:
        months.append({"key": f"{m.year}-{m.month:02d}", "year": m.year, "month": m.month})
        m = _shift_months(m, 1)

    charts = []
    for chart_id, title, series in TREND_CHARTS:
        charts.append({
            "id": chart_id,
            "title": title,
            "series": [
                {"key": key, "label": label, "color": color,
                 "values": [counts[chart_id][key][mo["key"]] for mo in months]}
                for key, label, color in series
            ],
        })
    values = lambda chart, key: [counts[chart][key][mo["key"]] for mo in months]
    details = {"finish", "glass", "mat"}
    components = {
        "id": "components",
        "title": "Baguettes, verres, passe-partout",
        # Mode « part » : verres et passe-partout en % des encadrements.
        "base": values("components", "wand"),
        "series": [
            {"key": "wand", "label": "Baguettes", "color": "#eb6834", "values": values("components", "wand")},
            {"key": "glass", "label": "Verres", "color": "#2a78d6", "values": values("components", "glass")},
            {"key": "mat", "label": "Passe-partout", "color": "#1baf7a", "values": values("components", "mat")},
        ],
        "details": [c for c in charts if c["id"] in details],
    }
    return {
        "months": months,
        "charts": [c for c in charts if c["id"] not in details],
        "components": components,
    }
