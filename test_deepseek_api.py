#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test skript pro DeepSeek API
Tento skript testuje připojení k DeepSeek API a generování odpovědí.
DeepSeek API používá formát kompatibilní s OpenAI API.

Použití:
    python test_deepseek_api.py

Požadavky:
    - Nainstalovaný balíček openai: pip install openai
    - Nastavený API klíč v proměnné prostředí DEEPSEEK_API_KEY nebo v souboru .env
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Načtení proměnných prostředí z .env souboru
load_dotenv()

# Získání API klíče z proměnných prostředí
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    print("❌ Chyba: API klíč není nastaven.")
    print("Nastavte proměnnou prostředí DEEPSEEK_API_KEY nebo přidejte ji do .env souboru.")
    exit(1)

# Inicializace klienta OpenAI s DeepSeek API
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"  # Můžete použít i "https://api.deepseek.com"
)

# Testovací prompt
system_prompt = "Jsi užitečný asistent, který odpovídá v češtině."
user_prompt = "Napiš krátké shrnutí o tom, co je to umělá inteligence."

# Výběr modelu
# 'deepseek-chat' = DeepSeek-V3
# 'deepseek-reasoner' = DeepSeek-R1
model = "deepseek-chat"

print(f"🔄 Odesílám požadavek na DeepSeek API s modelem {model}...")

try:
    # Odeslání požadavku na API
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        stream=False
    )

    # Výpis odpovědi
    print("\n✅ Odpověď z DeepSeek API:")
    print("=" * 50)
    print(response.choices[0].message.content)
    print("=" * 50)

    # Výpis informací o tokenech
    print("\n📊 Informace o tokenech:")
    print(f"Prompt tokens: {response.usage.prompt_tokens}")
    print(f"Completion tokens: {response.usage.completion_tokens}")
    print(f"Total tokens: {response.usage.total_tokens}")

    # Výpis celé odpovědi ve formátu JSON pro ladění
    print("\n🔍 Kompletní odpověď (JSON):")
    print(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))

except Exception as e:
    print(f"❌ Chyba při volání DeepSeek API: {e}")
