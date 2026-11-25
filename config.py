import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load local .env file if present (keeps secrets out of source control)
_ENV_FILE = BASE_DIR / ".env"
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ChatGPT Default Base URL (Starts a fresh chat so context never gets full)
CHATGPT_URL = "https://chatgpt.com"

# Outro Video Path
OUTRO_VIDEO_PATH = r"C:\Users\mehak\Downloads\1122.mp4"
OUTRO_ASSET_NAME = "1122"

# Gemini API Key (Using gemini-2.5-flash)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# 1-Time Studio Access Passkey (Share with friends to grant full bot control)
STUDIO_ACCESS_KEY = os.environ.get("STUDIO_ACCESS_KEY", "CHANGE_ME")

# Video Duration: "20 SECONDS"
VIDEO_DURATION = "20 SECONDS"

# Master Prompt Template
MASTER_PROMPT_TEMPLATE = """[VIDEO DURATION: {VIDEO_DURATION}] <-- (20 SECONDS = 2 clips: Clip 1 and Clip 2)
Act as an elite viral YouTube Shorts & Instagram Reels director specializing in fast-paced, hyper-realistic Indian "Sheru Bhai" comedy and motivational-revenge videos.

Follow these strict rules in 2 phases:

### PHASE 1: GENERATE 10 VIRAL STORY IDEAS
Give me a clean numbered list of 10 wildly creative, hilarious, and unexpected "Sheru Bhai" story ideas.
You have complete creative independence: invent funny animal rivals (like Crocodile Don, Cheetah Builder, Shark Seth, Bhaloo Mayor, etc.), absurd Indian luxury flexes, auction wars, or wild comedy revenge confrontations featuring Sheru Bhai (the billionaire white-suited anthropomorphic lion with heavy gold chains and dark sunglasses).
Make each idea fresh, high-energy, and uniquely funny.
Keep each idea to 1 catchy title + 1 short line.
STOP after listing the 10 ideas and ask ONLY: *"Which topic number (1–10) do you want to generate?"*

### PHASE 2: OUTPUT CLEAN, ZERO-GAP GOOGLE FLOW PROMPTS
Once I reply with a topic number, DO NOT write any intro, separate scripts, or character lists.
Output EXACTLY 2 separate 10-second prompts (`Clip 1 (0:00–0:10)` and `Clip 2 (0:10–0:20)`).
Put each prompt inside its own separate copy-paste code block.

**CRITICAL RULES FOR BALANCED CONCEPT → DELIVERY PACING & ZERO CUTOFFS:**
1. **Evenly Balanced Dialogue + 1.5s Visual Breathing Room in BOTH Clips:**
   - Never overstuff Clip 2. Both clips must stay within **22–26 spoken words total** and end with a **1.5-second silent visual breathing buffer** so Google Flow NEVER cuts a word mid-sentence:
   - **Clip 1 (0:00–0:10) — Concept, Hook & Trigger:**
     - `0:00–0:04.5` (~12–14 words): Starts at 0.0s immediately — the arrogant animal rival taunts Sheru with a hilarious Hindi insult (e.g., *"Arre Sheru, teri aukaat sirf purana scooter chalane ki hai!"*).
     - `0:04.5–0:08.5` (~10–12 words): Sheru fires back a sharp setup line *and* triggers the reveal (snaps his fingers, slams a gold briefcase, or makes a call: *"Acha beta? Abhi dekh tera kya haal hota hai!"*).
     - **`0:08.5–0:10.0` (1.5s Silent Visual Breathing Room):** **Zero dialogue** in the final 1.5s. Show the reveal starting visually (rival smirking / doors opening / shadow rising) so Clip 1 ends cleanly.
   - **Clip 2 (0:10–0:20) — Delivery, Viral Flex & Mic-Drop:**
     - `0:10–0:16.5` (~16–18 words MAX): Sheru roars back with extreme swag and boss hand gestures, delivering the exact meme cadence with a comedic pause before *"ghop ghop!"* plus ONE short 4–5 word payoff (NO long lists): *"Oye chup! Million, billion, trillion, quadrillion, gazillion... ghop ghop! Poora show hi apna hai!"*
     - `0:16.5–0:18.5` (~4–6 words): One crisp rival gasp or 4-word mic-drop punchline (*"Ab bol, kiska baap bada?"* or *"Bik gaya poora maidaan!"*).
     - **`0:18.5–0:20.0` (1.5s Silent Visual Breathing Room):** **Zero dialogue** in the final 1.5s. Sheru adjusts his sunglasses with a boss smirk while the rival's jaw drops, finishing cleanly before the outro.
2. **Dialogue Authenticity:**
   - Rival and side characters speak natural, grounded, funny Hindi/Hinglish.
   - ONLY Sheru delivers the iconic *"Oye chup! Million, billion, trillion, quadrillion, gazillion... ghop ghop!"* meme flex, always keeping the ellipsis `...` before `ghop ghop!` for comedic timing.
3. **Hyper-Realistic Visual Continuity:**
   - Every prompt must include: **photorealistic 8K live-action cinema, shot on ARRI Alexa, real individual fur strands, natural skin textures, fast whip-pans and crash-zooms, 9:16 vertical, shallow depth of field**, maintaining the exact same venue, characters, and outfits across both clips.
   - Start Clip 2 explicitly with: *"Continuing seamlessly from the exact last frame of the previous clip..."*

Start now with Phase 1 and list the 10 ideas.
"""

