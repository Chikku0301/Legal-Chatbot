# ⚖️ Legal Aid Bot

An AI-powered citizen legal assistance system that provides **procedural guidance, automated document generation, dispute classification, and case tracking** for common legal disputes.

The project includes both a **terminal-based prototype** and a **fully asynchronous Telegram Bot**, making legal procedural information more accessible and easier to understand.

> **⚠️ Disclaimer:** This system provides general procedural guidance and does **not** constitute legal advice. Users should consult a qualified legal professional for legal representation or advice regarding their specific case.

---

## ✨ Features

### 🧠 AI-Powered Dispute Classification

Automatically classifies a user's legal dispute using a fine-tuned `law-ai/InLegalBERT` model.

The classifier identifies:

- The likely dispute category
- The applicable legal procedure or workflow
- The appropriate court or authority

If the trained model is unavailable, the system automatically falls back to a **keyword-based classification system**, ensuring the application remains functional.

---

### 📄 Automated Legal Document Generation

Generates basic legal documents based on user-provided information, including:

- Petitions
- Complaints
- Legal notices

Documents can be generated in:

- **PDF format** using `reportlab`
- **Plain text format**

---

### 📅 Case Tracking and Deadline Reminders

The system allows users to track legal cases using an SQLite database.

Features include:

- Case creation and storage
- Evidence submission deadline tracking
- Court hearing reminders
- Pending case status monitoring

---

### 💬 LLM-Powered Guidance

Integrates **Groq** with the `llama-3.3-70b-versatile` model to explain complex legal forms and fields in simple, user-friendly language.

Users can request contextual explanations whenever they are unsure about the information required.

---

### 🤖 Fully Asynchronous Telegram Bot

Provides a multi-user Telegram interface built with asynchronous handling.

Users can:

- Start a legal assistance session
- Describe their dispute
- Receive procedural guidance
- Generate legal documents
- Track case deadlines
- Ask for explanations of legal fields

---

## 📂 Project Structure

```text
Legal-Bot/
│
├── core/
│   ├── classifier.py
│   │   # Dispute classification using InLegalBERT or keyword matching
│   │
│   ├── database.py
│   │   # SQLite database setup and management
│   │
│   ├── document_generator.py
│   │   # PDF and TXT legal document generation
│   │
│   ├── llm_helper.py
│   │   # Groq LLM integration for field explanations
│   │
│   ├── session.py
│   │   # User session and conversation state management
│   │
│   └── tracker.py
│       # Case creation and deadline tracking
│
├── data/
│   ├── constants.py
│   │   # Dispute categories, keywords, and legal workflows
│   │
│   └── synthetic_dataset.json
│       # Synthetic dataset for classifier training
│
├── models/
│   └── inlegalbert-dispute-classifier/
│       # Fine-tuned InLegalBERT model
│
├── scripts/
│   ├── generate_dataset.py
│   │   # Generates synthetic training data
│   │
│   ├── train_classifier.py
│   │   # Fine-tunes the InLegalBERT classifier
│   │
│   └── test_model.py
│       # Tests the trained classification model
│
├── utils/
│   └── ui.py
│       # ANSI-styled terminal UI components
│
├── outputs/
│   # Generated legal documents and SQLite database
│
├── main.py
│   # Terminal-based application entry point
│
├── telegram_bot.py
│   # Telegram Bot entry point
│
├── requirements.txt
│   # Project dependencies
│
└── .env
    # Environment variables and API keys
```

---

# 🚀 Installation

## 1. Clone the Repository

Clone the repository and navigate to the project directory:

```bash
git clone <your-repository-url>
cd Legal-Bot
```

---

## 2. Create a Virtual Environment

Using Conda:

```bash
conda create -n legalbot python=3.13
conda activate legalbot
```

Alternatively, using `venv`:

```bash
python -m venv venv
```

