---
name: public-release-review
description: Prepare a codebase for a public Git release by reviewing tracked, staged, untracked, and historical content, secrets, generated files, documentation, licensing gaps, and deployment distinctions. Use when the user asks whether a project is safe or ready to publish publicly.
metadata:
  short-description: Review readiness for public Git release
---

# Julkisen lähdekoodijulkaisun katselmus

Arvioi juuri ne tiedostot ja commitit, jotka voivat päätyä julkiseen Git-julkaisuun. Julkinen lähdekoodi ja internetiin julkaistu palvelu ovat eri riskikokonaisuuksia; käsittele molemmat erikseen.

## Menettely

- Lue ensin `AGENTS.md` ja security-sibling-skill. Selvitä projektin sijainti ja todellinen Git-juuri; tarkista status, stage, seuratut ja seuraamattomat tiedostot sekä olemassa oleva historia.
- Älä alusta repoa, stagea, commitoi, puske, poista tiedostoja tai muokkaa historiaa ilman käyttäjän erillistä pyyntöä. Älä suorita laajaa `git add .` -komentoa.
- Tunnista salaisuudet, henkilökohtaiset tiedot, paikalliset asetukset, lokit, välimuistit, tietokannat, arkistot, virtuaaliympäristöt ja generoidut artefaktit. Tulosta salaisista tiedostoista korkeintaan avaimen nimi ja arvoluokka.
- Vertaa `.gitignore`-sääntöjä todelliseen Git-seurantaan. Muista, ettei ignore-sääntö poista jo seurattua tiedostoa tai historiaan tallennettua salaisuutta.
- Etsi avainnimet käyttävä esimerkkiasetustiedosto, kuten `.env.example`, joka ei sisällä oikeita arvoja. Varmista, että julkinen README selittää asennuksen ja paikallisen asetuksen ilman salaisuuksia.
- Tarkista kansion mukana tulevat ZIPit, kuvakaappaukset, dumpit ja dokumentit. Huomioi lisenssin puuttuminen, yhteystiedot, kuvien/data-aineiston oikeudet ja vanhentuneet demoväitteet; älä valitse lisenssiä käyttäjän puolesta.
- Arvioi erikseen, mitä vaaditaan palvelun julkiseen käyttöönottoon: tunnistautuminen, nopeus- ja kokorajat, HTTPS, salaisuuksien hallinta, lokitus, kustannusrajat ja yksityisyys.
- Jos hakemisto ei ole Git-repo tai historiaa ei voi lukea, kerro rajoite täsmällisesti äläkä väitä, että repo tai historia on puhdas.

## Raportoi

Anna julkaisupäätelmää varten listaus löydöksistä vakavuuksineen, tarkat tiedostot, varmennettu Git-tila ja avoimet rajaukset. Erota nykyinen vuoto todellisesta vuodosta, joka vain voisi syntyä tulevassa stage-vaiheessa. Tee muutoksia vain, kun ne kuuluvat käyttäjän pyyntöön.
