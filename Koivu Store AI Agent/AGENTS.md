# Koivu Store AI Agent — työohjeet

Lue tämä tiedosto ennen projektin muokkaamista. Pidä käyttöliittymä, tuotekatalogi ja agentin rajapinta keskenään yhteensopivina. Älä muuta agentin haarautumis- tai eskalointikäyttäytymistä ilman erillistä pyyntöä.

## Projektin tarkoitus ja rakenne

Koivu Store on vaatekaupan demo, jossa on suomenkielinen verkkokaupan käyttöliittymä ja tuotekysymyksiin vastaava AI-asiakaspalvelu.

- `frontend/index.html`: sivun rakenne, katalogi-, ostoskori- ja chat-näkymät.
- `frontend/store.css`: sivun ulkoasu. Brändin pääsävyjä ovat metsänvihreä, lämmin luonnonvalkoinen ja hillityt maanläheiset sävyt; säilytä rauhallinen, vaatemallistoon sopiva ilme.
- `frontend/store.js`: tuotekortit, haku, suodatus, tuotetiedot, ostoskori, suosikit ja chatin API-kutsut. API-osoite on tällä hetkellä `http://127.0.0.1:8000`.
- `backend/main.py`: FastAPI-reitit ja pyyntö-/vastausmallit.
- `backend/agent/graph.py`: LangGraphin nodet ja siirtymäpäätökset.
- `backend/agent/nodes.py`: RAG-haku, luokittelu, verkkohaku, eskalointi ja vastauksen generointi.
- `backend/agent/state.py`: graafin mukana kulkevan tilan kentät.
- `backend/core/retrieval.py`: paikallinen Chroma-tallennus sekä BM25- ja vektorihakujen yhdistäminen.
- `backend/core/config.py`: mallien, API-avainten ja hakuasetusten oletusarvot.
- `backend/data/products.txt`: AI-agentin tuote-, toimitus-, palautus- ja kokotiedot.

## Projektin katselmusskillit

- `.agents/skills/security-review/SKILL.md`: yleinen tietoturva- ja Git-julkaisukatselmus.
- `.agents/skills/privacy-review/SKILL.md`: henkilötietojen tietovirrat ja tietosuojailmoituksen puutteet.
- `.agents/skills/ai-agent-review/SKILL.md`: agentin nodet, ehdolliset edget, työkalurajat ja eskalointikäyttäytyminen.
- `.agents/skills/public-release-review/SKILL.md`: julkiseen Git-julkaisuun tulevat tiedostot, salaisuudet ja lisenssihuomiot.

Käytä näitä tilanteeseen sopivia projektin skill-ohjeita, kun teet vastaavan katselmuksen.

Frontendin tuotenimet, kuvat, hinnat, kokovaihtoehdot ja väri-/saatavuustiedot ovat myös kovakoodattuina `frontend/store.js`-tiedostoon. Pidä ne linjassa `backend/data/products.txt`-tiedoston kanssa, etenkin kun muutat hintoja, varastotilannetta tai tuotetietoja.

## AI-agentti ja haarautuminen

`backend/agent/graph.py` rakentaa `StateGraph(AgentState)`-graafin. Normaali polku on `rag → evaluate`, jonka jälkeen ehdollinen reititys valitsee vastauksen, verkkohakupalvelun tai eskaloinnin. Web-solmun jälkeen graafi joko generoi vastauksen tai eskaloi. Eskalointi kulkee lopuksi `generate`-solmun kautta.

`evaluate_rag_node` luokittelee mallilla kaksi asiaa: vastaako katalogin RAG-konteksti kysymykseen (`rag_was_sufficient`) ja vaatiiko pyyntö tapauskohtaista ihmisen apua (`needs_human`). Suora pyyntö ihmiselle tai oman tilauksen, maksun, hyvityksen tai toimitusongelman selvittäminen kuuluu eskalointiin. Yleiset tuotetieto- ja ohjekysymykset pyritään hoitamaan automaattisesti.

RAG-reitityksen järjestys on tärkeä: `needs_human` johtaa ensin eskalointiin; riittävä RAG-tulos vastataan suoraan; muussa tapauksessa käytetään verkkohakua Tavilyn kautta, jos avain on asetettu ja iteraatioraja ei täyty. Web-haun virhe tai tulokseton haku eskaloi. Älä poista tai muuta näitä ehtoja käyttöliittymäuudistuksen yhteydessä.

`escalation_node` asettaa `should_escalate=True`. Frontend näyttää tämän perusteella Maija-siirtymän; jatkoviestit lähetetään `/human-chat`-reitille. Maija on demossa eri järjestelmäohjeella toimiva AI, ei oikea ihminen.

Säilytä frontendin ja backendin välinen sopimus:

