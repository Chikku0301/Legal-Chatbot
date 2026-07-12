# ⚖️ Legal Aid Bot

A citizen legal assistance system providing procedural guidance, document generation, and case tracking for various legal disputes. It includes a terminal-based prototype and a fully asynchronous Telegram Bot interface.

> **Disclaimer:** This system provides procedural guidance only and does not constitute legal advice. Users are strongly advised to consult a qualified legal professional for legal representation.

## ✨ Features

- **🧠 AI Dispute Classification**: Classifies legal disputes using a custom fine-tuned `law-ai/InLegalBERT` model (with a robust keyword-matching fallback) to identify the dispute category, legal process, and appropriate court.
- **📄 Legal Document Generation**: Generates automated legal petitions, complaints, and legal notices in PDF (using `reportlab`) or plain text format based on user inputs.
- **📅 Case Tracking & Reminders**: Tracks cases using SQLite (`core/database.py`) and provides deadline reminders for evidence submission and court hearings.
- **💬 LLM Guidance**: Integrates Groq (`llama-3.3-70b-versatile`) to explain complex legal form fields in simple language.
- **🤖 Telegram Interface**: A multi-user, fully asynchronous Telegram bot interface for remote usage.

## 📂 Project Structure

```
Legal-Bot/
├── core/
│   ├── classifier.py         # Dispute classification using InLegalBERT or keywords
│   ├── database.py           # SQLite database setup for tracking
│   ├── document_generator.py # PDF/TXT petition generator
│   ├── llm_helper.py         # Groq integration for field explanation
│   ├── session.py            # User session state management for Telegram
│   └── tracker.py            # Case creation and deadline tracker
├── data/
│   ├── constants.py          # Dispute keywords and workflows definitions
│   └── synthetic_dataset.json# Synthetic training data for classification
├── models/
│   └── inlegalbert-dispute-classifier/ # Fine-tuned InLegalBERT model directory
├── scripts/
│   ├── generate_dataset.py   # Script to generate synthetic_dataset.json
│   ├── train_classifier.py   # Script to train InLegalBERT on the dataset
│   └── test_model.py         # Quick test script for the classifier
├── utils/
│   └── ui.py                 # ANSI styled CLI UI components
├── main.py                   # Terminal prototype entry point
├── telegram_bot.py           # Telegram bot entry point
├── requirements.txt          # Python dependencies
└── .env                      # Environment variables (API Keys)
```

## 🚀 Installation

1. **Clone the repository:**
   Ensure you are in the `Legal-Bot` directory.

2. **Set up a Virtual Environment (Recommended: Conda or venv):**
   ```bash
   conda create -n agentic python=3.13
   conda activate agentic
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the `Legal-Bot` root directory (if not already present) and add your API keys:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

## 🛠️ Usage

### 1. Terminal Prototype
Run the terminal-based interactive prototype:
```bash
python main.py
```
This mode simulates a WhatsApp/Terminal chatbot. Follow the on-screen prompts to classify your dispute and generate a legal petition.

### 2. Telegram Bot
Run the Telegram bot server:
```bash
python telegram_bot.py
```
- Open Telegram and search for your bot using its username.
- Send `/start` to begin a session.
- Send `/status` to check pending case deadlines.
- Send `/help` or `?` at any prompt for LLM-powered explanations of legal fields.

### 3. Training the Classifier
If you wish to utilize the AI classification instead of keyword fallback, you must train the InLegalBERT model first:
```bash
python scripts/train_classifier.py
```
*Note: A GPU is highly recommended for training. If the model weights are not found, the bot will automatically fall back to accurate keyword matching.*

## 🗄️ Outputs
Generated documents (PDFs, TXTs) and the SQLite database (`legal_bot_cases.db`) will be saved in the `outputs/` directory automatically.