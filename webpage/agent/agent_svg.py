import sys
import os
from typing import Dict, List, Any, Tuple
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .prompts_svg import LLM_grammar_sys, SINGLE_CANDIDATE_GENERATION_PROMPT
from .prompts_vlm import vlm_description_sys, vlm_description_user
from .api_call_gpt import call_llm_parallel, call_llm
from .parser import parse_answer_json, format_message, parse_think


class Agent:
    """
    Agent that manages the iterative optimization process using VLM and LLM with candidate selection.
    """
    
    def __init__(self, model_name,
                 canvas_w=800, canvas_h=600):
        self.model_name = model_name
        self.LLM_grammar_sys = LLM_grammar_sys.format(canvas_width=canvas_w, canvas_height=canvas_h)
    
    def optimization_step_user(self, current_expression, actions) -> Tuple[str, Dict[str, Any], bool]:
        thought, candidates = self._generate_expressions(
            current_expression,
            actions
        )
        return thought, candidates[0]
    
    def optimization_step_vlm(self, current_expression, actions, image_base64: str) -> str:
        description = self._generate_description(actions=actions, image_base64=image_base64)
        thought, candidates = self._generate_expressions(
            current_expression,
            description
        )
        return thought, candidates[0], description

    def _generate_expressions(self, current_expression: List, actions: str) -> List[str]:
        # Prepare parallel requests
        requests = []
        user_prompt = SINGLE_CANDIDATE_GENERATION_PROMPT.format(
            current_expression=current_expression,
            current_actions=actions,
        )
        sys_prompt = self.LLM_grammar_sys
        messages = format_message(sys_prompt, user_prompt)
        
        requests.append({
            "messages": messages,
            "model_name": self.model_name,
        })
        
        # Execute parallel API calls
        results = call_llm_parallel(requests, max_workers=5)
        
        # Process results
        candidates = []
        for i, result in enumerate(results):
            if result["success"]:
                response = result["response"]
                # print(response)
                try:
                    thought = parse_think(response)
                    # Extract SVG code from response
                    modified_svg = parse_answer_json(response)
                    
                    if modified_svg:
                        candidates.append(modified_svg)
                    else:
                        candidates.append(current_expression)

                except Exception:
                    candidates.append(current_expression)
            else:
                candidates.append(current_expression)  # Fallback
        
        return thought, candidates[:1]
    
    def _generate_description(self, actions, image_base64: str) -> str:
        user_prompt = vlm_description_user.format(user_instructions=actions)
        requests = format_message(sys_prompt=vlm_description_sys, user_prompt=user_prompt)
        requests.append({
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_base64}}
            ]
        })

        response = call_llm(
            messages=requests,
            model_name=self.model_name
        )

        return response
