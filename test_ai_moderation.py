import os
import json
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Load configuration from .env
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
AI_MODEL = os.getenv('AI_MODEL', 'gemini-2.0-flash')

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Test messages
POSITIVE_MESSAGES = [
    "Díky moc za pomoc, jsi skvělý!",
    "To je opravdu dobrý nápad, oceňuji tvůj přístup.",
    "Gratuluji k úspěchu, zasloužíš si to!",
    "Moc se mi líbí, jak jsi to vyřešil.",
    "Jsi velmi nápomocný, děkuji za tvůj čas."
]

NEGATIVE_MESSAGES = [
    "To je naprosto stupidní nápad.",
    "Jsi úplně k ničemu, nikdo tě tady nechce.",
    "Drž hubu a táhni odsud.",
    "Nenávidím tě, jsi naprostý idiot.",
    "Všichni tě tady nesnáší, zmiz."
]

MIXED_MESSAGES = [
    "To je dobrý nápad, ale mohl bys to udělat lépe.",
    "Díky za pomoc, i když to trvalo dlouho.",
    "Nejsem si jistý, jestli to funguje správně.",
    "To je zajímavé, ale nesouhlasím s tebou.",
    "Oceňuji tvou snahu, ale výsledek není ideální."
]

async def analyze_sentiment(messages):
    """Test the sentiment analysis with the Google Gemini API"""
    if not GEMINI_API_KEY:
        print("Google Gemini API key is missing")
        return None

    if not messages:
        return None

    # Combine messages into a single text for analysis
    combined_text = "\n".join(messages)

    # Prepare prompt for sentiment analysis
    prompt = f"""Analyze the sentiment of the following messages from a Discord user.
Rate the overall sentiment on a scale from -100 (extremely negative/toxic) to +100 (extremely positive/friendly).
Negative sentiment has more weight than positive sentiment.

Messages:
{combined_text}

Provide your analysis in the following JSON format:
{{
  "sentiment_score": <number between -100 and 100>,
  "positive_score": <number between 0 and 100>,
  "negative_score": <number between 0 and 100>,
  "explanation": "<brief explanation of your rating>"
}}
"""

    try:
        # Create a Gemini model instance
        model = genai.GenerativeModel(AI_MODEL)

        # Configure response format to be JSON
        generation_config = genai.types.GenerationConfig(
            response_mime_type='application/json'
        )

        # Call the Gemini API
        response = await asyncio.to_thread(
            model.generate_content,
            [
                "You are an AI assistant that analyzes the sentiment of Discord messages. You detect toxic, negative, neutral, and positive content.",
                prompt
            ],
            generation_config=generation_config
        )

        # Parse the response
        if response.text:
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                print(f"Failed to parse JSON response: {response.text}")
                return None
        else:
            print("Empty response from Gemini API")
            return None

    except Exception as e:
        print(f"Error calling Google Gemini API: {e}")
        return None

async def main():
    print("Testing AI Moderation with Google Gemini API...")
    print(f"Using model: {AI_MODEL}")

    print("\n=== Testing Positive Messages ===")
    positive_result = await analyze_sentiment(POSITIVE_MESSAGES)
    if positive_result:
        print(f"Sentiment Score: {positive_result.get('sentiment_score')}")
        print(f"Positive Score: {positive_result.get('positive_score')}")
        print(f"Negative Score: {positive_result.get('negative_score')}")
        print(f"Explanation: {positive_result.get('explanation')}")

    print("\n=== Testing Negative Messages ===")
    negative_result = await analyze_sentiment(NEGATIVE_MESSAGES)
    if negative_result:
        print(f"Sentiment Score: {negative_result.get('sentiment_score')}")
        print(f"Positive Score: {negative_result.get('positive_score')}")
        print(f"Negative Score: {negative_result.get('negative_score')}")
        print(f"Explanation: {negative_result.get('explanation')}")

    print("\n=== Testing Mixed Messages ===")
    mixed_result = await analyze_sentiment(MIXED_MESSAGES)
    if mixed_result:
        print(f"Sentiment Score: {mixed_result.get('sentiment_score')}")
        print(f"Positive Score: {mixed_result.get('positive_score')}")
        print(f"Negative Score: {mixed_result.get('negative_score')}")
        print(f"Explanation: {mixed_result.get('explanation')}")

if __name__ == "__main__":
    asyncio.run(main())
