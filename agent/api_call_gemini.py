import os
from google import genai
from google.genai import types
from PIL import Image
from typing import List, Dict

# Configure Gemini API
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def format_for_gemini(messages: List[Dict[str, str]]):
    gemini_messages = []
    sys_instruction = ""
    for msg in messages:
        if msg['role'] == "user":
            gemini_messages.append(msg['content'])
        elif msg['role'] == "system":
            sys_instruction += msg['content']
    return gemini_messages, sys_instruction


def call_llm(
    messages: List[Dict[str, str]],
    model_name: str = "gemini-2.5-pro",
    temperature: float = 0.3,
) -> str:
    
    gemini_messages, sys_instruction = format_for_gemini(messages=messages)
    
    response = client.models.generate_content(
        model=model_name,
        contents=gemini_messages,
        config=types.GenerateContentConfig(
            system_instruction=sys_instruction,
            temperature=temperature)
    )
    return response.text


def call_vlm(
    messages: List[Dict[str, str]],
    image_paths: List[str],
    model_name: str = "gemini-2.5-pro",
    temperature: float = 0.3
) -> str:
    gemini_messages, sys_instruction = format_for_gemini(messages=messages)
    for image_path in image_paths:
        image = Image.open(image_path)
        gemini_messages.append(image)
    
    response = client.models.generate_content(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=sys_instruction,
            temperature=temperature),
        contents=gemini_messages
    )
    
    return response.text