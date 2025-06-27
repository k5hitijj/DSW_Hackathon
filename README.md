# 📦 GenAI Multi‑Agent BFSI Assistant

A **Streamlit**‑based conversational app showcasing a **multi‑agent Generative AI** solution for the **Banking, Financial Services & Insurance (BFSI)** sector.  
Interact with three specialized AI agents—Insurance Recommender, Claim Filing Helper, and General Q&A—powered by the Mistral chat API.

---

## ✨ Key Features

1. **Multi‑Agent Chat**  
   - **Insurance Recommender**: Suggests the best insurance product based on age, income, goals & risk appetite.  
   - **Claim Filing Helper**: Guides users step‑by‑step through claim submission, asking for details and documents.  
   - **General Q&A**: Answers any insurance‑related question in a friendly, concise tone.

2. **Smooth Conversational UI**  
   - Continuous chat bubbles with **avatars** (🧑 for user, 🤖 for agent).  
   - **Human‑friendly timestamps** (e.g. “June 27, 07:22 PM”).  
   - **Dark‑mode‑friendly** color scheme for readability in both light and dark themes.

3. **Easy Deployment & Use**  
   - Pure Python: no complex infrastructure required.  
   - Deploy to **Streamlit Community Cloud** in minutes.  
   - Configurable via a single environment variable.

---

## 🛠️ Tech Stack & Dependencies

- **Language**: Python 3.8+  
- **UI Framework**: [Streamlit](https://streamlit.io/)  
- **AI Backend**: Mistral Chat API (OpenAI‑compatible)  
- **HTTP Library**: `requests`  
- **PDF Export (optional)**: `fpdf`  

```bash
pip install streamlit requests fpdf

## Setup & Installation

To deploy this project run

```bash
  npm run deploy
```

git clone https://github.com/your‑username/genai‑bfsi‑assistant.git
cd genai‑bfsi‑assistant


## Install dependencies

pip install -r requirements.txt


## Configure your Mistral API key

Temporarily (per session):

 1. **macOS/Linux**
export MISTRAL_API_KEY="sk-your_key_here"

 2. **Windows (CMD)**
set MISTRAL_API_KEY=sk-your_key_here

## set MISTRAL_API_KEY=sk-your_key_here


Hardcode (for quick local tests):
In app.py, set:


MISTRAL_API_KEY = "sk-your_key_here"

## Running Locally

streamlit run app.py
