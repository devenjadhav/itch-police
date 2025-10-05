# Itch Police

A Python script that validates itch.io game links from Airtable and updates their status if they're playable in browser.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy the environment file and add your credentials:

```bash
cp .env.example .env
```

3. Edit `.env` with your Airtable API key and base ID:

## Usage

Run the validator:

```bash
python game_validator.py
```

## Current Usage (specifically built around Daydream Submissions)

1. Fetches all records from the 'projects' table in Airtable
2. Checks each 'gameplay_url' field to see if the itch.io game is playable in browser
3. Updates 'ysws_status' to 'Ready' if the game has a `.game_frame` element (browser playable)
4. Includes rate limiting and error handling
