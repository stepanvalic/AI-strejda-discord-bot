# AI Strejda Discord Bot

Discord bot vytvořený pro správu a moderování Discord serverů s využitím AI.

## Funkce

- **AI Moderace**: Automatická analýza zpráv pomocí Google Gemini AI pro detekci nevhodného obsahu
- **YouTube Notifikace**: Automatické oznámení nových videí z nastaveného YouTube kanálu
- **Počítání**: Herní kanál pro počítání s leaderboardem a statistikami
- **Audit Log**: Sledování všech událostí na serveru
- **Automatické Uvítání**: Personalizované uvítací zprávy pro nové členy
- **Moderační Příkazy**: Příkazy pro timeout, ban a další moderační akce
- **Chat Shrnutí**: Automatické shrnutí konverzací pomocí AI

## Instalace

1. Naklonujte repozitář:
```bash
git clone https://github.com/stepanvalic/AI-strejda-discord-bot.git
cd AI-strejda-discord-bot
```

2. Vytvořte virtuální prostředí a nainstalujte závislosti:
```bash
python -m venv venv
source venv/bin/activate  # Na Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Vytvořte soubor `.env` podle šablony `.env.template` a vyplňte potřebné API klíče:
```
DISCORD_TOKEN=váš_discord_token
GEMINI_API_KEY=váš_gemini_api_klíč
OPENROUTER_API_KEY=váš_openrouter_api_klíč
YOUTUBE_API_KEY=váš_youtube_api_klíč
```

## Použití

Spusťte bota příkazem:
```bash
source venv/bin/activate.fish && python bot.py
```

### Základní příkazy

- `!setup` - Nastavení všech potřebných kanálů (pouze pro adminy)
- `!youtube` - Zobrazí odkaz na YouTube kanál
- `!count` - Zobrazí aktuální stav počítání (pouze v počítacím kanálu)
- `!countstats` - Zobrazí statistiky počítání
- `!timeout @uživatel [čas]` - Timeout pro uživatele (pouze pro adminy)
- `!ban @uživatel [důvod]` - Ban pro uživatele (pouze pro adminy)
- `!unban [user_id]` - Odbanování uživatele (pouze pro adminy)
- `!prikazy` - Seznam všech dostupných příkazů

## Konfigurace

Konfigurace bota je uložena v souboru `config.json` v přehledném formátu. API klíče a tokeny jsou uloženy v souboru `.env`.

## Struktura projektu

- `bot.py` - Hlavní soubor bota
- `config.json` - Konfigurační soubor v JSON formátu
- `config_loader.py` - Modul pro načítání konfigurace
- `cogs/` - Moduly s funkcionalitou bota
- `utils/` - Pomocné utility
- `db/` - Databázové soubory (JSON)
- `log/` - Logy bota

## Licence

Tento projekt je licencován pod MIT licencí - viz soubor [LICENSE](LICENSE) pro detaily.
