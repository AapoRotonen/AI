# Nykyinen järjestelmä lyhyesti

Koivu Store on portfolio-vaatekauppademo. Katalogissa on 18 esimerkkituotetta neuleista kenkiin. `frontend/catalog.json` on yhteinen tuotetietolähde: käyttöliittymä näyttää katalogin ja erilliset tuotekohtaiset sivut, palvelin validoi tilausrivit samasta tiedosta ja BM25 hakee siitä myös AI-avustajalle tuotetietoa. Chroma-indeksi tarjoaa semanttisen haun tallennetusta indeksistä; se voi sisältää vanhemman katalogiversion, kunnes indeksi päivitetään erikseen. Tavilyä käytetään vain julkisen ajankohtaisen tiedon reitillä, jos se on asetettu.

Asiakaskohtaiset tilaus- ja tukitiedot vaativat kirjautumisen. Tilin kautta voi valita tuotteen, värin ja koon, tallentaa maksuttoman demotilauksen sekä tarkastella omia tilauksia. Valinnaiset Stripe-asetukset avaavat vain Stripe-testitilan kassan; palvelin laskee hinnat ja hyväksyy maksettu-tilan vain allekirjoitetusta webhookista. Testikassa ei veloita oikeaa rahaa eikä tilaus siirry toimitukseen. Näytetty saatavuus ei ole reaaliaikainen varastosaldo.

Kun asiakas pyytää ihmistä, kirjautuneelle käyttäjälle tallennetaan tukipyyntö ja paikallinen demokäsittelijä vastaa samaan chattiin selvästi merkittynä. Tukihenkilön suojatussa näkymässä voi lisäksi tarkastella, vastata ja sulkea pyyntöjä. Kirjautumattomalle käyttäjälle chat näyttää kirjautumispyynnön ja jatkotoiminto on käyttäjän valittavissa.

Kaupan esittelysivut ovat `shop.html`, `product.html?id=...`, `about.html`, `shipping.html` ja `returns.html`. Sivut kertovat, että hinnat, toimitus- ja palautusesimerkit sekä saatavuudet ovat demotietoja. Sovellus tallentaa paikalliseen SQLite-tietokantaan demoasiakkaat, istunnot, tilaukset ja tukipyynnöt. Ostoskori ja suosikit ovat selaimen tallennustilassa. Stripe-testikassa on valinnainen eikä sitä ole määritetty Azure-julkaisun workflow’hun; tämä ei ole tuotantomaksupalvelu eikä tuotantokäyttöön valmis verkkokauppa.

## Valmisteltu Azure-vaihtoehto

Paikallinen oletus ei muutu: kehityksessä käytetään SQLiteä ja paikallista Chroma-indeksiä. Azure-julkaisupolku käyttää Container Appsia, Cosmos DB serverlessiä ja yksityistä Blob Storagea Chroma-arkistolle. Resurssien luonti ja sovelluksen julkaisu vaativat erilliset, manuaalisesti käynnistettävät workflow-vaiheet; Azure-tilin tila ja kustannukset ovat ympäristökohtaisia. Katso [Azure-julkaisun tekniset ohjeet](azure/DEPLOYMENT.md) ja [arkkitehtuuri](azure/ARCHITECTURE.md).
