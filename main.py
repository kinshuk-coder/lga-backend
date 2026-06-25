# Importing necessary modules
from dotenv import load_dotenv
from tavily import TavilyClient
import os
import json
from openai import AsyncOpenAI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
from pydantic import BaseModel

# Injecting the enviroment variables
load_dotenv()

# Initializing our fastapi client
app = FastAPI()

# CORS to let the backend talk to only our specified URLs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True,
    allow_headers = ["*"],
    allow_methods = ["*"],

)

# Initializing clients 
groq_api_key = os.getenv("GROQ_API_KEY")

groq_client = AsyncOpenAI(api_key=groq_api_key,
                        base_url="https://api.groq.com/openai/v1")

tavily_api_key = os.getenv("TAVILY_API_KEY")

tavily_client = TavilyClient(api_key=tavily_api_key)

# Initializing class using BaseModel
class Company(BaseModel):
    name: str

# Chat endpoint for the agent to recieve comapny name
@app.post("/chat")
async def search_query(company : Company):

    async def stream_agent():

        # Exception Handling
        try:
            company_name = company.name

            # Using yield to send data periodically and await asyncio to rest the cpu for 100 ms after each stream, adding \n to separate lines
            yield json.dumps({"status":"scouting","message":f"Agent is scouting the web for recent {company_name} news..."}) + "\n"
            await asyncio.sleep(0.1)

            # calling tavily search to search the web
            search_response = tavily_client.search(query=f"{company_name} recent news and business updates 2026",
                                                    search_depth="advanced",
                                                    include_raw_content=True,
                                                    max_results=3)

            safe_data = []

            # Saving only top 2500 characters of each result 
            for result in search_response.get("results",[]):
                raw_text = result.get("raw_content","")

                truncated_text = raw_text[:2500] if raw_text else result.get("content","")

                safe_data.append({"title":result.get("title"),
                    "url":result.get("url"),
                    "content":truncated_text})        

            formatted_response = json.dumps(safe_data,indent=2)

            yield json.dumps({"status":"analyzing","message":"Strategist is analyzing data for business priorities..."}) + "\n"
            await asyncio.sleep(0.1)

            # Sending the formatted data to the strategist (llm)
            llm_response =  await groq_client.chat.completions.create(messages=[{"role":"system","content":"You are an elite B2B Sales Strategist. Your job is to read search results about a target company and identify exactly 2 high-level business initiatives or pain points they are currently focused on. Keep your output extremely concise and structured. Do not use any emojis."},
                                                                        {"role":"user","content":f"Here is the raw data scraped from the web today:\n\n{formatted_response}"}],
                                                                        model="openai/gpt-oss-120b")

            pain_points = llm_response.choices[0].message.content

            yield json.dumps({"status":"drafting","message":"Copywriter is drafting the hyper-personalized email..."}) + "\n"
            await asyncio.sleep(0.1)

            # Sending the formatted data to the copywriter (llm)
            llm_response2 = await groq_client.chat.completions.create(messages=[{"role":"system","content":"You are an elite B2B SDR (Sales Development Rep). Write a 3-sentence cold email to the CTO of the target company. Use the provided pain points to position our 'AI Infrastructure' software as a solution. Do not use buzzwords. Be direct, professional, and confident. Always include subject. Always write Hi [CTO Name] and the body of the email in separate paragraphs."},
                                                                        {"role":"user","content":f"Target Company: {company_name}\nIdentified Pain Points/Initiatives:\n{pain_points}"}],
                                                                        model="openai/gpt-oss-120b")
            
            final_email = llm_response2.choices[0].message.content

            yield json.dumps({"status":"complete",
                            "pain_points":pain_points,
                            "mail":final_email}) + "\n"
        except Exception as e:
            yield json.dumps({"status":"error","message":f"Error occured : {str(e)}"})
                

    # Calling the StreamingResponse class with our defined function    
    return StreamingResponse(stream_agent(),media_type="application/x-ndjson")    