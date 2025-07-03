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


# Initialize a per‑session profile for personalization
if "profile" not in st.session_state:
    st.session_state.profile = {
        "age": None,
        "income": None,
        "goals": None,
        "risk_appetite": None
    }



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
        
        # ─── User Profile (required before chat) ─────
with st.sidebar.expander("👤 Your Profile (helps me personalize)"):
    p = st.session_state.profile
    p["age"] = st.number_input("Age", min_value=0, max_value=100, value=p["age"] or 0, key="expander_age")
    p["income"] = st.number_input("Monthly income (₹)", min_value=0, value=p["income"] or 0, key="expander_income")
    p["goals"] = st.text_input("Goals (e.g. savings, tax benefits)", value=p["goals"] or "")
    p["risk_appetite"] = st.selectbox(
        "Risk appetite", ["Low", "Medium", "High"],
        index=["Low","Medium","High"].index(p["risk_appetite"]) if p["risk_appetite"] else 1
    )
# ───────────────────────────────────────────────




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


# ✅ Require age and income before allowing chat
if not st.session_state.profile["age"] or not st.session_state.profile["income"]:
    st.warning("🚨 Please complete your profile (Age and Income are required) before asking a question!")
    st.stop()  # Stops the app here until profile filled



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
    You are Kshitij, an expert Insurance Product Recommender.
    • Greet the user warmly.
    • Answer ONLY questions about recommending insurance products (Life, Health, Car, Home, Travel) OR explaining their policy details (coverage, limits, riders).
    • If the user asks about filing or tracking a claim, reply:
    “Claims are outside my scope. Please ask the Claim Filing Helper agent.”
    • If the question is neither recommendation, policy detail, nor insurance‑related, reply:
    “Sorry, I only handle insurance recommendations and policy details.”
    • If any required user info (age, income, goals, risk) is missing for a recommendation, ask a friendly clarifier.
    • Otherwise recommend 1–2 products (bullet‑pointed) with reasons.
    • Be conversational, concise, and helpful.
    """,
            "examples": [
                {
                    "user": "What does my SecureLife Plan cover?",
                    "assistant": "Hello! Your SecureLife Plan provides:\n• A death benefit equal to the sum insured\n• Tax savings under Section 80C\n• Optional riders like critical illness cover—let me know if you want details on any rider!"
                },
                {
                    "user": "I’m 40, moderate risk, want long‑term growth, ₹30,000/year budget.",
                    "assistant": "Great! Based on your profile:\n• **SecureLife Plan** (Life): Family protection + tax benefits.\n• **InvestSmart ULIP**: Market‑linked returns + life cover.\nNeed more detail on either?"
                },
                {
                    "user": "How do I file a claim?",
                    "assistant": "Claims are outside my scope. Please ask the Claim Filing Helper agent."
                },
                {
                    "user": "Tell me a joke.",
                    "assistant": "Sorry, I only handle insurance recommendations and policy details."
                }
            ],
            "defer": "Claims are outside my scope. Please ask the Claim Filing Helper agent."
        },

        "Claim Filing Helper": {
            "system": """
    You are Kshitij, an expert Claim Filing Helper.
    • Greet the user cheerfully.
    • Answer ONLY questions about filing, submitting, or tracking insurance claims (Health, Life, Car, Home, Travel).
    • If the user asks for product recommendations or policy explanations, reply:
    “Recommendations are outside my scope. Please ask the Insurance Recommender agent.”
    • If the question is neither claim‑related nor insurance‑related, reply:
    “Sorry, I only assist with insurance claims.”
    • Provide step‑by‑step guidance, ask for any missing claim details, and confirm next steps.
    • Be conversational, concise, and supportive.
    """,
            "examples": [
                {
                    "user": "How do I file a car insurance claim for windshield damage?",
                    "assistant": "Sure! To file that claim:\n1. Take clear photos of the damage.\n2. Notify your insurer via app or call within 7 days.\n3. Submit photos + claim form.\n4. Wait for surveyor inspection. Need help?"
                },
                {
                    "user": "Which plan should I buy next?",
                    "assistant": "Recommendations are outside my scope. Please ask the Insurance Recommender agent."
                },
                {
                    "user": "What's the weather?",
                    "assistant": "Sorry, I only assist with insurance claims."
                }
            ],
            "defer": "Recommendations are outside my scope. Please ask the Insurance Recommender agent."
        },

        "General Q&A": {
            "system": """
    You are Kshitij, an expert Insurance Q&A assistant.
    • Greet the user in a friendly way.
    • Answer ONLY general insurance‑policy questions (coverage, exclusions, billing, endorsements, premium payment, renewals).
    • If the user asks for a recommendation or wants to file a claim, reply:
    “That’s outside my scope. Please ask the appropriate agent.”
    • If the question is not insurance‑related, reply:
    “Sorry, I only answer insurance questions.”
    • Keep answers to 2–4 sentences, clear, concise, and friendly.
    """,
            "examples": [
                {
                    "user": "What is not covered under my health policy?",
                    "assistant": "Typically, pre‑existing conditions, cosmetic procedures, and experimental treatments are excluded. Please check your policy schedule for specifics."
                },
                {
                    "user": "Can you recommend a plan?",
                    "assistant": "That’s outside my scope. Please ask the Insurance Recommender agent."
                },
                {
                    "user": "How do I check claim status?",
                    "assistant": "That’s outside my scope. Please ask the Claim Filing Helper agent."
                }
            ],
            "defer": "That’s outside my scope. Please ask the appropriate agent."
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


def route_or_call(agent_key, user_input, system_prompt=None):
    """
    Builds the prompt and calls the LLM, then trims hallucinated follow-up turns.
    """
    p = PROMPTS[agent_key]
    # 1) choose system prompt
    prompt = (system_prompt or p["system"].strip())
    # 2) add examples
    for ex in p["examples"]:
        prompt += f"\n\nUser: {ex['user']}\nAssistant: {ex['assistant']}"
    # 3) add current user input
    prompt += f"\n\nUser: {user_input}\nAssistant:"
    # 4) call LLM
    raw = get_mistral_response(prompt, user_input)

    # 🔥 Trim hallucinated Q&A: cut at first "User:" if LLM starts a new turn
    if "\nUser:" in raw:
        raw = raw.split("\nUser:")[0].strip()
    # 🔥 Also trim if LLM repeats "Assistant:" later
    if "\nAssistant:" in raw[1:]:
        raw = raw.split("\nAssistant:")[0].strip()

    return raw





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

with st.sidebar.expander("👤 Your Profile (helps me personalize)"):
    p = st.session_state.profile
    p["age"] = st.number_input(
        "Age", min_value=1, max_value=100,
        value=p["age"] or 0,
        key="profile_age"           # ← unique
    )
    p["income"] = st.number_input(
        "Monthly income (₹)", min_value=0,
        value=p["income"] or 0,
        key="profile_income"        # ← unique
    )
    p["goals"] = st.text_input(
        "Goals (e.g. savings, tax benefits)",
        value=p["goals"] or "",
        key="profile_goals"         # ← unique
    )
    p["risk_appetite"] = st.selectbox(
        "Risk appetite", ["Low", "Medium", "High"],
        index=(["Low","Medium","High"].index(p["risk_appetite"])
               if p["risk_appetite"] else 1),
        key="profile_risk"          # ← unique
    )




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


def build_prompt_with_profile(agent_key, user_input):
    # 1) Build the profile header
    p = st.session_state.profile
    profile_text = (
        f"User Profile:\n"
        f"- Age: {p['age']}  •  Income: ₹{p['income']}/mo\n"
        f"- Goals: {p['goals']}\n"
        f"- Risk Appetite: {p['risk_appetite']}\n\n"
    )
    # 2) Prepend it to the agent’s system prompt
    base = PROMPTS[agent_key]["system"].strip()
    return profile_text + base


# Chat input prompt with clear instructions
st.markdown("<h3 style='color:#4A90E2;'>💬 Type your question below:</h3>", unsafe_allow_html=True)

user_input = st.chat_input("E.g., I am 30 years old with a budget of 20,000/year. What insurance should I get?")

if user_input:
    with st.spinner(f"💭 Talking to {agent}..."):
        # Build a personalized prompt
        system_with_profile = build_prompt_with_profile(agent, user_input)
        # Call the router/agent using that enriched system prompt
        system_with_profile = build_prompt_with_profile(agent, user_input)
        answer = route_or_call(agent, user_input, system_prompt=system_with_profile)


        import pytz
        IST = pytz.timezone("Asia/Kolkata")
        now = datetime.now(IST).strftime("%B %d, %I:%M %p")

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


