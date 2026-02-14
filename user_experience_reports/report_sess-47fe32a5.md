# Zpráva o testování použitelnosti: Bauhaus.cz

---

## 01 Úvod

> Tuto revizi provedla společnost AUX.
> Revize je založena na poznatcích o lidské kognici.
> Cílem je identifikovat konkrétní problémy s použitelností pozorované během reálné navigace a navrhnout jasné designové opravy.

Tato studie se zaměřuje na zkušenost profesionálního uživatele (B2B / stavbyvedoucí) při nákupu kritických stavebních materiálů.

---

## 02 Metoda: Navigace persony a kognitivní protokolování

*   **Kontext persony:** Lars, stavbyvedoucí s 15letou praxí, hledá specifické cementové směsi s certifikací 42.5 R pro nosné konstrukce.
*   **Provedené úkoly:** Vyhledávání, technická filtrace, analýza specifikací v detailu produktu, srovnání produktů, kontaktování servisu a proces košíku.
*   **Způsob záznamu:** Myšlenkové deníky zachycující reálné reakce, rozhodovací procesy a kognitivní stavy (např. zahlcení, frustrace).
*   **Identifikace problémů:** Analýza nesouladu mezi mentálním modelem profesionála a nabízeným rozhraním.

---

# 03 Pozorované UX výzvy

---

## 03.1 Absence technické filtrace pro stavební materiály

[Stránka s výsledky vyhledávání / Kategorie Cement]

---

### 🧠 Pozorované chování (z myšlenkových deníků)

> „Kde jsou technické filtry? Vidím tu cenu, značku, ale nic o pevnostní třídě nebo normách EN.“
> — Myšlenkový deník, Úkol 2

> „To budu muset rozklikávat každý produkt?“
> — Myšlenkový deník, Úkol 2

---

### 🔍 Kognitivní diagnóza

Interface nutí uživatele k **manuálnímu skenování** názvů produktů místo toho, aby mu umožnil **kategorické třídění**. U profesionálních materiálů je pevnostní třída (např. 42.5 R) primárním rozhodovacím faktorem. Absence tohoto filtru způsobuje **vysokou kognitivní zátěž** a zvyšuje riziko chyby při nákupu nevhodného materiálu pro projekt.

---

### 📸 Vizuální důkaz

![Aktuální stav filtrů](images/issue_01_current.png)

---

### 🛠 Designová oprava

Implementace dedikované sekce „PROFI FILTRY“ v bočním panelu, která umožní filtrování podle klíčových technických parametrů (třída pevnosti, norma, certifikace).

```html
<div class="profi-filter">
  <h3>PROFI PARAMETRY</h3>
  <label><input type="checkbox"> Pevnostní třída 42.5 R</label>
  <label><input type="checkbox"> Norma EN 197-1</label>
</div>
```

```css
.profi-filter {
  border: 2px solid #ed1c24;
  padding: 15px;
  background: #fefefe;
  margin-bottom: 20px;
}
.profi-filter h3 {
  color: #ed1c24;
  font-size: 1.1rem;
}
```

---

### 📐 Vizuální srovnání

:::columns
:::column
**Aktuální**

![Current](images/issue_01_current.png)
:::

:::column
**Vylepšené**

![Improved](images/issue_01_redesign.png)
:::
:::

---

## 03.2 Utopená technická data v detailu produktu

[Stránka detailu produktu (PDP)]

---

### 🧠 Pozorované chování

> „Tady to je, ale je to utopené v textu... chci tato data vidět hned vedle ceny.“
> — Myšlenkový deník, Úkol 3

---

### 🔍 Kognitivní diagnóza

Hierarchie informací je nastavena pro hobby uživatele (zaměření na vizuální dojem a obecný popis). Pro profesionála jsou **technické parametry a certifikáty** kritickými informacemi „nad ohybem“ (above the fold). Nutnost rolovat dolů pro ověření technické shody narušuje plynulost nákupního procesu.

---

### 📸 Vizuální důkaz

![Detail produktu - technická data](images/task_03_pdp.png)

---

### 🛠 Designová oprava

Vytvoření kompaktního bloku „Technický pas“ vedle nákupního tlačítka, který shrnuje 3-4 nejdůležitější parametry a certifikace.

---

# 04 Opakující se vzorce tření

*   **Informační hierarchie:** Web upřednostňuje DIY obsah (návody, blogy) před B2B informacemi, což způsobuje, že se profesionální uživatel cítí jako sekundární cílová skupina.
*   **Nedostatečná zpětná vazba ve vyhledávání:** Vyhledávání nevrací technické parametry přímo v náhledu (grid view), což nutí uživatele k nadbytečným kliknutím.
*   **Navigační ambivalence:** Sekce pro služby (doprava, záruky) jsou psány právním/obecným jazykem, který neodpovídá na specifické potřeby velkoobjemových zakázek (např. vykládka hydraulickou rukou).

---

## 05 Prvky podporující kognici

*   **Drive-In Aréna v lokátoru:** Jasné grafické odlišení prodejen, kam lze vjet s dodávkou, výrazně snižuje nejistotu při plánování logistiky.
*   **Srovnávací nástroj:** I přes drobné vady v zarovnání tabulky pomáhá srovnání snižovat nároky na pracovní paměť při porovnávání parametrů více produktů.
*   **Čistý design košíku:** Redukce vizuálního šumu v procesu pokladny podporuje soustředění na dokončení transakce.

---

## 06 Přístupnost a inkluzivní tření

| WCAG | Problém | Pozorovaný dopad | Oprava |
| :--- | :--- | :--- | :--- |
| Contrast | Nízký kontrast u filtrů | Snížená čitelnost technických specifikací v bočním panelu. | Zvýšit kontrastní poměr textu filtrů na 4.5:1. |
| Labels | Chybějící štítky ikon | Profesionál neví, co dělají malé ikony v gridu bez hoveru. | Přidat textové popisky k ikonám porovnání a wishlistu. |

---

## 07 Přehled UX oprav

| Výzva | Kognitivní příčina | Designová oprava |
| :--- | :--- | :--- |
| Filtrace cementu | Přetížení pracovní paměti | Zavedení technické sekce v bočním filtru |
| Dostupnost specifikací | Narušení plynulosti (Flow) | Přesun technického pasu k nákupnímu tlačítku |
| B2B identifikace | Nedostatek vizuálních vodítek | Přidání dedikovaného „Profi“ módu navigace |

---
