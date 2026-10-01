# Tietosuoja- ja tietoturvatarkastus

**Tarkastuspäivä:** 2026-10-01
**Kohde:** koko NewsLens-projektikansio sekä Gitin käytettävissä oleva historia ja asetukset.
**Tyyppi:** PoC-tason koodin, asetusten, riippuvuuksien ja Git-riskien tarkastus.

## Tarkastetut alueet

- Python-koodi, testit, migraatiot, YAML-konfiguraatiot, Dockerfile, Compose ja CI-workflow.
- Riippuvuuslukko ja OSV-tietokannan haavoittuvuustarkastus (`uv audit --locked`).
- Työpuun ja kaikkien paikallisesti saavutettavien Git-viitteiden tunnetut avain- ja tokenmuodot.
- `.env`- ja avaintiedostojen ohitussäännöt, nykyinen Git-haara, upstream ja GitHub-etäosoite.

## Korjatut löydökset

1. **Riippuvuushaavoittuvuus:** OSV löysi kaksi pytest 8.4.2:een kohdistuvaa ilmoitusta (GHSA-6w46-j5rx-g56g ja PYSEC-2026-1845; sama CVE-2025-71176). `pytest` päivitettiin lukossa versioon 9.1.1 ja `pytest-asyncio` versioon 1.4.0; hyväksytyt kehitysriippuvuusrajat päivitettiin vastaavasti.
2. **CI:n oikeudet ja toimitusketju:** GitHub Actions sai vain `contents: read` -oikeuden, checkoutin tunnisteen säilytys poistettiin ja molemmat ulkoiset actionit lukittiin commit-SHA:ihin. `uv`-versio lukittiin.
3. **Dockerin riippuvuuksien ajautuminen:** Docker-asennus käytti aiemmin avoimia `pip install .` -riippuvuusrajoja eikä `uv.lock`-tiedostoa. Kuva asentaa nyt lukon mukaiset riippuvuudet; `hatchling`-rakennusbackend on myös versionlukittu ja mukana haavoittuvuusauditoinnissa.
4. **Tietokannan verkkoaltistus:** PostgreSQL-portti sidottiin Compose-tiedostossa vain `127.0.0.1`-osoitteeseen.
5. **Komentojen väärinkäyttö:** Discord-komennot ovat nyt oletuksena pois käytöstä. Käyttäjät sallitaan eksplisiittisellä `DISCORD_ALLOWED_USER_IDS`-listalla; julkinen käyttö vaatii erillisen `DISCORD_ALLOW_PUBLIC_COMMANDS=true`-asetuksen.
6. **Palveluntarjoajan tunnistetietojen siirto:** mallipalvelimen URL hyväksyy HTTPS:n tai vain loopback-HTTP:n, ja hylkää userinfo-, query- ja fragmenttikentät.
7. **Discord Markdown -sisältö:** syötteet ja mallin tuottamat tekstit litistetään ja escapetaan; lähdelinkit hyväksyvät vain HTTP(S)-osoitteet. Tämä vähentää syötetekstin mahdollisuutta muotoilla viestiä harhaanjohtavasti.
8. **Lokien tietojen minimointi:** generointivirheiden lokitus ei enää tulosta poikkeusviestin sisältöä, johon palvelin tai ulkoinen API voisi sisällyttää käyttäjän syötettä.
9. **Git- ja rakennuskontekstin suojaus:** `.gitignore` ohittaa ympäristö-, paikalliset salaisuushakemistot, yleiset yksityisavain- ja sertifikaattitiedostot sekä Terraform-tilan. `.dockerignore` estää salaisuuksien ja paikallisten ympäristöjen päätymisen Dockerin rakennuskontekstiin. `.gitattributes` yhtenäistää tekstimuotoisten lähdetiedostojen rivinvaihdot.

## Yksityisyys ja säilytys

