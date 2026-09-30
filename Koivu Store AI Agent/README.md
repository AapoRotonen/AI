# Koivu Store AI Agent

Suomenkielinen vaatekaupan käyttöliittymä ja LangGraph-pohjainen AI-asiakaspalvelun demo. Tuotekatalogissa on haku, suodatus, lajittelu, suosikit ja ostoskorin käyttöliittymä.

## Ominaisuudet ja rajat

- Agentti hakee ensin paikallisesta Chroma-tuotekatalogista ja arvioi, riittääkö tieto vastaukseen. Muussa tapauksessa se voi hakea Tavilyllä tai eskaloida Maija-demolle. Reititys on toteutettu LangGraphin nodeilla ja ehdollisilla edgeillä.
- Maija on eri ohjeistuksella toimiva AI-simulaatio, ei oikea ihminen.
- Ostoskori, suosikit, suodattimet ja kassapainike ovat käyttöliittymädemoa. Oikeaa maksua, tilausten käsittelyä, varastonhallintaa tai asiakastilejä ei ole.
- Keskustelua ei tallenneta sovelluksen omaan pysyvään tietokantaan. Kysymykset ja keskusteluhistoria lähetetään OpenAI API:lle. Tavily saa kysymyksen vain, jos agentti etenee verkkohakuun. Lue [tietosuojatiedot](PRIVACY.md) ennen kokeilua.
- Esimerkkituotteet ovat tiedostoissa `frontend/store.js` ja `backend/data/products.txt`; pidä ne synkronoituina.

## Paikallinen käynnistys

Käynnistämiseen tarvitset Pythonin. Node.js tarvitaan vain valinnaiseen JavaScript-syntaksitarkistukseen. Backend tarvitsee OpenAI API-avaimen; Tavily-avain on valinnainen ja mahdollistaa verkkohakuhaaran. API-kutsut voivat aiheuttaa palveluntarjoajien veloituksia.

Luo virtuaaliympäristö ja asenna paketit:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Lisää omat avaimet `backend/.env`-tiedostoon. Tiedosto on tarkoitettu vain paikalliseen käyttöön eikä sitä saa commitoida. Käynnistä backend:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Avaa toisessa PowerShell-ikkunassa projektin juuresta:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Avaa `http://127.0.0.1:5500/`. Backendin terveystarkistus löytyy osoitteesta `http://127.0.0.1:8000/health`.

## Julkaisu ja tietoturva

Tämä on paikallinen demo, ei sellaisenaan julkiseen tuotantoon valmis verkkokauppa. API:ssa ei ole kirjautumista tai palvelintason nopeusrajoitusta. Ennen backendin julkaisemista internetiin lisää käyttöympäristön reunapalveluun nopeus- ja pyyntökokorajat, väärinkäytön esto ja käyttökiintiöt; rajaa CORS täsmällisiin tuotanto-osoitteisiin, käytä HTTPS:ää ja siirrä avaimet palveluntarjoajan salaisuuksienhallintaan. CORS ei korvaa tunnistautumista.

Julkinen Git-repo ei itsessään julkaise sovellusta, mutta jokainen mukana oleva tiedosto on muiden luettavissa. Tarkista [tietoturvaohje](SECURITY.md), [tietosuojakuvaus](PRIVACY.md), riippuvuuksien ajantasaisuus ja lisenssi ennen julkaisua. Projektissa ei ole vielä valittua lisenssiä; julkinen näkyvyys ei itsessään anna uudelleenkäyttöoikeutta.

Unsplash-kuvat ovat ulkoisia esimerkkikuvia. Varmista kuvien käyttöoikeudet ja vaihda demoyhteystiedot todellisiin tietoihin ennen asiakaskäyttöä.
