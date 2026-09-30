# Tietosuojan tekninen kuvaus

Tämä kuvaa nykyisen demokoodin tietovirtoja. Se ei ole valmis lakisääteinen tietosuojailmoitus eikä oikeudellinen arvio. Ennen oikeiden asiakkaiden käyttämistä täydennä vähintään rekisterinpitäjä, yhteystiedot, käsittelyn tarkoitukset ja oikeusperusteet, vastaanottajat/käsittelijät, säilytysajat, mahdolliset siirrot sekä rekisteröidyn oikeudet. GDPR:n 13 artikla edellyttää tietoja kerättäessä muun muassa tarkoituksista, oikeusperusteista, vastaanottajista ja säilytysajoista ([EUR-Lex: GDPR, 13 artikla](https://eur-lex.europa.eu/legal-content/EN/TXT/?qid=1772981449498&uri=CELEX%3A32016R0679)).

## Demossa tapahtuva käsittely

| Tieto | Mihin se kulkee | Koodista havaittu käsittely |
| --- | --- | --- |
| Chat-viesti ja keskustelun viimeiset viestit | Selaimesta Koivu-backendiin ja agentin OpenAI-kutsuihin | Keskusteluhistoria pysyy selaimen muistissa istunnon ajan; sovelluksessa ei ole keskustelun pysyvää tallennusta. Backend lähettää kysymyksen ja rajatun historian mallille luokitteluun ja vastauksen muodostukseen. |
| Katalogihaku | OpenAI Embeddings API | Käyttäjän kysymys muunnetaan upotukseksi vektorihakua varten. Tuotekatalogin aineisto muunnetaan upotuksiksi, kun tietokanta alustetaan. |
| Verkkohaku | Tavily | Kysymys lähetetään Tavilylle vain, jos agentin LangGraph-reititys valitsee verkkohakuhaaran ja Tavily-avain on asetettu. |
| Tuotekatalogi | Backendin paikallinen Chroma-tietokanta | Tuotekatalogi tallentuu oletuksena `backend/chroma_db`-hakemistoon. Tämä sisältää tuotetietoja, ei käyttäjätilauksia. |
| Ostoskori ja suosikit | Käyttäjän selain | Tallentuvat `localStorage`en selaimen avaimilla `koivu-cart` ja `koivu-favorites`. Ne eivät sisällä kirjautumis- tai maksutoimintoa. |
| Tuotekuvat | Unsplash | Selaimessa ladataan kuvia Unsplashin URL-osoitteista; kuvapalvelu saa tavanomaiset verkkopyynnön metatiedot. |

Koodista ei voi päätellä OpenAI:n tai Tavilyn säilytysaikoja, käsittelyn sijaintia tai tilisi ehtoja; tarkista ne palveluntarjoajien ajantasaisista ehdoista ja asetuksista. Palvelininfrastruktuuri voi kerätä omia lokitietojaan. Projektissa ei tällä hetkellä ole kassa-, maksu-, asiakastili- tai tilaustietokantaa.

## Julkaisemista edeltävät täydennykset

- Rekisterinpitäjä ja toimiva tietosuoja-/yhteydenottokanava: **täydennettävä**.
- Käsittelytarkoitukset ja soveltuva oikeusperuste: **arvioitava ja dokumentoitava**.
- Palveluntarjoajat, käsittelysopimukset, mahdolliset kansainväliset siirrot ja säilytysajat: **varmistettava käytössä olevien tilien ja sopimusten perusteella**.
- Käyttäjälle näkyvä ilmoitus ennen viestin lähettämistä: lisätty demoa varten, mutta ei korvaa täydennettyä lakisääteistä ilmoitusta.
- Älä pyydä demossa henkilötietoja, tilaustunnuksia, maksutietoja tai yksityisiä asiakastietoja.
