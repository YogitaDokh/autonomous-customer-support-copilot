from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect
)

from groq import Groq

from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

import uuid
import plotly.express as px
import plotly
import json

# =========================
# FLASK APP
# =========================
load_dotenv()
app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

# =========================
# DATABASE CONFIG
# =========================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///copilot.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# =========================
# DB INITIALIZATION
# =========================
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"

# =========================
# USER MODEL
# =========================
class User(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(100),
        nullable=False
    )

# =========================
# CHAT MODEL
# =========================
class Chat(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    title = db.Column(
        db.String(200)
    )

# =========================
# MESSAGE MODEL
# =========================
class Message(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    chat_id = db.Column(
        db.Integer,
        db.ForeignKey("chat.id")
    )

    user_message = db.Column(
        db.Text
    )

    bot_response = db.Column(
        db.Text
    )

    intent = db.Column(
        db.String(100)
    )

    escalated = db.Column(
        db.Boolean,
        default=False
    )
# =========================
# USER LOADER
# =========================
@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))

# =========================
# GROQ CLIENT
# =========================
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# =========================
# LOAD COMPANY DOCUMENTS
# =========================
loader = TextLoader("company_docs/support_data.txt")

documents = loader.load()

# =========================
# SPLIT DOCUMENTS
# =========================
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

docs = text_splitter.split_documents(documents)

# =========================
# LAZY LOAD AI COMPONENTS
# =========================
embeddings = None
vectorstore = None


def load_vectorstore():

    global embeddings, vectorstore

    if embeddings is None:

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    if vectorstore is None:

        vectorstore = FAISS.from_documents(
            docs,
            embeddings
        )

    return vectorstore

# =========================
# RAG FUNCTION
# =========================
def ask_rag(user_input):

    vectorstore = load_vectorstore()

    similar_docs = vectorstore.similarity_search(
        user_input,
        k=2
    )

    context = "\n".join([
        doc.page_content for doc in similar_docs
    ])

    prompt = f"""
    You are a professional customer support assistant.

    Use ONLY the following company knowledge.

    Company Knowledge:
    {context}

    Customer Question:
    {user_input}
    """

    try:

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:

        print("RAG ERROR:", e)

        return "Sorry, I am unable to respond right now."
# =========================
# INTENT DETECTION
# =========================
def detect_intent(user_input):

    prompt = f"""
    Classify query into:

    refund
    technical_issue
    password_reset
    complaint
    general_query

    Query:
    {user_input}

    Return ONLY category.
    """

    try:

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        return response.choices[0].message.content.strip().lower()

    except Exception as e:

        print("Intent Error:", e)

        return "general_query"

# =========================
# ESCALATION CHECK
# =========================
def needs_escalation(user_input):

    escalation_keywords = [
        "fraud",
        "lawsuit",
        "scam",
        "terrible",
        "worst",
        "hate",
        "cancel account"
    ]

    user_input = user_input.lower()

    for word in escalation_keywords:

        if word in user_input:
            return True

    return False

# =========================
# INITIALIZE SESSION
# =========================
def initialize_session():

    if "conversations" not in session:

        first_chat_id = str(uuid.uuid4())

        session["conversations"] = {
            first_chat_id: []
        }

        session["active_chat"] = first_chat_id

# =========================
# HOME
# =========================
@app.route("/")
def landing():

    if current_user.is_authenticated:

        return redirect("/chat")

    return redirect("/login")

# =========================
# CHAT PAGE
# =========================
@app.route("/chat")
@login_required
def chat_page():

    chats = Chat.query.filter_by(
        user_id=current_user.id
    ).all()

    active_chat_id = request.args.get("chat_id")

    if not active_chat_id:

        if len(chats) == 0:

            new_chat = Chat(
                user_id=current_user.id,
                title="New Chat"
            )

            db.session.add(new_chat)

            db.session.commit()

            active_chat_id = new_chat.id

        else:

            active_chat_id = chats[0].id

    messages = Message.query.filter_by(
        chat_id=active_chat_id
    ).all()

    return render_template(
        "index.html",
        chats=chats,
        messages=messages,
        active_chat_id=int(active_chat_id)
    )
