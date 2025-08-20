import re
import json


def parse_answer(response: str):
    if not response or not isinstance(response, str):
        return ""
    
    # Use DOTALL flag to handle multiline content
    match = re.search(r"<answer>\s*(.*?)\s*</answer>", response, re.DOTALL | re.IGNORECASE)
    
    if match:
        content = match.group(1)
        # Convert to single line: replace newlines/tabs with spaces, compress multiple spaces
        single_line = re.sub(r'\s+', ' ', content).strip()
        return single_line
    
    # Fallback: return original response as single line
    return re.sub(r'\s+', ' ', response).strip()


def parse_answer_json(llm_response: str) -> dict:
    # Extract content between <answer> and </answer>
    match = re.search(r'<answer>(.*?)</answer>', llm_response, re.DOTALL)
    
    if not match:
        raise ValueError("No <answer>...</answer> tags found in response")
    
    answer_content = match.group(1).strip()
    
    try:
        # Parse the JSON string into a dictionary
        return json.loads(answer_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in answer tags: {e}")
    

def format_message(sys_prompt=None, user_prompt=None):
    message = []
    if sys_prompt:
        message.append({"role": "system", "content": sys_prompt})
    if user_prompt:
        message.append({"role": "user", "content": user_prompt})
        
    return message