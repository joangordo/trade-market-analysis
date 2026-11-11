# Guia per publicar i presentar aquest projecte

> Aquest fitxer és per a tu, Joan — no forma part del projecte públic. Esborra'l
> abans de pujar-ho, o deixa'l si vols (està en català i no molesta). Conté els
> passos per publicar-ho a GitHub i com presentar-ho en una entrevista.

---

## 1. Passos per pujar-ho a GitHub

Des de la carpeta del projecte, al teu ordinador:

```bash
cd trade-market-analysis

# Inicialitza el repositori
git init
git add .
git commit -m "Market opportunity scoring for ES-CN imports (Eurostat data)"

# Crea el repo a github.com (botó New repository, nom: trade-market-analysis,
# públic, SENSE inicialitzar amb README perquè ja en tens un)

# Connecta i puja (substitueix USUARI pel teu usuari de GitHub)
git remote add origin https://github.com/USUARI/trade-market-analysis.git
git branch -M main
git push -u origin main
```

Un cop pujat, comprova que:
- El README es veu bé a la pàgina principal (GitHub el renderitza sol).
- La pestanya **Actions** mostra el workflow de tests en verd (✓). Això passa
  automàticament al primer push i queda molt professional.
- El notebook es visualitza amb els gràfics (GitHub els renderitza).

## 2. Abans de pujar: substitueix els gràfics per dades reals

Els gràfics d'`outputs/` ara són de la demo sintètica. Per a màxim impacte,
regenera'ls amb les dades reals d'Eurostat (ja vas comprovar que la connexió
funciona):

```bash
cd src
python run_analysis.py --source eurostat --reporter ES --partner CN
```

Això sobreescriu `outputs/` amb els gràfics reals. El README ja cita les
troballes reals (bicicletes com a fals positiu, marroquineria, vaixella), així
que tot quadrarà.

## 3. Petits retocs que apugen el nivell

- **Fixa el teu nom a la llicència:** ja hi és (Joan Gordó Guardia), revisa-ho.
- **Afegeix topics al repo** (a la pàgina de GitHub, roda dentada "About"):
  `data-science`, `pandas`, `eurostat`, `trade-data`, `market-analysis`,
  `python`. Ajuden que et trobin.
- **Descripció curta del repo:** "Data-driven import opportunity scoring from
  official EU trade data (Eurostat). Full pipeline: API ingestion, feature
  engineering, scoring, tests."
- **Fixa el repo** al teu perfil (Pin) perquè surti el primer.

## 4. Com presentar-ho en una entrevista (el que de debò importa)

Aquest projecte és fort perquè explica una **història completa**, no només codi.
Quan te'l preguntin, estructura-ho així:

**El problema (15 segons).** "Volia entendre quins productes tenia sentit
importar de la Xina a Espanya. En comptes de decidir per intuïció, vaig tractar
la tria de sector com un problema de dades."

**L'enfocament (30 segons).** "Vaig connectar l'API oficial d'Eurostat, vaig
construir quatre indicadors per categoria — creixement, mida de mercat,
momentum i preu unitari com a proxy de marge — i els vaig combinar en una
puntuació configurable que ordena les oportunitats."

**La part que impressiona — pensament crític.** "El més interessant va ser
descobrir que el primer del rànquing, les bicicletes, era un fals positiu: un
mercat d'un milió d'euros amb un creixement que era soroll estadístic sobre una
base minúscula. Això em va fer afegir la idea que el criteri humà va **sobre** el
model, no sota — i és exactament la mena de judici que distingeix un analista
d'un script."

**L'enginyeria.** "Vaig trobar dos bugs reals de l'API: l'endpoint correcte dels
datasets de comerç i el nom de la mesura de quantitat, que retornava buit i feia
petar un gràfic. El pipeline ara degrada amb elegància si falten dades, i tot
està cobert per tests amb CI a GitHub Actions."

### Les competències que demostra (digues-les si pots)

- **Ingesta de dades reals via API** (no un CSV de Kaggle): JSON-stat, paginació,
  gestió d'errors HTTP.
- **Feature engineering** amb sentit de negoci (CAGR, momentum, preu unitari).
- **Codi net i modular**: separació clara de responsabilitats, docstrings.
- **Rigor d'enginyeria**: tests unitaris, CI, maneig de casos límit.
- **Pensament crític**: detectar falsos positius, no fiar-se cegament del número.
- **Comunicació**: el README converteix l'anàlisi en una història llegible.

## 5. Una millora opcional d'alt impacte (si tens temps)

Si vols que destaqui encara més, la millora més valuosa seria **afegir preus de
venda reals a Espanya** per estimar el marge per sector (ara el projecte té el
preu d'importació, però no el de venda). Això el convertiria d'"anàlisi de
mercat" en "anàlisi de rendibilitat", que és molt més potent. No cal per
publicar-lo; és per a una segona versió.

---

**Resum:** tens un projecte que cobreix el cicle complet de data science amb
dades reals, rigor d'enginyeria i, sobretot, una història de pensament crític.
És material sòlid per a una entrevista de Data Scientist.
