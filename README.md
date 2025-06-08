
# 🤖 Autonomous LinkedIn Outreach Agent

Welcome to the Autonomous LinkedIn Outreach Agent! This project is a powerful, AI-driven tool designed to automate and scale your professional networking on LinkedIn. By intelligently personalizing messages and managing conversations, this agent streamlines the path to securing job referrals and professional connections.

---

## ✨ Key Features

* **🚀 High-Volume Outreach**: Sends **200+ personalized messages** every week.
* **🏆 Proven Success**: Secured **50+ referrals** for roles at Fortune 500 companies.
* **⏱️ Massive Time Savings**: Reduces manual message drafting time by **80%**.
* **📈 Enhanced Engagement**: **Doubled positive reply rates** with smart, automated follow-ups.
* **⚡ Optimized Performance**: Sliced query latency by **40%** with an advanced RAG architecture.

---

## 🛠️ How It Works & Core Components

This agent operates through a series of interconnected scripts, each with a specific role in the automation pipeline.

### 📂 `referral_requester.ipynb`
**🎬 Action**: Kicks off the outreach process.
This notebook crafts and sends highly personalized connection requests on LinkedIn. It customizes each message based on the recipient's profile, ensuring a strong and engaging first impression.

### 📲 `linkedin_manager.py`
**📥 Action**: Captures incoming communication.
Once a connection replies, this Python script automatically scrapes the new messages from your LinkedIn inbox. This ensures all conversation data is captured in real-time for the next stage.

### 🗄️ `add_messages.py`
**💾 Action**: Persists conversation data.
This script takes the scraped messages and securely stores them in a local **PostgreSQL** database. This creates a structured, queryable history of all your professional interactions.

### 🧠 `generate_summaries.py`
**✍️ Action**: Generates intelligent, human-like replies.
Leveraging the power of **OpenAI's Large Language Models (LLMs)**, this script analyzes conversation histories, generates concise summaries, and drafts context-aware responses. It ensures every follow-up is relevant, timely, and personal.

### 📧 `email_automate.py`
**📮 Action**: Expands outreach to email.
When a contact provides an email address, this script takes over to automate sending follow-up emails. This creates a seamless, multi-channel communication strategy.

### 🌐 `apollo_automate.py`
**🔎 Action**: Enriches contact data.
To maximize outreach potential, this script automatically scrapes professional email addresses from **Apollo.io**. This provides a valuable, alternative channel for direct communication.

### ⚡ `pinecone_vector_base.py`
**🧠 Action**: Powers the AI memory and search.
This is the intelligent core of the agent. It embeds all conversations using the `bge-large-en` model and stores them in a **Pinecone** vector database. This establishes a sophisticated **Retrieval-Augmented Generation (RAG)** system, enabling lightning-fast semantic search. You can instantly "chat" with your entire messaging history to find key details and craft perfectly informed replies.