Activate the environment.

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root directory and add the required API credentials:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
```

> **Important:** Never commit your `.env` file or API keys to a public repository.

---

# 🛠️ Usage

## 1. Terminal Prototype

Run the terminal-based version of the application:

```bash
python main.py
```

The terminal interface simulates a conversational legal assistant.

Users can:

1. Describe their legal dispute
2. Receive a dispute classification
3. Follow the suggested procedural workflow
4. Provide the required case details
5. Generate a legal document

---

## 2. Telegram Bot

Start the Telegram bot using:

```bash
python telegram_bot.py
```

Then open Telegram and search for your bot using its configured username.

### Available Commands

| Command   | Description                                                    |
| --------- | -------------------------------------------------------------- |
| `/start`  | Start a new legal assistance session                           |
| `/status` | View pending case deadlines and reminders                      |
| `/help`   | Get help using the bot                                         |
| `?`       | Request an explanation for the current legal field or question |

The Telegram bot supports multiple users and manages individual conversation states asynchronously.

---

## 3. Train the Dispute Classifier

To use the AI-powered dispute classifier, train the `InLegalBERT` model:

```bash
python scripts/train_classifier.py
```

The training script uses the synthetic dataset located at:

```text
data/synthetic_dataset.json
```

The trained model will be saved to:

```text
models/inlegalbert-dispute-classifier/
```

> **Note:** A GPU is recommended for faster model training. If trained model weights are unavailable, the application automatically uses the keyword-based classifier as a fallback.

---

## 🗄️ Generated Outputs

The application automatically creates an `outputs/` directory for generated files.

This may include:

```text
outputs/
├── legal_bot_cases.db
├── generated_petition.pdf
├── generated_complaint.pdf
├── legal_notice.pdf
└── generated_documents.txt
```

The SQLite database stores case-related information, while generated legal documents are saved in PDF or plain text format.

---

## 🔄 System Workflow

The overall workflow of the system is:

```text
User Input
    │
    ▼
Dispute Classification
    │
    ├── Fine-Tuned InLegalBERT Model
    │
    └── Keyword-Based Fallback
    │
    ▼
Legal Workflow Identification
    │
    ▼
User Provides Required Information
    │
    ├── LLM Assistance for Complex Fields
    │
    ▼
Document Generation
    │
    ├── PDF
    └── TXT
    │
    ▼
Case Creation and Storage
    │
    ▼
Deadline Tracking and Reminders
```

---

## 🧰 Technology Stack

| Category               | Technologies                                    |
| ---------------------- | ----------------------------------------------- |
| Language               | Python                                          |
| NLP / Classification   | Hugging Face Transformers, `law-ai/InLegalBERT` |
| LLM                    | Groq, `llama-3.3-70b-versatile`                 |
| Database               | SQLite                                          |
| Document Generation    | ReportLab                                       |
| Bot Framework          | Telegram Bot API                                |
| Environment Management | Conda / venv                                    |
| Configuration          | `.env`                                          |

---

## ⚠️ Disclaimer

This project is intended for **educational and informational purposes only**.

The Legal Aid Bot:

- Does not provide professional legal advice
- Does not replace a qualified lawyer or legal professional
- Does not guarantee the accuracy or applicability of generated documents
- Should not be relied upon as the sole basis for legal decisions

Users are strongly encouraged to consult a qualified legal professional before initiating legal proceedings or submitting legal documents.

---

## 📌 Future Improvements

Potential future enhancements include:

- Support for additional categories of legal disputes
- Retrieval-Augmented Generation (RAG) using verified legal resources
- Multilingual support for Indian regional languages
- Integration with official court or case-status APIs
- Web-based dashboard for case management
- Improved document templates for different jurisdictions
- Authentication and secure user data management
- Advanced notification and reminder systems
- Fine-tuning on larger, legally verified datasets

---

## 👨‍💻 Project Purpose

The goal of **Legal Aid Bot** is to explore how **Artificial Intelligence, Natural Language Processing, Large Language Models, and conversational interfaces** can make basic legal procedural information more accessible to citizens.

The project combines:

**AI Classification + LLM Assistance + Document Generation + Case Tracking + Conversational Interface**

to create an end-to-end prototype for citizen-focused legal procedural assistance.
