# AI Strejda Discord Bot

Node.js rewrite Discord bota postavený čistě na slash commandech. Projekt je navržený kolem lokálních JSON dat v `db/`, aby šlo navázat na existující historii bez okamžité migrace do SQL.

## Co je hotové v kostře

- slash command router a registrace commandů
- config store rozdeleny na `.env` a `config/runtime.local.json`
- JSON persistence vrstva pro stávající `db/*.json` a `db/sumar/*.json`
- doménové služby pro welcome, moderation, counting, AI score, summary, YouTube, bookmarky a reaction roles
- schedulery pro YouTube polling a denni summary

## Doporučený layout konfigurace

1. Zkopiruj `.env.example` na `.env`
2. Zkopiruj `config/runtime.example.json` na `config/runtime.local.json`
3. Doplň tokeny do `.env`
4. Doplň guild/channel/role ID a texty do `config/runtime.local.json`

Tajnosti patří do `.env`, provozní stav a ID do `config/runtime.local.json`.
`DISCORD_GUILD_ID` v `.env` je nadřazený a bot mimo tenhle server nic nezpracuje.

## Zakladni skripty

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

## Poznamky

- `db/` a `docs/` zůstávají lokální a ignorované v gitu.
- Runtime config je zapisovatelný, aby setup slash commandy uměly měnit channel/message ID.
- Pro summary a AI integrace je připravený fetch-based client, ale bez tokenů se jen bezpečně vypnou.
