from dotenv import load_dotenv
from tavily import TavilyClient
import os
import json
from openai import OpenAI
import streamlit as st

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")

groq_client = OpenAI(api_key=groq_api_key,
                        base_url="https://api.groq.com/openai/v1")

tavily_api_key = os.getenv("TAVILY_API_KEY")

tavily_client = TavilyClient(api_key=tavily_api_key)

st.set_page_config(page_title="Lead Gen Agent",page_icon="🕵🏻")

st.title("Autonomous Lead Generation & Outreach Agent")
st.write("Enter a company name below. The agent will autonomously search the web, analyze current business pain points, and draft a hyper-personalized B2B outreach email.")

company_name = st.text_input("Wrtie the comapny name here",placeholder="For eg: Nothing, Apple, Meta, etc.")

if st.button("Run Agent!",type="primary"):

    if not company_name:
        st.warning("write a company name!")
    else:    
        with st.status("Agent running....",expanded=True) as status:
            st.write(f"Searching the web for {company_name} news......")

            search_response = tavily_client.search(query=f"{company_name} recent news and business updates 2026",
                                            search_depth="advanced",
                                            include_raw_content=True,
                                            max_results=3)

            safe_data = []

            for result in search_response.get("results",[]):
                raw_text = result.get("raw_content","")

                truncated_text = raw_text[:2500] if raw_text else result.get("content","")

                safe_data.append({"title":result.get("title"),
                    "url":result.get("url"),
                    "content":truncated_text})        

            formatted_response = json.dumps(safe_data,indent=2)

            st.write("Sending the searched data to the strategist.....")

            llm_response =  groq_client.chat.completions.create(messages=[{"role":"system","content":"You are an elite B2B Sales Strategist. Your job is to read search results about a target company and identify exactly 2 high-level business initiatives or pain points they are currently focused on. Keep your output extremely concise and structured."},
                                                                        {"role":"user","content":f"Here is the raw data scraped from the web today:\n\n{formatted_response}"}],
                                                                        model="openai/gpt-oss-120b")

            pain_points = llm_response.choices[0].message.content

            pain_points2 = json.dumps(pain_points,indent = 2)

            st.write("Sending the data received from the strategist to copywriter.....")

            llm_response2 =  groq_client.chat.completions.create(messages=[{"role":"system","content":"You are an elite B2B SDR (Sales Development Rep). Write a 3-sentence cold email to the CTO of the target company. Use the provided pain points to position our 'AI Infrastructure' software as a solution. Do not use buzzwords. Be direct, professional, and confident. Always include subject. Always write Hi [CTO Name] and the body of the email in separate paragraphs."},
                                                                        {"role":"user","content":f"Target Company: {company_name}\nIdentified Pain Points/Initiatives:\n{pain_points2}"}],
                                                                        model="openai/gpt-oss-120b")

            status.update(label="Agent sucessfully completed the action!",state="complete",expanded=False)

        st.success("Agent completed the mission!")

        st.subheader(f"Pain Points of {company_name} : ")
        st.info(pain_points)
        st.subheader(f"B2B cold email : ")
        st.text_area(label="Draft email (ready to copy/paste) : ",value=llm_response2.choices[0].message.content,height=250)