# =========================
# SIGNUP
# =========================
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:

            return "Username already exists!"

        new_user = User(
            username=username,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)

        db.session.commit()

        return redirect("/")

    return render_template("signup.html")

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            return redirect("/chat")

        return "Invalid username or password"

    return render_template("login.html")

# =========================
# LOGOUT
# =========================
@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/login")
# =========================
# NEW CHAT
# =========================
@app.route("/new_chat")
@login_required
def new_chat():

    chat = Chat(
        user_id=current_user.id,
        title="New Chat"
    )

    db.session.add(chat)

    db.session.commit()

    return jsonify({
        "success": True,
        "chat_id": chat.id
    })
# =========================
# SWITCH CHAT
# =========================
@app.route("/switch_chat/<chat_id>")
def switch_chat(chat_id):

    conversations = session.get("conversations", {})

    if chat_id in conversations:

        session["active_chat"] = chat_id

        session.modified = True

        return jsonify({
            "success": True
        })

    return jsonify({
        "success": False
    })

# =========================
# DELETE CHAT
# =========================
@app.route("/delete_chat/<chat_id>")
def delete_chat(chat_id):

    conversations = session.get("conversations", {})

    if chat_id in conversations:
        del conversations[chat_id]

    if len(conversations) == 0:

        new_chat_id = str(uuid.uuid4())

        conversations[new_chat_id] = []

        session["active_chat"] = new_chat_id

    else:
        session["active_chat"] = list(conversations.keys())[0]

    session["conversations"] = conversations

    session.modified = True

    return jsonify({"success": True})

# =========================
# CHATBOT
# =========================
@app.route("/get", methods=["POST"])
@login_required
def chatbot_response():

    data = request.get_json()

    user_input = data.get("message")

    chat_id = data.get("chat_id")

    intent = detect_intent(user_input)

    escalated = False

    if needs_escalation(user_input):

        escalated = True

        response = (
            "Your issue has been escalated "
            "to a human support agent."
        )

    else:

        response = ask_rag(user_input)

    new_message = Message(

        chat_id=chat_id,

        user_message=user_input,

        bot_response=response,

        intent=intent,

        escalated=escalated
    )

    db.session.add(new_message)

    db.session.commit()

    return jsonify({

        "response": response,

        "intent": intent
    })
# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
@login_required
def dashboard():

    conversations = session.get("conversations", {})

    total_conversations = len(conversations)

    intents = {
        "refund": 0,
        "technical_issue": 0,
        "password_reset": 0,
        "complaint": 0,
        "general_query": 0
    }

    escalation_count = 0

    for chat_id, messages in conversations.items():

        for msg in messages:

            detected_intent = msg.get(
                "intent",
                "general_query"
            )

            if detected_intent in intents:
                intents[detected_intent] += 1

            if msg.get("escalated") == True:
                escalation_count += 1

    pie_fig = px.pie(
        names=list(intents.keys()),
        values=list(intents.values()),
        title="Customer Intent Distribution"
    )

    pie_fig.update_traces(
        textinfo="label+percent+value"
    )

    pie_fig.update_layout(
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        font_color="white"
    )

    bar_fig = px.bar(
        x=list(intents.keys()),
        y=list(intents.values()),
        title="Customer Support Intent Analytics",
        labels={
            "x": "Intent Categories",
            "y": "Number of Queries"
        },
        text=list(intents.values())
    )

    bar_fig.update_traces(
        textposition="outside"
    )

    bar_fig.update_layout(
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        font_color="white"
    )

    pie_graph = json.dumps(
        pie_fig,
        cls=plotly.utils.PlotlyJSONEncoder
    )

    bar_graph = json.dumps(
        bar_fig,
        cls=plotly.utils.PlotlyJSONEncoder
    )

    return render_template(
        "dashboard.html",
        total_conversations=total_conversations,
        total_escalations=escalation_count,
        pie_graph=pie_graph,
        bar_graph=bar_graph
    )

# =========================
# SETTINGS
# =========================
@app.route("/settings")
def settings():

    return render_template("settings.html")

# =========================
# CREATE DATABASE
# =========================
with app.app_context():
    db.create_all()

# =========================
# RUN APP
# =========================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )