"""
Mappa regioni → province → comuni principali.

Usato dal runner per iterare sulle query di ricerca per ogni zona.
"""

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Provincia:
    nome: str
    sigla: str
    comuni_principali: list[str] = field(default_factory=list)


@dataclass
class Regione:
    nome: str
    slug: str
    province: list[Provincia] = field(default_factory=list)
    comuni_extra: list[str] = field(default_factory=list)


REGIONI: dict[str, Regione] = {
    "marche": Regione(
        nome="Marche",
        slug="marche",
        province=[
            Provincia("Ancona", "AN", ["Ancona", "Senigallia", "Jesi", "Falconara Marittima", "Osimo", "Fabriano"]),
            Provincia("Pesaro-Urbino", "PU", ["Pesaro", "Urbino", "Fano", "Mondolfo", "Fossombrone", "Cagli"]),
            Provincia("Macerata", "MC", ["Macerata", "Civitanova Marche", "Tolentino", "Recanati", "Porto Recanati"]),
            Provincia("Ascoli Piceno", "AP", ["Ascoli Piceno", "San Benedetto del Tronto", "Grottammare", "Offida"]),
            Provincia("Fermo", "FM", ["Fermo", "Porto San Giorgio", "Sant'Elpidio a Mare", "Montegranaro"]),
        ],
    ),
    "emilia-romagna": Regione(
        nome="Emilia-Romagna",
        slug="emilia-romagna",
        province=[
            Provincia("Bologna", "BO", ["Bologna", "Imola", "San Lazzaro di Savena", "Casalecchio di Reno"]),
            Provincia("Modena", "MO", ["Modena", "Carpi", "Sassuolo", "Vignola"]),
            Provincia("Reggio Emilia", "RE", ["Reggio Emilia", "Correggio", "Scandiano"]),
            Provincia("Parma", "PR", ["Parma", "Fidenza", "Salsomaggiore Terme"]),
            Provincia("Rimini", "RN", ["Rimini", "Riccione", "Cattolica", "Misano Adriatico"]),
            Provincia("Forlì-Cesena", "FC", ["Forlì", "Cesena", "Cesenatico"]),
            Provincia("Ravenna", "RA", ["Ravenna", "Faenza", "Lugo"]),
            Provincia("Ferrara", "FE", ["Ferrara", "Comacchio"]),
            Provincia("Piacenza", "PC", ["Piacenza", "Fiorenzuola d'Arda"]),
        ],
    ),
    "lombardia": Regione(
        nome="Lombardia",
        slug="lombardia",
        province=[
            Provincia("Milano", "MI", ["Milano", "Sesto San Giovanni", "Rho", "Legnano", "Monza"]),
            Provincia("Bergamo", "BG", ["Bergamo", "Treviglio", "Dalmine"]),
            Provincia("Brescia", "BS", ["Brescia", "Desenzano del Garda", "Montichiari"]),
            Provincia("Como", "CO", ["Como", "Cantù", "Erba"]),
            Provincia("Varese", "VA", ["Varese", "Busto Arsizio", "Gallarate"]),
            Provincia("Pavia", "PV", ["Pavia", "Vigevano", "Voghera"]),
            Provincia("Mantova", "MN", ["Mantova", "Suzzara", "Castiglione delle Stiviere"]),
            Provincia("Cremona", "CR", ["Cremona", "Crema"]),
            Provincia("Lecco", "LC", ["Lecco", "Merate"]),
            Provincia("Lodi", "LO", ["Lodi", "Codogno"]),
            Provincia("Sondrio", "SO", ["Sondrio", "Morbegno"]),
        ],
    ),
    "lazio": Regione(
        nome="Lazio",
        slug="lazio",
        province=[
            Provincia("Roma", "RM", ["Roma", "Guidonia Montecelio", "Tivoli", "Fiumicino", "Pomezia", "Velletri", "Civitavecchia", "Frascati"]),
            Provincia("Latina", "LT", ["Latina", "Aprilia", "Terracina", "Formia", "Gaeta"]),
            Provincia("Frosinone", "FR", ["Frosinone", "Cassino", "Alatri", "Sora"]),
            Provincia("Viterbo", "VT", ["Viterbo", "Civita Castellana", "Tarquinia"]),
            Provincia("Rieti", "RI", ["Rieti", "Poggio Mirteto"]),
        ],
    ),
    "toscana": Regione(
        nome="Toscana",
        slug="toscana",
        province=[
            Provincia("Firenze", "FI", ["Firenze", "Scandicci", "Empoli", "Sesto Fiorentino"]),
            Provincia("Pisa", "PI", ["Pisa", "Cascina", "San Giuliano Terme", "Pontedera"]),
            Provincia("Livorno", "LI", ["Livorno", "Piombino", "Cecina", "Rosignano Marittimo"]),
            Provincia("Lucca", "LU", ["Lucca", "Viareggio", "Capannori", "Pietrasanta"]),
            Provincia("Arezzo", "AR", ["Arezzo", "Montevarchi", "San Giovanni Valdarno"]),
            Provincia("Siena", "SI", ["Siena", "Poggibonsi", "Colle di Val d'Elsa"]),
            Provincia("Grosseto", "GR", ["Grosseto", "Follonica", "Orbetello"]),
            Provincia("Prato", "PO", ["Prato", "Montemurlo"]),
            Provincia("Pistoia", "PT", ["Pistoia", "Montecatini Terme", "Pescia"]),
            Provincia("Massa-Carrara", "MS", ["Massa", "Carrara"]),
        ],
    ),
    "abruzzo": Regione(
        nome="Abruzzo",
        slug="abruzzo",
        province=[
            Provincia("Chieti", "CH", ["Chieti", "Lanciano", "Vasto", "Ortona"]),
            Provincia("L'Aquila", "AQ", ["L'Aquila", "Avezzano", "Sulmona", "Celano"]),
            Provincia("Pescara", "PE", ["Pescara", "Montesilvano", "Spoltore", "Città Sant'Angelo"]),
            Provincia("Teramo", "TE", ["Teramo", "Roseto degli Abruzzi", "Giulianova", "Atri"]),
        ],
    ),
    "basilicata": Regione(
        nome="Basilicata",
        slug="basilicata",
        province=[
            Provincia("Potenza", "PZ", ["Potenza", "Melfi", "Lagonegro", "Venosa"]),
            Provincia("Matera", "MT", ["Matera", "Pisticci", "Policoro", "Bernalda"]),
        ],
    ),
    "calabria": Regione(
        nome="Calabria",
        slug="calabria",
        province=[
            Provincia("Catanzaro", "CZ", ["Catanzaro", "Lamezia Terme", "Soverato"]),
            Provincia("Cosenza", "CS", ["Cosenza", "Rende", "Corigliano-Rossano", "Castrovillari"]),
            Provincia("Reggio Calabria", "RC", ["Reggio Calabria", "Palmi", "Siderno", "Locri"]),
            Provincia("Crotone", "KR", ["Crotone", "Cirò Marina", "Isola Capo Rizzuto"]),
            Provincia("Vibo Valentia", "VV", ["Vibo Valentia", "Tropea", "Pizzo"]),
        ],
    ),
    "campania": Regione(
        nome="Campania",
        slug="campania",
        province=[
            Provincia("Napoli", "NA", ["Napoli", "Pozzuoli", "Casoria", "Torre del Greco", "Giugliano in Campania", "Afragola"]),
            Provincia("Salerno", "SA", ["Salerno", "Battipaglia", "Cava de' Tirreni", "Nocera Inferiore", "Eboli"]),
            Provincia("Avellino", "AV", ["Avellino", "Ariano Irpino", "Mercogliano"]),
            Provincia("Benevento", "BN", ["Benevento", "Montesarchio", "Sant'Agata de' Goti"]),
            Provincia("Caserta", "CE", ["Caserta", "Aversa", "Marcianise", "Maddaloni", "Santa Maria Capua Vetere"]),
        ],
    ),
    "friuli-venezia-giulia": Regione(
        nome="Friuli-Venezia Giulia",
        slug="friuli-venezia-giulia",
        province=[
            Provincia("Trieste", "TS", ["Trieste", "Muggia"]),
            Provincia("Udine", "UD", ["Udine", "Codroipo", "Tavagnacco", "Cervignano del Friuli"]),
            Provincia("Pordenone", "PN", ["Pordenone", "Sacile", "San Vito al Tagliamento"]),
            Provincia("Gorizia", "GO", ["Gorizia", "Monfalcone", "Grado"]),
        ],
    ),
    "liguria": Regione(
        nome="Liguria",
        slug="liguria",
        province=[
            Provincia("Genova", "GE", ["Genova", "Rapallo", "Chiavari", "Sestri Levante"]),
            Provincia("Savona", "SV", ["Savona", "Albenga", "Varazze", "Finale Ligure"]),
            Provincia("Imperia", "IM", ["Imperia", "Sanremo", "Ventimiglia", "Bordighera"]),
            Provincia("La Spezia", "SP", ["La Spezia", "Sarzana", "Lerici"]),
        ],
    ),
    "molise": Regione(
        nome="Molise",
        slug="molise",
        province=[
            Provincia("Campobasso", "CB", ["Campobasso", "Termoli", "Bojano"]),
            Provincia("Isernia", "IS", ["Isernia", "Venafro", "Agnone"]),
        ],
    ),
    "piemonte": Regione(
        nome="Piemonte",
        slug="piemonte",
        province=[
            Provincia("Torino", "TO", ["Torino", "Moncalieri", "Rivoli", "Settimo Torinese", "Collegno", "Pinerolo"]),
            Provincia("Cuneo", "CN", ["Cuneo", "Alba", "Bra", "Savigliano", "Mondovì"]),
            Provincia("Alessandria", "AL", ["Alessandria", "Casale Monferrato", "Novi Ligure", "Tortona"]),
            Provincia("Asti", "AT", ["Asti", "Nizza Monferrato", "Canelli"]),
            Provincia("Novara", "NO", ["Novara", "Borgomanero", "Trecate"]),
            Provincia("Biella", "BI", ["Biella", "Cossato"]),
            Provincia("Verbano-Cusio-Ossola", "VB", ["Verbania", "Domodossola", "Omegna"]),
            Provincia("Vercelli", "VC", ["Vercelli", "Santhià", "Borgosesia"]),
        ],
    ),
    "puglia": Regione(
        nome="Puglia",
        slug="puglia",
        province=[
            Provincia("Bari", "BA", ["Bari", "Altamura", "Bitonto", "Molfetta", "Monopoli", "Corato"]),
            Provincia("Lecce", "LE", ["Lecce", "Nardò", "Galatina", "Gallipoli", "Otranto"]),
            Provincia("Taranto", "TA", ["Taranto", "Martina Franca", "Grottaglie", "Massafra"]),
            Provincia("Foggia", "FG", ["Foggia", "San Severo", "Manfredonia", "Cerignola", "Lucera"]),
            Provincia("Brindisi", "BR", ["Brindisi", "Fasano", "Ostuni", "Francavilla Fontana"]),
            Provincia("Barletta-Andria-Trani", "BT", ["Andria", "Barletta", "Trani", "Bisceglie"]),
        ],
    ),
    "sardegna": Regione(
        nome="Sardegna",
        slug="sardegna",
        province=[
            Provincia("Cagliari", "CA", ["Cagliari", "Quartu Sant'Elena", "Selargius", "Assemini"]),
            Provincia("Sassari", "SS", ["Sassari", "Alghero", "Porto Torres", "Olbia"]),
            Provincia("Nuoro", "NU", ["Nuoro", "Siniscola", "Tortolì"]),
            Provincia("Oristano", "OR", ["Oristano", "Terralba", "Cabras", "Bosa"]),
            Provincia("Sud Sardegna", "SU", ["Carbonia", "Iglesias", "Villacidro", "Sant'Antioco"]),
        ],
    ),
    "sicilia": Regione(
        nome="Sicilia",
        slug="sicilia",
        province=[
            Provincia("Palermo", "PA", ["Palermo", "Bagheria", "Monreale", "Partinico", "Cefalù"]),
            Provincia("Catania", "CT", ["Catania", "Acireale", "Paternò", "Caltagirone", "Misterbianco"]),
            Provincia("Messina", "ME", ["Messina", "Barcellona Pozzo di Gotto", "Milazzo", "Taormina"]),
            Provincia("Siracusa", "SR", ["Siracusa", "Augusta", "Noto", "Avola"]),
            Provincia("Trapani", "TP", ["Trapani", "Marsala", "Mazara del Vallo", "Alcamo"]),
            Provincia("Ragusa", "RG", ["Ragusa", "Vittoria", "Modica", "Comiso"]),
            Provincia("Agrigento", "AG", ["Agrigento", "Sciacca", "Licata", "Canicattì"]),
            Provincia("Caltanissetta", "CL", ["Caltanissetta", "Gela", "Niscemi", "San Cataldo"]),
            Provincia("Enna", "EN", ["Enna", "Piazza Armerina", "Troina"]),
        ],
    ),
    "trentino-alto-adige": Regione(
        nome="Trentino-Alto Adige",
        slug="trentino-alto-adige",
        province=[
            Provincia("Trento", "TN", ["Trento", "Rovereto", "Pergine Valsugana", "Riva del Garda"]),
            Provincia("Bolzano", "BZ", ["Bolzano", "Merano", "Bressanone", "Brunico", "Laives"]),
        ],
    ),
    "umbria": Regione(
        nome="Umbria",
        slug="umbria",
        province=[
            Provincia("Perugia", "PG", ["Perugia", "Foligno", "Città di Castello", "Spoleto", "Assisi"]),
            Provincia("Terni", "TR", ["Terni", "Orvieto", "Narni", "Amelia"]),
        ],
    ),
    "valle-d-aosta": Regione(
        nome="Valle d'Aosta",
        slug="valle-d-aosta",
        province=[
            Provincia("Aosta", "AO", ["Aosta", "Sarre", "Saint-Christophe", "Chatillon"]),
        ],
        comuni_extra=["Courmayeur", "La Salle", "Morgex"],
    ),
    "veneto": Regione(
        nome="Veneto",
        slug="veneto",
        province=[
            Provincia("Venezia", "VE", ["Venezia", "Mestre", "Chioggia", "San Donà di Piave", "Jesolo"]),
            Provincia("Padova", "PD", ["Padova", "Abano Terme", "Monselice", "Cittadella"]),
            Provincia("Verona", "VR", ["Verona", "Legnago", "San Bonifacio", "Villafranca di Verona"]),
            Provincia("Vicenza", "VI", ["Vicenza", "Bassano del Grappa", "Schio", "Thiene"]),
            Provincia("Treviso", "TV", ["Treviso", "Conegliano", "Montebelluna", "Castelfranco Veneto"]),
            Provincia("Rovigo", "RO", ["Rovigo", "Adria", "Porto Viro", "Lendinara"]),
            Provincia("Belluno", "BL", ["Belluno", "Feltre", "Cortina d'Ampezzo", "Sedico"]),
        ],
    ),
}


def get_comuni_for_regione(regione_slug: str) -> list[str]:
    """Restituisce tutti i comuni principali di una regione."""
    regione = REGIONI.get(regione_slug.lower())
    if not regione:
        # Fallback: solo il nome regione
        return [regione_slug]
    comuni: list[str] = list(regione.comuni_extra)
    for prov in regione.province:
        comuni.extend(prov.comuni_principali)
    return comuni


def get_tutte_le_regioni() -> list[str]:
    return list(REGIONI.keys())


def get_sigla_to_nome_provincia() -> dict[str, str]:
    """Restituisce mappa sigla → nome provincia da tutte le regioni."""
    result: dict[str, str] = {}
    for regione in REGIONI.values():
        for prov in regione.province:
            result[prov.sigla] = prov.nome
    return result
