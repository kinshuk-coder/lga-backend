# Autonomous Lead Gen Agent: Backend API

This repository contains the FastAPI Python microservice that acts as the reasoning engine and orchestration layer for the **Autonomous Lead Generation Agent**. It manages asynchronous internet scraping, context window optimization, and multi-prompt LLM chaining to draft hyper-personalized B2B cold outreach.

## Live API Endpoint
* **Backend Hosted On:** [[lga-backend.onrender.com](https://lga-backend.onrender.com)]
* **Frontend UI Repository:** [[github.com/kinshuk-coder/lga-frontend](https://github.com/kinshuk-coder/lga-frontend)]

## Architecture & Tech Stack

**Core Technologies:**
* **Framework:** FastAPI (Python) for asynchronous, high-performance API routing.
* **LLM Inference:** Groq LPU processing utilizing `gpt-oss-120b` for near-instantaneous language generation.
* **Search Engine:** Tavily API for AI-optimized web scraping and news aggregation.
* **Hosting:** Deployed via Render as a cloud-native web service.

**System Design:**
* Exposes a `/chat` POST endpoint protected by strict CORS middleware, ensuring only the authorized React frontend can trigger the agentic loop.

## Key Engineering Decisions

* **Agentic Multi-Step Workflow:** Instead of a single zero-shot prompt, the system relies on an orchestrated pipeline:
  1. **The Scout:** Fetches live internet data regarding a target company.
  2. **The Strategist:** Analyzes the raw data to identify active corporate pain points.
  3. **The Copywriter:** Drafts targeted, high-conversion SDR copy based strictly on the Strategist's findings.
* **Server-Sent Events (SSE) via NDJSON:** Standard HTTP requests timeout or cause poor UX during long LLM generations. This API utilizes Python's asynchronous generator functions (`yield`) to stream Newline-Delimited JSON chunks back to the client. This allows the frontend to render the agent's internal reasoning steps in real-time.
* **Context Window Protection:** To prevent token limit overflow and "Lost in the Middle" degradation, the API actively intercepts and truncates raw HTML/text payloads from the Search Tool before injecting them into the LLM's system prompt.

## Local Setup & Installation

**1. Clone the repository**
```bash
git clone [https://github.com/kinshuk-coder/lga-backend.git](https://github.com/kinshuk-coder/lga-backend.git)
cd lga-backend
```

**2. Create a virtual environment & install dependencies**
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

**3. Configure Environment Variables**
Create a `.env` file in the root directory and add your required API keys:
```text
TAVILY_API_KEY=your_tavily_key_here
GROQ_API_KEY=your_groq_key_here
```

**4. Run the development server**
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
*Note: The API will be available at `http://127.0.0.1:8000`. You can view the automatic Swagger UI documentation at `http://127.0.0.1:8000/docs`.*

## 👨‍💻 Author
* **Kinshuk** - Architect & Developer
