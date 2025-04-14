# AI Moderation Feature

## Overview

The AI Moderation feature uses Google's Gemini AI to analyze user messages and automatically moderate your Discord server. It evaluates the sentiment of messages, rewards positive behavior with multiple role levels, and takes action against negative behavior.

## Features

- **Sentiment Analysis**: Analyzes batches of 51 user messages to determine if they are positive or negative
- **Multi-Level Scoring System**: Maintains a score for each user with multiple reward tiers
- **Automatic Timeouts**: Applies timeouts to users with excessively negative scores
- **Role Rewards**: Assigns special roles to users at different positive score thresholds (800, 2000, 5000)
- **Negative Role**: Assigns a negative role to users with extremely negative scores (-1000)
- **Extra Penalties**: Applies additional -50 point penalties for very negative messages
- **User Statistics**: Tracks and displays user sentiment scores and moderation history
- **Admin Commands**: Provides commands for admins to view rules and manage the system

## Configuration

To use the AI Moderation feature, you need to set up the following in your `.env` file:

```
# AI Moderation Configuration
# Google Gemini API key for AI moderation
# Get your API key from: https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here
# AI model to use for moderation
AI_MODEL=gemini-2.0-flash
# Number of messages to analyze per user
AI_MESSAGES_BATCH=51
# Database file for AI moderation
AI_MODERATION_SAVE_FILE=db/ai_moderation.json
# Interval in minutes to process message batches
AI_MODERATION_INTERVAL_MINUTES=5
# Positive score thresholds for role rewards
AI_POSITIVE_THRESHOLD_1=800
AI_POSITIVE_THRESHOLD_2=2000
AI_POSITIVE_THRESHOLD_3=5000
# Negative score thresholds
AI_NEGATIVE_THRESHOLD=-30
AI_VERY_NEGATIVE_THRESHOLD=-1000
# Penalty for very negative messages
AI_NEGATIVE_PENALTY=-50
# Role IDs for different levels
# Level 1 positive role (800+ points)
AI_POSITIVE_ROLE_ID_1=your_positive_role_id_level1_here
# Level 2 positive role (2000+ points)
AI_POSITIVE_ROLE_ID_2=your_positive_role_id_level2_here
# Level 3 positive role (5000+ points)
AI_POSITIVE_ROLE_ID_3=your_positive_role_id_level3_here
# Negative role (-1000 points)
AI_NEGATIVE_ROLE_ID=your_negative_role_id_here
```

### Google Gemini API Setup

1. Create an account at [Google AI Studio](https://aistudio.google.com/)
2. Generate an API key
3. Add the API key to your `.env` file
4. Enable the Generative Language API in Google Cloud Console

### Role Setup

1. Create roles in your Discord server for each level:
   - Level 1 Positive Role (for users with 800+ points)
   - Level 2 Positive Role (for users with 2000+ points)
   - Level 3 Positive Role (for users with 5000+ points)
   - Negative Role (for users with -1000 or lower points)
2. Get the role IDs (right-click on each role and select "Copy ID")
3. Add the role IDs to your `.env` file

## How It Works

1. The bot collects messages from users (up to 51 messages per user)
2. When a user reaches 51 messages or at regular intervals, it analyzes these messages using the AI model
3. Each analysis produces a positive and negative score
4. Very negative messages receive an additional -50 point penalty
5. These scores are added to the user's total score
6. If a user's total score falls below -30, they receive a timeout
7. If a user's total score falls below -1000, they receive the negative role
8. If a user's total score rises above the positive thresholds, they receive the corresponding positive roles:
   - 800+ points: Level 1 positive role
   - 2000+ points: Level 2 positive role
   - 5000+ points: Level 3 positive role
9. Timeout duration increases with repeated offenses
10. All data is stored in a JSON file for persistence

## Commands

- `!aiscore [@user]` - Shows the AI sentiment score for yourself or a mentioned user
- `!aitop` - Shows the top 10 users with the highest AI sentiment scores
- `!aibottom` - Shows the 10 users with the lowest AI sentiment scores
- `!airules` - Shows the rules and thresholds of the AI moderation system (admin only)
- `!aireset [@user]` - Resets the AI score for a specific user (admin only)
- `!airesetall` - Resets the AI scores for all users (admin only)

## Technical Details

- Messages are analyzed in batches of 51 (configurable)
- Analysis occurs when a user reaches the batch size or every 5 minutes (configurable)
- Scores range from -100 (extremely negative) to +100 (extremely positive)
- Very negative messages (>80 negative score) receive an additional -50 point penalty
- Timeout duration doubles with each offense (starting at 5 minutes, up to 24 hours)
- Admins are analyzed but not penalized
- All data is stored in a JSON file for persistence

## Customization

You can customize the behavior of the AI moderation system by adjusting the following parameters in your `.env` file:

- `AI_MESSAGES_BATCH`: Number of messages to analyze per user (default: 51)
- `AI_MODERATION_INTERVAL_MINUTES`: How often to analyze messages (default: 5)
- `AI_POSITIVE_THRESHOLD_1/2/3`: Scores required for positive roles (default: 800/2000/5000)
- `AI_NEGATIVE_THRESHOLD`: Score that triggers a timeout (default: -30)
- `AI_VERY_NEGATIVE_THRESHOLD`: Score that triggers the negative role (default: -1000)
- `AI_NEGATIVE_PENALTY`: Extra penalty for very negative messages (default: -50)

## Troubleshooting

- If the bot is not analyzing messages, check that your Google Gemini API key is valid and the API is enabled
- If timeouts are not being applied, ensure the bot has the "Moderate Members" permission
- If roles are not being assigned, ensure the bot has the "Manage Roles" permission and its role is higher than all the AI moderation roles in the server settings
