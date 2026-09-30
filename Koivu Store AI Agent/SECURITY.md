# Tietoturva ja julkaisun tarkistuslista

Koivu Store AI Agent on demoprojekti. Ilmoita tietoturvaongelmasta ylläpitäjälle yksityisesti, kun projektilla on julkaistu yksityinen yhteydenottokanava. Älä julkaise haavoittuvuusraportissa API-avaimia, asiakkaiden tietoja tai käyttökelpoisia hyökkäysohjeita.

## Nykyinen uhkamalli

- Backendin chat-reitit ovat anonyymejä ja voivat käynnistää maksullisia OpenAI-kutsuja. Pidä backend paikallisessa kehityksessä. Ennen julkista palvelua lisää reunapalveluun nopeus- ja pyyntökokorajat, väärinkäytön esto sekä palveluntarjoajan kustannusrajat. Lisää tunnistautuminen, jos API ei ole aidosti julkinen.
- CORS-alkuperät rajataan `CORS_ALLOWED_ORIGINS`-asetuksella. Selaimen CORS-suojaus ei estä suoria HTTP-kutsuja eikä korvaa tunnistautumista.
- Pyyntömalli rajoittaa viestin ja historiavuoron 4 000 merkkiin sekä historian 12 vuoroon. Julkisen palvelun edessä pitää lisäksi valvoa koko HTTP-pyynnön kokoa.
- Malli näkee käyttäjän viestin ja haetun katalogi-/verkkohakutekstin. Mallille ei anneta työkalua, jolla se pääsisi koneen tiedostoihin tai tekisi tilausmuutoksia. Ulkoinen sisältö voi silti vaikuttaa mallin vastauksen sisältöön.
- API-avaimet kuuluvat palvelimen ympäristöön tai paikalliseen `backend/.env`-tiedostoon. Käytä julkaisuympäristössä salaisuuksienhallintaa ja vähimmän oikeuden avaimia.

## Ennen Git-julkaisua

- Tarkista Git-juuri, työpuu, stage ja aiempi historia. Älä lisää koko kansiota sokkona.
- Varmista, ettei `.env`, token, loki, tietokanta, virtuaaliympäristö, cache, vanha ZIP tai henkilökohtainen tiedosto kuulu julkaisuun. `.gitignore` ei poista jo seurannassa olevia tiedostoja tai historiassa olevia salaisuuksia.
- Käytä `backend/.env.example`-tiedostoa asetusten nimille; älä kopioi oikeita arvoja dokumentaatioon.
- Valitse projektille lisenssi ennen kuin annat muille luvan käyttää koodia.
- Tarkista riippuvuuspäivitykset ja lukitse tuotantoon asennettavat versiot ennen käyttöönottoa.

## Ennen internetiin julkaisemista

- Käytä HTTPS:ää, rajattua CORS-listaa, pyyntöjen nopeus- ja kokorajoja, kustannuskiintiöitä sekä seurantaa, joka ei tallenna tarpeettomasti keskustelujen sisältöä.
- Suojaa API autentikoinnilla tai julkiseen käyttöön sopivalla väärinkäytön torjunnalla. Rajoita ylläpito-/setup-toiminnot.
- Tarkista avainten käyttöoikeudet, tietojen käsittelysopimukset ja tietosuojailmoitus. Älä pyydä demochatissa henkilötietoja, maksu- tai tilaustietoja.
- Varmista, että kuvat, yhteystiedot, toimitus- ja palautuslupaukset vastaavat todellista palvelua.

Jos salaisuus joskus lisätään Git-historiaan, poista se käytöstä palveluntarjoajalla ja luo uusi. Pelkkä tiedoston poistaminen myöhemmässä commitissa ei poista sitä historiasta.
