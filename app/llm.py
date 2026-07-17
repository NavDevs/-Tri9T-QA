import os
import json
from pydantic import ValidationError
from groq import Groq
from app.schemas import TestCaseList

def generate_test_cases(text: str) -> dict:
    """
    Generates test cases using Groq.
    Returns:
    {
        "status": "ok" | "retried" | "failed",
        "raw_response": str,
        "parsed": list[dict]
    }
    """
    api_key = os.environ.get("GROQ_API_KEY", "dummy")
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        return {"status": "failed", "raw_response": f"Failed to initialize client: {str(e)}", "parsed": []}
        
    prompt = f"""
You are a medical device QA engineer.
Based on the following device manual section, generate 3 to 5 QA test case ideas.

Manual text:
{text}

Return ONLY a valid JSON object containing a single key "test_cases" which maps to an array of objects. 
Each object must have the keys 'title' (string), 'steps' (array of strings), and 'expected_result' (string).
Do not add prose.
"""

    def parse_attempt(raw: str):
        # clean markdown if present
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        
        try:
            data = json.loads(raw.strip())
            parsed = TestCaseList(**data)
            return parsed.model_dump()["test_cases"], "ok"
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            return str(e), "malformed"

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        raw_text = response.choices[0].message.content
    except Exception as e:
        return {"status": "failed", "raw_response": str(e), "parsed": []}

    parsed_data, status = parse_attempt(raw_text)
    
    if status == "ok":
        return {"status": "ok", "raw_response": raw_text, "parsed": parsed_data}
        
    # Retry once
    retry_prompt = f"""
Your last response was not valid JSON matching the schema. 
Error: {parsed_data}
Return ONLY a valid JSON object with the key "test_cases", mapping to the array. No prose.
"""
    try:
        response2 = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": raw_text},
                {"role": "user", "content": retry_prompt}
            ],
            response_format={"type": "json_object"}
        )
        raw_text2 = response2.choices[0].message.content
        parsed_data2, status2 = parse_attempt(raw_text2)
        if status2 == "ok":
            return {"status": "retried", "raw_response": raw_text2, "parsed": parsed_data2}
        else:
            return {"status": "failed", "raw_response": raw_text2, "parsed": []}
    except Exception as e:
         return {"status": "failed", "raw_response": str(e), "parsed": []}
