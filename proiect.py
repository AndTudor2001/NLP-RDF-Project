import spacy
from spacy.matcher import Matcher
from docx import Document
from rdflib import Graph, Literal, RDF, URIRef, Namespace
import requests

# Încarcă modelul SpaCy
nlp = spacy.load("ro_core_news_sm")

# Funcția pentru a citi textul dintr-un document Word
def read_word_file(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

# Citește textul din documentul Word
file_path = r"C:\Users\andri\OneDrive\Desktop\Proiect.docx"  # Specifică calea către documentul tău Word
text = read_word_file(file_path)

# Procesarea textului
doc = nlp(text)

# Crearea unui matcher
matcher = Matcher(nlp.vocab)

# Definirea sabloanelor pentru matcher
wood_patterns = [
    [{"LEMMA": {"IN": ["brad", "cedru", "pin", "brad alb", "ienupar", "tei", "plop tremurator", "plop simplu", "salcie", "arina", "castan",
                       "fag", "mesteacan", "stejar", "ulm", "platan", "artar", "scorus", "nuc grecesc", "frasin", "mar",
                       "salcam alb", "carpen", "corn", "fistic", "tisa", "cires", "mahon"]}}]
]

material_patterns = [
    [{"TEXT": {"IN": ["metal", "sticla", "plastic", "piele", "bambus", "ratan", "marmură", "granite", "fibră de sticlă"]}}]
]

color_patterns = [
    [{"LIKE_NUM": True}, {"IS_PUNCT": True}, {"IS_ALPHA": True}]
]

matcher.add("WOOD_PATTERN", wood_patterns)
matcher.add("MATERIAL_PATTERN", material_patterns)
matcher.add("COLOR_PATTERN", color_patterns)

# Apelarea matcher-ului pe document
matches = matcher(doc)

# Extragem și catalogăm entitățile
wood_list = []
material_list = []
color_list = []

for match_id, start, end in matches:
    span = doc[start:end]
    match_label = nlp.vocab.strings[match_id]
    if match_label == "WOOD_PATTERN":
        wood_list.append(span.text.strip())
    elif match_label == "MATERIAL_PATTERN":
        material_list.append(span.text.strip())
    elif match_label == "COLOR_PATTERN":
        color_list.append(span[-1].text.strip())

# Eliminăm duplicatele și sortăm rezultatele
wood_list = sorted(set(wood_list))
material_list = sorted(set(material_list))
color_list = sorted(set(color_list))

# Crearea unui grafic RDF
g = Graph()
n = Namespace("http://proiect.com/")

# Adăugarea triplelor în graf
for wood in wood_list:
    wood_uri = URIRef(n[wood.replace(" ", "_")])
    g.add((wood_uri, RDF.type, n.Wood))
    g.add((wood_uri, n.name, Literal(wood)))

for material in material_list:
    material_uri = URIRef(n[material.replace(" ", "_")])
    g.add((material_uri, RDF.type, n.Material))
    g.add((material_uri, n.name, Literal(material)))

for color in color_list:
    color_uri = URIRef(n[color.replace(" ", "_")])
    g.add((color_uri, RDF.type, n.Color))
    g.add((color_uri, n.name, Literal(color)))

# Conectarea la GraphDB și încărcarea datelor RDF în graful specificat
graph_name = "<http://proiect.com/ExtragereDocument>"  # Specifică URI-ul grafului între paranteze unghiulare
endpoint_url = f"http://TUDOR:7200/repositories/Proiect/statements?context={graph_name}"  # Specifică URL-ul endpoint-ului tău SPARQL
username = "admin"  # Specifică numele de utilizator pentru GraphDB
password = "password"  # Specifică parola pentru GraphDB

headers = {
    "Content-Type": "application/x-turtle",
    "Accept": "application/sparql-results+json"
}

rdf_data = g.serialize(format="turtle")

# Inserarea datelor RDF în GraphDB
response = requests.post(endpoint_url, data=rdf_data, headers=headers, auth=(username, password))

if response.status_code == 204:
    print("Graficul RDF a fost încărcat în GraphDB")
else:
    print(f"Încărcarea a eșuat cu status code {response.status_code}")
    print(response.text)

# Funcția pentru a citi date din GraphDB
def query_graphdb(sparql_query):
    sparql_endpoint = "http://TUDOR:7200/repositories/Proiect"  # URL-ul endpoint-ului SPARQL pentru interogare
    response = requests.get(sparql_endpoint, params={'query': sparql_query}, headers={'Accept': 'application/sparql-results+json'}, auth=(username, password))
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Interogarea a eșuat cu status code {response.status_code}")
        print(response.text)
        return None

# Interogare pentru a citi datele din graful "Materiale"
sparql_query = """
SELECT ?subject ?predicate ?object
WHERE {
    GRAPH <http://proiect.com/ExtragereDocument> {
        ?subject ?predicate ?object.
    }
}
LIMIT 10
"""

result = query_graphdb(sparql_query)
if result:
    for binding in result['results']['bindings']:
        subject = binding['subject']['value']
        predicate = binding['predicate']['value']
        object_ = binding['object']['value']
        print(f"{subject} {predicate} {object_}")

# Funcție pentru inserarea unei triple suplimentare manual
def insert_triple(subject, predicate, object_):
    insert_query = f"""
    PREFIX ns: <http://proiect.com/>

    INSERT DATA {{
        GRAPH {graph_name} {{
            ns:{subject} ns:{predicate} "{object_}" .
        }}
    }}
    """
    response = requests.post(endpoint_url, data=insert_query, headers={'Content-Type': 'application/sparql-update'}, auth=(username, password))
    if response.status_code == 204:
        print("Triplă inserată cu succes în GraphDB")
    else:
        print(f"Încărcarea triplei a eșuat cu status code {response.status_code}")
        print(response.text)

# Inserarea unei triple suplimentare
insert_triple("PVC", "name", "PVC")
