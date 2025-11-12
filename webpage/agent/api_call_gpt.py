import os
import base64
import mimetypes
from openai import OpenAI
from typing import List, Dict, Any, Optional
import concurrent.futures
from dotenv import load_dotenv


load_dotenv()

# instantiate once
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def call_llm(
    messages: List[Dict[str, str]],
    model_name: str = "gpt-5",
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
    model_name: str = "gpt-5",
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


def call_llm_parallel(
    requests: List[Dict[str, Any]],
    max_workers: int = 5,
    timeout: Optional[float] = None,
) -> List[Dict[str, Any]]:

    def process_single_request(idx: int, req: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = call_llm(
                messages=req["messages"],
                model_name=req.get("model_name", "gpt-5"),
                temperature=req.get("temperature", 1),
                max_tokens=req.get("max_tokens", 2000),
            )
            return {
                "success": True,
                "response": response,
                "request_index": idx,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "request_index": idx,
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_request, i, req): i
            for i, req in enumerate(requests)
        }

        results = []
        for future in concurrent.futures.as_completed(futures, timeout=timeout):
            results.append(future.result())

    # Sort by original request order
    results.sort(key=lambda x: x["request_index"])
    return results


def call_vlm_parallel(
    requests: List[Dict[str, Any]],
    max_workers: int = 5,
    timeout: Optional[float] = None,
) -> List[Dict[str, Any]]:

    def process_single_request(idx: int, req: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = call_vlm(
                messages=req["messages"],
                image_paths=req["image_paths"],
                model_name=req.get("model_name", "gpt-5"),
                temperature=req.get("temperature", 1),
                max_tokens=req.get("max_tokens", 2000),
            )
            return {
                "success": True,
                "response": response,
                "request_index": idx,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "request_index": idx,
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_request, i, req): i
            for i, req in enumerate(requests)
        }

        results = []
        for future in concurrent.futures.as_completed(futures, timeout=timeout):
            results.append(future.result())

    # Sort by original request order
    results.sort(key=lambda x: x["request_index"])
    return results


if __name__ == "__main__":
    requests = [
        {
            "messages": [{"role": "user", "content": "What is Python?"}],
            "temperature": 0.7,
        },
        {
            "messages": [{"role": "user", "content": "What is JavaScript?"}],
            "temperature": 0.7,
        },
        {
            "messages": [{"role": "user", "content": "What is Rust?"}],
            "temperature": 0.7,
        },
    ]

    results = call_llm_parallel(requests, max_workers=3)

    for result in results:
        if result["success"]:
            print(f"Request {result['request_index']}: {result['response'][:100]}...")
        else:
            print(f"Request {result['request_index']} failed: {result['error']}")