Kun ominaisuudet on konfiguroitu, `/ask`- ja `/investigate`-pyyntöjen kysymystekstiä ja rajattuja lähdeotteita voidaan lähettää valitulle OpenAI-yhteensopivalle mallipalvelulle. Hakukyselyt lähetetään Tavilylle. Discord käsittelee komennot ja briefing-julkaisut. Sovellus ei tarkoituksella tallenna Discord-käyttäjätunnuksia, mutta PostgreSQLiin tallentuvat uutisotsikot, kanoniset URL-osoitteet, lähdetiedot, enintään lyhyet tekstikatkelmat, johdetut yhteenvedot ja upotukset.

Tietokantatiedoille ei ole automaattista vanhenemista tai poistotoimintoa. Ylläpitäjän on määritettävä varmuuskopiointi, säilytys, levyn salaus ja poistaminen ennen jatkuvaa tai laajempaa käyttöä. Compose-tiedoston oletussalasana on vain paikalliseen kehitykseen; vaihda se ja tietokantaosoite yhdessä muussa käytössä. Käyttäjille tulee kertoa ulkoisista palveluista, eikä tutkimuskyselyihin pidä syöttää henkilötietoja tai luottamuksellista aineistoa.

## Git-tulokset

- Nykyinen haara `AI` seuraa `origin/AI`-haaraa, jonka etäosoite on GitHubissa.
- Työpuusta ei löytynyt tunnettuihin API-avain-, GitHub-token-, AWS-avain-, Discord-token- tai yksityisavaimen muotoihin osuvia osumia.
- Samat haut tehtiin kaikille paikallisesti saavutettaville Git-historian blob-tiedostoille; osumia ei löytynyt.
- Tarkastuksen alussa `.env`-tiedostoa tai tavallisia yksityisavaintiedostoja ei ollut projektikansiossa. Gitin ohitussäännöt vahvistettiin komennoilla `git check-ignore`.
- GitHub-haaran suojausasetuksia ei voitu vahvistaa paikallisesta Git-asiakasohjelmasta.

## Jäljelle jäävät rajoitteet

- **DNS rebinding:** julkisen IP:n tarkistus ja HTTPX-yhteyden DNS-ratkaisu ovat erillisiä, joten hyökkääjä voi teoriassa vaihtaa DNS-vastauksen niiden välillä. Kiinnitetty IP-yhteys ja TLS-hostname-varmennus tarvitaan tämän riskin poistamiseen.
- **Säilytys:** tietokannan automaattista retention- tai GDPR-poistoprosessia ei ole toteutettu.
- **Tunnistehaku:** automaattinen Git-haku tunnistaa yleisiä salaisuusmuotoja, mutta ei korvaa varsinaista secrets-skanneria. Aiemmin vahingossa julkaistua avainta ei saa jättää käyttöön, vaikka se myöhemmin poistettaisiin historiasta.
- **GitHub-hallinta:** haarasuojausta, pakollisia tarkistuksia ja GitHubin salaisuusasetuksia ei voitu lukea paikallisesti.
- **Ulkoiset kuvat ja tietokanta:** Compose-kuvat seuraavat version tagia ilman digest-lukitusta. Tuotantoon vietäessä lukitse image digestit ja käytä hallittua salaisuuksien säilytystä.
- **Muu PoC-riski:** lähteiden oikeellisuus, mallin hallusinaatiot, palveluntarjoajien tietojen käsittelyehdot sekä syötteiden väärinkäyttö on arvioitava ennen tuotantokäyttöä.

## Varmistus

- `uv audit --locked`: ei tunnettuja haavoittuvuuksia tai haitallisia projektitiloja 77 riippuvuuspaketissa.
- `ruff check` ja `ruff format --check`: läpäisty.
- `pytest`: 33 testiä läpäisi. Riippuvuudesta tuli lisäksi `audioop`-vanhentumisvaroitus.
- `uv build --no-sources --no-build-isolation`: wheel ja sdist rakentuivat; paketit eivät sisältäneet ympäristö-, salaisuus- tai välimuistipolkuja.
- Gitin ohitussäännöt tarkistettiin `.env`-, avain-, salaisuus- ja Terraform-esimerkkipoluilla. Työpuun ja paikallisen historian salaisuustunnistehaut antoivat nolla osumaa.
- CI-workflow jäsentyi YAML-muotoon. Docker CLI ei ollut saatavilla, joten varsinaista konttikuvan rakennusta ei voitu ajaa.
