import logging
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .memory import Memory, State
from .prompts_svg import LLM_grammar_sys, LLM_program_synthesis_prompt, SINGLE_CANDIDATE_GENERATION_PROMPT
from .prompts import VLM_edits_sys, VLM_edits_user_2, VLM_scene_description_prompt, VLM_edits_with_feedback_prompt
from .prompts_vlm_select import VLM_CANDIDATE_SELECTION_PROMPT, VLM_CANDIDATE_SELECTION_SYS
from .api_call_gemini import call_llm, call_vlm
from .parser import parse_answer, parse_answer_json, format_message
from .utils import compute_iou
from render_svg import SVGAgent


logging.basicConfig(
    filename='agent_svg.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class Agent:
    """
    Agent that manages the iterative optimization process using VLM and LLM with candidate selection.
    """
    
    def __init__(self, model_name,
                 target_image_path: str, canvas_w=600, canvas_h=600):
        self.model_name = model_name
        self.target_image_path = target_image_path
        self.memory = Memory()
        self.SVGrender = SVGAgent(canvas_height=canvas_h, canvas_width=canvas_w)
        
        # Target scene description (set during initialization)
        self.target_scene_description: Optional[Dict[str, Any]] = None
        
        # Track feedback for VLM
        self.last_failed_suggestions: Optional[str] = None
        self.current_iou: float = 0.0
        
        # Track optimization history
        self.optimization_history: List[Dict[str, Any]] = []

        self.LLM_grammar_sys = LLM_grammar_sys.format(canvas_width=canvas_w, canvas_height=canvas_h)
    
    def initialize(self, cus_instruct=None) -> str:
        logging.info("🎯 Step 1: Analyzing target image and generating initial program...")
        
        # Get target scene description from VLM
        self.target_scene_description = self._describe_scene_with_vlm(self.target_image_path, cus_instruct)
        logging.info(f"📋 Target scene description: {len(self.target_scene_description.get('primitives', []))} primitives")
        
        # Generate initial program using LLM
        initial_expression = self._generate_initial_program(self.target_scene_description)
        logging.info(f"🔧 Initial expression: {initial_expression}...")

        current_state = State(
            current_expression=initial_expression,
            scene_description=None,
            primitive_actions=None
        )
        # Update memory with new state
        self.memory.add_state(current_state)
        
        return initial_expression
    
    def optimization_step(self, current_image_path: str, current_expression, output_path, cus_instruct=None) -> Tuple[str, Dict[str, Any], bool]:
        logging.info("🔄 Optimization step starting...")
        # Calculate current IoU for comparison
        self.current_iou = compute_iou(current_image_path, self.target_image_path)
        logging.info(f"📊 Current IoU: {self.current_iou:.4f}")
        
        # Step 1: Generate modification actions (with feedback if available)
        logging.info("⚡ Step 1: Generating modification actions...")
        actions = self._generate_modification_actions_with_feedback(
            self.target_image_path, current_image_path, cus_instruct
        )
        
        # Step 2: Generate 5 candidate expressions
        logging.info("🎲 Step 2: Generating 5 candidate expressions...")
        candidates = self._generate_candidate_expressions(
            current_expression,
            actions
        )
        
        # Step 3: Evaluate candidates and select best one
        logging.info("🏆 Step 3: Evaluating candidates and selecting best...")
        best_candidate, candidate_ious, improvement_made = self._select_best_candidate(
            candidates, output_path
        )
        
        # Step 4: Update state and feedback based on results
        step_info = {
            "actions": actions,
            "candidates": candidates,
            "candidate_ious": candidate_ious,
            "best_candidate": best_candidate,
            "improvement_made": improvement_made,
            "current_iou": self.current_iou,
            "best_candidate_iou": max(candidate_ious) if candidate_ious else self.current_iou
        }
        
        if improvement_made:
            logging.info(f"✅ Improvement found! IoU: {self.current_iou:.4f} → {max(candidate_ious):.4f}")
            new_expression = best_candidate
            self.last_failed_suggestions = None  # Reset feedback
        else:
            logging.info(f"❌ No improvement. Keeping current expression. Best candidate IoU: {max(candidate_ious):.4f}")
            new_expression = current_expression
            self.last_failed_suggestions = actions  # Store for feedback
        
        # Update memory
        current_state = State(
            current_expression=new_expression,
            scene_description=None,
            primitive_actions=[actions]
        )
        self.memory.add_state(current_state)
        
        # Track optimization history
        self.optimization_history.append(step_info)
        
        logging.info(f"🔄 Optimization step complete.")
        return new_expression, step_info, improvement_made
    
    def optimization_step_vlm(self, current_image_path: str, current_expression, output_path, cus_instruct=None) -> Tuple[str, Dict[str, Any], bool]:
        logging.info("🔄 VLM-based optimization step starting...")
        
        # Step 1: Generate modification actions (with feedback if available)
        logging.info("⚡ Step 1: Generating modification actions...")
        actions = self._generate_modification_actions_with_feedback(
            self.target_image_path, current_image_path, cus_instruct
        )
        
        # Step 2: Generate 5 candidate expressions
        logging.info("🎲 Step 2: Generating 5 candidate expressions...")
        candidates = self._generate_candidate_expressions(
            current_expression,
            actions
        )
        
        # Step 3: Use VLM to select the best candidate
        logging.info("🧠 Step 3: Using VLM to select best candidate...")
        best_candidate, vlm_selection_info, improvement_made = self._select_best_candidate_vlm(
            candidates, output_path, current_image_path
        )
        
        # Step 4: Update state and feedback based on results
        step_info = {
            "actions": actions,
            "candidates": candidates,
            "vlm_selection_info": vlm_selection_info,
            "best_candidate": best_candidate,
            "improvement_made": improvement_made,
            "selection_method": "vlm"
        }
        
        if improvement_made:
            selected_candidate = vlm_selection_info["vlm_selection"]
            reasoning = vlm_selection_info["reasoning"]
            logging.info(f"✅ VLM found improvement! Selected: {selected_candidate}")
            logging.info(f"💭 Reasoning: {reasoning}...")
            new_expression = best_candidate
            self.last_failed_suggestions = None  # Reset feedback
        else:
            reasoning = vlm_selection_info["reasoning"]
            logging.info(f"❌ No improvement according to VLM. Keeping current expression.")
            logging.info(f"💭 Reasoning: {reasoning}...")
            new_expression = current_expression
            self.last_failed_suggestions = actions  # Store for feedback
        
        # Update memory
        new_state = State(
            current_expression=new_expression,
            scene_description=None,
            primitive_actions=[actions]
        )
        self.memory.add_state(new_state)
        
        # Track optimization history
        self.optimization_history.append(step_info)
        
        logging.info(f"🔄 VLM-based optimization step complete.")
        return new_expression, step_info, improvement_made
    
    def _describe_scene_with_vlm(self, image_path: str, cus_instruct=None) -> Dict[str, Any]:
        user_prompt = VLM_scene_description_prompt.format(customer_instruction=cus_instruct)
        # logging.info(user_prompt)
        messages = format_message(user_prompt=user_prompt)
        response = call_vlm(messages, image_paths=[image_path], model_name=self.model_name)
        logging.info(response)
        scene_description = parse_answer_json(response)
        return scene_description
    
    def _generate_initial_program(self, scene_description: Dict[str, Any]) -> str:
        """Generate initial tinySVG program using LLM."""
        user_prompt = LLM_program_synthesis_prompt.format(vlm_description=scene_description)
        sys_prompt = self.LLM_grammar_sys
        messages = format_message(sys_prompt, user_prompt)
        response = call_llm(messages, model_name=self.model_name)
        logging.info(response)
        init_program = parse_answer_json(response)
        return init_program
    
    def _generate_modification_actions_with_feedback(self, target_image_path: str, current_image_path: str, cus_instruct=None) -> str:
        """Generate modification actions using VLM, with feedback from previous failed attempts."""
        
        if self.last_failed_suggestions is None:
            # First time or previous suggestions worked
            user_prompt = VLM_edits_user_2
        else:
            # Previous suggestions didn't improve IoU, provide feedback
            user_prompt = VLM_edits_with_feedback_prompt.format(
                previous_suggestions=self.last_failed_suggestions
            )
        sys_prompt = VLM_edits_sys.format(customer_instruction=cus_instruct)
        logging.info(f"🔄 Providing feedback to VLM about failed suggestions")
        
        messages = format_message(sys_prompt=sys_prompt, user_prompt=user_prompt)
        response = call_vlm(messages, image_paths=[target_image_path, current_image_path], model_name=self.model_name)
        logging.info(response)
        return response
    
    def _generate_single_candidate(self, current_expression: List, actions: str, strategy: str) -> str:
        """Generate a single candidate expression using the specified strategy."""
        
        user_prompt = SINGLE_CANDIDATE_GENERATION_PROMPT.format(
            current_expression=current_expression,
            current_actions=actions,
            strategy=strategy
        )
        
        sys_prompt = self.LLM_grammar_sys
        messages = format_message(sys_prompt, user_prompt)
        response = call_llm(messages, model_name=self.model_name)
        logging.info(f"Single candidate ({strategy}) response: {response}")
        
        try:
            # Extract SVG code from response
            modified_svg = parse_answer_json(response)
            
            if modified_svg:
                return modified_svg
            else:
                logging.warning(f"Failed to generate valid SVG with {strategy} strategy, using current expression")
                return current_expression
                
        except Exception as e:
            logging.error(f"Error generating candidate with {strategy} strategy: {e}")
            return current_expression

    def _generate_candidate_expressions(self, current_expression: List, actions: str) -> List[str]:
        """Generate 5 candidate expressions using different strategies."""
        
        # Define 5 different strategies for diverse exploration
        strategies = [
            "conservative",  # Minimal changes
            "moderate",      # Balanced adjustments  
            "aggressive",    # Bold transformations
            "alternative",   # Different approach
            "focused"        # Target specific feedback intensively
        ]
        
        candidates = []
        
        for strategy in strategies:
            try:
                candidate = self._generate_single_candidate(current_expression, actions, strategy)
                candidates.append(candidate)
            except Exception as e:
                logging.error(f"Failed to generate {strategy} candidate: {e}")
                candidates.append(current_expression)  # Fallback
        
        # Ensure we have exactly 5 candidates
        while len(candidates) < 5:
            candidates.append(current_expression)
        
        return candidates[:5]
    
    def _select_best_candidate(self, candidates: List[List], output_path) -> Tuple[str, List[float], bool]:
        candidate_ious = []
        
        for i, candidate in enumerate(candidates):
            try:
                self.SVGrender.clear()
                self.SVGrender.create_from_dict(candidate)
                candidate_image_path = self.SVGrender.save_png(os.path.join(output_path, f"candidate_{i}.png"))
                # Calculate IoU with target
                iou = compute_iou(candidate_image_path, self.target_image_path)
                candidate_ious.append(iou)
                
                logging.info(f"📊 Candidate {i+1} IoU: {iou:.4f}")
                
            except Exception as e:
                logging.error(f"❌ Error evaluating candidate {i+1}: {e}")
                candidate_ious.append(0.0)  # Assign lowest score on error
        
        # Find best candidate
        best_idx = candidate_ious.index(max(candidate_ious))
        best_candidate = candidates[best_idx]
        best_iou = candidate_ious[best_idx]
        
        # Check if there's improvement
        improvement_made = best_iou > self.current_iou
        
        logging.info(f"🏆 Best candidate: {best_idx+1} with IoU {best_iou:.4f}")
        
        return best_candidate, candidate_ious, improvement_made

    def _select_best_candidate_vlm(self, candidates: List[List], output_path: str, current_image_path) -> Tuple[str, Dict[str, Any], bool]:
        candidate_image_paths = []
        
        # Generate images for all candidates
        for i, candidate in enumerate(candidates):
            try:
                self.SVGrender.clear()
                self.SVGrender.create_from_dict(candidate)
                candidate_image_path = self.SVGrender.save_png(os.path.join(output_path, f"candidate_{i}.png"))
                candidate_image_paths.append(candidate_image_path)
                logging.info(f"📷 Generated image for candidate {i+1}")
                
            except Exception as e:
                logging.error(f"❌ Error generating image for candidate {i+1}: {e}")
                candidate_image_paths.append(None)
        
        # Prepare images for VLM: target + current + valid candidates
        vlm_image_paths = [self.target_image_path, current_image_path]
        valid_candidate_indices = []
        
        for i, img_path in enumerate(candidate_image_paths):
            if img_path is not None:
                vlm_image_paths.append(img_path)
                valid_candidate_indices.append(i)
        
        # Call VLM for selection
        try:
            vlm_response = self._call_vlm_for_candidate_selection(vlm_image_paths, len(valid_candidate_indices))
            selection_result = parse_answer(vlm_response)
            
            logging.info(f"🧠 VLM selected: {selection_result}")
            logging.info(f"💭 VLM reasoning: {vlm_response}")
            
            # Determine the result based on VLM selection
            if selection_result == "current":
                # No improvement - keep current expression
                current_state = self.memory.get_current_state()
                best_candidate = current_state.current_expression
                improvement_made = False
            else:
                # VLM selected a candidate
                try:
                    candidate_idx = int(selection_result.replace("candidate_", "")) - 1
                    if 0 <= candidate_idx < len(valid_candidate_indices):
                        actual_candidate_idx = valid_candidate_indices[candidate_idx]
                        best_candidate = candidates[actual_candidate_idx]
                        improvement_made = True
                    else:
                        raise ValueError(f"Invalid candidate index: {candidate_idx}")
                except (ValueError, IndexError) as e:
                    logging.error(f"❌ Error parsing VLM selection: {e}. Defaulting to current.")
                    current_state = self.memory.get_current_state()
                    best_candidate = current_state.current_expression
                    improvement_made = False
            
            selection_info = {
                "vlm_selection": selection_result,
                "reasoning": vlm_response,
                "candidate_images": candidate_image_paths,
                "valid_candidates": len(valid_candidate_indices),
                "improvement_made": improvement_made
            }
            
            return best_candidate, selection_info, improvement_made
            
        except Exception as e:
            logging.error(f"❌ Error in VLM candidate selection: {e}")
            # Fallback to current expression
            current_state = self.memory.get_current_state()
            best_candidate = current_state.current_expression
            selection_info = {
                "vlm_selection": "error",
                "reasoning": f"Error in VLM selection: {e}",
                "candidate_images": candidate_image_paths,
                "valid_candidates": len(valid_candidate_indices),
                "improvement_made": False
            }
            return best_candidate, selection_info, False

    def _call_vlm_for_candidate_selection(self, image_paths: List[str], num_candidates: int) -> str:
        """Call VLM to select the best candidate."""
        
        user_prompt = VLM_CANDIDATE_SELECTION_PROMPT.format(
            num_candidates=num_candidates
        )
        
        messages = format_message(
            sys_prompt=VLM_CANDIDATE_SELECTION_SYS,
            user_prompt=user_prompt
        )
        
        response = call_vlm(messages, image_paths=image_paths, model_name=self.model_name)
        logging.info(f"VLM candidate selection response: {response}")
        return response
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of the current memory state."""
        return {
            "total_states": self.memory.size(),
            "current_expression": self.memory.get_current_state().current_expression if self.memory.size() > 0 else None,
            "target_primitives": len(self.target_scene_description.get('primitives', [])) if self.target_scene_description else 0,
            "current_iou": self.current_iou,
            "optimization_steps": len(self.optimization_history),
            "improvements_made": sum(1 for step in self.optimization_history if step.get("improvement_made", False)),
            "has_failed_suggestions": self.last_failed_suggestions is not None
        }
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Get the full optimization history."""
        return self.optimization_history
    
    def reset_feedback(self):
        self.last_failed_suggestions = None