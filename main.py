import spacy
from spacy.matcher import Matcher
import docx

# Funcție pentru a citi textul din documentul .docx
def read_docx(file_path):
    doc = docx.Document(file_path)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return "\n".join(text)

# Încarcă modelul de limbaj românesc
nlp = spacy.load("ro_core_news_sm")

# Citește textul din document
file_path = r"C:\Users\andri\OneDrive\Desktop\Proiect.docx"   # Specifică calea către documentul tău Word
text = read_docx(file_path)

# Creează un obiect Matcher
matcher = Matcher(nlp.vocab)

# Definește un pattern pentru a potrivi numere urmate de punct și un cuvânt
patterns = [
    [{"LIKE_NUM": True}, {"IS_PUNCT": True}, {"IS_ALPHA": True}]
]

# Adaugă pattern-urile în Matcher
matcher.add("CULORI", patterns)

# Procesează textul
doc = nlp(text)

# Aplică Matcher-ul pe document
matches = matcher(doc)

# Extrage cuvintele după cifră și punct
culori_extrase = []
for match_id, start, end in matches:
    span = doc[start:end]
    culori_extrase.append(span[-1].text)

# Filtrează rezultatele pentru a elimina duplicatele și a le face distincte
culori_unice = list(set(culori_extrase))

# Afișează culorile extrase
print("Culori extrase:", culori_unice)

