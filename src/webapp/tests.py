from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from . import brevo
from .forms import NewCustomerForm, OrderCustomerForm
from .models import BrevoSync, Customer, Order, OrderHasProduct, Product


class FakeResponse:
    def __init__(self, status=200, data=None):
        self.status_code = status
        self._data = data or {}
        self.content = b"{}"
        self.text = str(data)

    def json(self):
        return self._data


class FakeBrevo:
    """Imite l'API Brevo : liste et attributs absents au départ, imports enregistrés."""

    def __init__(self):
        self.calls = []
        self.imports = []

    def request(self, method, url, **kwargs):
        path = url.replace(brevo.API, "")
        self.calls.append((method, path))
        if method == "GET" and path.startswith("/contacts/lists"):
            return FakeResponse(data={"lists": []})
        if method == "GET" and path.startswith("/contacts/folders"):
            return FakeResponse(data={"folders": []})
        if method == "POST" and path == "/contacts/folders":
            return FakeResponse(data={"id": 7})
        if method == "POST" and path == "/contacts/lists":
            return FakeResponse(data={"id": 42})
        if method == "GET" and path == "/contacts/attributes":
            return FakeResponse(data={"attributes": [{"name": "FIRSTNAME"}]})
        if method == "POST" and path == "/contacts/import":
            self.imports.append(kwargs["json"])
            return FakeResponse(data={"processId": len(self.imports)})
        return FakeResponse(data={})


def make_customer(**kwargs):
    defaults = {"first_name": "Camille", "last_name": "Martin", "phone_number": "+33612345678",
                "mail": "camille@example.com"}
    defaults.update(kwargs)
    return Customer.objects.create(**defaults)


def make_order(customer, price, status="Archivée", days_ago=10):
    order = Order.objects.create(label="Cadre", customer=customer, status=status)
    Order.objects.filter(pk=order.pk).update(created_at=timezone.now() - timedelta(days=days_ago))
    product = Product.objects.create(label="Cadre", selling_price_unit=price)
    OrderHasProduct.objects.create(order=order, product=product)
    return order


class BrevoSyncTests(TestCase):
    def sync(self):
        fake = FakeBrevo()
        client = brevo.BrevoClient(key="test", session=fake)
        return brevo.sync_customers(client=client, list_name="OrderNest – clients"), fake

    def test_contacts_attributes_and_consent(self):
        loyal = make_customer()
        make_order(loyal, 100, days_ago=400)
        make_order(loyal, 50, days_ago=20)
        make_order(loyal, 999, status="Devis")  # un devis ne compte pas
        make_customer(first_name="Léa", mail="lea@example.com", marketing_email=False, marketing_sms=False)
        make_customer(first_name="Sans mail", mail="")

        summary, fake = self.sync()

        self.assertEqual(summary["contacts"], 2)
        self.assertEqual(summary["unsubscribed"], 1)
        self.assertIn(("POST", "/contacts/lists"), fake.calls)  # liste créée au premier passage
        body = fake.imports[0]
        self.assertEqual(body["listIds"], [42])
        self.assertFalse(body["emptyContactsAttributes"])
        contacts = {c["email"]: c for c in body["jsonBody"]}

        camille = contacts["camille@example.com"]["attributes"]
        self.assertEqual(camille["NB_COMMANDES"], 2)
        self.assertEqual(camille["TOTAL_DEPENSE"], 150.0)
        self.assertTrue(camille["CLIENT_FIDELE"])
        self.assertEqual(camille["SMS"], "+33612345678")
        # Un client consentant n'est jamais « réinscrit » : pas de emailBlacklisted=False.
        self.assertNotIn("emailBlacklisted", contacts["camille@example.com"])

        lea = contacts["lea@example.com"]
        self.assertTrue(lea["emailBlacklisted"])
        self.assertTrue(lea["smsBlacklisted"])
        self.assertNotIn("SMS", lea["attributes"])

    def test_duplicate_emails_sent_once(self):
        make_customer(mail="Camille@Example.com")
        make_customer(mail="camille@example.com")
        summary, fake = self.sync()
        self.assertEqual(summary["contacts"], 1)

    def test_failure_is_logged(self):
        class Broken(FakeBrevo):
            def request(self, method, url, **kwargs):
                return FakeResponse(status=401, data={"message": "Key not found"})

        make_customer()
        sync = brevo.run_sync(client=brevo.BrevoClient(key="bad", session=Broken()))
        self.assertFalse(sync.success)
        self.assertIn("401", sync.message)
        self.assertEqual(BrevoSync.objects.count(), 1)

    def test_not_configured_without_key(self):
        with mock.patch.object(brevo, "api_key", return_value=""):
            self.assertFalse(brevo.is_configured())
            with self.assertRaises(brevo.BrevoError):
                brevo.BrevoClient()


class ConsentFormTests(TestCase):
    def data(self, **extra):
        data = {"first_name": "Camille", "last_name": "Martin", "phone_number": "0612345678",
                "address": "", "mail": "camille@example.com", "comments": ""}
        data.update(extra)
        return data

    def test_order_page_form_keeps_consent(self):
        # La page de commande n'affiche pas les cases : enregistrer ne doit pas les décocher.
        customer = make_customer()
        form = OrderCustomerForm(self.data(), instance=customer)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        customer.refresh_from_db()
        self.assertTrue(customer.marketing_email)
        self.assertTrue(customer.marketing_sms)

    def test_customer_form_records_refusal_date(self):
        customer = make_customer()
        form = NewCustomerForm(self.data(marketing_sms="on"), instance=customer)  # e-mail décoché
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        customer.refresh_from_db()
        self.assertFalse(customer.marketing_email)
        self.assertTrue(customer.marketing_sms)
        self.assertIsNotNone(customer.marketing_updated_at)
