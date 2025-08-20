from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class State:
    current_expression: str
    scene_description: Dict[str, Any]
    primitive_actions: Dict[str, List[str]] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"State(expression='{self.current_expression[:50]}...', primitives={len(self.scene_description.get('primitives', []))}, actions={len(self.primitive_actions)})"
    
    def __repr__(self) -> str:
        return self.__str__()


class Memory:
    def __init__(self):
        self.states: List[State] = []
    
    def add_state(self, state: State) -> None:
        """Add a new state to memory."""
        # Store a deep copy to prevent unintended modifications
        self.states.append(deepcopy(state))
    
    def get_current_state(self) -> Optional[State]:
        """Get the most recent state."""
        return self.states[-1] if self.states else None
    
    def get_history(self, length: int = None) -> List[State]:
        if length is None:
            return deepcopy(self.states)
        
        if length <= 0:
            return []

        start_idx = max(0, len(self.states) - length)
        return deepcopy(self.states[start_idx:])
    
    def get_state_at_index(self, index: int) -> Optional[State]:
        """Get state at specific index (supports negative indexing)."""
        try:
            return deepcopy(self.states[index])
        except IndexError:
            return None
    
    def size(self) -> int:
        """Get the number of states in memory."""
        return len(self.states)
    
    def clear(self) -> None:
        """Clear all states from memory."""
        self.states.clear()
    
    def get_expression_history(self, length: int = None) -> List[str]:
        """Get history of expressions only."""
        history = self.get_history(length)
        return [state.current_expression for state in history]
    
    def get_actions_history(self, length: int = None) -> List[Dict[str, List[str]]]:
        """Get history of primitive actions only."""
        history = self.get_history(length)
        return [state.primitive_actions for state in history]
    
    def format_history_for_prompt(self, length: int = None) -> List[Dict[str, Any]]:
        """
        Format history for use in LLM prompts.
        
        Returns:
            List of dicts with 'expression', 'actions', and 'result' keys
        """
        history = self.get_history(length)
        formatted = []
        
        for i in range(len(history) - 1):
            current_state = history[i]
            next_state = history[i + 1]
            
            formatted.append({
                "expression": current_state.current_expression,
                "actions": current_state.primitive_actions,
                "result": next_state.current_expression
            })
        
        return formatted
    
    def __len__(self) -> int:
        return len(self.states)
    
    def __str__(self) -> str:
        return f"Memory(states={len(self.states)})"
    
    def __repr__(self) -> str:
        return self.__str__()
