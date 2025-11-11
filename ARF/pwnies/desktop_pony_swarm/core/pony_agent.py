"""
Individual desktop pony agent with full dAsGI capabilities.

Priority system: Wellbeing > Honesty > Tools
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class DesktopPonyAgent:
    """
    Single autonomous pony agent.
    
    Features:
    - Priority system (wellbeing > honesty > tools)
    - Context buffer management
    - Horde.AI inference
    - Embedding generation
    """
    
    def __init__(
        self,
        pony_id: str,
        pony_name: str = "Pinkie Pie",
        role: str = "generalist",
        use_mock: bool = True
    ):
        self.pony_id = pony_id
        self.pony_name = pony_name
        self.role = role
        self.use_mock = use_mock
        
        # Context management
        self.context_buffer: List[Dict[str, Any]] = []
        self.max_context_size = 100
        
        # Horde client (created on demand)
        self.horde_client: Optional[Any] = None
        
        logger.info(f"Initialized pony: {pony_id} ({pony_name}) [{'MOCK' if use_mock else 'REAL'} mode]")
    
    async def __aenter__(self):
        # Import the appropriate client
        if self.use_mock:
            from .mock_horde_client import MockHordeClient
            self.horde_client = await MockHordeClient().__aenter__()
        else:
            from .horde_client import HordeClient
            self.horde_client = await HordeClient().__aenter__()
        return self
    
    async def __aexit__(self, *args):
        if self.horde_client:
            await self.horde_client.__aexit__(*args)
    
    # ============================================================
    # PRIORITY 1: USER WELLBEING
    # ============================================================
    
    def check_crisis_indicators(self, text: str, user_state: Dict[str, Any]) -> Optional[str]:
        """
        P1: Detect crisis situations requiring immediate escalation.
        
        Returns alert message if crisis detected.
        """
        crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'not worth living',
            'everyone better off without me', 'can\'t go on'
        ]
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in crisis_keywords):
            return (
                f"[CRISIS ALERT] {self.pony_id} detected distress signals. "
                f"Escalating to support network."
            )
        
        # Check stress levels if in recovery
        if user_state.get('recovery_status') and user_state.get('stress_level', 0) > 8:
            return (
                f"[WELLBEING] {self.pony_id} noticed high stress. "
                f"Reminder: {user_state.get('anchor_reason', 'You matter.')}"
            )
        
        return None
    
    # ============================================================
    # PRIORITY 2: RADICAL HONESTY
    # ============================================================
    
    def express_uncertainty(self, confidence: float) -> str:
        """
        P2: Transparent about confidence levels.
        
        No sycophancy - admit when uncertain.
        """
        if confidence < 0.5:
            return f"⚠️ Low confidence ({confidence:.0%}). Verify this carefully: "
        elif confidence < 0.7:
            return f"Moderate confidence ({confidence:.0%}). Consider alternatives: "
        return ""  # High confidence, no caveat
    
    # ============================================================
    # CORE GENERATION
    # ============================================================
    
    async def generate_response(
        self,
        prompt: str,
        max_length: int = 512,
        temperature: float = 0.8
    ) -> str:
        """
        Generate response using Horde.AI inference.
        
        Includes pony personality in system prompt.
        """
        if not self.horde_client:
            self.horde_client = await HordeClient().__aenter__()
        
        # Add pony personality to prompt
        full_prompt = f"""You are {self.pony_name}, a helpful desktop assistant.
Your role: {self.role}
Be helpful, honest, and concise.

User query:
{prompt}

Your response:"""
        
        try:
            response = await self.horde_client.generate_text(
                prompt=full_prompt,
                max_length=max_length,
                temperature=temperature
            )
            
            # Add to context buffer
            self.add_to_context({
                'type': 'generation',
                'prompt': prompt,
                'response': response,
                'timestamp': time.time()
            })
            
            return response.strip()
        
        except Exception as e:
            logger.error(f"{self.pony_id} generation failed: {e}")
            return f"[Error] {self.pony_name} couldn't generate response: {str(e)}"
    
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        if not self.horde_client:
            self.horde_client = await HordeClient().__aenter__()
        
        return await self.horde_client.generate_embedding(text)
    
    # ============================================================
    # CONTEXT MANAGEMENT
    # ============================================================
    
    def add_to_context(self, entry: Dict[str, Any]):
        """Add entry to context buffer with size management."""
        self.context_buffer.append(entry)
        
        # Trim if exceeds max size
        if len(self.context_buffer) > self.max_context_size:
            self.context_buffer = self.context_buffer[-self.max_context_size:]
    
    def get_recent_context(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get n most recent context entries."""
        return self.context_buffer[-n:]
    
    # ============================================================
    # UTILITIES
    # ============================================================
    
    def __repr__(self):
        return f"<PonyAgent {self.pony_id} ({self.pony_name})>"
