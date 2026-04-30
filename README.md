# AI Strejda Discord Bot

Node.js rewrite Discord bota postavený čistě na slash commandech. Projekt je navržený kolem lokálních JSON dat v `db/`, aby šlo navázat na existující historii bez okamžité migrace do SQL.

## Co je hotové v kostře

- slash command router a registrace commandů
- config store rozdělený na `.env` a `config/runtime.local.json`
- JSON persistence vrstva pro stávající `db/*.json` a `db/sumar/*.json`
- doménové služby pro welcome, moderation, counting, AI score, summary, YouTube, bookmarky a reaction roles
- schedulery pro YouTube polling a denní summary

## Doporučený layout konfigurace

1. Zkopíruj `.env.example` na `.env`
2. Zkopíruj `config/runtime.example.json` na `config/runtime.local.json`
3. Doplň tokeny do `.env`
4. Doplň guild/channel/role ID a texty do `config/runtime.local.json`

Tajnosti patří do `.env`, provozní stav a ID do `config/runtime.local.json`.
`DISCORD_GUILD_ID` v `.env` je nadřazený a bot mimo tenhle server nic nezpracuje.

## Základní skripty

```bash
npm install
npm run register:commands
npm start
```

## Struktura

```txt
src/
  app/
  config/
  discord/
  domains/
  infrastructure/
  shared/
scripts/
config/
```

## Poznámky

- `db/` a `docs/` zůstávají lokální a ignorované v gitu.
- Runtime config je zapisovatelný, aby setup slash commandy uměly měnit channel/message ID.
- Pro summary a AI integrace je připravený fetch-based client, ale bez tokenů se jen bezpečně vypnou.

## Odškrtávací seznam testů

- [x] Router a registrace slash commandů
  - [x] Bot se úspěšně připojí po `npm start`.
  - [x] Registrace commandů proběhne bez chyb (`npm run register:commands`).
  - [x] `/` příkazy se zobrazí v serveru a vrací odpověď bez internal error.
- [x] Doména: `welcome`
  - [x] Přivítání se spustí na `guildMemberAdd`.
  - [x] Odesláná zpráva je ve správném kanálu a s nastavenými parametry.
- [ ] Doména: `counting`
  - [ ] Pořadí zpráv a ochrana proti duplicitám funguje.
  - [ ] Konfigurace kanálu přes runtime config drží stav i po restartu.
- [ ] Doména: `AI score`
  - [ ] Výpočet skóre vrací rozumné hodnoty při validních datech.
  - [ ] Při chybějících přihlašovacích údajích se modul bezpečně vypne a bot nekoliduje.
- [ ] Doména: `summary`
  - [ ] Denní/periodický souhrn se vygeneruje podle plánu.
  - [ ] Výsledek se pošle do cílového kanálu a formát odpovídá.
- [x] Doména: `YouTube`
  - [x] Poller správně zpracuje nový upload a nehlásí false positive.
  - [x] Notifikace se neposílají mimo nastavený seznam kanálů.
- [ ] Doména: `bookmarky`
  - [ ] Uložení bookmarku a zobrazení funguje i po restartu.
  - [ ] Validace vstupu zachytí prázdný/špatný odkaz.
- [x] Doména: `reaction roles`
  - [x] Přidání/odebrání role při reakci funguje.
  - [x] Ošetření chyb (neautorizovaný bot, invalid role, missing permission) je stabilní.
- [ ] Datová vrstva `db/*.json`
  - [ ] Zápis změn je atomický a soubory se nepokazí při paralelním přístupu.
  - [ ] Migrace / kompatibilita se staršími záznamy drží konzistenci.
- [ ] Scheduler
  - [ ] Cron joby se spustí po startu a po změně nastavení se přepnou.
  - [ ] Na opakované spuštění botu nedojde k duplikaci úloh.
