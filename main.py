import streamlit as st
from dotenv import load_dotenv
import os
import requests
from datetime import datetime

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




st.set_page_config(page_title="GenAI Multi-Agent BFSI Assistant", page_icon="🔮")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("🔮 GenAI Multi-Agent Insurance Assistant")

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
# ✅ 5) Streamlit UI
# ===========================
st.markdown("Choose the agent you'd like to interact with:")

agent = st.selectbox(
    "🧠 Select Agent",
    list(PROMPTS.keys()),
    index=0,
)

st.markdown("Enter your question or details below:")

user_input = st.text_area(
    "💬 Your input:",
    placeholder="E.g., I am 30 years old with a budget of 20,000/year. What insurance should I get?",
    height=150
)

if st.button("🚀 Get Response"):
    if not user_input.strip():
        st.warning("⚠️ Please enter your input before submitting.")
    else:
        with st.spinner(f"Talking to the {agent}..."):
            answer = get_mistral_response(PROMPTS[agent], user_input)

            now = datetime.now().strftime("%B %d, %I:%M %p")

            # Save this turn to session state
            st.session_state.chat_history.append({
                "agent": agent,
                "user_input": user_input,
                "agent_response": answer,
                "timestamp": now,
            })

            print("Saved chat:", st.session_state.chat_history[-1])  # this line for debugging

# Show response immediately
if 'answer' in locals():
    st.success(f"**{agent} Response:**\n\n{answer}")
else:
    st.warning("Start a conversation.")


st.markdown("## 🗨️ Chat History")

if st.session_state.chat_history:
    for chat in st.session_state.chat_history:
        ts = chat.get("timestamp", "No timestamp")
        # User bubble
        st.markdown(format_message("user", chat["user_input"], ts), unsafe_allow_html=True)
        # Agent bubble
        st.markdown(format_message("agent", chat["agent_response"], ts), unsafe_allow_html=True)

st.markdown("---")


# ===========================
# ✅ 6) Optional: Display Mock Products for Recommender
# ===========================
if agent == "Insurance Recommender":
    st.markdown("---")
    st.subheader("📦 Example Insurance Products")
    for product in INSURANCE_PRODUCTS:
        st.markdown(
            f"**{product['name']}**\n"
            f"- Type: {product['type']}\n"
            f"- Risk: {product['risk']}\n"
            f"- Features: {product['features']}\n"
        )
