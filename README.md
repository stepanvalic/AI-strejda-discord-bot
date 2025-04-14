# AI Strejda Discord Bot

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Discord Bot Setup](#discord-bot-setup)
  - [YouTube API Setup](#youtube-api-setup-for-youtube-notifications)
  - [Google Gemini API Setup](#google-gemini-api-setup-for-ai-moderation)
- [Usage](#usage)
  - [Commands](#commands)
- [How AI Moderation Works](#how-ai-moderation-works)
  - [Troubleshooting AI Moderation](#troubleshooting-ai-moderation)
- [Project Structure](#project-structure)
- [Extending the Bot](#extending-the-bot)
- [License](#license)
- [Česká verze](#ai-strejda-discord-bot-česky)

[Česká verze níže](#ai-strejda-discord-bot-česky)

## Overview

AI Strejda Discord Bot is a versatile Discord bot designed to enhance your server with welcome messages, YouTube notifications, and dynamic status updates. The bot is built with modularity in mind, allowing for easy extension and customization.

## Features

- **Welcome Messages**: Automatically sends personalized welcome embeds when new members join your server
- **YouTube Notifications**: Monitors your YouTube channel and sends notifications with rich embeds when new videos are uploaded
- **Dynamic Status**: Displays the current member count in the bot's status
- **Counting Game**: Provides a fun counting game where users count up from 1 to infinity with rules and statistics
- **AI Moderation**: Uses Google Gemini AI to analyze message sentiment, reward positive behavior with multiple role levels (800/2000/5000 points), and penalize negative behavior with timeouts and roles (-30/-1000 points). Analyzes batches of messages per user, applies additional penalties for very negative messages, and provides comprehensive user statistics
- **Database Storage**: Uses JSON files to store information about announced videos, counting statistics, and user behavior
- **Automatic Updates**: Regularly updates YouTube video embeds with current view and like counts

## Requirements

- Python 3.8 or higher
- Discord Bot Token
- YouTube API Key (for YouTube notifications)
- Google Gemini API Key (for AI moderation)
- Discord server with appropriate permissions

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/stepanvalic/AI-strejda-discord-bot.git
   cd AI-strejda-discord-bot
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the template:
   ```
   cp .env.template .env
   ```

5. Edit the `.env` file with your configuration details:
   - Discord Bot Token
   - Server ID
   - Welcome Channel ID
   - YouTube API Key (if using YouTube notifications)
   - YouTube Channel ID

   Note: You can use the `!setup` command to automatically create and configure the YouTube notification channel and counting channel.

## Configuration

### Discord Bot Setup

1. Create a new application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Go to the "Bot" tab and click "Add Bot"
3. Under "Privileged Gateway Intents", enable:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
4. Copy the bot token and add it to your `.env` file
5. Generate an invite link with appropriate permissions and invite the bot to your server

### YouTube API Setup (for YouTube notifications)

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the YouTube Data API v3
3. Create an API key and add it to your `.env` file
4. Add your YouTube channel handle (with @ symbol) or channel ID to the `.env` file

### Google Gemini API Setup (for AI moderation)

1. Create an account at [Google AI Studio](https://aistudio.google.com/)
2. Generate an API key
3. Add the API key to your `.env` file as `GEMINI_API_KEY`
4. Enable the Generative Language API in Google Cloud Console
5. Configure the AI moderation settings in your `.env` file:
   ```
   # AI Moderation Configuration
   GEMINI_API_KEY=your_gemini_api_key_here
   AI_MODEL=gemini-2.0-flash
   AI_MESSAGES_BATCH=51
   AI_MODERATION_SAVE_FILE=db/ai_moderation.json
   AI_MODERATION_INTERVAL_MINUTES=5
   AI_POSITIVE_THRESHOLD_1=800
   AI_POSITIVE_THRESHOLD_2=2000
   AI_POSITIVE_THRESHOLD_3=5000
   AI_NEGATIVE_THRESHOLD=-30
   AI_VERY_NEGATIVE_THRESHOLD=-1000
   AI_NEGATIVE_PENALTY=-50
   AI_POSITIVE_ROLE_ID_1=your_positive_role_id_level1_here
   AI_POSITIVE_ROLE_ID_2=your_positive_role_id_level2_here
   AI_POSITIVE_ROLE_ID_3=your_positive_role_id_level3_here
   AI_NEGATIVE_ROLE_ID=your_negative_role_id_here
   ```

6. Create roles in your Discord server for each level:
   - Level 1 Positive Role (for users with 800+ points)
   - Level 2 Positive Role (for users with 2000+ points)
   - Level 3 Positive Role (for users with 5000+ points)
   - Negative Role (for users with -1000 or lower points)
7. Get the role IDs (right-click on each role and select "Copy ID")
8. Add the role IDs to your `.env` file

## Usage

Start the bot with:
```
python bot.py
```

### Commands

#### Utility Commands
- `!uptime` - Shows how long the bot has been running
- `!discord` or `!dc` - Generates a Discord server invite
- `!prikazy` or `!commands` - Lists all available commands

#### YouTube Commands
- `!yt` or `!youtube` - Shows the YouTube channel link
- `!kanal` - Shows the channel with the best flow
- `!checkyoutube` - Manually check for the latest YouTube video (admin only)
- `!updatevideos` - Manually update all video embeds (admin only)

#### Counting Game Commands
- `!count` - Show the current counting status and next number
- `!countstats` - Display the top 10 users in the counting game with statistics
- `!countrules` - Show the rules of the counting game
- `!countreset` - Reset the counting game (admin only)

#### AI Moderation Commands
- `!aiscore [@user]` - Shows the AI sentiment score for yourself or a mentioned user
- `!aitop` - Shows the top 10 users with the highest AI sentiment scores
- `!aibottom` - Shows the 10 users with the lowest AI sentiment scores
- `!airules` - Shows the rules and thresholds of the AI moderation system (admin only)
- `!aireset [@user]` - Resets the AI score for a specific user (admin only)
- `!airesetall` - Resets the AI scores for all users (admin only)

#### Moderation Commands
- `!timeout [@user] [time]` - Timeout a user for the specified time (admin only). Time format: 5s, 3m, 2h, 1d, 1y or combinations like 1d12h30m (maximum 28 days due to Discord limit)
- `!untimeout` or `!unmute [@user]` - Remove timeout from a user (admin only)
- `!ban [@user] [reason]` - Permanently ban a user with optional reason (admin only)
- `!unban [user_id]` - Unban a user by their ID (admin only)
- `!welcome [@user]` - Manually send a welcome message for a user (admin only)

#### System Commands
- `!shutdown` - Shutdown the bot (owner only)

## How AI Moderation Works

The AI Moderation system uses Google's Gemini AI to analyze user messages and automatically moderate your Discord server:

1. The bot collects messages from users (up to 51 messages per user by default)
2. When a user reaches the batch size or at regular intervals (default: 5 minutes), it analyzes these messages using the AI model
3. Each analysis produces a positive and negative score
4. Very negative messages receive an additional -50 point penalty
5. These scores are added to the user's total score
6. If a user's total score falls below -30, they receive a timeout
7. If a user's total score falls below -1000, they receive the negative role
8. If a user's total score rises above the positive thresholds, they receive the corresponding positive roles
9. Timeout duration increases with repeated offenses (starting at 5 minutes, up to 24 hours)
10. Admins are analyzed but not penalized
11. All data is stored in a JSON file for persistence

### Troubleshooting AI Moderation

- If the bot is not analyzing messages, check that your Google Gemini API key is valid and the API is enabled
- If timeouts are not being applied, ensure the bot has the "Moderate Members" permission
- If roles are not being assigned, ensure the bot has the "Manage Roles" permission and its role is higher than all the AI moderation roles in the server settings

## Project Structure

- `bot.py` - Main bot file that loads all modules
- `cogs/` - Directory containing all bot modules:
  - `welcome.py` - Welcome message functionality
  - `bot_activity.py` - Bot status functionality
  - `youtube_video_ping.py` - YouTube notification functionality
  - `counting.py` - Counting game functionality
  - `setup.py` - Automatic channel setup functionality
  - `utility.py` - Utility commands functionality
  - `moderation.py` - Moderation commands functionality
  - `ai_moderation.py` - AI moderation functionality
- `utils/` - Utility modules:
  - `db.py` - Database functionality for storing video information
- `db/` - Directory for JSON database files
- `.env` - Configuration file for bot settings
- `requirements.txt` - Python dependencies

## Extending the Bot

To add new functionality, create a new cog file in the `cogs` directory and load it in `bot.py`. See the existing cogs for examples.

## License

This project is open source and available under the [MIT License](LICENSE).

---

# AI Strejda Discord Bot (Česky)

## Obsah
- [Přehled](#přehled)
- [Funkce](#funkce)
- [Požadavky](#požadavky)
- [Instalace](#instalace)
- [Konfigurace](#konfigurace)
  - [Nastavení Discord Bota](#nastavení-discord-bota)
  - [Nastavení YouTube API](#nastavení-youtube-api-pro-youtube-oznámení)
  - [Nastavení Google Gemini API](#nastavení-google-gemini-api-pro-ai-moderaci)
- [Použití](#použití)
  - [Příkazy](#příkazy)
- [Jak funguje AI moderace](#jak-funguje-ai-moderace)
  - [Řešení problémů s AI moderací](#řešení-problémů-s-ai-moderací)
- [Struktura projektu](#struktura-projektu)
- [Rozšíření bota](#rozšíření-bota)
- [Licence](#licence)

## Přehled

AI Strejda Discord Bot je všestranný Discord bot navržený pro vylepšení vašeho serveru pomocí uvítacích zpráv, oznámení o nových YouTube videích a dynamických aktualizací statusu. Bot je vytvořen s důrazem na modularitu, což umožňuje snadné rozšíření a přizpůsobení.

## Funkce

- **Uvítací zprávy**: Automaticky odesílá personalizované uvítací embedy, když se na server připojí noví členové
- **YouTube oznámení**: Sleduje váš YouTube kanál a odesílá oznámení s bohatými embedy, když jsou nahrána nová videa
- **Dynamický status**: Zobrazuje aktuální počet členů ve statusu bota
- **Hra na počítání**: Poskytuje zábavnou hru, kde uživatelé počítají od 1 do nekonečna s pravidly a statistikami
- **AI Moderace**: Používá Google Gemini AI k analýze sentimentu zpráv, odměňování pozitivního chování více úrovněmi rolí (800/2000/5000 bodů) a penalizaci negativního chování timeouty a rolemi (-30/-1000 bodů). Analyzuje dávky zpráv od uživatelů, aplikuje dodatečné penalizace za velmi negativní zprávy a poskytuje komplexní statistiky uživatelů
- **Ukládání dat**: Používá JSON soubory pro ukládání informací o oznámených videích, statistikách počítání a chování uživatelů
- **Automatické aktualizace**: Pravidelně aktualizuje YouTube embedy s aktuálními počty zhlédnutí a lajků

## Požadavky

- Python 3.8 nebo vyšší
- Discord Bot Token
- YouTube API klíč (pro YouTube oznámení)
- Google Gemini API klíč (pro AI moderaci)
- Discord server s příslušnými oprávněními

## Instalace

1. Naklonujte tento repozitář:
   ```
   git clone https://github.com/stepanvalic/AI-strejda-discord-bot.git
   cd AI-strejda-discord-bot
   ```

2. Vytvořte a aktivujte virtuální prostředí:
   ```
   python -m venv venv
   source venv/bin/activate  # Na Windows: venv\Scripts\activate
   ```

3. Nainstalujte potřebné závislosti:
   ```
   pip install -r requirements.txt
   ```

4. Vytvořte soubor `.env` podle šablony:
   ```
   cp .env.template .env
   ```

5. Upravte soubor `.env` s vašimi konfiguračními údaji:
   - Discord Bot Token
   - ID serveru
   - ID kanálu pro uvítací zprávy
   - YouTube API klíč (pokud používáte YouTube oznámení)
   - ID YouTube kanálu

   Poznámka: Setup příkazy byly deaktivovány. Kanály je nyní potřeba vytvořit ručně a ID přidat do .env souboru.

## Konfigurace

### Nastavení Discord Bota

1. Vytvořte novou aplikaci na [Discord Developer Portal](https://discord.com/developers/applications)
2. Přejděte na záložku "Bot" a klikněte na "Add Bot"
3. V sekci "Privileged Gateway Intents" povolte:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
4. Zkopírujte token bota a přidejte ho do vašeho souboru `.env`
5. Vygenerujte pozvánku s příslušnými oprávněními a pozvěte bota na váš server

### Nastavení YouTube API (pro YouTube oznámení)

1. Vytvořte projekt v [Google Cloud Console](https://console.cloud.google.com/)
2. Povolte YouTube Data API v3
3. Vytvořte API klíč a přidejte ho do vašeho souboru `.env`
4. Přidejte handle vašeho YouTube kanálu (se symbolem @) nebo ID kanálu do souboru `.env`

### Nastavení Google Gemini API (pro AI moderaci)

1. Vytvořte účet na [Google AI Studio](https://aistudio.google.com/)
2. Vygenerujte API klíč
3. Přidejte API klíč do vašeho souboru `.env` jako `GEMINI_API_KEY`
4. Povolte Generative Language API v Google Cloud Console
5. Nakonfigurujte nastavení AI moderace ve vašem souboru `.env`:
   ```
   # Konfigurace AI Moderace
   GEMINI_API_KEY=vas_gemini_api_klic_zde
   AI_MODEL=gemini-2.0-flash
   AI_MESSAGES_BATCH=51
   AI_MODERATION_SAVE_FILE=db/ai_moderation.json
   AI_MODERATION_INTERVAL_MINUTES=5
   AI_POSITIVE_THRESHOLD_1=800
   AI_POSITIVE_THRESHOLD_2=2000
   AI_POSITIVE_THRESHOLD_3=5000
   AI_NEGATIVE_THRESHOLD=-30
   AI_VERY_NEGATIVE_THRESHOLD=-1000
   AI_NEGATIVE_PENALTY=-50
   AI_POSITIVE_ROLE_ID_1=id_pozitivni_role_uroven1_zde
   AI_POSITIVE_ROLE_ID_2=id_pozitivni_role_uroven2_zde
   AI_POSITIVE_ROLE_ID_3=id_pozitivni_role_uroven3_zde
   AI_NEGATIVE_ROLE_ID=id_negativni_role_zde
   ```

6. Vytvořte role na vašem Discord serveru pro každou úroveň:
   - Role pro 1. úroveň pozitivního skóre (pro uživatele s 800+ body)
   - Role pro 2. úroveň pozitivního skóre (pro uživatele s 2000+ body)
   - Role pro 3. úroveň pozitivního skóre (pro uživatele s 5000+ body)
   - Negativní role (pro uživatele s -1000 nebo nižším skóre)
7. Získejte ID rolí (klikněte pravým tlačítkem na každou roli a vyberte "Kopírovat ID")
8. Přidejte ID rolí do vašeho souboru `.env`

## Použití

Spusťte bota příkazem:
```
python bot.py
```

### Příkazy

#### Užitečné příkazy
- `!uptime` - Zobrazí, jak dlouho je bot online
- `!discord` nebo `!dc` - Vygeneruje pozvánku na Discord server
- `!prikazy` nebo `!commands` - Zobrazí seznam všech dostupných příkazů

#### YouTube příkazy
- `!yt` nebo `!youtube` - Zobrazí odkaz na YouTube kanál
- `!kanal` - Zobrazí kanál s nejlepší flow
- `!checkyoutube` - Ručně zkontroluje nejnovější YouTube video (pouze admin)
- `!updatevideos` - Ručně aktualizuje všechny video embedy (pouze admin)

#### Počítací příkazy
- `!count` - Zobrazí aktuální stav počítání a další číslo
- `!countstats` - Zobrazí top 10 uživatelů ve hře na počítání se statistikami
- `!countrules` - Zobrazí pravidla hry na počítání
- `!countreset` - Resetuje hru na počítání (pouze admin)

#### AI Moderace příkazy
- `!aiscore [@uživatel]` - Zobrazí AI skóre sentimentu pro vás nebo zmíněného uživatele
- `!aitop` - Zobrazí top 10 uživatelů s nejvyšším AI skóre sentimentu
- `!aibottom` - Zobrazí 10 uživatelů s nejnižším AI skóre sentimentu
- `!airules` - Zobrazí pravidla a hranice AI moderačního systému (pouze admin)
- `!aireset [@uživatel]` - Resetuje AI skóre pro konkrétního uživatele (pouze admin)
- `!airesetall` - Resetuje AI skóre pro všechny uživatele (pouze admin)

#### Moderační příkazy
- `!timeout [@uživatel] [čas]` - Dá uživateli timeout na určitou dobu (pouze admin). Formát času: 5s, 3m, 2h, 1d, 1y nebo kombinace např. 1d12h30m (maximum 28 dní kvůli omezení Discordu)
- `!untimeout` nebo `!unmute [@uživatel]` - Zruší timeout uživateli (pouze admin)
- `!ban [@uživatel] [důvod]` - Trvale zabanuje uživatele s volitelným důvodem (pouze admin)
- `!unban [user_id]` - Odbanuje uživatele podle jeho ID (pouze admin)
- `!welcome [@uživatel]` - Ručně odešle uvítací zprávu pro uživatele (pouze admin)

#### Systémové příkazy
- `!shutdown` - Vypne bota (pouze vlastník)

## Jak funguje AI moderace

Systém AI moderace používá Google Gemini AI k analýze zpráv uživatelů a automatické moderaci vašeho Discord serveru:

1. Bot sbírá zprávy od uživatelů (standardně až 51 zpráv na uživatele)
2. Když uživatel dosáhne velikosti dávky nebo v pravidelných intervalech (standardně: 5 minut), analyzuje tyto zprávy pomocí AI modelu
3. Každá analýza vytvoří pozitivní a negativní skóre
4. Velmi negativní zprávy dostanou dodatečnou penalizaci -50 bodů
5. Tato skóre se přičítají k celkovému skóre uživatele
6. Pokud celkové skóre uživatele klesne pod -30, dostane timeout
7. Pokud celkové skóre uživatele klesne pod -1000, dostane negativní roli
8. Pokud celkové skóre uživatele stoupne nad pozitivní hranice, dostane odpovídající pozitivní role
9. Délka timeoutu se zvyšuje s opakovanými přestupky (začíná na 5 minutách, až do 24 hodin)
10. Admini jsou analyzováni, ale nejsou penalizováni
11. Všechna data jsou uložena v JSON souboru pro persistenci

### Řešení problémů s AI moderací

- Pokud bot neanalyzuje zprávy, zkontrolujte, že váš Google Gemini API klíč je platný a API je povoleno
- Pokud nejsou aplikovány timeouty, ujistěte se, že bot má oprávnění "Moderate Members"
- Pokud nejsou přiřazovány role, ujistěte se, že bot má oprávnění "Manage Roles" a jeho role je výše než všechny AI moderační role v nastavení serveru

## Struktura projektu

- `bot.py` - Hlavní soubor bota, který načítá všechny moduly
- `cogs/` - Adresář obsahující všechny moduly bota:
  - `welcome.py` - Funkcionalita uvítacích zpráv
  - `bot_activity.py` - Funkcionalita statusu bota
  - `youtube_video_ping.py` - Funkcionalita YouTube oznámení
  - `counting.py` - Funkcionalita hry na počítání
  - `setup.py` - Funkcionalita automatického nastavení kanálů
  - `utility.py` - Funkcionalita užitečných příkazů
  - `moderation.py` - Funkcionalita moderačních příkazů
  - `ai_moderation.py` - Funkcionalita AI moderace
- `utils/` - Užitečné moduly:
  - `db.py` - Databázová funkcionalita pro ukládání informací o videích
- `db/` - Adresář pro JSON databázové soubory
- `.env` - Konfigurační soubor pro nastavení bota
- `requirements.txt` - Python závislosti

## Rozšíření bota

Pro přidání nové funkcionality vytvořte nový cog soubor v adresáři `cogs` a načtěte ho v `bot.py`. Podívejte se na existující cogy pro příklady.

## Licence

Tento projekt je open source a dostupný pod [MIT licencí](LICENSE).
