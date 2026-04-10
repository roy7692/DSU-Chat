import streamlit as st
import requests
import json
import hashlib
from collections import deque

# ---------------- CONFIG ----------------
OLLAMA_URL = "http://localhost:11434/api/generate"

MODELS = {
    "Llama 3 (Fast)": "llama3",
    "Mistral 7B (Accurate)": "mistral",
}

CACHE = {}
CACHE_SIZE = 100

# ---------------- MEMORY ----------------
class Memory:
    def __init__(self, max_len=6):
        self.history = deque(maxlen=max_len)

    def add(self, role, content):
        self.history.append((role, content))

    def get_context(self):
        return "\n".join([f"{r}: {c}" for r, c in self.history])

    def clear(self):
        self.history.clear()

# ---------------- CACHE ----------------
def cache_key(user, ctx, model):
    return hashlib.md5(f"{user}|{ctx[-300:]}|{model}".encode()).hexdigest()

def get_cache(key):
    return CACHE.get(key)

def set_cache(key, value):
    if len(CACHE) > CACHE_SIZE:
        CACHE.pop(next(iter(CACHE)))
    CACHE[key] = value

# ---------------- OLLAMA STREAM ----------------
def stream_ollama(prompt, model):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": 0.3}
    }

    try:
        res = requests.post(OLLAMA_URL, json=payload, stream=True)
        for line in res.iter_lines():
            if line:
                data = json.loads(line.decode())
                token = data.get("response", "")
                yield token
                if data.get("done"):
                    break
    except Exception as e:
        yield f"⚠️ Error: {e}"

# ---------------- RESPONSE ENGINE ----------------
def generate_response(user_input):
    context = st.session_state.memory.get_context()

    DSU_CONTEXT = """
Dayananda Sagar University (DSU), Bangalore:

ACADEMICS:
- Engineering (CSE, AI, ECE, Mechanical, Civil, Biotech)
- MBA, BBA, BCA, MCA
- Law, Design, Health Sciences, Sciences

ADMISSIONS:
- KCET, COMEDK, JEE, CAT, MAT, CLAT
- Online application + counseling

FEES:
- B.Tech: ₹2.5L–₹4L/year
- MBA: ₹3L–₹5L/year
- Scholarships available

PLACEMENTS:
- Avg: ₹6–7 LPA
- Top: ₹40+ LPA
- Recruiters: Amazon, Microsoft, Infosys

CAMPUS:
- Smart classrooms, labs, library, sports

HOSTEL:
- AC/non-AC, WiFi, mess

RESULTS:
- https://results.dsu.edu.in

EVENTS:
- Cultural fest, tech events

CONTACT:
- https://dsu.edu.in
"""

    prompt = f"""
You are an expert assistant for Dayananda Sagar University (DSU).

Rules:
- Answer ONLY DSU-related queries
- Use the DSU knowledge below
- Be confident and helpful
- If unrelated → say:
  "This is not related to DSU. Visit https://dsu.edu.in"

DSU DATA:
{DSU_CONTEXT}

Conversation:
{context}

User: {user_input}
Assistant:
"""

    key = cache_key(user_input, context, MODEL_NAME)
    cached = get_cache(key)
    if cached:
        return cached

    full = ""
    for token in stream_ollama(prompt, MODEL_NAME):
        full += token

    # fallback safeguard
    if len(full.strip()) < 20:
        full = """
I couldn't find a strong DSU-specific answer.

🔗 https://dsu.edu.in
"""

    set_cache(key, full)
    return full

# ---------------- INIT ----------------
st.set_page_config(page_title="DSU Assistant", page_icon="💬", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = Memory()

# ---------------- UI ----------------
st.markdown("""
<style>
.stApp { background-color: #0b0b0b; }
header, footer { visibility: hidden; }

.chat-container { max-width: 900px; margin: auto; padding-bottom: 120px; }
.chat-scroll { max-height: 75vh; overflow-y: auto; }

.user { display: flex; justify-content: flex-end; }
.bot { display: flex; justify-content: flex-start; }

.bubble {
    padding: 14px 18px;
    border-radius: 18px;
    margin: 8px;
    max-width: 75%;
    font-size: 20px;
}

.user .bubble {
    background: linear-gradient(135deg, #0095F6, #0077cc);
    color: white;
}

.bot .bubble {
    background: #1e1e1e;
    color: #e6e6e6;
}

.avatar { font-size: 22px; margin: 8px; }

.stChatInput {
    position: fixed;
    bottom: 10px;
    left: 0;
    right: 0;
    max-width: 900px;
    margin: auto;
}

textarea {
    background: #1e1e1e !important;
    color: white !important;
}

h1 { text-align: center; color: white; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>🎓 DSU AI Assistant</h1>", unsafe_allow_html=True)

MODEL_NAME = st.sidebar.selectbox("Model", list(MODELS.values()))

if st.sidebar.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.session_state.memory.clear()
    st.rerun()

# ---------------- CHAT ----------------
st.markdown('<div class="chat-container"><div class="chat-scroll">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="user">
            <div class="bubble">{msg["content"]}</div>
            <div class="avatar">👤</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="bot">
            <div class="avatar">🤖</div>
            <div class="bubble">{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)

# ---------------- INPUT ----------------
user_input = st.chat_input("Message DSU Assistant...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.memory.add("User", user_input)

    with st.spinner("Thinking..."):
        response = generate_response(user_input)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.memory.add("Assistant", response)

    st.rerun()