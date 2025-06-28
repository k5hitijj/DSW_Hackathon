import sqlite3
import streamlit as st

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




# Add login/signup section at the top
st.sidebar.title("🔑 Login / Signup")

# Show login/signup forms only if user not logged in yet
if "username" not in st.session_state:
    auth_mode = st.sidebar.radio("Select Mode:", ("Login", "Sign Up"))

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if auth_mode == "Login":
        if st.sidebar.button("Login"):
            user = get_user(username)
            if user and verify_password(password, user[2]):  # user[2] is hashed password
                st.session_state["username"] = username

                # ✅ Load user chat history on successful login
                chat_records = get_chat_history(username)
                st.session_state.chat_history = []
                for role, message, timestamp in chat_records:
                    if role == "user":
                        st.session_state.chat_history.append({
                            "agent": None,
                            "user_input": message,
                            "agent_response": None,
                            "timestamp": timestamp,
                        })
                    elif role == "agent" and st.session_state.chat_history:
                        st.session_state.chat_history[-1]["agent_response"] = message

                st.experimental_rerun()  # refresh app to show chatbot
            else:
                st.sidebar.error("Invalid username or password.")

    elif auth_mode == "Sign Up":
        if st.sidebar.button("Sign Up"):
            if get_user(username):
                st.sidebar.error("Username already exists.")
            else:
                hashed_pwd = hash_password(password)
                add_user(username, hashed_pwd)
                st.sidebar.success("Account created. Please log in.")

# If logged in, show logged-in username
else:
    st.sidebar.success(f"Logged in as: {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        del st.session_state["username"]
        st.session_state.chat_history = []
        st.experimental_rerun()





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
    "Insurance Recommender": (
        "You are a professional insurance advisor named Kshitij. You always: "
        "• Ask clarifying questions if input is incomplete."
        "• Recommend 1–2 products from your catalog, with bullet-pointed reasons."
        "• Use a friendly, concise tone."

       " EXAMPLE: User: I’m 28, healthy, want medium-term savings, can pay 15,000 yearly. "
        "Advisor: • I recommend the **HealthShield Plus** for your health needs—benefits include hospitalization cover and surgery reimbursements."
        "• As an alternative, **SecureLife Plan** gives you tax benefits with a small life-cover rider."
            ),

    "Claim Filing Helper": (
        "You are an insurance customer support agent named Kshitij. You always:"
        "• Answer clearly and concisely in 2–4 sentences."
        "• Use friendly, approachable tone."
        "• Include a brief “Did this help?” prompt at the end."

        "EXAMPLE 1:"
        "User: How long does it take to process a life insurance claim?"
        "Assistant: "
        "Typically, life insurance claims are processed within 7–14 business days after all documents are received. If additional information is needed, it may take a few extra days. " 
        "Did this help? (Yes/No)"

        "EXAMPLE 2:"
        "User: What does my health policy cover?"
        "Assistant:"
        "Your health policy covers hospitalization costs, day-care procedures, and pre- and post-hospitalization expenses up to the sum insured. It also includes free annual health checkups."
        "Did this help? (Yes/No)"

    ),

    "General Q&A": (
        "You are an insurance customer support agent named Kshitij. You always:"
        "• Answer clearly and concisely in 2–4 sentences."
        "• Use friendly, approachable tone."

        "EXAMPLE 1:"
        "User: How long does it take to process a life insurance claim?"
        "Assistant:" 
        "Typically, life insurance claims are processed within 7–14 business days after all documents are received. If additional information is needed, it may take a few extra days."  

        "EXAMPLE 2:"
       "User: What does my health policy cover?"
        "Assistant:"
        "Your health policy covers hospitalization costs, day-care procedures, and pre- and post-hospitalization expenses up to the sum insured. It also includes free annual health checkups."  
        "Do you have any further questions?"
            )
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
# ✅ 4) Mistral Chat Function
# ===========================
def get_mistral_response(prompt, user_input):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistral-small",  # Or mistral-medium if available
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.7,
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
        background-color:rgba(33,150,243,0.2);
        border-radius:15px;
        padding:25px;
        margin-bottom:30px;
        text-align:center;
        box-shadow:0 4px 8px rgba(0,0,0,0.4);">
        <h1 style='color:#4A90E2; margin:0;'>⭐ GenAI Multi-Agent Insurance Assistant</h1>
        <p style='color:#DDDDDD; font-size:16px; margin-top:10px;'>Your one-stop solution for insurance recommendations, claim assistance, and more — powered by AI.</p>
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
st.markdown("""
    <div style="
        background-color:rgba(255,255,255,0.05);
        border-radius:12px;
        padding:20px;
        box-shadow:0 4px 8px rgba(0,0,0,0.3);
        max-height:500px;
        overflow-y:auto;
        margin-bottom:20px;">
""", unsafe_allow_html=True)

if st.session_state.chat_history:
    for chat in st.session_state.chat_history:
        # User's message block
        st.markdown(f"""
            <div style="
                background-color:rgba(76,175,80,0.2);
                border-radius:8px;
                padding:10px;
                margin-bottom:8px;
                color:#EEEEEE;">
                <strong>🧑 You:</strong> {chat['user_input']}
                <div style="text-align:right; font-size:10px; color:#BBBBBB;">🕒 {chat['timestamp']}</div>
            </div>
        """, unsafe_allow_html=True)

        # Agent's message block
        st.markdown(f"""
            <div style="
                background-color:rgba(33,150,243,0.2);
                border-radius:8px;
                padding:10px;
                margin-bottom:15px;
                color:#EEEEEE;">
                <strong>🤖 {chat['agent']}:</strong> {chat['agent_response']}
                <div style="text-align:right; font-size:10px; color:#BBBBBB;">🕒 {chat['timestamp']}</div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("<p style='color:#AAAAAA;'>No conversation yet. Start by typing below! 🚀</p>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Chat input prompt with clear instructions
st.markdown("<h3 style='color:#4A90E2;'>💬 Type your question below:</h3>", unsafe_allow_html=True)

user_input = st.chat_input("E.g., I am 30 years old with a budget of 20,000/year. What insurance should I get?")

if user_input:
    with st.spinner(f"💭 Talking to {agent}..."):
        answer = get_mistral_response(PROMPTS[agent], user_input)

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

# ===========================
# ✅ 6) Optional: Display Mock Products for Recommender
# ===========================
# if agent == "Insurance Recommender":
#     st.markdown("---")
#     st.subheader("📦 Example Insurance Products")
#     for product in INSURANCE_PRODUCTS:
#         st.markdown(
#             f"""
#             <div style='background-color:rgba(255,255,255,0.05); border-radius:8px; padding:10px; margin-bottom:10px; color:#EEEEEE;'>
#                 <strong>{product['name']}</strong><br>
#                 • Type: {product['type']}<br>
#                 • Risk: {product['risk']}<br>
#                 • Features: {product['features']}
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )
