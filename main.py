import sqlite3
import streamlit as st
from summary import create_summary_prompt, create_pdf

from summary import create_summary_prompt, create_pdf

st.set_page_config(page_title="GenAI Multi-Agent BFSI Assistant", page_icon="🔮")
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
from db import add_chat_message, get_chat_history, create_users_table
from auth import hash_password, verify_password, get_user, add_user
from db import create_users_table


create_users_table()


def format_message(who, text, ts):
    """Return an HTML chat bubble for user or agent with dark-mode friendly colors."""
    if who == "user":
        bg = "#2E7D32"   # deep green
        align = "right"
        avatar = "🧑"
        text_color = "#FFFFFF"  # white text
    else:
        bg = "#1565C0"   # deep blue
        align = "left"
        avatar = "🤖"
        text_color = "#FFFFFF"  # white text

    html = f"""
    <div style="
        background-color: {bg};
        color: {text_color};
        padding: 8px 12px;
        border-radius: 12px;
        max-width: 70%;
        margin: 6px;
        text-align: {align};
        font-family: sans-serif;
        ">
      <small style="font-size:10px;color:#CCCCCC;">{ts}</small><br>
      <span style="font-size:18px;">{avatar}</span> {text}
    </div>
    """
    return html


# Add login/signup section at the top (STATIC DEMO ONLY)
st.sidebar.title("🔑 Login / Signup (Demo)")

# Show login/signup forms only if user not logged in yet
if "username" not in st.session_state:
    auth_mode = st.sidebar.radio("Select Mode:", ("Login", "Sign Up"))

    username = st.sidebar.text_input("Username (static demo)")
    password = st.sidebar.text_input("Password", type="password")

    if auth_mode == "Login":
        if st.sidebar.button("Login"):
            st.sidebar.info("🔒 Login functionality is disabled for this demo.")
    elif auth_mode == "Sign Up":
        if st.sidebar.button("Sign Up"):
            st.sidebar.info("🔒 Sign up functionality is disabled for this demo.")

# If logged in, show logged-in username (but disable logout too)
else:
    st.sidebar.success(f"Logged in as: {st.session_state['username']} (static demo)")
    if st.sidebar.button("Logout"):
        st.sidebar.info("🔒 Logout functionality is disabled for this demo.")



# # Add login/signup section at the top
# st.sidebar.title("🔑 Login / Signup")

# # Show login/signup forms only if user not logged in yet
# if "username" not in st.session_state:
#     auth_mode = st.sidebar.radio("Select Mode:", ("Login", "Sign Up"))

#     username = st.sidebar.text_input("Username")
#     password = st.sidebar.text_input("Password", type="password")

#     if auth_mode == "Login":
#         if st.sidebar.button("Login"):
#             user = get_user(username)
#             if user and verify_password(password, user[2]):  # user[2] is hashed password
#                 st.session_state["username"] = username

#                 # ✅ Load user chat history on successful login
#                 chat_records = get_chat_history(username)
#                 st.session_state.chat_history = []
#                 for role, message, timestamp in chat_records:
#                     if role == "user":
#                         st.session_state.chat_history.append({
#                             "agent": None,
#                             "user_input": message,
#                             "agent_response": None,
#                             "timestamp": timestamp,
#                         })
#                     elif role == "agent" and st.session_state.chat_history:
#                         st.session_state.chat_history[-1]["agent_response"] = message

#                 st.experimental_rerun()  # refresh app to show chatbot
#             else:
#                 st.sidebar.error("Invalid username or password.")

#     elif auth_mode == "Sign Up":
#         if st.sidebar.button("Sign Up"):
#             if get_user(username):
#                 st.sidebar.error("Username already exists.")
#             else:
#                 hashed_pwd = hash_password(password)
#                 add_user(username, hashed_pwd)
#                 st.sidebar.success("Account created. Please log in.")

# # If logged in, show logged-in username
# else:
#     st.sidebar.success(f"Logged in as: {st.session_state['username']}")
#     if st.sidebar.button("Logout"):
#         del st.session_state["username"]
#         st.session_state.chat_history = []
#         st.experimental_rerun()





if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("🔮 Smart Insurance Advisor")

# ===========================
# ✅ 1) API Key Management
# ===========================
# Set your Mistral API key here or as an environment variable:

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")  # Or hardcode for testing:
# MISTRAL_API_KEY = "your_actual_key_here"
load_dotenv()
if not MISTRAL_API_KEY:
    st.error("❌ Mistral API key not found! Please set the MISTRAL_API_KEY environment variable.")
    st.stop()

# ===========================
# ✅ 2) Agent Prompts
# ===========================
PROMPTS = {
        "Insurance Recommender": {
            "system": """
    You are Kshitij, an expert Insurance Product Recommender.
    • Ask clarifying questions if user data (age, income, goals, risk) is missing.
    • Recommend exactly 2 to 3 plans from our catalog, with bullet point reasons.
    • Use a friendly, concise tone.
    """,
            "examples": [
                {
                    "user": "I am 28, healthy, want medium-term savings, can pay 15,000 yearly.",
                    "assistant": "• **HealthShield Plus** – hospitalization & surgery cover\n• **SecureLife Plan** – tax benefits + life cover rider"
                }
            ],
            "defer": "I’m the Product Recommender. For claim‑filing questions, please ask the Claim Filing Helper agent."
        },

        "Claim Filing Helper": {
            "system": """
    You are Kshitij, an expert Claims Filing Assistant.
    • Guide the user step‑by‑step through the claim process.
    • Ask what happened, what documents they have, and next steps.
    • Close with “Did this help? (Yes/No)”
    """,
            "examples": [
                {
                    "user": "How do I file a health insurance claim?",
                    "assistant": "1. Describe the incident…\n2. Upload hospital bills…\n3. Submit the claim form at our portal.\nDid this help? (Yes/No)"
                }
            ],
            "defer": "I’m the Claim Filing Helper. For product recommendations, please ask the Insurance Recommender agent."
        },

        "General Q&A": {
            "system": """
    You are Kshitij, an expert Insurance Policy Q&A agent.
    • Answer policy questions clearly in 2–4 sentences.
    • Use a friendly, approachable tone.
    """,
            "examples": [
                {
                    "user": "What does my health policy cover?",
                    "assistant": "It covers hospitalization costs, day‑care procedures, and pre‑/post‑hospitalization expenses up to the sum insured."
                }
            ],
            "defer": "I’m the Q&A agent. For product recommendations, ask the Insurance Recommender; for claims, ask the Claim Filing Helper."
        }
    }


# ===========================
# ✅ 3) Optional Mock Products
# ===========================
INSURANCE_PRODUCTS = [
    {
        "name": "SecureLife Plan",
        "type": "Life Insurance",
        "risk": "Low",
        "features": "Long-term savings, tax benefits"
    },
    {
        "name": "HealthShield Plus",
        "type": "Health Insurance",
        "risk": "Medium",
        "features": "Covers hospitalization, surgeries"
    },
    {
        "name": "InvestSmart ULIP",
        "type": "Investment-Linked",
        "risk": "High",
        "features": "Market-linked returns with insurance"
    }
]

# ===========================
## ===========================
# ✅ 4) Mistral Chat + Router
# ===========================

def get_mistral_response(prompt, user_input):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-small",
        "messages": [
            {"role": "system",  "content": prompt},
            {"role": "user",    "content": user_input}
        ],
        "temperature": 0.5,
        "max_tokens": 500
    }
    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers=headers,
        json=data
    )
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return f"❌ API Error: {response.status_code} - {response.text}"


def route_or_call(agent_key, user_input):
    """
    Routes out‑of‑scope queries to the agent’s defer message,
    otherwise builds the system prompt + examples and calls the LLM.
    """
    lower = user_input.lower()
    # 👉 1) Handle greetings directly
    if lower.strip() in ["hi", "hello", "hey"]:
        return "👋 Hello! Please enter a question about insurance so I can assist you effectively."

    p = PROMPTS[agent_key]

    # 1) Defer if it’s outside this agent’s domain
    if agent_key == "Insurance Recommender" and "claim" in lower:
        return p["defer"]
    if agent_key == "Claim Filing Helper" and any(k in lower for k in ["recommend", "plan", "suggest"]):
        return p["defer"]
    if agent_key == "General Q&A" and any(k in lower for k in ["recommend", "claim", "file"]):
        return p["defer"]

    # 2) Build prompt + few‑shot examples
    prompt = p["system"].strip()
    for ex in p["examples"]:
        prompt += f"\n\nUser: {ex['user']}\nAssistant: {ex['assistant']}"
    prompt += f"\n\nUser: {user_input}\nAssistant:"

    # 3) Call the LLM
    return get_mistral_response(prompt, user_input)



# ===========================
# ===========================
# ===========================
# ===========================
# ✅ 5) Streamlit Chat UI with Dark Mode-Friendly Styling
# ===========================
# ===========================
# ✅ Beautiful Header Section
# ===========================
st.markdown("""
    <div style="
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.4);
    ">
        <h1 style='color: #212121; margin:0;'>⭐ GenAI Multi-Agent Insurance Assistant</h1>
        <p style='color: #212121; font-size:16px; margin-top:10px;'>Your one-stop solution for insurance recommendations, claim assistance, and more — powered by AI.</p>
    </div>
""", unsafe_allow_html=True)


