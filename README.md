# ReaperScans DL Bot

![Manga Search Bot](https://envs.sh/aWZ.jpg)

Welcome to the Manga Search Bot! This bot allows you to search, read, and download manga chapters directly from Reaper Scans. It supports both novels and comics and provides options to download chapters as PDFs or view them online.

---

## Features

- Search for manga by name.
- View manga details, including description, chapters, and type (novel or comic).
- Download individual chapters or entire ranges as PDFs.
- Inline buttons for easy navigation.
- Background task handling with a queue system for efficient downloads.

---

## How to Get Started

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/<your-username>/ReaperScansDLBot.git
   cd ReaperScansDLBot
   ```

2. **Set Up Environment Variables:**
   Fill Up `Environment Variables` in [bot.py](https://github.com/Rahat4089/ReaperScansDLBot/blob/main/bot.py):
   ```
   API_ID=<your_telegram_api_id> #in line 18
   API_HASH=<your_telegram_api_hash> #in line 19
   BOT_TOKEN=<your_bot_token> #in line 20
   ```

   You can obtain these values by following the steps below:

   - **API_ID and API_HASH:** Register your application at [Telegram Core](https://my.telegram.org/apps).
   - **BOT_TOKEN:** Create a bot via [BotFather](https://t.me/botfather) on Telegram and obtain your token.

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Bot:**
   ```bash
   python bot.py
   ```

5. **Interact with Your Bot:**
   Open Telegram, search for your bot, and start a conversation. Use `/start` to begin!

---

## How to Deploy

### Deploy on Heroku
1. Install the Heroku CLI:
   ```bash
   https://devcenter.heroku.com/articles/heroku-cli
   ```

2. Log in to Heroku:
   ```bash
   heroku login
   ```

3. Create a Heroku app:
   ```bash
   heroku create <app-name>
   ```

4. Set environment variables on Heroku:
   ```bash
   heroku config:set API_ID=<your_telegram_api_id>
   heroku config:set API_HASH=<your_telegram_api_hash>
   heroku config:set BOT_TOKEN=<your_bot_token>
   ```

5. Deploy the app:
   ```bash
   git push heroku main
   ```

6. Scale the bot:
   ```bash
   heroku ps:scale worker=1
   ```

### Deploy on Local Server
1. Install Python (if not installed already).
2. Set up the bot as described in **How to Get Started**.

---

## Contribution

We welcome contributions to this project! Here's how you can contribute:

1. **Fork the Repository:**
   Click the "Fork" button in the top-right corner of this repository.

2. **Create a New Branch:**
   ```bash
   git checkout -b feature/new-feature
   ```

3. **Make Changes:**
   Add new features, fix bugs, or improve documentation.

4. **Push Your Changes:**
   ```bash
   git push origin feature/new-feature
   ```

5. **Open a Pull Request:**
   Go to the original repository, click "Pull Requests," and submit your PR.

---

## Credits

This bot was originally created by [RAHAT](https://t.me/r4h4t_69). Feel free to modify and enhance it as you like, but please retain the original credits.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---
