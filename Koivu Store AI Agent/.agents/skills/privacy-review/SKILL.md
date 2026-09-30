---
name: privacy-review
description: Map personal-data flows, privacy risks, and disclosure gaps in an application. Use when the user asks for a privacy review, data-flow inventory, privacy notice assessment, or privacy-by-design improvements.
metadata:
  short-description: Review privacy and data flows
---

# Tietosuojakatselmus

Arvioi sovelluksen tiedonkeruuta, tallennusta, siirtoja, säilytystä ja käyttäjälle annettavaa tietoa. Aloita lähdekoodista ja seuraa tiedot käyttöliittymästä tietokantoihin, lokeihin, malleihin ja ulkoisiin palveluihin.

## Menettely

- Lue ensin projektin `AGENTS.md` ja muut asiaankuuluvat ohjeet. Käytä sibling-skillin `security-review` ohjeita, kun tietosuojan rinnalla tarvitaan yleinen uhkamallin katselmus.
- Tee ensin vain lukuun perustuva kartoitus. Älä lähetä testidataa ulkoisille palveluille äläkä tulosta salaisuuksia tai henkilötietoja.
- Kirjaa kullekin tietoryhmälle lähde, tarkoitus, vastaanottaja, tallennuspaikka ja kesto vain siltä osin kuin koodi tai luotettava dokumentti vahvistaa ne. Nimeä tuntemattomat kohdat tuntemattomiksi; älä arvaa palveluntarjoajien säilytysaikoja tai sijainteja.
- Erota tekninen tietovirtakuvaus lakisääteisestä ilmoituksesta. Älä väitä ilmoitusta vaatimustenmukaiseksi ilman rekisterinpitäjän, tarkoitusten, oikeusperusteiden, vastaanottajien, säilytyksen ja oikeuksien tietoja.
- Kun oikeudellinen vaatimus tai palveluntarjoajan ehto on ajankohtainen tai epävarma, tarkista ensisijainen virallinen lähde ja linkitä se.
- Suosittele minimointia, käyttötarkoitussidonnaisuutta, poistamista, rajaamista ja selkeää ennakkotietoa. Toteuta vain käyttäjän pyytämät turvalliset ja palautettavat muutokset.

## Raportoi

Kerro tärkeimmät todetut tietovirrat ja vaikutukset, puuttuvat tosiasiat sekä konkreettiset korjaukset. Erota demodata ja oikeiden käyttäjien henkilötiedot. Kuvaa myös, mitä et pystynyt varmistamaan; älä esitä teknistä analyysiä lakineuvontana.
