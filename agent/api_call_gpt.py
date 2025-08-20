import os
import base64
import mimetypes
from openai import OpenAI
from typing import List, Dict, Optional

# instantiate once
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_llm(
    messages: List[Dict[str, str]],
    model_name: str = "gpt-4o",
    temperature: float = 1,
    max_tokens: int = 2000,
) -> str:
    resp = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()


def local_image_to_data_url(image_path: str) -> str:
    """
    Convert a local image file to a base64-encoded data URL.
    """
    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "application/octet-stream"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def call_vlm(
    messages: List[Dict[str, str]],
    image_paths: List[str],
    model_name: str = "gpt-4o",
    temperature: float = 1,
    max_tokens: int = 2000,
) -> str:
    # convert all images to data URLs
    data_urls = [local_image_to_data_url(path) for path in image_paths]

    # locate last user message
    last_user_idx = max(i for i, m in enumerate(messages) if m["role"] == "user")

    # build new messages list with images embedded
    new_msgs: List[Dict] = []
    for i, m in enumerate(messages):
        if i == last_user_idx:
            # Start with the text content
            content = [{"type": "text", "text": m["content"]}]
            
            # Add all images
            for data_url in data_urls:
                content.append({
                    "type": "image_url", 
                    "image_url": {"url": data_url}
                })
            
            new_msgs.append({
                "role": "user",
                "content": content
            })
        else:
            new_msgs.append(m)

    resp = client.chat.completions.create(
        model=model_name,
        messages=new_msgs,
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()


def call_vlm_flexible(
    messages: List[Dict[str, str]],
    image_paths: List[str] = None,
    image_path: str = None,  # backward compatibility
    model_name: str = "gpt-4o",
    temperature: float = 0.3,
    max_tokens: int = 500,
) -> str:
    # Handle backward compatibility and argument validation
    if image_paths is None and image_path is None:
        raise ValueError("Must provide either image_paths (list) or image_path (single)")
    
    if image_paths is None:
        image_paths = [image_path]
    elif image_path is not None:
        # Both provided, prefer image_paths but warn
        print("Warning: Both image_paths and image_path provided. Using image_paths.")
    
    # convert all images to data URLs
    data_urls = [local_image_to_data_url(path) for path in image_paths]

    # locate last user message
    last_user_idx = max(i for i, m in enumerate(messages) if m["role"] == "user")

    # build new messages list with images embedded
    new_msgs: List[Dict] = []
    for i, m in enumerate(messages):
        if i == last_user_idx:
            # Start with the text content
            content = [{"type": "text", "text": m["content"]}]
            
            # Add all images
            for data_url in data_urls:
                content.append({
                    "type": "image_url", 
                    "image_url": {"url": data_url}
                })
            
            new_msgs.append({
                "role": "user",
                "content": content
            })
        else:
            new_msgs.append(m)

    resp = client.chat.completions.create(
        model=model_name,
        messages=new_msgs,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()