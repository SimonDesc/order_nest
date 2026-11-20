"""
Modèles de campagne proposés : points de départ prêts à adapter.

Les passages entre crochets [comme ceci] sont à compléter : la page les signale et
refuse l'envoi tant qu'il en reste. Chaque modèle suggère un public (modifiable).
Les SMS évitent ê, œ, ’… pour tenir dans un seul SMS (160 caractères, STOP compris).
"""

SITE = "https://galerielibrecours.fr"

SUGGESTIONS = [
    # --- Galerie : œuvres d'artistes locaux --------------------------------------------
    {
        "key": "nouvel-artiste",
        "name": "Nouvel artiste à la galerie",
        "channel": "email",
        "audience": "tous",
        "subject": "Nouvel artiste à la galerie : [nom de l'artiste]",
        "message": (
            "Bonjour {prenom},\n\n"
            "Nous avons le plaisir d'accueillir un nouvel artiste à la Galerie Libre Cours : "
            "[nom de l'artiste], [peintre / photographe / sculpteur] de [ville ou région].\n\n"
            "[Deux ou trois phrases sur son travail : sa technique, ses thèmes, ce qui nous a touchés.]\n\n"
            "Ses œuvres sont à découvrir dès maintenant à la galerie et sur notre site, à partir de [prix] €.\n\n"
            "Au plaisir de vous y retrouver !"
        ),
        "button_label": "Découvrir ses œuvres",
        "button_url": f"{SITE}/galerie",
    },
    {
        "key": "tous-budgets",
        "name": "Des œuvres pour tous les budgets",
        "channel": "email",
        "audience": "tous",
        "subject": "De l'art local pour tous les budgets",
        "message": (
            "Bonjour {prenom},\n\n"
            "Vous nous connaissez pour l'encadrement : la Galerie Libre Cours vous propose aussi "
            "des œuvres originales d'artistes de la région, pour tous les budgets.\n\n"
            "Peintures, photographies, gravures, sculptures : à partir de [prix] €, de quoi trouver "
            "la pièce qui vous ressemble, ou un cadeau qui sort de l'ordinaire.\n\n"
            "Et bien sûr, nous pouvons l'encadrer sur place.\n\n"
            "Venez flâner à la galerie, ou faites un premier tour sur notre site."
        ),
        "button_label": "Voir les œuvres",
        "button_url": f"{SITE}/galerie",
    },
    {
        "key": "vernissage",
        "name": "Invitation au vernissage",
        "channel": "email",
        "audience": "tous",
        "subject": "Vernissage le [date] : [titre de l'exposition]",
        "message": (
            "Bonjour {prenom},\n\n"
            "Nous serions ravis de vous accueillir au vernissage de l'exposition "
            "« [titre de l'exposition] », consacrée à [nom de l'artiste].\n\n"
            "Rendez-vous le [jour et date] à partir de [heure] à la galerie. "
            "L'artiste sera présent pour échanger avec vous autour d'un verre.\n\n"
            "L'exposition se poursuit jusqu'au [date de fin].\n\n"
            "Au plaisir de vous y voir !"
        ),
        "button_label": "Voir l'exposition",
        "button_url": f"{SITE}/galerie",
    },
    {
        "key": "avant-premiere",
        "name": "Avant-première pour les fidèles",
        "channel": "email",
        "audience": "fideles",
        "subject": "{prenom}, découvrez les nouvelles œuvres en avant-première",
        "message": (
            "Bonjour {prenom},\n\n"
            "Client de la galerie depuis {client_depuis}, vous faites partie de ceux qui nous font "
            "confiance : merci !\n\n"
            "Avant tout le monde, nous vous invitons à découvrir les nouvelles œuvres de "
            "[nom de l'artiste], du [date] au [date]. [Avantage réservé : par exemple, l'encadrement "
            "offert ou -10 % sur l'œuvre de votre choix.]\n\n"
            "À très bientôt à la galerie."
        ),
        "button_label": "Voir les œuvres",
        "button_url": f"{SITE}/galerie",
    },
    # --- Moments de l'année ------------------------------------------------------------
    {
        "key": "noel",
        "name": "Idées cadeaux de Noël",
        "channel": "email",
        "audience": "tous",
        "subject": "Pour Noël, offrez une œuvre d'un artiste d'ici",
        "message": (
            "Bonjour {prenom},\n\n"
            "Cette année, pourquoi ne pas offrir une œuvre originale ? Les artistes de la galerie "
            "proposent des pièces uniques à partir de [prix] €, et nous préparons aussi des bons cadeaux.\n\n"
            "Vous avez une photo ou une affiche à faire encadrer pour l'offrir ? Déposez-la avant le "
            "[date limite] pour qu'elle soit prête à temps.\n\n"
            "Belles fêtes de fin d'année !"
        ),
        "button_label": "Trouver un cadeau",
        "button_url": f"{SITE}/galerie",
    },
    {
        "key": "fete-des-meres",
        "name": "Fête des mères / des pères",
        "channel": "email",
        "audience": "tous",
        "subject": "Un cadeau unique pour la fête des [mères / pères]",
        "message": (
            "Bonjour {prenom},\n\n"
            "Le [date], c'est la fête des [mères / pères]. Une œuvre d'un artiste local, une photo de "
            "famille joliment encadrée : un cadeau qui dure.\n\n"
            "Pour un encadrement prêt à temps, passez nous voir avant le [date limite].\n\n"
            "À bientôt à la galerie !"
        ),
        "button_label": "Voir les idées cadeaux",
        "button_url": f"{SITE}/galerie",
    },
    # --- Fidélisation ------------------------------------------------------------------
    {
        "key": "reconquete",
        "name": "Vous nous manquez",
        "channel": "email",
        "audience": "inactifs",
        "subject": "Du nouveau à la Galerie Libre Cours",
        "message": (
            "Bonjour {prenom},\n\n"
            "Votre dernier passage à la galerie remonte à {date_derniere_commande}, et il s'est passé "
            "beaucoup de choses depuis !\n\n"
            "De nouveaux artistes de la région exposent chez nous, avec des œuvres pour tous les budgets. "
            "Et notre atelier d'encadrement est toujours là pour vos photos, affiches et souvenirs.\n\n"
            "Nous serions heureux de vous revoir."
        ),
        "button_label": "Voir les nouveautés",
        "button_url": f"{SITE}/galerie",
    },
    {
        "key": "encadrement",
        "name": "Rappel : l'atelier d'encadrement",
        "channel": "email",
        "audience": "une_fois",
        "subject": "Une photo, une affiche, un souvenir à encadrer ?",
        "message": (
            "Bonjour {prenom},\n\n"
            "Merci encore pour votre confiance. Si vous avez d'autres œuvres, photos ou souvenirs "
            "qui attendent dans un tiroir, notre atelier les met en valeur sur mesure : choix de la "
            "baguette, du passe-partout et du verre, conseils compris.\n\n"
            "Passez nous voir avec votre pièce, le devis est gratuit."
        ),
        "button_label": "L'encadrement sur mesure",
        "button_url": f"{SITE}/encadrement",
    },
    {
        "key": "devis",
        "name": "Votre projet d'encadrement",
        "channel": "email",
        "audience": "devis",
        "subject": "Votre projet d'encadrement est-il toujours d'actualité ?",
        "message": (
            "Bonjour {prenom},\n\n"
            "Vous nous aviez demandé un devis pour un projet d'encadrement. Si vous y réfléchissez encore, "
            "nous restons à votre disposition pour en reparler ou ajuster le devis.\n\n"
            "Au plaisir de vous revoir à la galerie."
        ),
        "button_label": "Nous contacter",
        "button_url": f"{SITE}/contact",
    },
    # --- SMS (courts : un seul SMS par client) ------------------------------------------
    {
        "key": "sms-nouvel-artiste",
        "name": "Nouvel artiste (SMS)",
        "channel": "sms",
        "audience": "tous",
        "message": (
            "Bonjour {prenom}, nouvel artiste à la Galerie Libre Cours : [nom], à découvrir "
            "dès [prix] € sur galerielibrecours.fr/galerie"
        ),
    },
    {
        "key": "sms-vernissage",
        "name": "Vernissage (SMS)",
        "channel": "sms",
        "audience": "tous",
        "message": (
            "Bonjour {prenom}, vernissage de [artiste] le [date] à [heure] à la Galerie Libre Cours. "
            "Venez nombreux !"
        ),
    },
    {
        "key": "sms-noel",
        "name": "Cadeaux de Noël (SMS)",
        "channel": "sms",
        "audience": "tous",
        "message": (
            "Bonjour {prenom}, pour les cadeaux de fin d'année, offrez une oeuvre d'un artiste "
            "local dès [prix] € ou un bon cadeau. Galerie Libre Cours"
        ),
    },
    {
        "key": "sms-reconquete",
        "name": "Vous nous manquez (SMS)",
        "channel": "sms",
        "audience": "inactifs",
        "message": (
            "Bonjour {prenom}, de nouveaux artistes de la région exposent à la Galerie Libre Cours, "
            "oeuvres dès [prix] €. Au plaisir de vous revoir !"
        ),
    },
]


def as_list():
    """Pour la page : même forme que les modèles enregistrés, identifiant préfixé « s: »."""
    return [
        {
            "id": f"s:{s['key']}", "suggested": True, "name": s["name"], "channel": s["channel"],
            "audience": s["audience"], "subject": s.get("subject", ""), "message": s["message"],
            "button_label": s.get("button_label", ""), "button_url": s.get("button_url", ""),
        }
        for s in SUGGESTIONS
    ]