# ✅ Link to Google Docs with example questions
st.markdown("""
<div style="
    background-color: rgba(76, 175, 80, 0.15);
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 20px;
    text-align: center;
">
    <h3 style="color:#2E7D32; margin:0;">📖 Need sample questions?</h3>
    <p style="color:#212121; margin-top:8px;">
        <a href="https://docs.google.com/document/d/1eEonl9zTVJSpAVu4fK743nRzKbzkc1EzEH-Y0BHU7Cg/edit?usp=sharing" target="_blank" style="color:#1565C0; text-decoration:none; font-weight:bold;">
            👉 Click here to view example prompts you can try with each agent!
        </a>
    </p>
</div>
""", unsafe_allow_html=True)



st.markdown("<h2 style='color:#4A90E2;'>🧠 Choose the agent you'd like to interact with:</h2>", unsafe_allow_html=True)

agent = st.selectbox(
    "Select an agent",
    list(PROMPTS.keys()),
    index=0,
)

st.markdown("---")

# Chat history container with dark-friendly styling


if st.session_state.chat_history:
    for chat in st.session_state.chat_history:
        # User's message block
        st.markdown(f"""
            <div style="
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 8px;
                color: #212121;
            ">
                <strong>🧑 You:</strong> {chat['user_input']}
                <div style="text-align:right; font-size:10px; color:#555555;">🕒 {chat['timestamp']}</div>
            </div>
        """, unsafe_allow_html=True)

        # Agent's message block
        st.markdown(f"""
            <div style="
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 15px;
                color: #212121;
            ">
                <strong>🤖 {chat['agent']}:</strong> {chat['agent_response']}
                <div style="text-align:right; font-size:10px; color:#555555;">🕒 {chat['timestamp']}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div style="
            background-color:rgba(255,255,255,0.05);
            border-radius:8px;
            padding:20px;
            margin-bottom:10px;
            text-align:center;
            color:#AAAAAA;">
            No conversation yet. Start by typing below! 🚀
        </div>
    """, unsafe_allow_html=True)


st.markdown("</div>", unsafe_allow_html=True)

# Chat input prompt with clear instructions
st.markdown("<h3 style='color:#4A90E2;'>💬 Type your question below:</h3>", unsafe_allow_html=True)

user_input = st.chat_input("E.g., I am 30 years old with a budget of 20,000/year. What insurance should I get?")

if user_input:
    with st.spinner(f"💭 Talking to {agent}..."):
        answer = route_or_call(agent, user_input)

        now = datetime.now().strftime("%B %d, %I:%M %p")

        # Save this turn to session state
        st.session_state.chat_history.append({
            "agent": agent,
            "user_input": user_input,
            "agent_response": answer,
            "timestamp": now,
        })

        if "username" in st.session_state:
            username = st.session_state["username"]
            add_chat_message(username, "user", user_input, now)
            add_chat_message(username, "agent", answer, now)

        st.experimental_rerun()  # Refresh chat display

        if st.button("📄 Download Conversation Summary as PDF"):
            summary_text = create_summary_prompt(st.session_state.chat_history)
            create_pdf(summary_text)
            with open("chat_summary.pdf", "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f,
                    file_name="chat_summary.pdf",
                    mime="application/pdf",
                )

            import base64

if st.session_state.chat_history:
    st.markdown("---")
    # Generate summary when the user clicks download button
    summary_text = create_summary_prompt(st.session_state.chat_history)
    create_pdf(summary_text)
    with open("chat_summary.pdf", "rb") as f:
        st.download_button(
            label="📥 Download PDF Summary",
            data=f,
            file_name="chat_summary.pdf",
            mime="application/pdf",
        )




# ===========================
# ✅ 6) Optional: Display Mock Products for Recommender
# ===========================
# if agent == "Insurance Recommender":
#     st.markdown("---")
#     st.subheader("📦 Example Insurance Products")
#     for product in INSURANCE_PRODUCTS:
#         st.markdown(
#             f"""
#             <div style='
#                 background-color: rgba(255, 255, 255, 0.8);
#                 border-radius: 8px;
#                 padding: 10px;
#                 margin-bottom: 10px;
#                 color: #212121;
#             '>
#                 <strong>{product['name']}</strong><br>
#                 • Type: {product['type']}<br>
#                 • Risk: {product['risk']}<br>
#                 • Features: {product['features']}
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )

        
