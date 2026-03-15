# AI Strejda Discord Bot

Node.js + TypeScript rewrite Discord bota postaveny nad mistni dokumentaci v `docs/rewrite/`.

Aktualni stav:

- slash-command kostra pro vsechny hlavni domeny z docs
- validace `.env` a verejneho JSON configu
- bootstrap Discord klienta, slash registrace a zakladni event wiring
- zakladni utility, onboarding a moderation flow
- placeholder domenove sluzby pro counting, AI, summary, bookmarks, audit a YouTube

Zakladni soubory:

- `.env.example` - vsechny dulezite env promenne
- `config/bot.config.example.json` - netajne texty, feature flagy a reaction role mapping
- `src/scripts/register-slash-commands.ts` - registrace guild slash commandu
- `src/index.ts` - start aplikace

Dalsi krok:

1. zkopirovat `.env.example` do `.env`
2. vytvorit `config/bot.config.json` z prikladu
3. nainstalovat zavislosti
4. spustit `npm run register:commands`
5. spustit `npm run dev`

Poznamka:

- `server.cfg` zustal beze zmen
- nic se automaticky neinstalovalo
