# Casino bonus scraper

Pulls welcome bonus data for 3 casinos from one public source (Livescore ZA
online casinos page), uses an LLM to turn free text into structured fields,
writes `data.json`, and shows it on a static page.

## Install
    python -m venv .venv
    .venv\Scripts\activate        (Mac/Linux: source .venv/bin/activate)
    pip install -r requirements.txt

Create a `.env` file with a free Groq API key (console.groq.com):

    GROQ_API_KEY=your_key_here

## Run
    python casino_scraper.py

This checks robots.txt, fetches the page, extracts the fields with the LLM,
validates them, and writes `data.json`.

## View the page locally
    python -m http.server 8000
then open http://localhost:8000

## Notes
- Source: https://www.livescore.com/en-za/online-casinos/ (robots.txt allows it).
- Wagering multiplier is not stated on this source, so it is `null` rather
  than guessed. Getting it would mean following each casino's T&Cs page.
- Casinos are matched by name from the table, and the display name is fixed
  in code so the LLM cannot mislabel a casino.