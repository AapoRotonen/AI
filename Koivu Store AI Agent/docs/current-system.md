# Nykyinen järjestelmä lyhyesti

Koivu Store on paikallinen vaatekauppademo. Tuotekysymyksissä agentti hakee vastaukselle tuotekatalogista tietoa hybridillä RAG-haulla (Chroma-vektorihaku sekä BM25), arvioi lähteiden riittävyyden ja tarkistaa, että vastaus viittaa palautettuihin lähteisiin. Tyylikysymyksissä se voi täydentää tuotetietoa yleisellä tyylineuvolla ja käyttää Tavily-verkkohakua, jos se on asetettu. Keskustelun polku näkyy käyttöliittymässä.

Asiakaskohtaiset tilaus- ja tukitiedot vaativat kirjautumisen. Tilin kautta voi valita tuotteen, värin ja koon, tehdä maksuttoman demotilauksen sekä tarkastella ja perua omia tilauksia. Palvelin tarkistaa valikoiman, hinnat ja omistajuuden; maksua ei veloiteta eikä tilausta välitetä oikeaan toimitusjärjestelmään.

Kun asiakas pyytää ihmistä, kirjautuneelle käyttäjälle tallennetaan tukipyyntö ja paikallinen demokäsittelijä vastaa samaan chattiin selvästi merkittynä. Tukihenkilön suojatussa näkymässä voi lisäksi tarkastella, vastata ja sulkea pyyntöjä. Kirjautumattomalle käyttäjälle chat näyttää kirjautumispyynnön ja jatkotoiminto on käyttäjän valittavissa.

Sovellus tallentaa paikalliseen SQLite-tietokantaan demoasiakkaat, istunnot, tilaukset ja tukipyynnöt. Ostoskori ja suosikit ovat selaimen tallennustilassa. Tämä ei ole maksupalvelu eikä tuotantokäyttöön valmis verkkokauppa.
