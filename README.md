# 🔮 GenAI Multi‑Agent Insurance Assistant

**An end‑to‑end, industry‑ready AI chatbot for the BFSI sector**  
Personalized insurance recommendations, claim‑filing assistance, and policy Q&A—powered by Mistral LLMs, wrapped in a modern Streamlit UI, with persistent storage and download‑able summaries.

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)  
2. [Problem Statement & Objectives](#problem-statement--objectives)  
3. [Solution Architecture](#solution-architecture)  
4. [Features & User Flows](#features--user-flows)  
5. [Technology Stack & Dependencies](#technology-stack--dependencies)  
6. [Installation & Setup](#installation--setup)  
7. [Usage & Demo](#usage--demo)  
8. [Project Structure & Key Modules](#project-structure--key-modules)  
9. [PDF Summary Generation](#pdf-summary-generation)  
10. [Multilingual Support (Optional)](#multilingual-support-optional)  
11. [Future Enhancements](#future-enhancements)  
12. [Testing & Validation](#testing--validation)  
13. [Deployment](#deployment)  
14. [Contribution Guidelines](#contribution-guidelines)  
15. [License](#license)  

---

## 📝 Project Overview  
Insurance customers often struggle with product selection, claim filing, and policy queries. This project delivers a **multi‑agent AI assistant** that:

- **Recommends** insurance products based on user profile.  
- **Guides** users through claim processes step by step.  
- **Answers** general insurance questions instantly.  
- **Persists** each conversation per user.  
- **Summarizes** key highlights in a downloadable PDF.

All powered by a Streamlit frontend, Mistral LLM API, and SQLite backend.

---

## 🎯 Problem Statement & Objectives

- **Product Recommendation Pain**: Users have difficulty choosing the right insurance plan.  
- **Claim Filing Complexity**: Claim processes are often opaque and paper‑heavy.  
- **Support Overload**: Repetitive queries strain customer‑support teams.

**Objectives:**  
1. Build an intuitive chat UI with multi‑agent selection.  
2. Implement specialized “agents” (Recommender, Claim Helper, Q&A) via prompt engineering.  
3. Store and load per‑user chat history with SQLite.  
4. Generate succinct PDF summaries for user records.

---

## UI AI Generated (Future Scope)

###  Profile Page

![Profile](Prototype_SS/Profile%20Dark.png)

### Login

![Login](Prototype_SS/Login%20Dark.png)

### Signup

![Signup](Prototype_SS/Signup%20dark.png)

### Dashboard

![Dashboard](Prototype_SS/Dashboard%20Dark.png)

### Chat History

![Chat History](Prototype_SS/Chat%20History%20Dark.png)

### Settings

![Setting](Prototype_SS/User%20dark.png)



## Project Structure




**main.py** — Streamlit application entrypoint

**db.py** — SQLite helper: create tables, add/retrieve messages

**auth.py** — (Optional) Signup/Login functions & password hashing

**summary.py** — PDF summary: prompt builder & ReportLab generator

**requirements.txt** — Python dependencies

**.env** — Stores MISTRAL_API_KEY

**README.md** — This documentation file
## Key Functions & Modules

- main.py
        get_mistral_response(prompt, input)

        format_message(who, text, ts)

- Streamlit UI elements, PDF download logic, agent selection

- db.py
        create_users_table()

        add_user(), get_user()

        add_chat_message(), get_chat_history()

- summary.py
        create_summary_prompt(chat_history) → str

        create_pdf(summary_text, pdf_path)
## Run Locally

Clone the project

```bash
  git clone https://github.com/k5hitijj/DSW_Hackathon.git
cd DSW_Hackathon

```

Install dependencies

```bash
  pip install -r requirements.txt

```

Add your .env file with Mistral API Key:

```bash
  MISTRAL_API_KEY=your_actual_key

```

Run the Streamlit App

```bash
  Run the Streamlit App
```


## Setup & Installation

Deployed via Streamlit Cloud.
To deploy:

Push code to GitHub

Connect GitHub repo to Streamlit Cloud

Set MISTRAL_API_KEY in Secrets Manager

```bash
  npm run deploy
```

git clone https://github.com/your‑username/genai‑bfsi‑assistant.git
cd genai‑bfsi‑assistant


## Install dependencies

pip install -r requirements.txt



## Usage/Examples


- Choose an agent

- Ask your question

- View conversational responses

- Export PDF Summary of Chat


## Acknowledgements

 - Mistral AI for language models

 - Streamlit for low-code app building

 - ReportLab for PDF generation


## Tech Stack

| Layer      | Technology      |
| ---------- | --------------- |
| Frontend   | Streamlit       |
| Backend    | Python, SQLite  |
| LLM        | Mistral API     |
| PDF        | ReportLab       |
| Auth       | bcrypt          |
| Deployment | Streamlit Cloud |

## FAQ

#### Question 1

Where is data stored? 

→ Locally using SQLite.

#### Question 2

Can I use my own API key? 

→ Yes, set MISTRAL_API_KEY in .env

#### Question 3

Does it work offline? 

→ Only the UI works offline. Mistral API requires internet.
## Feedback

Suggestions or improvements? Create an issue or pull request!
## License

MIT License © 2025 Kshitij Varma


## Authors
- ✍️ Author

Made with ❤️ by Kshitij Varma

GitHub: https://github.com/k5hitijj

Project Repo: https://github.com/k5hitijj/DSW_Hackathon