- `POST /setup` valmistelee RAG-tuotekatalogin; nykyinen reitti ei lisää samaa aineistoa uudelleen, jos Chroma-kokoelmassa on jo dataa.
- `POST /chat` ja `POST /human-chat` ottavat JSON-rungon `{ "message": "...", "history": [{"role":"user|assistant","content":"..."}] }`.
- Viesti ja jokainen historiavuoro ovat enintään 4 000 merkkiä; historia on enintään 12 vuoroa. Paikallisen CORS-listan oletus on portin 5500 frontend; aseta `CORS_ALLOWED_ORIGINS` täsmällisiin verkkotunnuksiin julkaisussa.
- Vastauksessa on `answer`, `path` ja `should_escalate`.
- Frontend välittää enintään 12 aiempaa keskusteluvuoroa. Keskustelun historia säilyy frontendissä; LangGraphille ei ole asetettu pysyvää checkpointeria.
- Muita käytännöllisiä tarkistusreittejä ovat `GET /health` ja `GET /products/count`.

## Ajo, pilvipalvelut ja avaimet

Kehityspalvelut kuuntelevat vain paikallisessa koneessa:

```powershell
# Backend, projektin juuresta
Set-Location backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Avaa toinen PowerShell-ikkuna frontendille
Set-Location frontend
..\backend\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1
```

Avaa sitten `http://127.0.0.1:5500/`. Tarkista backend ensin osoitteesta `http://127.0.0.1:8000/health`. `/health` vahvistaa backendin käynnissäolon, mutta ei ulkoisten mallipalveluiden toimivuutta.

Agentin LangGraph, FastAPI, BM25 ja Chroma-tietokannan oletustallennus (`backend/chroma_db`) ovat paikallisia. `ChatOpenAI` käyttää oletuksena `gpt-4o`-mallia, ja RAG-vektorihaut käyttävät OpenAI:n `text-embedding-3-small`-upotuksia. Tavily on verkkohakupalvelu ja sitä käytetään vain, kun `TAVILY_API_KEY` on määritetty. Chat-kysymykset, keskusteluhistoria ja haun konteksti välitetään OpenAI API:lle; Tavily-haussa käyttäjän kysymys sisällytetään hakupyyntöön.

API-avaimet kuuluvat `backend/.env`-tiedostoon tai palvelimen ympäristöön. Älä tulosta, kopioi frontend-koodiin, lisää dokumentaatioon tai commitoi avaimia. Älä lue `.env`-sisältöä tulosteeseen; tarkista tarvittaessa vain, onko asetus määritetty. Älä tyhjennä tai korvaa `backend/chroma_db`-kansiota ilman erillistä syytä, sillä se sisältää pysyvää RAG-dataa.

## Vianetsintä ja tarkistukset

- Jos sivu ei aukea, tarkista frontendin portti `5500`; jos `/health` ei vastaa, tarkista backendin portti `8000`.
- Jos `/health` toimii mutta chat näyttää yhteysvirheen, tarkista backend-loki. RAG kutsuu OpenAI-embedding-palvelua jo ennen varsinaista vastausta. `WinError 10013` / `APIConnectionError` tarkoittaa yleensä, että backendin ympäristö estää lähtevän HTTPS-yhteyden OpenAI API:lle; palvelin voi silti näyttää terveeltä. Virheellinen avain näkyy tavallisesti autentikointivirheenä.
- OpenAI- ja Tavily-kutsut tarvitsevat internet-yhteyden, toimivan avaimen ja voivat aiheuttaa API-kuluja. Pelkkä `node --check frontend/store.js` ei tee mallikutsuja. Älä lähetä maksullisia end-to-end-testipyyntöjä automaattisesti, ellei toiminnallisuuden tarkistus sitä nimenomaisesti vaadi.
- Kevyt JavaScript-syntaksitarkistus projektin juuresta: `node --check frontend/store.js`.
- End-to-end-chat-testi `POST /chat`-reitille tekee oikeita OpenAI-kutsuja; käytä vain yleistä testikysymystä, älä henkilötietoja.

Tämänhetkisessä työpöytäympäristössä `backend/.venv` on toimiva virtuaaliympäristö. `backend/venv` viittaa vanhan koneen Python-polkuun, joten älä käytä tai poista sitä sokkona. Tarkista Python-ympäristö ennen asennuksia; jos `.venv` puuttuu toisessa ympäristössä, luo se siellä `backend/requirements.txt`-tiedoston perusteella.

## Verkkokaupan nykyiset rajat

Tuotteen koko- ja värivalinta, suodatus, järjestäminen, haku, suosikit ja ostoskori ovat demossa käyttöliittymätoimintoja; kori ja suosikit tallentuvat selaimen `localStorage`-tilaan (`koivu-cart`, `koivu-favorites`). Kassapainike näyttää demoviestin. Maksupalvelua, tilausten backend-tallennusta tai oikeaa varastonhallintaa ei ole toteutettu — älä esitä niitä toimivina ominaisuuksina.

Tuotekuvat ovat ulkoisista Unsplash-URL-osoitteista. Julkista tuotantokauppaa varten varmista käyttöoikeudet, toimitusvarmuus ja että kuvat vastaavat myytäviä tuotteita.

README:n käynnistys- ja ihmissiirtymän esimerkit voivat olla vanhentuneita (esimerkiksi nimi Liisa). Tarkista aina nykyinen toiminta lähdekoodista; tämän projektin demossa ihmispersoona on Maija.
