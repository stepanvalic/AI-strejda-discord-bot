# Dokumentace bota

Tohle je rychlá provozní dokumentace pro Node.js slash verzi bota. Cílem je, aby šlo:

1. vyplnit `.env`
2. vyplnit `config/runtime.local.json`
3. zaregistrovat slash commandy
4. bota pustit

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

## Single-server rezim

Bot je schválně zamčený na jeden server.

- `DISCORD_GUILD_ID` v `.env` je hlavni zdroj pravdy.
- Pokud přijde event nebo slash command z jiného serveru, bot ho ignoruje.
- Pokud `DISCORD_GUILD_ID` chybí, bot nenastartuje.

## Commandy a oprávnění

### Utility

Vsechni:

- `/youtube` - odkaz na sledovany YouTube kanal
- `/youtube-kanal` - ukaze Discord kanal pro YouTube notifikace
- `/uptime` - jak dlouho bot bezi
- `/pozvanka` - vytvori invite
- `/prikazy` - seznam vsech dostupnych commandu
- `/help` - seznam commandu pro bezne uzivatele
- `/pravidla` - ukaze pravidla serveru

Admin:

- `/pravidla-publikovat` - posle nebo upravi embed s pravidly

### Onboarding

Admin:

- `/uvitat` - znovu pusti welcome flow
- `/doplnit-default-roli` - doplni default roli vsem
- `/reaction-roles-sync` - znovu vytvori nebo upravi reaction role panel

### Moderation

Admin:

- `/timeout` - timeout clena
- `/untimeout` - zrusi timeout
- `/ban` - banne clena
- `/unban` - unban podle user ID

### Counting

Vsechni:

- `/counting-pravidla` - pravidla countingu
- `/counting-statistiky` - top 10 nebo detail clena
- `/counting-formaty` - podporovane ciselne formaty

Admin:

- `/counting-stav` - aktualni stav countingu
- `/counting-reset` - reset na nulu
- `/counting-block` - manualni blokace uzivatele
- `/counting-blocklist` - vypis blokovanych
- `/counting-unblock` - odblokace uzivatele
- `/counting-kanal-nastav` - prepise counting kanal
- `/counting-kanal` - ukaze aktivni counting kanal

### AI scoring

Vsechni:

- `/ai-skore` - tvoje nebo cizi AI score
- `/ai-top` - top 10 podle AI score
- `/ai-bottom` - bottom 10 podle AI score

Admin:

- `/ai-sync-role` - oprav role podle score
- `/ai-pravidla` - ukaze AI thresholds a konfiguraci
- `/ai-reset-user` - reset score jednoho clena
- `/ai-reset-all` - reset score vsech

### Summary

Vsechni:

- `/summary-posledni` - posle DM shrnuti poslednich N zprav

Admin:

- `/summary-den` - vygeneruje denni shrnuti
- `/summary-pocet-dnes` - pocet dnes ulozenych zprav

### Bookmarky

Vsechni:

- `/bookmark-uloz` - ulozi bookmark podle message linku
- `/bookmarky` - posle bookmarky do DM
- `/bookmark-smaz` - smaze bookmark podle poradi

### Setup

Admin:

- `/setup-youtube-kanal` - vytvori YouTube kanal
- `/setup-counting-kanal` - vytvori counting kanal
- `/setup-summary-kanal` - vytvori summary kanal
- `/setup-audit-kanal` - vytvori audit kanal
- `/setup-vse` - udela zakladni setup naraz
- `/setup-prava` - nastavi zakladni prava
- `/setup-audit-existujici` - pouzije existujici kanal jako audit
- `/log-level` - zmeni log level
- `/filter-pridej-slovo` - prida slovo do blacklistu

### YouTube admin

Admin:

- `/youtube-check` - zkontroluje nejnovesi video
- `/youtube-refresh` - refreshne metadata poslednich videi
- `/youtube-posli-znovu` - posle posledni video znovu

### Hidden

Admin:

- `/shutdown` - vypne proces bota

Tenhle command je zamerne schovany z bezneho vypisu, ale registruje se.

## Co dela kdo na pozadi

### Bezni uzivatele

- mohou pouzivat utility commandy
- mohou pouzivat bookmarky
- mohou pouzivat counting kanal
- mohou si nechat poslat DM summary
- mohou videt AI score

### Admini

- maji pristup ke setupu
- maji moderaci
- resi AI resety a sync roli
- ridi denni summary
- spravuji reaction roles

## Background chovani

- welcome flow bezi na `GuildMemberAdd`
- reaction roles poslouchaji add/remove reakci
- word filter maze blacklistovana slova
- counting bezi jen v `counting.channelId`
- AI scoring bezi jen v `ai.moderationChannelIds`
- summary uklada zpravy jen z `summary.sourceChannelId`
- YouTube polling jede intervalove
- daily summary se generuje v hodinu `summary.dailyHour`

## Doporuceny start

1. Zkopiruj `.env.example` na `.env`
2. Zkopiruj `config/runtime.example.json` na `config/runtime.local.json`
3. Vypln vsechna ID a klice
4. `npm install`
5. `npm run register:commands`
6. `npm start`

## Poznamky k datum a DM summary

- `/summary-den` umi `DD/MM/YYYY` i `YYYY-MM-DD`
- `/summary-posledni` ma cooldown pro bezne uzivatele
- admin cooldown obchazi
