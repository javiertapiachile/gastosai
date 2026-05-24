"""
Reglas de clasificación por defecto para el mercado chileno.
Basadas en investigación de comercios reales (mayo 2026).

Estructura: lista de dicts con:
  - patron: texto a buscar (lowercase)
  - categoria: nombre exacto de la categoría
  - prioridad: 0-100 (mayor = más prioritaria)
  - descripcion: comentario humano

Se insertan automáticamente para cada usuario nuevo
y se pueden actualizar vía tarea programada.
"""

REGLAS_DEFAULT = [

    # ──────────────────────────────────────────────
    # ALIMENTACIÓN — Supermercados Chile
    # ──────────────────────────────────────────────
    {"patron": "jumbo",         "categoria": "Alimentación", "prioridad": 80, "descripcion": "Supermercado Jumbo (Cencosud)"},
    {"patron": "lider",         "categoria": "Alimentación", "prioridad": 80, "descripcion": "Supermercado Lider (Walmart)"},
    {"patron": "santa isabel",  "categoria": "Alimentación", "prioridad": 80, "descripcion": "Supermercado Santa Isabel (Cencosud)"},
    {"patron": "unimarc",       "categoria": "Alimentación", "prioridad": 80, "descripcion": "Supermercado Unimarc (SMU)"},
    {"patron": "tottus",        "categoria": "Alimentación", "prioridad": 80, "descripcion": "Supermercado Tottus (Falabella)"},
    {"patron": "acuenta",       "categoria": "Alimentación", "prioridad": 80, "descripcion": "Supermercado Acuenta (Walmart)"},
    {"patron": "mayorista 10",  "categoria": "Alimentación", "prioridad": 80, "descripcion": "Mayorista 10 (SMU)"},
    {"patron": "ok market",     "categoria": "Alimentación", "prioridad": 75, "descripcion": "Tienda de conveniencia OK Market"},
    {"patron": "big john",      "categoria": "Alimentación", "prioridad": 75, "descripcion": "Supermercado Big John"},
    {"patron": "ekono",         "categoria": "Alimentación", "prioridad": 75, "descripcion": "Supermercado Ekono"},
    {"patron": "la cabaña",     "categoria": "Alimentación", "prioridad": 70, "descripcion": "Supermercado La Cabaña"},
    {"patron": "cugat",         "categoria": "Alimentación", "prioridad": 70, "descripcion": "Supermercado Cugat"},

    # Restaurantes y comida rápida
    {"patron": "mcdonalds",     "categoria": "Alimentación", "prioridad": 85, "descripcion": "McDonald's"},
    {"patron": "mcd",           "categoria": "Alimentación", "prioridad": 80, "descripcion": "McDonald's (abreviado)"},
    {"patron": "burger king",   "categoria": "Alimentación", "prioridad": 85, "descripcion": "Burger King"},
    {"patron": "subway",        "categoria": "Alimentación", "prioridad": 85, "descripcion": "Subway"},
    {"patron": "dominos",       "categoria": "Alimentación", "prioridad": 85, "descripcion": "Domino's Pizza"},
    {"patron": "papa johns",    "categoria": "Alimentación", "prioridad": 85, "descripcion": "Papa John's"},
    {"patron": "pizza hut",     "categoria": "Alimentación", "prioridad": 85, "descripcion": "Pizza Hut"},
    {"patron": "kfc",           "categoria": "Alimentación", "prioridad": 85, "descripcion": "KFC"},
    {"patron": "popeyes",       "categoria": "Alimentación", "prioridad": 85, "descripcion": "Popeyes"},
    {"patron": "starbucks",     "categoria": "Alimentación", "prioridad": 85, "descripcion": "Starbucks"},
    {"patron": "juan valdez",   "categoria": "Alimentación", "prioridad": 80, "descripcion": "Juan Valdez Café"},
    {"patron": "doggis",        "categoria": "Alimentación", "prioridad": 80, "descripcion": "Doggis (completos)"},
    {"patron": "telepizza",     "categoria": "Alimentación", "prioridad": 80, "descripcion": "Telepizza"},
    {"patron": "el rincón",     "categoria": "Alimentación", "prioridad": 70, "descripcion": "El Rincón"},

    # Delivery / apps de comida
    {"patron": "rappi",         "categoria": "Alimentación", "prioridad": 75, "descripcion": "Rappi delivery"},
    {"patron": "pedidosya",     "categoria": "Alimentación", "prioridad": 75, "descripcion": "PedidosYa delivery"},
    {"patron": "uber eats",     "categoria": "Alimentación", "prioridad": 75, "descripcion": "Uber Eats"},
    {"patron": "didi food",     "categoria": "Alimentación", "prioridad": 75, "descripcion": "DiDi Food delivery"},

    # ──────────────────────────────────────────────
    # TRANSPORTE
    # ──────────────────────────────────────────────
    {"patron": "copec",         "categoria": "Transporte", "prioridad": 85, "descripcion": "Estación de servicio Copec"},
    {"patron": "shell",         "categoria": "Transporte", "prioridad": 85, "descripcion": "Estación de servicio Shell"},
    {"patron": "petrobras",     "categoria": "Transporte", "prioridad": 85, "descripcion": "Estación de servicio Petrobras"},
    {"patron": "enex",          "categoria": "Transporte", "prioridad": 85, "descripcion": "Estación de servicio Enex"},
    {"patron": "bencina",       "categoria": "Transporte", "prioridad": 80, "descripcion": "Bencina genérica"},
    {"patron": "autopista",     "categoria": "Transporte", "prioridad": 80, "descripcion": "Peaje autopista"},
    {"patron": "peaje",         "categoria": "Transporte", "prioridad": 80, "descripcion": "Pago de peaje"},
    {"patron": "vias chile",    "categoria": "Transporte", "prioridad": 80, "descripcion": "Vías Chile (autopistas)"},
    {"patron": "autoexpreso",   "categoria": "Transporte", "prioridad": 80, "descripcion": "AutoExpreso peaje electrónico"},
    {"patron": "globalvia",     "categoria": "Transporte", "prioridad": 80, "descripcion": "Globalvia autopistas"},
    {"patron": "troncal sur",   "categoria": "Transporte", "prioridad": 80, "descripcion": "Autopista Troncal Sur"},
    {"patron": "costanera norte","categoria": "Transporte", "prioridad": 80, "descripcion": "Autopista Costanera Norte"},
    {"patron": "ruta 5",        "categoria": "Transporte", "prioridad": 75, "descripcion": "Ruta 5 (peaje)"},
    {"patron": "uber",          "categoria": "Transporte", "prioridad": 80, "descripcion": "Uber taxi"},
    {"patron": "cabify",        "categoria": "Transporte", "prioridad": 80, "descripcion": "Cabify taxi"},
    {"patron": "didi",          "categoria": "Transporte", "prioridad": 75, "descripcion": "DiDi taxi"},
    {"patron": "indriver",      "categoria": "Transporte", "prioridad": 75, "descripcion": "inDrive taxi"},
    {"patron": "metro de santiago","categoria": "Transporte","prioridad": 85,"descripcion": "Metro de Santiago"},
    {"patron": "bip",           "categoria": "Transporte", "prioridad": 75, "descripcion": "Tarjeta Bip transporte público"},
    {"patron": "tur bus",       "categoria": "Transporte", "prioridad": 80, "descripcion": "Tur Bus (buses interurbanos)"},
    {"patron": "pullman",       "categoria": "Transporte", "prioridad": 80, "descripcion": "Pullman Bus"},
    {"patron": "condor bus",    "categoria": "Transporte", "prioridad": 75, "descripcion": "Cóndor Bus"},
    {"patron": "jetsmart",      "categoria": "Transporte", "prioridad": 85, "descripcion": "JetSMART aerolínea"},
    {"patron": "sky airline",   "categoria": "Transporte", "prioridad": 85, "descripcion": "Sky Airline"},
    {"patron": "latam",         "categoria": "Transporte", "prioridad": 85, "descripcion": "LATAM Airlines"},
    {"patron": "estacionamiento","categoria": "Transporte","prioridad": 75, "descripcion": "Pago estacionamiento"},
    {"patron": "parking",       "categoria": "Transporte", "prioridad": 75, "descripcion": "Parking/estacionamiento"},
    {"patron": "muevo",         "categoria": "Transporte", "prioridad": 80, "descripcion": "Muevo (app estaciones de servicio)"},

    # ──────────────────────────────────────────────
    # SALUD
    # ──────────────────────────────────────────────
    {"patron": "cruz verde",    "categoria": "Salud", "prioridad": 90, "descripcion": "Farmacia Cruz Verde"},
    {"patron": "salcobrand",    "categoria": "Salud", "prioridad": 90, "descripcion": "Farmacia Salcobrand"},
    {"patron": "ahumada",       "categoria": "Salud", "prioridad": 85, "descripcion": "Farmacias Ahumada"},
    {"patron": "dr simi",       "categoria": "Salud", "prioridad": 85, "descripcion": "Farmacias Dr. Simi"},
    {"patron": "dr. simi",      "categoria": "Salud", "prioridad": 85, "descripcion": "Farmacias Dr. Simi"},
    {"patron": "dr ahorro",     "categoria": "Salud", "prioridad": 80, "descripcion": "Farmacias Dr. Ahorro"},
    {"patron": "farmacia",      "categoria": "Salud", "prioridad": 75, "descripcion": "Farmacia genérica"},
    {"patron": "clinica",       "categoria": "Salud", "prioridad": 80, "descripcion": "Clínica médica"},
    {"patron": "clínica",       "categoria": "Salud", "prioridad": 80, "descripcion": "Clínica médica"},
    {"patron": "hospital",      "categoria": "Salud", "prioridad": 80, "descripcion": "Hospital"},
    {"patron": "laboratorio",   "categoria": "Salud", "prioridad": 75, "descripcion": "Laboratorio clínico"},
    {"patron": "optica",        "categoria": "Salud", "prioridad": 75, "descripcion": "Óptica"},
    {"patron": "óptica",        "categoria": "Salud", "prioridad": 75, "descripcion": "Óptica"},
    {"patron": "biomedica",     "categoria": "Salud", "prioridad": 75, "descripcion": "Biomédica laboratorio"},
    {"patron": "integramédica", "categoria": "Salud", "prioridad": 80, "descripcion": "Integramédica"},
    {"patron": "alemana",       "categoria": "Salud", "prioridad": 75, "descripcion": "Clínica Alemana"},
    {"patron": "santa maria",   "categoria": "Salud", "prioridad": 75, "descripcion": "Clínica Santa María"},
    {"patron": "bupa",          "categoria": "Salud", "prioridad": 75, "descripcion": "Bupa salud"},
    {"patron": "fonasa",        "categoria": "Salud", "prioridad": 80, "descripcion": "FONASA"},
    {"patron": "isapre",        "categoria": "Salud", "prioridad": 80, "descripcion": "Isapre"},

    # ──────────────────────────────────────────────
    # ENTRETENIMIENTO
    # ──────────────────────────────────────────────
    {"patron": "netflix",       "categoria": "Entretenimiento", "prioridad": 90, "descripcion": "Netflix streaming"},
    {"patron": "spotify",       "categoria": "Entretenimiento", "prioridad": 90, "descripcion": "Spotify música"},
    {"patron": "disney",        "categoria": "Entretenimiento", "prioridad": 85, "descripcion": "Disney+ streaming"},
    {"patron": "hbo",           "categoria": "Entretenimiento", "prioridad": 85, "descripcion": "HBO Max streaming"},
    {"patron": "amazon prime",  "categoria": "Entretenimiento", "prioridad": 85, "descripcion": "Amazon Prime Video"},
    {"patron": "apple tv",      "categoria": "Entretenimiento", "prioridad": 85, "descripcion": "Apple TV+"},
    {"patron": "paramount",     "categoria": "Entretenimiento", "prioridad": 80, "descripcion": "Paramount+ streaming"},
    {"patron": "crunchyroll",   "categoria": "Entretenimiento", "prioridad": 80, "descripcion": "Crunchyroll anime"},
    {"patron": "youtube premium","categoria": "Entretenimiento","prioridad": 80,"descripcion": "YouTube Premium"},
    {"patron": "steam",         "categoria": "Entretenimiento", "prioridad": 80, "descripcion": "Steam videojuegos"},
    {"patron": "playstation",   "categoria": "Entretenimiento", "prioridad": 80, "descripcion": "PlayStation Store"},
    {"patron": "xbox",          "categoria": "Entretenimiento", "prioridad": 80, "descripcion": "Xbox Game Pass"},
    {"patron": "cine hoyts",    "categoria": "Entretenimiento", "prioridad": 85, "descripcion": "Cine Hoyts"},
    {"patron": "cinemark",      "categoria": "Entretenimiento", "prioridad": 85, "descripcion": "Cinemark"},
    {"patron": "cine",          "categoria": "Entretenimiento", "prioridad": 70, "descripcion": "Cine genérico"},
    {"patron": "ticketmaster",  "categoria": "Entretenimiento", "prioridad": 80, "descripcion": "Ticketmaster entradas"},
    {"patron": "puntoticket",   "categoria": "Entretenimiento", "prioridad": 80, "descripcion": "Puntoticket entradas"},
    {"patron": "teleticket",    "categoria": "Entretenimiento", "prioridad": 80, "descripcion": "Teleticket entradas"},
    {"patron": "twitch",        "categoria": "Entretenimiento", "prioridad": 75, "descripcion": "Twitch streaming"},
    {"patron": "google one",    "categoria": "Entretenimiento", "prioridad": 75, "descripcion": "Google One suscripción"},
    {"patron": "deezer",        "categoria": "Entretenimiento", "prioridad": 75, "descripcion": "Deezer música"},
    {"patron": "apple music",   "categoria": "Entretenimiento", "prioridad": 75, "descripcion": "Apple Music"},

    # ──────────────────────────────────────────────
    # COMPRAS (retail)
    # ──────────────────────────────────────────────
    {"patron": "falabella",     "categoria": "Compras", "prioridad": 85, "descripcion": "Tienda Falabella"},
    {"patron": "ripley",        "categoria": "Compras", "prioridad": 85, "descripcion": "Tienda Ripley"},
    {"patron": "paris",         "categoria": "Compras", "prioridad": 85, "descripcion": "Tienda Paris"},
    {"patron": "la polar",      "categoria": "Compras", "prioridad": 85, "descripcion": "Tienda La Polar"},
    {"patron": "hites",         "categoria": "Compras", "prioridad": 80, "descripcion": "Tienda Hites"},
    {"patron": "corona",        "categoria": "Compras", "prioridad": 75, "descripcion": "Tienda Corona"},
    {"patron": "abcdin",        "categoria": "Compras", "prioridad": 80, "descripcion": "ABCDin electrodomésticos"},
    {"patron": "amazon",        "categoria": "Compras", "prioridad": 80, "descripcion": "Amazon marketplace"},
    {"patron": "amzn",          "categoria": "Compras", "prioridad": 80, "descripcion": "Amazon (abreviado)"},
    {"patron": "mercadolibre",  "categoria": "Compras", "prioridad": 80, "descripcion": "MercadoLibre"},
    {"patron": "mercado libre", "categoria": "Compras", "prioridad": 80, "descripcion": "MercadoLibre"},
    {"patron": "meli",          "categoria": "Compras", "prioridad": 75, "descripcion": "MercadoLibre (abreviado)"},
    {"patron": "shein",         "categoria": "Compras", "prioridad": 80, "descripcion": "Shein moda online"},
    {"patron": "aliexpress",    "categoria": "Compras", "prioridad": 80, "descripcion": "AliExpress"},
    {"patron": "sodimac",       "categoria": "Compras", "prioridad": 80, "descripcion": "Sodimac hogar y construcción"},
    {"patron": "easy",          "categoria": "Compras", "prioridad": 75, "descripcion": "Easy hogar y construcción"},
    {"patron": "ikea",          "categoria": "Compras", "prioridad": 80, "descripcion": "IKEA muebles"},
    {"patron": "pcfactory",     "categoria": "Compras", "prioridad": 80, "descripcion": "PC Factory tecnología"},
    {"patron": "tecnofactory",  "categoria": "Compras", "prioridad": 75, "descripcion": "TecnoFactory tecnología"},
    {"patron": "adidas",        "categoria": "Compras", "prioridad": 80, "descripcion": "Adidas tienda"},
    {"patron": "nike",          "categoria": "Compras", "prioridad": 80, "descripcion": "Nike tienda"},
    {"patron": "zara",          "categoria": "Compras", "prioridad": 80, "descripcion": "Zara moda"},
    {"patron": "h&m",           "categoria": "Compras", "prioridad": 80, "descripcion": "H&M moda"},
    {"patron": "oneclick",      "categoria": "Compras", "prioridad": 70, "descripcion": "Compra OneClick (pago online)"},

    # ──────────────────────────────────────────────
    # SERVICIOS (utilities y telecomunicaciones)
    # ──────────────────────────────────────────────
    {"patron": "entel",         "categoria": "Servicios", "prioridad": 85, "descripcion": "Entel telefonía"},
    {"patron": "movistar",      "categoria": "Servicios", "prioridad": 85, "descripcion": "Movistar telefonía"},
    {"patron": "claro",         "categoria": "Servicios", "prioridad": 85, "descripcion": "Claro telefonía"},
    {"patron": "wom",           "categoria": "Servicios", "prioridad": 85, "descripcion": "WOM telefonía"},
    {"patron": "gtd",           "categoria": "Servicios", "prioridad": 80, "descripcion": "GTD internet/telefonía"},
    {"patron": "vtr",           "categoria": "Servicios", "prioridad": 85, "descripcion": "VTR telecomunicaciones"},
    {"patron": "enel",          "categoria": "Servicios", "prioridad": 85, "descripcion": "Enel electricidad"},
    {"patron": "cge",           "categoria": "Servicios", "prioridad": 80, "descripcion": "CGE electricidad"},
    {"patron": "esval",         "categoria": "Servicios", "prioridad": 80, "descripcion": "ESVAL agua potable"},
    {"patron": "aguas andinas", "categoria": "Servicios", "prioridad": 80, "descripcion": "Aguas Andinas agua potable"},
    {"patron": "metrogas",      "categoria": "Servicios", "prioridad": 80, "descripcion": "Metrogas"},
    {"patron": "abastible",     "categoria": "Servicios", "prioridad": 75, "descripcion": "Abastible gas"},
    {"patron": "lipigas",       "categoria": "Servicios", "prioridad": 75, "descripcion": "Lipigas gas"},
    {"patron": "gasco",         "categoria": "Servicios", "prioridad": 75, "descripcion": "Gasco gas"},
    {"patron": "serv bco",      "categoria": "Servicios", "prioridad": 70, "descripcion": "Servicio bancario"},
    {"patron": "comision",      "categoria": "Servicios", "prioridad": 60, "descripcion": "Comisión bancaria"},
    {"patron": "google play",   "categoria": "Servicios", "prioridad": 75, "descripcion": "Google Play Store"},
    {"patron": "apple store",   "categoria": "Servicios", "prioridad": 75, "descripcion": "Apple App Store"},
    {"patron": "icloud",        "categoria": "Servicios", "prioridad": 75, "descripcion": "iCloud almacenamiento"},
    {"patron": "dropbox",       "categoria": "Servicios", "prioridad": 70, "descripcion": "Dropbox almacenamiento"},
    {"patron": "microsoft 365", "categoria": "Servicios", "prioridad": 75, "descripcion": "Microsoft 365"},
    {"patron": "office 365",    "categoria": "Servicios", "prioridad": 75, "descripcion": "Microsoft Office 365"},
    {"patron": "adobe",         "categoria": "Servicios", "prioridad": 75, "descripcion": "Adobe Creative Cloud"},
    {"patron": "chatgpt",       "categoria": "Servicios", "prioridad": 75, "descripcion": "ChatGPT / OpenAI"},
    {"patron": "openai",        "categoria": "Servicios", "prioridad": 75, "descripcion": "OpenAI"},
    {"patron": "airbnb",        "categoria": "Servicios", "prioridad": 75, "descripcion": "Airbnb alojamiento"},
    {"patron": "transferencia", "categoria": "Servicios", "prioridad": 50, "descripcion": "Transferencia bancaria"},

    # ──────────────────────────────────────────────
    # EDUCACIÓN
    # ──────────────────────────────────────────────
    {"patron": "duolingo",      "categoria": "Educación", "prioridad": 80, "descripcion": "Duolingo idiomas"},
    {"patron": "coursera",      "categoria": "Educación", "prioridad": 80, "descripcion": "Coursera cursos online"},
    {"patron": "udemy",         "categoria": "Educación", "prioridad": 80, "descripcion": "Udemy cursos online"},
    {"patron": "platzi",        "categoria": "Educación", "prioridad": 80, "descripcion": "Platzi cursos online"},
    {"patron": "linkedin learn","categoria": "Educación", "prioridad": 75, "descripcion": "LinkedIn Learning"},
    {"patron": "preuniversitario","categoria": "Educación","prioridad": 80,"descripcion": "Preuniversitario"},
    {"patron": "colegio",       "categoria": "Educación", "prioridad": 75, "descripcion": "Colegio/escuela"},
    {"patron": "universidad",   "categoria": "Educación", "prioridad": 80, "descripcion": "Universidad"},
    {"patron": "kindle",        "categoria": "Educación", "prioridad": 70, "descripcion": "Amazon Kindle libros"},

    # ──────────────────────────────────────────────
    # HOGAR
    # ──────────────────────────────────────────────
    {"patron": "homecenter",    "categoria": "Hogar", "prioridad": 80, "descripcion": "Homecenter (Sodimac)"},
    {"patron": "construmart",   "categoria": "Hogar", "prioridad": 80, "descripcion": "Construmart materiales"},
    {"patron": "ferreter",      "categoria": "Hogar", "prioridad": 70, "descripcion": "Ferretería"},
    {"patron": "maestranza",    "categoria": "Hogar", "prioridad": 70, "descripcion": "Maestranza/ferretería"},
    {"patron": "muebles",       "categoria": "Hogar", "prioridad": 65, "descripcion": "Muebles/decoración"},
    {"patron": "casaideas",     "categoria": "Hogar", "prioridad": 75, "descripcion": "CasaIdeas decoración"},
    {"patron": "casa ideas",    "categoria": "Hogar", "prioridad": 75, "descripcion": "CasaIdeas decoración"},
    {"patron": "multihogar",    "categoria": "Hogar", "prioridad": 70, "descripcion": "Multihogar"},
    {"patron": "sherwin",       "categoria": "Hogar", "prioridad": 70, "descripcion": "Sherwin-Williams pinturas"},
    {"patron": "pinturas",      "categoria": "Hogar", "prioridad": 65, "descripcion": "Pinturas/pinturería"},

    # ──────────────────────────────────────────────
    # VIAJES
    # ──────────────────────────────────────────────
    {"patron": "booking",       "categoria": "Viajes", "prioridad": 85, "descripcion": "Booking.com hotel"},
    {"patron": "despegar",      "categoria": "Viajes", "prioridad": 85, "descripcion": "Despegar.com viajes"},
    {"patron": "trivago",       "categoria": "Viajes", "prioridad": 80, "descripcion": "Trivago hoteles"},
    {"patron": "expedia",       "categoria": "Viajes", "prioridad": 80, "descripcion": "Expedia viajes"},
    {"patron": "hotel",         "categoria": "Viajes", "prioridad": 70, "descripcion": "Hotel/alojamiento"},
    {"patron": "hostal",        "categoria": "Viajes", "prioridad": 70, "descripcion": "Hostal/alojamiento"},
    {"patron": "aeropuerto",    "categoria": "Viajes", "prioridad": 75, "descripcion": "Aeropuerto"},
]
