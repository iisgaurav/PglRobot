<div align="center">
  <img src="https://telegra.ph/file/f1d7b30b05ba9f0dbf4e5.jpg" alt="PglRobot Logo">
  
  # 🤖 PglRobot
  
  **A Next-Generation Telegram Group Management Bot**
  
  *Built from the ground up using modern asynchronous architecture with Aiogram 3 and SQLAlchemy 2.0.*
</div>

---

## 🌟 About PglRobot
PglRobot is a highly advanced, lightning-fast Telegram Bot designed to securely and efficiently manage group chats of any size. Moving away from legacy synchronous wrappers, PglRobot is built using **Aiogram 3** and **Telethon** in a Hybrid Architecture, offering fully non-blocking I/O and rapid MTProto message processing, making it one of the most responsive moderation bots available today.

### 💎 Why use PglRobot?
- ⚡ **Blazing Fast Async Core**: Entirely built on Aiogram 3.x and SQLAlchemy 2.0 (`asyncpg`). This guarantees massive scalability and zero lag, completely avoiding the blocking bottlenecks of legacy SQLite bots.
- 🧠 **Hybrid Engine**: Seamlessly combines the standard Bot API (Aiogram) for rapid command processing with deep MTProto functionality (Telethon) for advanced tasks.
- 🛡️ **Intelligent Anti-Spam**: Drops reliance on broken third-party APIs. Uses a built-in heuristic scoring system to instantly catch and ban crypto-scammers and spam rings before they can disrupt your chat.
- 🌐 **Native Federations**: Cross-group ban networks are fully supported natively to protect your entire community ecosystem. Ban once, secure everywhere.
- 🔒 **Enterprise Stability**: 100% strictly typed codebase verified by `basedpyright` with 0 typing errors. Written entirely from scratch to be crash-proof.

---

## 🔥 Key Features

PglRobot comes packed with a powerful suite of plugins and features:

### 🛡️ Moderation & Management
- **AntiSpam:** Strict anti-spam protections to keep your group clean.
- **Purge System:** Quickly delete bulk messages (`/purge`, `/del`). Includes a robust chunking algorithm to bypass API limits on massive purges.
- **Rules:** Set and enforce group rules (`/rules`, `/setrules`).
- **Locks & Blacklists:** Advanced content locking (`/lock url`, `/lock photo`) and text censoring (`/addblacklist`).
- **Approvals & Trust:** Whitelist your most loyal members (`/approve`) or use the Karma-like Trust system (`/trust`) to automatically bypass locks.
- **Force Subscribe & Join Requests:** Force members to join a channel (`/fsub`) and auto-approve their group join requests (`/autoapprove`).
- **Custom Filters:** Create highly customized text or media auto-replies (`/filter`, `/stop`).
- **Connections:** Manage your group's settings privately by connecting to it in PM (`/connect`).
- **NSFW Detection:** Machine-learning powered image scanning to automatically delete nudity or gore (powered by Sightengine).
- **Global Bans (GBan):** Sudo users can globally ban scammers across *all* groups the bot manages simultaneously.
- **Federations (Feds):** Group creators can link multiple groups into a federation to share a unified ban list. Ban once, remove everywhere!
- **Zombies (MTProto):** Uses Telethon to bypass Bot API limits and scan for or kick "Deleted Accounts" from your groups (`/zombies`, `/zombies clean`).

### 🎉 Engagement & Utility
- **Welcome & Goodbye:** Highly customizable welcome messages supporting Text, Photos, Videos, and Gifs, with inline buttons and dynamic formatting tags (e.g., `{first}`, `{chatname}`).
- **Karma System:** A fun reputation system! Users can reply to messages with `+1`, `thanks`, or `pro` to give Karma, and `-1` or `noob` to take it away.
- **AFK (Away From Keyboard):** Let your friends know when you are busy. The bot will automatically reply to anyone who mentions you!
- **Notes System:** Save important text or media using `/save <notename>` and retrieve it using `#<notename>`.

### 🌙 Automation
- **Night Mode:** Automatically locks your group (disabling messaging and media) at 12:00 AM IST and unlocks it at 6:00 AM IST to prevent late-night spam while admins are asleep!

---

## 🛠️ Technology Stack
- **Framework:** [Aiogram 3.x](https://docs.aiogram.dev/en/v3.0.0/)
- **Database:** PostgreSQL (with `asyncpg`)
- **ORM:** [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- **Scheduling:** [APScheduler](https://apscheduler.readthedocs.io/en/3.x/)

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/PglRobot.git
   cd PglRobot
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Edit the `PglRobot/config.py` file to include your tokens and database URI, or export them as environment variables:
   - `BOT_TOKEN`: Your Telegram Bot Token.
   - `OWNER_ID`: Your Telegram User ID.
   - `SQLALCHEMY_DATABASE_URI`: Your PostgreSQL URI (e.g., `postgresql+asyncpg://user:pass@localhost/dbname`).

4. **Run the Bot:**
   ```bash
   python -m PglRobot
   ```

---

## 📚 Help & Commands
Once the bot is running, simply add it to your group, promote it to Admin, and type `/help` to see a fully interactive menu of all available commands and how to configure each plugin!

---

## 🌟 Credits & Acknowledgements

Every line of plugin logic in PglRobot 2.0 has been meticulously written from scratch to leverage modern asynchronous paradigms. We would like to extend our gratitude to the developers of our core underlying technologies:

- **[Aiogram Team](https://github.com/aiogram/aiogram)**: For their incredibly robust and blazing-fast Telegram Bot API framework.
- **[Telethon Team](https://github.com/LonamiWebs/Telethon)**: For providing unparalleled access to the MTProto library.
- **[SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy)**: For the powerful async ORM.

---

<div align="center">
  <i>Developed with ❤️ by iisgaurav</i>
</div>
