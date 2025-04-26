import os
import json
from datetime import datetime
from utils import config

# Cesta k souboru s daty o tokenech
TOKEN_USAGE_FILE = "token_usage.json"

# Ceník tokenů (cena za 1000 tokenů v USD)
TOKEN_PRICES = {
    # DeepSeek modely
    "deepseek-chat": {
        "input": 0.0005,  # $0.0005 za 1000 input tokenů (DeepSeek-V3)
        "output": 0.0025  # $0.0025 za 1000 output tokenů (DeepSeek-V3)
    },
    "deepseek-reasoner": {
        "input": 0.0005,  # $0.0005 za 1000 input tokenů (DeepSeek-R1)
        "output": 0.0025  # $0.0025 za 1000 output tokenů (DeepSeek-R1)
    },
    # OpenRouter modely (ceny se mohou lišit podle konkrétního modelu)
    "deepseek/deepseek-chat-v3-0324:free": {
        "input": 0.0005,
        "output": 0.0025
    },
    # Gemini modely
    "gemini-2.0-flash": {
        "input": 0.00035,  # $0.00035 za 1000 input tokenů
        "output": 0.00035  # $0.00035 za 1000 output tokenů
    }
}

# Výchozí ceny pro neznámé modely
DEFAULT_PRICE = {
    "input": 0.001,
    "output": 0.002
}

def load_token_data():
    """Načte data o tokenech z JSON souboru"""
    if not os.path.exists(TOKEN_USAGE_FILE):
        return {"entries": []}

    try:
        with open(TOKEN_USAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"[Token Tracker] Chyba při načítání souboru {TOKEN_USAGE_FILE}, vytvářím nový")
        return {"entries": []}

def save_token_data(data):
    """Uloží data o tokenech do JSON souboru"""
    with open(TOKEN_USAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def calculate_cost(model, prompt_tokens, completion_tokens):
    """Vypočítá cenu za tokeny podle modelu

    Args:
        model (str): Název modelu
        prompt_tokens (int): Počet tokenů v promptu
        completion_tokens (int): Počet tokenů v odpovědi

    Returns:
        float: Cena v USD
    """
    # Získání cen pro daný model nebo použití výchozích cen
    prices = TOKEN_PRICES.get(model, DEFAULT_PRICE)

    # Výpočet ceny
    input_cost = (prompt_tokens / 1000) * prices["input"]
    output_cost = (completion_tokens / 1000) * prices["output"]

    return input_cost + output_cost

def log_token_usage(provider, model, operation, prompt_tokens, completion_tokens, total_tokens=None):
    """Zaznamená využití tokenů do JSON souboru

    Args:
        provider (str): Poskytovatel API (deepseek, openrouter, openai, gemini)
        model (str): Název použitého modelu
        operation (str): Typ operace (např. 'summary', 'moderation')
        prompt_tokens (int): Počet tokenů v promptu
        completion_tokens (int): Počet tokenů v odpovědi
        total_tokens (int, optional): Celkový počet tokenů. Pokud není zadáno, vypočítá se jako součet.
    """
    # Pokud není zadán celkový počet tokenů, vypočítáme ho
    if total_tokens is None:
        total_tokens = prompt_tokens + completion_tokens

    # Výpočet ceny
    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    # Aktuální čas
    now = datetime.now()
    timestamp = now.isoformat()
    date = now.strftime('%Y-%m-%d')
    time = now.strftime('%H:%M:%S')

    # Vytvoření záznamu
    entry = {
        "timestamp": timestamp,
        "date": date,
        "time": time,
        "provider": provider,
        "model": model,
        "operation": operation,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost
    }

    # Načtení existujících dat
    data = load_token_data()

    # Přidání nového záznamu
    data["entries"].append(entry)

    # Uložení dat
    save_token_data(data)

    print(f"[Token Tracker] Zaznamenáno využití tokenů: {provider}/{model} - {operation}: {prompt_tokens} + {completion_tokens} = {total_tokens} tokenů, cena: ${cost:.6f}")

def extract_tokens_from_deepseek_response(response_data, operation):
    """Extrahuje informace o tokenech z odpovědi DeepSeek API

    Args:
        response_data (dict): Odpověď z DeepSeek API (kompatibilní s OpenAI API formátem)
        operation (str): Typ operace

    Returns:
        bool: True pokud se podařilo extrahovat a zaznamenat tokeny
    """
    try:
        # DeepSeek API vrací informace o tokenech v klíči 'usage' (stejně jako OpenAI API)
        if 'usage' in response_data:
            usage = response_data['usage']
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)

            # Získáme model z odpovědi nebo z konfigurace
            # 'deepseek-chat' odpovídá DeepSeek-V3, 'deepseek-reasoner' odpovídá DeepSeek-R1
            model = response_data.get('model', config.get('DEEPSEEK_MODEL', 'unknown'))

            log_token_usage('deepseek', model, operation, prompt_tokens, completion_tokens, total_tokens)
            return True
    except Exception as e:
        print(f"[Token Tracker] Chyba při extrakci tokenů z DeepSeek odpovědi: {e}")

    return False

def extract_tokens_from_openrouter_response(response_data, operation):
    """Extrahuje informace o tokenech z odpovědi OpenRouter API

    Args:
        response_data (dict): Odpověď z OpenRouter API
        operation (str): Typ operace

    Returns:
        bool: True pokud se podařilo extrahovat a zaznamenat tokeny
    """
    try:
        # OpenRouter API vrací informace o tokenech v klíči 'usage'
        if 'usage' in response_data:
            usage = response_data['usage']
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)

            model = response_data.get('model', config.get('OPENROUTER_MODEL', 'unknown'))

            log_token_usage('openrouter', model, operation, prompt_tokens, completion_tokens, total_tokens)
            return True
    except Exception as e:
        print(f"[Token Tracker] Chyba při extrakci tokenů z OpenRouter odpovědi: {e}")

    return False

def extract_tokens_from_gemini_response(response, operation, prompt_text=None):
    """Extrahuje informace o tokenech z odpovědi Gemini API

    Args:
        response: Odpověď z Gemini API
        operation (str): Typ operace
        prompt_text (str, optional): Text promptu pro odhad počtu tokenů

    Returns:
        bool: True pokud se podařilo extrahovat a zaznamenat tokeny
    """
    try:
        # Gemini API nevrací přímo počet tokenů, ale můžeme je odhadnout
        # Přibližný odhad: 1 token = 4 znaky
        model = config.get('AI_MODEL', 'unknown')

        # Odhad tokenů v odpovědi
        completion_text = response.text if hasattr(response, 'text') else str(response)
        completion_tokens = len(completion_text) // 4

        # Odhad tokenů v promptu
        prompt_tokens = 0
        if prompt_text:
            prompt_tokens = len(prompt_text) // 4

        total_tokens = prompt_tokens + completion_tokens

        log_token_usage('gemini', model, operation, prompt_tokens, completion_tokens, total_tokens)
        return True
    except Exception as e:
        print(f"[Token Tracker] Chyba při extrakci tokenů z Gemini odpovědi: {e}")

    return False
