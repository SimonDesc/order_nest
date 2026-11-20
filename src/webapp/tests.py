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


# --- Campagnes ------------------------------------------------------------------------

from . import campaigns  # noqa: E402
from .models import Campaign  # noqa: E402


class FakeBrevoCampaigns(FakeBrevo):
    """FakeBrevo + campagnes e-mail et suivi des imports."""

    def request(self, method, url, **kwargs):
        path = url.replace(brevo.API, "")
        if path == "/emailCampaigns" and method == "POST":
            self.calls.append((method, path))
            self.created = kwargs["json"]
            return FakeResponse(data={"id": 99})
        if path.startswith("/emailCampaigns/") or path.startswith("/processes/"):
            self.calls.append((method, path))
            if method == "PUT":
                self.updates = getattr(self, "updates", []) + [kwargs.get("json")]
            return FakeResponse(data={"status": "completed"})
        return super().request(method, url, **kwargs)


class FakeSms:
    def __init__(self):
        self.posts = []

    def post(self, url, json=None, timeout=None):
        self.posts.append((url, json))
        return FakeResponse(data={"success": True})


class CampaignTests(TestCase):
    def setUp(self):
        self.loyal = make_customer(first_name="Camille", mail="camille@example.com", phone_number="+33612345678")
        make_order(self.loyal, 100, days_ago=500)
        make_order(self.loyal, 80, days_ago=30)
        self.once = make_customer(first_name="", last_name="Durand", mail="durand@example.com", phone_number="+33712345678")
        make_order(self.once, 60, days_ago=400)
        self.refuses = make_customer(first_name="Léa", mail="lea@example.com", phone_number="+33611111111",
                                     marketing_email=False, marketing_sms=False)
        make_order(self.refuses, 50, days_ago=10)
        self.landline = make_customer(first_name="Fixe", mail="", phone_number="+33145454545")
        make_order(self.landline, 40, days_ago=10)
        self.quote = make_customer(first_name="Paul", mail="paul@example.com", phone_number="+33622222222")
        make_order(self.quote, 300, status="Devis", days_ago=20)

    def test_audiences_respect_consent_and_channel(self):
        emails = lambda key: {c.pk for c in campaigns.audience(key, "email")}
        sms = lambda key: {c.pk for c in campaigns.audience(key, "sms")}
        self.assertEqual(emails("tous"), {self.loyal.pk, self.once.pk, self.quote.pk})  # pas Léa (refus)
        self.assertEqual(sms("tous"), {self.loyal.pk, self.once.pk, self.quote.pk})  # pas de fixe
        self.assertEqual(emails("fideles"), {self.loyal.pk})
        self.assertEqual(emails("recents"), {self.loyal.pk})
        self.assertEqual(emails("inactifs"), {self.once.pk})
        self.assertEqual(emails("une_fois"), {self.once.pk})
        self.assertEqual(emails("devis"), {self.quote.pk})
        counts = campaigns.audience_counts()
        self.assertEqual(counts["tous"], {"email": 3, "sms": 3})
        self.assertEqual(counts["fideles"]["sms"], 1)

    def test_personalize(self):
        text = "Bonjour {prenom} {nom}, ça va ?"
        self.assertEqual(campaigns.personalize(text, {"prenom": "Camille", "nom": "Martin"}), "Bonjour Camille Martin, ça va ?")
        self.assertEqual(campaigns.personalize(text, {"nom": "Martin"}), "Bonjour Martin, ça va ?")
        self.assertEqual(campaigns.personalize(text, {}), "Bonjour, ça va ?")
        self.assertEqual(campaigns.personalize("{prenom}\n\nSuite", {}), "\n\nSuite")  # pas de saut de ligne mangé
        self.assertEqual(campaigns.unknown_variables("Bonjour {prénom}", "{nom} {promo}"), ["{prénom}", "{promo}"])

    def test_email_html_uses_brevo_tags_and_escapes(self):
        campaign = Campaign(channel="email", subject="Noël", message="Bonjour {prenom},\n\n<b>Promo</b> -20 %")
        html = campaigns.email_html(campaign)
        self.assertIn("Bonjour{% if contact.FIRSTNAME %} {{ contact.FIRSTNAME }}{% endif %},", html)
        self.assertIn("Bonjour Camille,", campaigns.email_html(campaign, sample=True))
        self.assertIn("&lt;b&gt;Promo&lt;/b&gt;", html)
        self.assertIn("{{ unsubscribe }}", html)

    def test_send_email_creates_list_and_sends(self):
        campaign = Campaign.objects.create(channel="email", audience="tous", name="Noël", subject="Noël", message="Bonjour {prenom}")
        fake = FakeBrevoCampaigns()
        campaigns.send_email(campaign, client=brevo.BrevoClient(key="k", session=fake), wait=lambda c, p: None)
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, "envoyee")
        self.assertEqual(campaign.recipients, 3)
        self.assertEqual(campaign.brevo_id, 99)
        self.assertEqual(fake.created["sender"]["email"], "contact@galerielibrecours.fr")
        emails = {c["email"] for c in fake.imports[0]["jsonBody"]}
        self.assertEqual(emails, {"camille@example.com", "durand@example.com", "paul@example.com"})
        self.assertIn(("POST", "/emailCampaigns/99/sendNow"), fake.calls)

    def test_schedule_email_does_not_send_now(self):
        campaign = Campaign.objects.create(channel="email", audience="fideles", name="x", subject="x", message="x")
        fake = FakeBrevoCampaigns()
        when = timezone.now() + timedelta(days=1)
        campaigns.send_email(campaign, scheduled_at=when, client=brevo.BrevoClient(key="k", session=fake), wait=lambda c, p: None)
        self.assertEqual(campaign.status, "programmee")
        self.assertNotIn(("POST", "/emailCampaigns/99/sendNow"), fake.calls)
        self.assertEqual(fake.updates[-1]["scheduledAt"], when.isoformat())

    def test_send_sms_personalized_with_stop(self):
        campaign = Campaign.objects.create(channel="sms", audience="tous", name="x", message="Bonjour {prenom}, promo !")
        fake = FakeSms()
        with mock.patch.object(campaigns, "sms_window_open", return_value=True), \
                mock.patch.dict("os.environ", {"SMS_API": "key"}):
            campaigns.send_sms(campaign, session=fake)
        url, body = fake.posts[0]
        self.assertTrue(url.endswith("/bulk-send"))
        self.assertEqual(body["isStopSms"], 1)
        messages = {m["phoneNumber"]: m["message"] for m in body["SMSList"]}
        self.assertEqual(messages["+33612345678"], "Bonjour Camille, promo !")
        self.assertEqual(messages["+33712345678"], "Bonjour, promo !")
        self.assertNotIn("+33611111111", messages)
        self.assertEqual(campaign.recipients, 3)

    def test_sms_blocked_outside_hours(self):
        campaign = Campaign.objects.create(channel="sms", audience="tous", name="x", message="x")
        with mock.patch.object(campaigns, "sms_window_open", return_value=False):
            with self.assertRaises(campaigns.CampaignError):
                campaigns.send_sms(campaign, session=FakeSms())

    def test_sms_window(self):
        tz = timezone.get_current_timezone()
        from datetime import datetime
        self.assertTrue(campaigns.sms_window_open(datetime(2026, 11, 21, 10, 0, tzinfo=tz)))   # samedi 10 h
        self.assertFalse(campaigns.sms_window_open(datetime(2026, 11, 22, 10, 0, tzinfo=tz)))  # dimanche
        self.assertFalse(campaigns.sms_window_open(datetime(2026, 11, 20, 20, 30, tzinfo=tz)))  # 20 h 30


class CampaignTemplateTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.client.force_login(User.objects.create_user("gerant", password="x"))

    def save(self, **data):
        body = {"name": "Soldes", "channel": "email", "subject": "Soldes", "message": "Bonjour {prenom}"}
        body.update(data)
        return self.client.post("/campagnes/modeles/", data=body, content_type="application/json").json()

    def test_save_update_and_delete(self):
        from .models import CampaignTemplate
        first = self.save(button_url="galerielibrecours.fr")
        self.assertTrue(first["ok"], first)
        self.assertTrue(first["created"])
        self.assertEqual(first["template"]["button_url"], "https://galerielibrecours.fr")
        again = self.save(message="Nouveau texte")  # même nom : remplacé, pas dupliqué
        self.assertFalse(again["created"])
        self.assertEqual(CampaignTemplate.objects.get().message, "Nouveau texte")
        self.save(channel="sms", subject="ignoré")  # même nom, autre canal : un autre modèle
        self.assertEqual(CampaignTemplate.objects.count(), 2)
        self.assertEqual(CampaignTemplate.objects.get(channel="sms").subject, "")
        pk = first["template"]["id"]
        self.assertTrue(self.client.post(f"/campagnes/modeles/{pk}/supprimer/").json()["ok"])
        self.assertEqual(CampaignTemplate.objects.count(), 1)

    def test_rejects_empty_and_bad_link(self):
        self.assertFalse(self.save(name="")["ok"])
        self.assertFalse(self.save(message=" ")["ok"])
        self.assertFalse(self.save(button_url="gege")["ok"])


