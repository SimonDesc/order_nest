import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from webapp.models import Order

@login_required
def export_orders_csv(request):
    """
    Exporte toutes les commandes au format CSV
    """
    # Créer la réponse HTTP avec le type de contenu CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="commandes_export.csv"'

    # Ajouter le BOM UTF-8 pour Excel
    response.write('\ufeff')

    # Créer le writer CSV
    writer = csv.writer(response, delimiter=';')

    # En-têtes
    writer.writerow([
        'ID Commande',
        'Date de création',
        'Client',
        'Téléphone',
        'Libellé',
        'Statut',
        'État paiement',
        'Mode de paiement',
        'Acompte',
        'Prix total',
        'Reste à payer',
        'Date de livraison',
        'Date de facturation',
        'Commentaire',
        'Produits'
    ])

    # Récupérer toutes les commandes actives
    orders = Order.objects.filter(active=True).select_related('customer').prefetch_related('products')

    # Écrire les données
    for order in orders:
        # Calculer le prix total
        total_price = 0
        product_list = []

        for relation in order.orderhasproduct_set.all():
            if relation.product:
                product_price = relation.product.selling_price_unit
                total_price += product_price
                product_info = f"{relation.product.label}"
                if relation.product.wand:
                    product_info += f" - Baguette: {relation.product.wand}"
                if relation.product.size:
                    product_info += f" - Dimension: {relation.product.size}"
                product_info += f" ({product_price}€)"
                product_list.append(product_info)

        # Calculer le reste à payer
        reste_a_payer = total_price - order.deposit if order.deposit else total_price

        # Formater les données
        writer.writerow([
            order.id,
            order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else '',
            f"{order.customer.first_name} {order.customer.last_name}" if order.customer else '',
            order.customer.formatted_phone_number() if order.customer else '',
            order.label,
            order.status,
            order.payment,
            order.payment_method or '',
            str(order.deposit).replace('.', ',') if order.deposit else '0',
            str(total_price).replace('.', ','),
            str(reste_a_payer).replace('.', ','),
            order.estimated_delivery_date.strftime('%d/%m/%Y') if order.estimated_delivery_date else '',
            order.invoice_date.strftime('%d/%m/%Y') if order.invoice_date else '',
            order.comments or '',
            ' | '.join(product_list)
        ])

    return response

@login_required
def export_orders_csv_filtered(request):
    """
    Exporte les commandes filtrées par statut au format CSV
    """
    # Récupérer le paramètre de statut depuis l'URL
    status_filter = request.GET.get('status', None)

    # Créer la réponse HTTP avec le type de contenu CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')

    # Nom du fichier selon le filtre
    if status_filter:
        filename = f"commandes_{status_filter.lower().replace(' ', '_')}.csv"
    else:
        filename = "commandes_export.csv"

    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Ajouter le BOM UTF-8 pour Excel
    response.write('\ufeff')

    # Créer le writer CSV
    writer = csv.writer(response, delimiter=';')

    # En-têtes
    writer.writerow([
        'ID Commande',
        'Date de création',
        'Client',
        'Téléphone',
        'Libellé',
        'Statut',
        'État paiement',
        'Mode de paiement',
        'Acompte',
        'Prix total',
        'Reste à payer',
        'Date de livraison',
        'Date de facturation',
        'Commentaire',
        'Produits'
    ])

    # Construire la requête
    orders_query = Order.objects.filter(active=True).select_related('customer').prefetch_related('products')

    # Appliquer le filtre de statut si fourni
    if status_filter:
        # Si plusieurs statuts sont séparés par des virgules
        if ',' in status_filter:
            statuses = [s.strip() for s in status_filter.split(',')]
            orders_query = orders_query.filter(status__in=statuses)
        else:
            orders_query = orders_query.filter(status=status_filter)

    # Trier par date de création décroissante
    orders = orders_query.order_by('-created_at')

    # Écrire les données
    for order in orders:
        # Calculer le prix total
        total_price = 0
        product_list = []

        for relation in order.orderhasproduct_set.all():
            if relation.product:
                product_price = relation.product.selling_price_unit
                total_price += product_price
                product_info = f"{relation.product.label}"
                if relation.product.wand:
                    product_info += f" - Baguette: {relation.product.wand}"
                if relation.product.size:
                    product_info += f" - Dimension: {relation.product.size}"
                product_info += f" ({product_price}€)"
                product_list.append(product_info)

        # Calculer le reste à payer
        reste_a_payer = total_price - order.deposit if order.deposit else total_price

        # Formater les données
        writer.writerow([
            order.id,
            order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else '',
            f"{order.customer.first_name} {order.customer.last_name}" if order.customer else '',
            order.customer.formatted_phone_number() if order.customer else '',
            order.label,
            order.status,
            order.payment,
            order.payment_method or '',
            str(order.deposit).replace('.', ',') if order.deposit else '0',
            str(total_price).replace('.', ','),
            str(reste_a_payer).replace('.', ','),
            order.estimated_delivery_date.strftime('%d/%m/%Y') if order.estimated_delivery_date else '',
            order.invoice_date.strftime('%d/%m/%Y') if order.invoice_date else '',
            order.comments or '',
            ' | '.join(product_list)
        ])

    return response