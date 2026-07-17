import os
import json
from pydantic import ValidationError
from google import genai
from app.schemas import TestCaseList

def generate_test_cases(text: str) -> dict:
    """
    Generates test cases using Gemini.
    Returns:
    {
        "status": "ok" | "retried" | "failed",
        "raw_response": str,
        "parsed": list[dict]
    }
    """
    api_key = os.environ.get("GEMINI_API_KEY", "dummy")
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return {"status": "failed", "raw_response": f"Failed to initialize client: {str(e)}", "parsed": []}
    
    prompt = f"""
You are a medical device QA engineer.
Based on the following device manual section, generate 3 to 5 QA test case ideas.

Manual text:
{text}

Return ONLY a JSON array of objects with the keys 'title', 'steps' (a list of strings), and 'expected_result'.
Do not wrap the JSON in markdown code blocks. Do not add prose.
"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        raw_text = response.text
    except Exception as e:
        return {"status": "failed", "raw_response": str(e), "parsed": []}
        
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
            if isinstance(data, list):
                parsed = TestCaseList(test_cases=data)
            elif isinstance(data, dict) and "test_cases" in data:
                parsed = TestCaseList(**data)
            else:
                raise ValueError("Not an array or TestCaseList")
            return parsed.model_dump()["test_cases"], "ok"
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            return str(e), "malformed"
            
    parsed_data, status = parse_attempt(raw_text)
    
    if status == "ok":
        return {"status": "ok", "raw_response": raw_text, "parsed": parsed_data}
        
    # Retry once on malformed
    retry_prompt = f"""
Your last response was not valid JSON matching the schema. 
Error: {parsed_data}
Return ONLY a JSON array of objects with keys 'title', 'steps', 'expected_result', no prose.
"""
    try:
        response2 = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt + retry_prompt,
        )
        raw_text2 = response2.text
        parsed_data2, status2 = parse_attempt(raw_text2)
        if status2 == "ok":
            return {"status": "retried", "raw_response": raw_text2, "parsed": parsed_data2}
        else:
            return {"status": "failed", "raw_response": raw_text2, "parsed": []}
    except Exception as e:
         return {"status": "failed", "raw_response": str(e), "parsed": []}
