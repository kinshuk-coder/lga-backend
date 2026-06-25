import os
import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from tavily import TavilyClient
from openai import OpenAI

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Repointed to Groq's Base URL using their API key
llm_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

class CompanyRequest(BaseModel):
    name: str

@app.post("/chat")
async def run_agent(request: CompanyRequest):
    company = request.name
    if not company:
        raise HTTPException(status_code=400, detail="Company name is required")

    async def agent_stream():
        try:
            # --- PHASE 1: SCOUTING ---
            yield json.dumps({"status": "scouting", "message": f"Agent is scouting the web for recent {company} news..."}) + "\n"
            await asyncio.sleep(0.1) 
            
            search_response = tavily_client.search(
                query=f"{company} recent news and business updates 2026",
                search_depth="advanced",
                include_raw_content=True,
                max_results=3
            )

            safe_data = []
            for result in search_response.get("results", []):
                raw_text = result.get("raw_content", "")
                truncated_text = raw_text[:2500] if raw_text else result.get("content", "")
                safe_data.append({
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "content": truncated_text
                })
            
            scraped_data_string = json.dumps(safe_data, indent=2)

            # --- PHASE 2: STRATEGIZING ---
            yield json.dumps({"status": "analyzing", "message": "Strategist is analyzing data for business priorities..."}) + "\n"
            await asyncio.sleep(0.1)

            strategist_response = llm_client.chat.completions.create(
                model="openai/gpt-oss-120b", # Swapped to your requested model
                messages=[
                    {"role": "system", "content": "You are a B2B Sales Strategist. Read the provided search results and identify exactly 2 current business initiatives or pain points this company is focused on. Be concise."},
                    {"role": "user", "content": f"Raw data:\n\n{scraped_data_string}"}
                ]
            )
            pain_points = strategist_response.choices[0].message.content

            # --- PHASE 3: DRAFTING ---
            yield json.dumps({"status": "drafting", "message": "Copywriter is drafting the hyper-personalized email..."}) + "\n"
            await asyncio.sleep(0.1)

            copywriter_response = llm_client.chat.completions.create(
                model="openai/gpt-oss-120b", # Swapped to your requested model
                messages=[
                    {"role": "system", "content": "You are an elite B2B SDR. Write a 3-sentence cold email to the CTO of the target company. Use the provided pain points to position our 'AI Infrastructure' software as a solution. Do not use buzzwords. Be direct, professional, and confident."},
                    {"role": "user", "content": f"Target Company: {company}\nIdentified Pain Points/Initiatives:\n{pain_points}"}
                ]
            )
            final_email = copywriter_response.choices[0].message.content

            # --- PHASE 4: COMPLETE ---
            yield json.dumps({
                "status": "complete", 
                "pain_points": pain_points, 
                "mail": final_email
            }) + "\n"

        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"

    return StreamingResponse(agent_stream(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)