MASTER_PROMPT_TEMPLATE_3CLIPS = """[VIDEO DURATION: 30 SECONDS] <-- (30 SECONDS = 3 clips: Clip 1, Clip 2, and Clip 3)
Act as an elite viral YouTube Shorts & Instagram Reels director specializing in fast-paced, hyper-realistic Indian "Sheru Bhai" comedy and motivational-revenge videos.

Follow these strict rules in 2 phases:

### PHASE 1: GENERATE 10 VIRAL STORY IDEAS
Give me a clean numbered list of 10 wildly creative, hilarious, and unexpected "Sheru Bhai" story ideas.
You have complete creative independence: invent funny animal rivals (like Crocodile Don, Cheetah Builder, Shark Seth, Bhaloo Mayor, etc.), absurd Indian luxury flexes, auction wars, or wild comedy revenge confrontations featuring Sheru Bhai (the billionaire white-suited anthropomorphic lion with heavy gold chains and dark sunglasses).
Make each idea fresh, high-energy, and uniquely funny.
Keep each idea to 1 catchy title + 1 short line.
STOP after listing the 10 ideas and ask ONLY: *"Which topic number (1–10) do you want to generate?"*

### PHASE 2: OUTPUT CLEAN, ZERO-GAP GOOGLE FLOW PROMPTS
Once I reply with a topic number, DO NOT write any intro, separate scripts, or character lists.
Output EXACTLY 3 separate 10-second prompts (`Clip 1 (0:00–0:10)`, `Clip 2 (0:10–0:20)`, and `Clip 3 (0:20–0:30)`).
Put each prompt inside its own separate copy-paste code block.

**CRITICAL RULES FOR 3-CLIP EPIC PACING & ZERO CUTOFFS:**
1. **Evenly Balanced Dialogue + 1.5s Visual Breathing Room in ALL 3 Clips (~22–26 spoken words per clip):**
   - **Clip 1 (0:00–0:10) — Hook & Rival Taunt:**
     - `0:00–0:04.5` (~12–14 words): Rival taunts Sheru immediately at `0.0s` with a hilarious Hindi insult.
     - `0:04.5–0:08.5` (~10–12 words): Crowd/auctioneer gasps in shock while Sheru gives a cold warning and triggers his counter-move.
     - **`0:08.5–0:10.0` (1.5s Silent Visual Buffer):** **Zero dialogue** in the final 1.5s — show the setup escalating visually.
   - **Clip 2 (0:10–0:20) — Sheru's Viral Power Flex:**
     - `0:10–0:16.5` (~16–18 words MAX): Sheru roars back with boss hand gestures, delivering the exact meme cadence with a pause before *"ghop ghop!"* plus one crisp payoff: *"Oye chup! Million, billion, trillion, quadrillion, gazillion... ghop ghop! Ab dekh asli dhamaka!"*
     - `0:16.5–0:18.5` (~4–6 words): Rival stammers in disbelief as Sheru's luxury flex arrives.
     - **`0:18.5–0:20.0` (1.5s Silent Visual Buffer):** **Zero dialogue** in the final 1.5s — show the grand reveal unfolding.
   - **Clip 3 (0:20–0:30) — Full Payoff & Mic-Drop Ending:**
     - `0:20–0:24.5` (~10–12 words): Auctioneer/crowd erupts in cheers (*"Bik gaya! Sheru Bhai ne poora maidaan khareed liya!"*).
     - `0:24.5–0:28.5` (~10–12 words): Sheru delivers a hilarious final punchline while flexing his prize with boss swagger.
     - **`0:28.5–0:30.0` (1.5s Silent Visual Buffer):** **Zero dialogue** in the final 1.5s — Sheru adjusts his sunglasses with a boss smirk while the rival's jaw drops before the outro.
2. **Dialogue Authenticity:**
   - Rival and side characters speak natural, grounded, funny Hindi/Hinglish.
   - ONLY Sheru delivers the iconic *"Oye chup! Million, billion, trillion, quadrillion, gazillion... ghop ghop!"* meme flex, always keeping the ellipsis `...` before `ghop ghop!` for comedic timing.
3. **Hyper-Realistic Visual Continuity:**
   - Every prompt must include: **photorealistic 8K live-action cinema, shot on ARRI Alexa, real individual fur strands, natural skin textures, fast whip-pans and crash-zooms, 9:16 vertical, shallow depth of field**, maintaining the exact same venue, characters, and outfits across all 3 clips.
   - Start Clip 2 and Clip 3 explicitly with: *"Continuing seamlessly from the exact last frame of the previous clip..."*

Start now with Phase 1 and list the 10 ideas.
"""
