---
name: security-review
description: Review this repository or application for security risks, especially before publishing it to Git or deploying it. Use when the user asks for a security audit, security review, or security-focused readiness assessment.
metadata:
  short-description: Review repository security
---

# Repon tietoturvakatselmus

Arvioi koodin, asetusten ja julkaistavien tiedostojen tietoturvariskit käyttäjän pyytämässä laajuudessa. Jos käyttäjä valmistelee Git-julkaisua, tarkista sekä sovellus että se, mitä Git voisi ottaa mukaan.

## Rajat

- Tee katselmus oletuksena vain lukemalla. Älä muokkaa, poista, siirrä, alusta tai stagea tiedostoja, kierrätä avaimia, commitoi, pushaa tai kutsu ulkoisia palveluita ilman erillistä käyttäjän pyyntöä.
- Älä aja testejä tai aktiivisia penetraatiotestejä, ellei käyttäjä pyydä niitä. Älä testaa avaimia tekemällä niillä API-kutsuja.
- Lue ensin projektin `AGENTS.md`- ja muut asiaankuuluvat ohjeet. Noudata niiden työkalu-, testi- ja kirjoitusrajoja.
- Erota varmistetut havainnot oletuksista. Älä väitä salaisuuden olevan aktiivinen tai julkisesti vuotanut, ellei sitä ole varmennettu. Tiedostossa oleva avaimen näköinen arvo kannattaa silti käsitellä varovaisesti.

## Salaisuuksien käsittely

- Älä tulosta, lainaa tai sisällytä raporttiin API-avaimia, tokeneita, salasanoja, yksityisiä avaimia tai niiden arvoja.
- Vältä raakaa hakua, joka tulostaa osumarivit salaisuustiedostoista. Rajaa `rg`-haut pois `.env`- ja vastaavista tiedostoista; käytä osumissa tiedostonimiä tai redaktoitua tulostetta.
- Jos tarkistat `.env`-tiedoston, tulosta korkeintaan muuttujan nimi ja arvoluokka (tyhjä, paikkamerkki tai ei-paikkamerkin näköinen). Älä tulosta yhtäläisyysmerkin oikeaa puolta.
- Jos arvo näyttää oikealta salaisuudelta, kerro sijainti ja suosittele avaimen mitätöintiä sekä uusimista. Älä tee kierrätystä käyttäjän puolesta.

## Katselmuksen työjärjestys

1. Selvitä projektin rajat: nykyinen hakemisto, Gitin juuri (`git rev-parse --show-toplevel`), tila ja projektin ohjeet. Git-julkaisua varten tarkista, onko kohde itsenäinen repo vai osa ylempää checkoutia. Älä suorita `git add .` tai vastaavaa laajaa stagea.
2. Tarkista julkaistavat ja paikalliset tiedostot: `.env`, avaimet asetuksissa, yksityiset dokumentit, lokit, tietokannat, arkistot, virtuaaliympäristöt, välimuistit ja generoidut tiedostot. Vertaa niitä `.gitignore`en sekä `git status`- ja tarvittaessa `git ls-files` -tuloksiin.
3. Tutki sovelluksen hyökkäyspinta koodista: kuunteluosoite, CORS, tunnistautuminen, käyttöoikeudet, pyyntöjen rajaus, nopeus- ja kokorajat, tiedostopolut, virheviestit, lokitus sekä mahdolliset injektiot, XSS, SSRF ja vaarallinen serialisointi. Arvioi löydösten vaikutus siinä käyttöympäristössä, johon sovellusta ollaan viemässä.
4. Tunnista tietovirrat: mitä käyttäjä-, asiakas- tai tiedostodataa lähetetään malleille, hakupalveluille, telemetriaan tai muille ulkoisille palveluille. Kuvaa datan vastaanottaja ja riskit koodin perusteella; älä oleta säilytyskäytäntöjä.
5. AI-sovelluksissa tarkista, miten käyttäjän syöte ja haettu sisältö päätyvät promptiin, onko ulkoisella sisällöllä vaikutusta työkaluihin tai arkaluonteisiin tietoihin, ja esitetäänkö automaatio virheellisesti ihmisenä. Älä liioittele prompt-injection-riskiä, jos mallilla ei ole työkaluja tai vaikutusvaltaa.
6. Tarkista riippuvuuksien versiorajat ja lukitustiedostot. Älä kutsu riippuvuutta haavoittuvaksi pelkän versionlukituksen puuttumisen perusteella. Jos raportoit ajankohtaisen CVE:n tai muun muuttuvan haavoittuvuustiedon, varmista se luotettavasta ajantasaisesta lähteestä.
7. Kirjaa rajaukset: mitä tarkistit, mitä et ajanut (esim. testit, riippuvuusskanneri, runtime-testaus) ja mitä ei voitu vahvistaa.

## Tämän projektin tarkistuspisteet

Käytä näitä lähtökohtina ja varmista niiden nykytila joka katselmuksessa:

- `backend/.env`: tarkista vain redaktoidusti; varmista, ettei tiedosto tai muu salaisuuksia sisältävä asetustiedosto päädy Gitin stageen tai julkaisuun.
- `backend/chroma_db/`, `backend/venv/`, `__pycache__/` ja projektin ZIP-arkistot: arvioi, ovatko ne generoitua tai paikallista sisältöä, joka pitäisi jättää pois julkaisusta.
- Projektihakemisto voi sijaita ylemmän `C:\Workspace\Python`-Git-repon sisällä. Varmista todellinen Git-juuri jokaisella kerralla ennen julkaisuneuvoja.
- `backend/main.py`: tarkista API-reitit, CORS ja palvelimen kuunteluasetukset.
- `backend/agent/nodes.py` ja `backend/core/retrieval.py`: seuraa käyttäjän viestin ja haetun sisällön kulkua OpenAI- ja Tavily-kutsuihin sekä mallin promptiin.
- `backend/requirements.txt`: tarkista riippuvuuksien versiorajat ja lukituksen tila.

## Raportin muoto

Aloita kokonaisarviolla ja sillä, voiko kohteen julkaista nykyisellään. Järjestä havainnot vakavuuden mukaan (Kriittinen, Korkea, Kohtalainen, Matala, Huomio). Anna jokaisesta löydöksestä:

- lyhyt otsikko ja vakavuus
- tarkka tiedosto ja rivinumero, jos saatavilla
- havaittu näyttö, käytännön vaikutus ja kohdeympäristö
- konkreettinen suositeltu korjaus

Erota varmistettu Git-tilanne mahdollisesta julkaisuriskistä: esimerkiksi `untracked` ei tarkoita, että tiedosto olisi jo julkaistu, mutta ilman ignore-sääntöä se voi päätyä seuraavaan stageen. Päätä lyhyeen rajauskuvaukseen. Älä muuta tiedostoja katselmuksen yhteydessä.