class PreheaderTests(TestCase):
    def test_default_skips_greeting_and_is_hidden_first(self):
        c = Campaign(channel="email", subject="Noël", message="Bonjour {prenom},\n\nUne œuvre à offrir ?\n\nÀ bientôt")
        self.assertEqual(campaigns.preheader_of(c), "Une œuvre à offrir ? À bientôt")
        html = campaigns.email_html(c)
        # Le texte d'aperçu vient avant le logo « LC », sinon Gmail affiche « LC Galerie Libre Cours… »
        self.assertLess(html.index("Une œuvre à offrir"), html.index(">LC<"))

    def test_typed_preheader_is_sent_to_brevo(self):
        c = Campaign(channel="email", subject="x", message="x", preheader="Pour {prenom} : -10 %")
        self.assertEqual(campaigns._email_payload(c)["previewText"],
                         "Pour{% if contact.FIRSTNAME %} {{ contact.FIRSTNAME }}{% endif %} : -10 %")


class SuggestionTests(TestCase):
    GSM = set("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZ"
              "ÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà^{}\\[~]|€")

    def test_suggestions_are_valid(self):
        from .campaign_suggestions import as_list
        for s in as_list():
            self.assertIn(s["audience"], campaigns.AUDIENCE_LABELS, s["name"])
            self.assertEqual(campaigns.unknown_variables(s["subject"], s["message"]), [], s["name"])
            if s["channel"] == "sms":
                # Un seul SMS : alphabet GSM et 160 caractères avec la mention STOP, à prénom égal.
                text = campaigns.personalize(s["message"], {"prenom": "Camille"}) + " STOP au 36180"
                self.assertTrue(set(text) <= self.GSM, (s["name"], set(text) - self.GSM))
                self.assertLessEqual(len(text) + text.count("€"), 160, s["name"])

    def test_send_blocked_until_brackets_are_filled(self):
        from django.contrib.auth.models import User
        self.client.force_login(User.objects.create_user("gerant", password="x"))
        body = {"action": "send", "channel": "email", "audience": "tous", "subject": "Nouvel artiste : [nom]",
                "message": "Bonjour {prenom}, découvrez [nom] dès [prix] €."}
        data = self.client.post("/campagnes/envoyer/", data=body, content_type="application/json").json()
        self.assertFalse(data["ok"])
        self.assertIn("[nom]", data["error"])
        self.assertIn("[prix]", data["error"])


class RecipientsTests(TestCase):
    setUp = CampaignTests.setUp  # mêmes clients que CampaignTests

    def test_exclusion_is_respected(self):
        campaign = Campaign.objects.create(channel="sms", audience="tous", name="x", message="Bonjour {prenom}",
                                           excluded=[self.once.pk])
        fake = FakeSms()
        with mock.patch.object(campaigns, "sms_window_open", return_value=True), \
                mock.patch.dict("os.environ", {"SMS_API": "key"}):
            campaigns.send_sms(campaign, session=fake)
        phones = {m["phoneNumber"] for m in fake.posts[0][1]["SMSList"]}
        self.assertNotIn("+33712345678", phones)
        self.assertEqual(campaign.recipients, 2)

    def test_recipients_endpoint_and_variables(self):
        from django.contrib.auth.models import User
        from .variables import values_of
        self.client.force_login(User.objects.create_user("gerant", password="x"))
        rows = self.client.get("/campagnes/destinataires/?audience=fideles&channel=email").json()["rows"]
        self.assertEqual([r["name"] for r in rows], ["Camille Martin"])
        self.assertEqual(rows[0]["orders"], 2)
        self.assertEqual(rows[0]["spent"], 180)
        values = values_of(campaigns.audience("fideles", "email")[0])
        self.assertEqual(values["nb_commandes"], "2")
        self.assertEqual(values["derniere_commande"], "Cadre")
        self.assertRegex(values["date_derniere_commande"], r"^\w+ \d{4}$")
        first_year = (timezone.now() - timedelta(days=500)).year  # première commande : il y a 500 jours
        self.assertEqual(campaigns.personalize("depuis {client_depuis}", values), f"depuis {first_year}")


class SmsLengthTests(TestCase):
    def test_sms_parts(self):
        self.assertEqual(campaigns.sms_parts("a" * 146), 1)   # 146 + 14 (STOP) = 160
        self.assertEqual(campaigns.sms_parts("a" * 147), 2)
        self.assertEqual(campaigns.sms_parts("œ" * 10), 1)     # unicode : 70 caractères
        self.assertEqual(campaigns.sms_parts("œ" * 60), 2)

    def test_too_long_sms_is_refused(self):
        customer = make_customer(first_name="Camille", phone_number="+33612345678")
        make_order(customer, 50)
        campaign = Campaign.objects.create(channel="sms", audience="tous", name="x", message="a" * 400)
        with mock.patch.object(campaigns, "sms_window_open", return_value=True):
            with self.assertRaises(campaigns.CampaignError):
                campaigns.send_sms(campaign, session=FakeSms())
