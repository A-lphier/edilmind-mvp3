"""
Database completo province italiane con coordinate
"""

PROVINCE_ITALIANE = {
    # Abruzzo
    "L'Aquila": {"regione": "Abruzzo", "lat": 42.3498, "lon": 13.3995},
    "Teramo": {"regione": "Abruzzo", "lat": 42.6589, "lon": 13.7036},
    "Pescara": {"regione": "Abruzzo", "lat": 42.4618, "lon": 14.2154},
    "Chieti": {"regione": "Abruzzo", "lat": 42.3517, "lon": 14.1678},
    
    # Basilicata
    "Potenza": {"regione": "Basilicata", "lat": 40.6389, "lon": 15.7989},
    "Matera": {"regione": "Basilicata", "lat": 40.6663, "lon": 16.6043},
    
    # Calabria
    "Catanzaro": {"regione": "Calabria", "lat": 38.9097, "lon": 16.5877},
    "Cosenza": {"regione": "Calabria", "lat": 39.2979, "lon": 16.2520},
    "Crotone": {"regione": "Calabria", "lat": 39.0808, "lon": 17.1252},
    "Reggio Calabria": {"regione": "Calabria", "lat": 38.1080, "lon": 15.6435},
    "Vibo Valentia": {"regione": "Calabria", "lat": 38.6750, "lon": 16.1000},
    
    # Campania
    "Napoli": {"regione": "Campania", "lat": 40.8518, "lon": 14.2681},
    "Salerno": {"regione": "Campania", "lat": 40.6824, "lon": 14.7681},
    "Avellino": {"regione": "Campania", "lat": 40.9147, "lon": 14.7906},
    "Benevento": {"regione": "Campania", "lat": 41.1297, "lon": 14.7824},
    "Caserta": {"regione": "Campania", "lat": 41.0732, "lon": 14.3327},
    
    # Emilia-Romagna
    "Bologna": {"regione": "Emilia-Romagna", "lat": 44.4949, "lon": 11.3426},
    "Ferrara": {"regione": "Emilia-Romagna", "lat": 44.8381, "lon": 11.6198},
    "Forlì-Cesena": {"regione": "Emilia-Romagna", "lat": 44.2226, "lon": 12.0408},
    "Modena": {"regione": "Emilia-Romagna", "lat": 44.6471, "lon": 10.9252},
    "Parma": {"regione": "Emilia-Romagna", "lat": 44.8015, "lon": 10.3279},
    "Piacenza": {"regione": "Emilia-Romagna", "lat": 45.0526, "lon": 9.6924},
    "Ravenna": {"regione": "Emilia-Romagna", "lat": 44.4184, "lon": 12.2035},
    "Reggio Emilia": {"regione": "Emilia-Romagna", "lat": 44.6989, "lon": 10.6297},
    "Rimini": {"regione": "Emilia-Romagna", "lat": 44.0678, "lon": 12.5695},
    
    # Friuli-Venezia Giulia
    "Trieste": {"regione": "Friuli-Venezia Giulia", "lat": 45.6495, "lon": 13.7768},
    "Udine": {"regione": "Friuli-Venezia Giulia", "lat": 46.0710, "lon": 13.2346},
    "Pordenone": {"regione": "Friuli-Venezia Giulia", "lat": 45.9636, "lon": 12.6611},
    "Gorizia": {"regione": "Friuli-Venezia Giulia", "lat": 45.9410, "lon": 13.6222},
    
    # Lazio
    "Roma": {"regione": "Lazio", "lat": 41.9028, "lon": 12.4964},
    "Frosinone": {"regione": "Lazio", "lat": 41.6396, "lon": 13.3508},
    "Latina": {"regione": "Lazio", "lat": 41.4677, "lon": 12.9035},
    "Rieti": {"regione": "Lazio", "lat": 42.4049, "lon": 12.8623},
    "Viterbo": {"regione": "Lazio", "lat": 42.4174, "lon": 12.1084},
    
    # Liguria
    "Genova": {"regione": "Liguria", "lat": 44.4056, "lon": 8.9463},
    "Imperia": {"regione": "Liguria", "lat": 43.8879, "lon": 8.0271},
    "La Spezia": {"regione": "Liguria", "lat": 44.1024, "lon": 9.8246},
    "Savona": {"regione": "Liguria", "lat": 44.3084, "lon": 8.4812},
    
    # Lombardia
    "Milano": {"regione": "Lombardia", "lat": 45.4642, "lon": 9.1900},
    "Bergamo": {"regione": "Lombardia", "lat": 45.6983, "lon": 9.6773},
    "Brescia": {"regione": "Lombardia", "lat": 45.5416, "lon": 10.2118},
    "Como": {"regione": "Lombardia", "lat": 45.8081, "lon": 9.0852},
    "Cremona": {"regione": "Lombardia", "lat": 45.1333, "lon": 10.0224},
    "Lecco": {"regione": "Lombardia", "lat": 45.8563, "lon": 9.3930},
    "Lodi": {"regione": "Lombardia", "lat": 45.3142, "lon": 9.5035},
    "Mantova": {"regione": "Lombardia", "lat": 45.1564, "lon": 10.7914},
    "Monza e Brianza": {"regione": "Lombardia", "lat": 45.5845, "lon": 9.2744},
    "Pavia": {"regione": "Lombardia", "lat": 45.1847, "lon": 9.1582},
    "Sondrio": {"regione": "Lombardia", "lat": 46.1699, "lon": 9.8782},
    "Varese": {"regione": "Lombardia", "lat": 45.8205, "lon": 8.8250},
    
    # Marche
    "Ancona": {"regione": "Marche", "lat": 43.6158, "lon": 13.5189},
    "Ascoli Piceno": {"regione": "Marche", "lat": 42.8534, "lon": 13.5759},
    "Fermo": {"regione": "Marche", "lat": 43.1605, "lon": 13.7185},
    "Macerata": {"regione": "Marche", "lat": 43.2999, "lon": 13.4532},
    "Pesaro e Urbino": {"regione": "Marche", "lat": 43.9103, "lon": 12.9131},
    
    # Molise
    "Campobasso": {"regione": "Molise", "lat": 41.5630, "lon": 14.6561},
    "Isernia": {"regione": "Molise", "lat": 41.5890, "lon": 14.2335},
    
    # Piemonte
    "Torino": {"regione": "Piemonte", "lat": 45.0703, "lon": 7.6869},
    "Alessandria": {"regione": "Piemonte", "lat": 44.9132, "lon": 8.6151},
    "Asti": {"regione": "Piemonte", "lat": 44.9008, "lon": 8.2061},
    "Biella": {"regione": "Piemonte", "lat": 45.5629, "lon": 8.0580},
    "Cuneo": {"regione": "Piemonte", "lat": 44.3841, "lon": 7.5418},
    "Novara": {"regione": "Piemonte", "lat": 45.4469, "lon": 8.6218},
    "Verbano-Cusio-Ossola": {"regione": "Piemonte", "lat": 45.9217, "lon": 8.5513},
    "Vercelli": {"regione": "Piemonte", "lat": 45.3206, "lon": 8.4186},
    
    # Puglia
    "Bari": {"regione": "Puglia", "lat": 41.1171, "lon": 16.8719},
    "Barletta-Andria-Trani": {"regione": "Puglia", "lat": 41.3167, "lon": 16.2833},
    "Brindisi": {"regione": "Puglia", "lat": 40.6383, "lon": 17.9467},
    "Foggia": {"regione": "Puglia", "lat": 41.4621, "lon": 15.5446},
    "Lecce": {"regione": "Puglia", "lat": 40.3515, "lon": 18.1750},
    "Taranto": {"regione": "Puglia", "lat": 40.4668, "lon": 17.2472},
    
    # Sardegna
    "Cagliari": {"regione": "Sardegna", "lat": 39.2238, "lon": 9.1217},
    "Nuoro": {"regione": "Sardegna", "lat": 40.3211, "lon": 9.3303},
    "Oristano": {"regione": "Sardegna", "lat": 39.9059, "lon": 8.5914},
    "Sassari": {"regione": "Sardegna", "lat": 40.7259, "lon": 8.5598},
    "Sud Sardegna": {"regione": "Sardegna", "lat": 39.1652, "lon": 8.5611},
    
    # Sicilia
    "Palermo": {"regione": "Sicilia", "lat": 38.1157, "lon": 13.3615},
    "Agrigento": {"regione": "Sicilia", "lat": 37.3113, "lon": 13.5765},
    "Caltanissetta": {"regione": "Sicilia", "lat": 37.4907, "lon": 14.0625},
    "Catania": {"regione": "Sicilia", "lat": 37.5079, "lon": 15.0830},
    "Enna": {"regione": "Sicilia", "lat": 37.5671, "lon": 14.2792},
    "Messina": {"regione": "Sicilia", "lat": 38.1938, "lon": 15.5540},
    "Ragusa": {"regione": "Sicilia", "lat": 36.9268, "lon": 14.7258},
    "Siracusa": {"regione": "Sicilia", "lat": 37.0755, "lon": 15.2866},
    "Trapani": {"regione": "Sicilia", "lat": 38.0176, "lon": 12.5365},
    
    # Toscana
    "Firenze": {"regione": "Toscana", "lat": 43.7696, "lon": 11.2558},
    "Arezzo": {"regione": "Toscana", "lat": 43.4632, "lon": 11.8796},
    "Grosseto": {"regione": "Toscana", "lat": 42.7634, "lon": 11.1138},
    "Livorno": {"regione": "Toscana", "lat": 43.5485, "lon": 10.3106},
    "Lucca": {"regione": "Toscana", "lat": 43.8376, "lon": 10.4950},
    "Massa-Carrara": {"regione": "Toscana", "lat": 44.0366, "lon": 10.1414},
    "Pisa": {"regione": "Toscana", "lat": 43.7228, "lon": 10.4017},
    "Pistoia": {"regione": "Toscana", "lat": 43.9330, "lon": 10.9176},
    "Prato": {"regione": "Toscana", "lat": 43.8777, "lon": 11.1023},
    "Siena": {"regione": "Toscana", "lat": 43.3188, "lon": 11.3308},
    
    # Trentino-Alto Adige
    "Trento": {"regione": "Trentino-Alto Adige", "lat": 46.0664, "lon": 11.1257},
    "Bolzano": {"regione": "Trentino-Alto Adige", "lat": 46.4983, "lon": 11.3548},
    
    # Umbria
    "Perugia": {"regione": "Umbria", "lat": 43.1107, "lon": 12.3908},
    "Terni": {"regione": "Umbria", "lat": 42.5635, "lon": 12.6450},
    
    # Valle d'Aosta
    "Aosta": {"regione": "Valle d'Aosta", "lat": 45.7372, "lon": 7.3206},
    
    # Veneto
    "Venezia": {"regione": "Veneto", "lat": 45.4408, "lon": 12.3155},
    "Belluno": {"regione": "Veneto", "lat": 46.1386, "lon": 12.2166},
    "Padova": {"regione": "Veneto", "lat": 45.4064, "lon": 11.8768},
    "Rovigo": {"regione": "Veneto", "lat": 45.0708, "lon": 11.7903},
    "Treviso": {"regione": "Veneto", "lat": 45.6669, "lon": 12.2430},
    "Verona": {"regione": "Veneto", "lat": 45.4384, "lon": 10.9916},
    "Vicenza": {"regione": "Veneto", "lat": 45.5476, "lon": 11.5448},
}

def get_provincia_coords(provincia: str):
    """Ottieni coordinate di una provincia"""
    return PROVINCE_ITALIANE.get(provincia)

def get_province_by_regione(regione: str):
    """Ottieni tutte le province di una regione"""
    return {k: v for k, v in PROVINCE_ITALIANE.items() if v['regione'] == regione}