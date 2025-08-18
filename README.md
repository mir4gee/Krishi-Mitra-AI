# 🌱 KrishiMitraAI

**An Agentic AI Advisor for Agriculture**

KrishiMitraAI is an **AI-powered agricultural assistant** that helps farmers, vendors, and other stakeholders make **timely, confident, and informed decisions** about crop selling, storage, and market conditions.

Unlike a traditional chatbot, KrishiMitraAI uses a **multi-agent pipeline** that combines forecasting, sentiment analysis, and spoilage modeling before responding. Each answer is **grounded in data**, with **reasoning and confidence scores explained transparently**.

---

## 🌱 Overview

Agriculture is one of India’s most critical sectors, where **small decisions carry big risks**. Farmers routinely face questions like:

- *When should I sell my crop?*
- *How long can I safely store it?*
- *Will market conditions improve next week?*
- *What government schemes or policies can help me?*

Our solution is designed as a **human-aligned agentic AI advisor** that:

- Understands natural, multilingual farmer queries (Hindi + English).
- Uses **specialized agents** for price forecasting, spoilage risk estimation, and market sentiment analysis.
- Fuses insights into reliable, context-aware recommendations.
- Provides **text and voice-based interfaces** for inclusivity.

---

## 🔑 Key Features

### Core Agentic Capabilities

- **Conversational Agricultural Advisor**
    - Text + voice interaction with AI
    - Multilingual (Hindi/English) with automatic translation
- **Agentic Decision Fusion**
    - Price forecaster (Prophet-based time series agent)
    - Spoilage risk agent (storage condition modeling)
    - News sentiment agent (real-time NewsAPI integration)
    - Supervisor agent that synthesizes signals into one clear recommendation

### Intelligence Layers

- **Real-Time Market Analysis**
    - 15-day price forecasts using Prophet & exponential smoothing
    - Market volatility tracking
- **News Sentiment Analysis**
    - Extracts themes from agricultural news
    - Detects bullish/bearish/neutral signals
- **Spoilage Risk Assessment**
    - Shelf-life estimation per crop
    - Storage condition impact modeling (temperature, humidity)
    - Quantified risk score (0–1 scale)

### Personalization

- Tailored advice based on user context: crop type, location, quality grade, quantity, and harvest timeline.
- Support for multiple user personas:
    - **Farmers (sellers)** → when/where to sell crops
    - **Vendors (buyers/sellers)** → trade intelligence
    - **General users** → agricultural information
    - **Future roadmap** → lenders, policymakers, cooperatives

---

## 📊 Example Capabilities

1. **Price Forecasting**
    - Predicts 15-day price trends using historical market data.
    - Assesses volatility and market stability.
2. **News & Weather Sentiment Analysis**
    - Fetches real-time agricultural news and IMD weather updates.
    - Scores sentiment (bullish/bearish/neutral).
    - Explains the reasoning (e.g., “Government subsidy expected → bullish outlook”).
3. **Spoilage Risk Assessment**
    - Estimates shelf life by crop type, storage temperature, and humidity.
    - Provides a **risk score (0–1)** and storage advice.
4. **Grounded Chat Response**
    - Example:
        
        > “Based on price forecast (+7% in 10 days), low spoilage risk (0.2), and bullish sentiment from market news, it is advisable to wait before selling. Confidence: 0.78”
        > 

---

## 🧠 Tech Stack

**Backend**

- Flask (API framework)
- Python 3.8+
- Google Generative AI (Gemini)
- Prophet + statsmodels (time series forecasting)
- pandas/numpy (data processing)
- NewsAPI (real-time news integration)
- deep-translator (multilingual support)

**Frontend**

- React (hooks-based UI)
- Lucide React (icons)
- MediaRecorder API (voice input)
- Fetch API (backend integration)

---

## ⚡ Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

```bash
git clone <repository-url>
cd agricultural-ai-chatbot
python -m venv agri_env
source agri_env/bin/activate   # Windows: agri_env\Scripts\activate
pip install -r requirements.txt

```

Create `.env` file:

```
GEMINI_API_KEY=your_gemini_api_key_here
NEWSAPI_KEY=your_newsapi_key_here

```

### Frontend Setup

```bash
cd frontend
npm install
npm start

```

---

## 🚀 Usage

**Start Backend**

```bash
python app.py

```

Runs at `http://localhost:5000`

**Start Frontend**

```bash
cd frontend
npm start

```

Runs at `http://localhost:3000`

---

## 📡 API Endpoints

**Text Chat**

```
POST /api/chat
Content-Type: application/json

```

Example Payload:

```json
{
  "prompt": "Should I sell my wheat now?",
  "model": "gemini-1.5-flash",
  "userContext": {
    "name": "Farmer",
    "cropType": "wheat",
    "quantity": "100",
    "qualityGrade": "A",
    "farmerLocation": "110001",
    "spoilageDate": "2024-09-15"
  }
}

```

**Audio Chat**

```
POST /api/audio-chat
Content-Type: multipart/form-data

```

Form Data:

- `audio`: [file]
- `model`: gemini-1.5-flash
- `userContext`: [JSON string]

---

## 📊 Data Sources

- [Agmarknet](https://agmarknet.gov.in/) → market prices
- [IMD](https://mausam.imd.gov.in/) → weather data
- [ICAR](https://icar.org.in/) → crop & soil guidelines
- [Press Information Bureau](https://pib.gov.in/) → government policies
- **Sample CSV** included (`market_data_csv.csv`) for demo purposes

---

## 🔮 Roadmap

- Expand to **SMS/IVR/WhatsApp interfaces** for low-connectivity regions
- Retrieval-augmented generation (RAG) to ground LLM answers in factual agri datasets
- Confidence scoring + source citations for trust & explainability
- Multi-agent orchestration (market, weather, soil, finance)

---

## 🏆 Why This Matters

This project demonstrates how **agentic AI can transform agriculture**:

- Farmers gain confidence to sell at the right time.
- Vendors and markets get transparency.
- Policymakers and lenders can integrate insights.

By combining **AI forecasting, multilingual interaction, and decision fusion**, this solution directly addresses the Launchpad theme of building **agentic AI systems with real-world societal impact**.

By combining **AI forecasting, multilingual interaction, and decision fusion**, this solution directly addresses the Launchpad theme of building **agentic AI systems with real-world societal impact**.

---
