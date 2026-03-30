# Dokumentace bota

Tohle je rychlá provozní dokumentace pro Node.js slash verzi bota. Cílem je, aby šlo:

1. vyplnit `.env`
2. vyplnit `config/runtime.local.json`
3. zaregistrovat slash commandy
4. bota spustit

## Co kam patří

### `.env`

Sem patří tajné věci a hard lock na jeden Discord server.

Povinné:

- `DISCORD_TOKEN`
- `DISCORD_CLIENT_ID`
- `DISCORD_GUILD_ID`

Další podle zapnutých feature:

- `YOUTUBE_API_KEY`
- `GEMINI_API_KEY`
- `DEEPSEEK_API_KEY`

Provozní:

- `BOT_CONFIG_PATH`
- `DATA_DIR`
- `SUMMARY_DIR`
- `LOG_LEVEL`
- `TIMEZONE`

### `config/runtime.local.json`

Sem patří všechna Discord ID, texty, mapování rolí a feature nastavení.

Vyplň hlavně:

- `guild.welcomeChannelId`
- `guild.defaultRoleId`
- `reactionRoles.channelId`
- `reactionRoles.mappings`
- `youtube.notificationChannelId`
- `youtube.pingRoleId`
- `counting.channelId`
- `ai.moderationChannelIds`
- `ai.positiveRoleIds`
- `ai.negativeRoleId`
- `summary.sourceChannelId`
- `summary.targetChannelId`
- `audit.channelId`
- `features.setup` (nastavení, jestli mají být setup commandy aktivní)
- `youtube.checkIntervalSeconds` už se aktuálně nepoužívá, interval je řízen schedulerem na 60 sekund

### `db/`

Sem se ukládají lokální JSON data bota.

- bookmarky jsou natvrdo v `db/bookmarks.json`
- ostatní runtime data jedou podle `DATA_DIR`
- denní summary se ukládají do `db/sumar/` nebo podle `SUMMARY_DIR`
- token usage se zapisuje do `db/token_usage.json` ve formátu s `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_usd`

## Single-server režim

Bot je schválně zamčený na jeden server.

- `DISCORD_GUILD_ID` v `.env` je hlavní zdroj pravdy
- pokud přijde event nebo slash command z jiného serveru, bot ho ignoruje
- pokud `DISCORD_GUILD_ID` chybí, bot nenastartuje

## Commandy a oprávnění

### Utility

Všichni:

- `/uptime` - jak dlouho bot běží
- `/pozvanka` - vytvoří invite
- `/prikazy` - seznam všech dostupných commandů
- `/help` - seznam commandů pro běžné uživatele
- `/pravidla` - ukáže pravidla serveru

Admin:

- `/pravidla-publikovat` - pošle nebo upraví embed s pravidly

### Onboarding

Admin:

- `/doplnit-default-roli` - doplní default roli všem
- `/reaction-roles-sync` - znovu vytvoří nebo upraví reaction role panel

### Moderation

Admin:

- `/timeout` - timeout člena
- `/untimeout` - zruší timeout
- `/ban` - banuje člena
- `/unban` - unban podle user ID

### Counting

Všichni:

- `/counting-pravidla` - pravidla countingu
- `/counting-statistiky` - top 10 nebo detail člena
- `/counting-formaty` - podporované číselné formáty

Admin:

- `/counting-stav` - aktuální stav countingu
- `/counting-block` - manuální blokace uživatele
- `/counting-blocklist` - výpis blokovaných
- `/counting-unblock` - odblokace uživatele
- `/counting-kanal-nastav` - přepíše counting kanál
- `/counting-kanal` - ukáže aktivní counting kanál

### AI scoring

Všichni:

- `/ai-skore` - tvoje nebo cizí AI score
- `/ai-top` - top 10 podle AI score
- `/ai-bottom` - bottom 10 podle AI score

Admin:

- `/ai-sync-role` - opraví role podle score
- `/ai-pravidla` - ukáže AI thresholds a konfiguraci

### Summary

Všichni:

- `/summary-posledni` - pošle DM shrnutí posledních N zpráv

Admin:

- `/summary-den` - vygeneruje denní shrnutí
- `/summary-pocet-dnes` - počet dnes uložených zpráv

### Bookmarky

Všichni:

- `/bookmark-uloz` - uloží bookmark podle message linku
- `/bookmarky` - pošle bookmarky do DM
- `/bookmark-smaz` - smaže bookmark podle pořadí

### Setup

Admin:

- `/setup-youtube-kanal` - vytvoří YouTube kanál
- `/setup-counting-kanal` - vytvoří counting kanál
- `/setup-summary-kanal` - vytvoří summary kanál
- `/setup-audit-kanal` - vytvoří audit kanál
- `/setup-vse` - udělá základní setup naráz
- `/setup-prava` - nastaví základní práva
- `/setup-audit-existujici` - použije existující kanál jako audit
- `/setup-reakcni-role` - nastaví kanál pro reakční role a založí panel
- `/log-level` - změní log level
- `/filter-pridej-slovo` - přidá slovo do blacklistu

Poznámka:

- setup commandy lze vypnout přes `features.setup`

### YouTube admin

Admin:

- `/youtube-check` - zkontroluje nejnovější video
- `/youtube-refresh` - refreshne metadata posledních videí
- `/youtube-posli-znovu` - pošle poslední video znovu

### YouTube automatika

- scheduler kontroluje nové video každou minutu
- po kontrole nového videa se aktualizují metriky posledních 10 odeslaných oznámení (`zhlédnutí`, `lajky`, `komentáře`)
- metriky se při této aktualizaci přepisují přímo v odeslaných embed zprávách, bez opakovaného pingu

## Co dělá kdo na pozadí

### Běžní uživatelé

- mohou používat utility commandy
- mohou používat bookmarky
- mohou používat counting kanál
- mohou si nechat poslat DM summary
- mohou vidět AI score

### Admini

- mají přístup k setupu
- mají moderaci
- řeší AI sync rolí
- řídí denní summary
- spravují reaction roles

## Background chování

- welcome flow běží automaticky 24/7 na `GuildMemberAdd`
- reaction roles poslouchají add/remove reakcí
- word filter maže blacklistovaná slova
- counting běží jen v `counting.channelId`
- AI scoring běží jen v `ai.moderationChannelIds`
- summary ukládá zprávy jen z `summary.sourceChannelId`
- YouTube polling jede intervalově
- daily summary se generuje v hodinu `summary.dailyHour`

## Doporučený start

1. zkopíruj `.env.example` na `.env`
2. zkopíruj `config/runtime.example.json` na `config/runtime.local.json`
3. vyplň všechna ID a klíče
4. `npm install`
5. `npm run register:commands`
6. `npm start`

## Poznámky k datu a DM summary

- `/summary-den` umí `DD/MM/YYYY` i `YYYY-MM-DD`
- `/summary-posledni` má cooldown pro běžné uživatele
- admin cooldown obchází

## DeepSeek tokenová spotřeba

- Každá AI sumarizace přes DeepSeek se zapisuje do `db/token_usage.json`.
- `cost_usd` se počítá podle interního ceníku:
  - `deepseek-chat` input: `0.0005 USD / 1 000 tokenů`
  - `deepseek-chat` output: `0.0025 USD / 1 000 tokenů`

## Setup commandy

- Všechny setup commandy lze globálně vypnout nastavením `"features.setup": false` v `config/runtime.local.json`.
- Když jsou vypnuté, v registraci Discord commandů se vůbec neukazují.
