"""
Validator agent pool for committee-based validation.

Manages a pool of LLM validators that can be randomly selected for
validation tasks. Supports both mock and real LLM backends.
"""

import asyncio
import logging
import random
import re
from typing import List, Optional
from abc import ABC, abstractmethod

from .models import Vote, VoteDecision, ValidatorConfig

logger = logging.getLogger(__name__)


class ValidatorBackend(ABC):
    """Abstract base class for validator LLM backends."""

    @abstractmethod
    async def generate(self, prompt: str, config: ValidatorConfig) -> str:
        """Generate a response from the LLM."""
        pass


class MockValidatorBackend(ValidatorBackend):
    """Mock validator backend for testing."""

    def __init__(self, acceptance_rate: float = 0.8, response_time_ms: float = 100):
        """
        Initialize mock backend.

        Args:
            acceptance_rate: Probability of accepting a triple (0.0-1.0)
            response_time_ms: Simulated response time in milliseconds
        """
        self.acceptance_rate = acceptance_rate
        self.response_time_ms = response_time_ms

    async def generate(self, prompt: str, config: ValidatorConfig) -> str:
        """Generate a mock response."""
        # Simulate network delay
        await asyncio.sleep(self.response_time_ms / 1000.0)

        # Randomly decide based on acceptance rate
        accept = random.random() < self.acceptance_rate
        confidence = random.uniform(0.7, 0.95) if accept else random.uniform(0.6, 0.85)

        vote = "YES" if accept else "NO"
        reasoning = (
            "The triple appears factually correct and follows ontology rules."
            if accept
            else "The triple may be a hallucination or violates ontology constraints."
        )

        return f"""Vote: {vote}
Confidence: {confidence:.2f}
Reasoning: {reasoning}"""


class AnthropicValidatorBackend(ValidatorBackend):
    """Anthropic Claude validator backend."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Anthropic backend."""
        self.api_key = api_key
        # Import is deferred to avoid dependency issues
        self._client = None

    async def _get_client(self):
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                logger.error("anthropic package not installed. Run: pip install anthropic")
                raise

        return self._client

    async def generate(self, prompt: str, config: ValidatorConfig) -> str:
        """Generate response using Anthropic Claude."""
        client = await self._get_client()

        try:
            message = await client.messages.create(
                model=config.model_name,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class Validator:
    """Individual validator agent."""

    def __init__(self, config: ValidatorConfig, backend: ValidatorBackend):
        """
        Initialize validator.

        Args:
            config: Validator configuration
            backend: LLM backend to use
        """
        self.config = config
        self.backend = backend

    async def judge(self, prompt: str) -> Vote:
        """
        Judge a triple based on the prompt.

        Args:
            prompt: Validation prompt

        Returns:
            Vote object with decision and confidence
        """
        try:
            # Generate response with timeout
            response = await asyncio.wait_for(
                self.backend.generate(prompt, self.config),
                timeout=self.config.timeout_seconds
            )

            # Parse response
            decision, confidence, reasoning = self._parse_response(response)

            return Vote(
                validator_id=self.config.validator_id,
                decision=decision,
                confidence=confidence,
                reasoning=reasoning
            )

        except asyncio.TimeoutError:
            logger.warning(f"Validator {self.config.validator_id} timed out")
            return Vote(
                validator_id=self.config.validator_id,
                decision=VoteDecision.ABSTAIN,
                confidence=0.0,
                reasoning="Validation timed out"
            )
        except Exception as e:
            logger.error(f"Validator {self.config.validator_id} error: {e}")
            return Vote(
                validator_id=self.config.validator_id,
                decision=VoteDecision.ABSTAIN,
                confidence=0.0,
                reasoning=f"Error: {str(e)}"
            )

    def _parse_response(self, response: str) -> tuple[VoteDecision, float, str]:
        """
        Parse validator response.

        Expected format:
            Vote: YES/NO
            Confidence: 0.0-1.0
            Reasoning: explanation

        Returns:
            Tuple of (decision, confidence, reasoning)
        """
        # Extract vote decision
        vote_match = re.search(r'Vote:\s*(YES|NO|ABSTAIN)', response, re.IGNORECASE)
        if vote_match:
            decision = VoteDecision(vote_match.group(1).upper())
        else:
            # Try to infer from content
            response_lower = response.lower()
            if 'yes' in response_lower or 'accept' in response_lower or 'valid' in response_lower:
                decision = VoteDecision.YES
            elif 'no' in response_lower or 'reject' in response_lower or 'invalid' in response_lower:
                decision = VoteDecision.NO
            else:
                decision = VoteDecision.ABSTAIN

        # Extract confidence
        conf_match = re.search(r'Confidence:\s*(0?\.\d+|1\.0|1)', response)
        if conf_match:
            confidence = float(conf_match.group(1))
        else:
            # Default confidence based on decision
            confidence = 0.7 if decision != VoteDecision.ABSTAIN else 0.0

        # Extract reasoning
        reasoning_match = re.search(r'Reasoning:\s*(.+?)(?:\n\n|$)', response, re.DOTALL)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else response

        return decision, confidence, reasoning


class ValidatorPool:
    """Pool of validator agents for committee validation."""

    def __init__(
        self,
        pool_size: int = 10,
        use_mock: bool = True,
        backend: Optional[ValidatorBackend] = None
    ):
        """
        Initialize validator pool.

        Args:
            pool_size: Number of validators in the pool
            use_mock: Use mock backend for testing
            backend: Custom backend (overrides use_mock)
        """
        self.pool_size = pool_size
        self.validators: List[Validator] = []

        # Create backend
        if backend is not None:
            self.backend = backend
        elif use_mock:
            self.backend = MockValidatorBackend()
        else:
            self.backend = AnthropicValidatorBackend()

        # Initialize validator pool
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the validator pool."""
        for i in range(self.pool_size):
            config = ValidatorConfig(
                validator_id=f"validator-{i:02d}",
                use_mock=isinstance(self.backend, MockValidatorBackend)
            )
            validator = Validator(config, self.backend)
            self.validators.append(validator)

        logger.info(f"Initialized validator pool with {self.pool_size} validators")

    def select_validators(self, count: int = 5) -> List[Validator]:
        """
        Randomly select validators from the pool.

        Args:
            count: Number of validators to select (default: 5)

        Returns:
            List of selected validators
        """
        if count > self.pool_size:
            logger.warning(
                f"Requested {count} validators but pool only has {self.pool_size}. "
                f"Using all available validators."
            )
            count = self.pool_size

        return random.sample(self.validators, count)

    def get_validator(self, validator_id: str) -> Optional[Validator]:
        """Get a specific validator by ID."""
        for validator in self.validators:
            if validator.config.validator_id == validator_id:
                return validator
        return None

    async def close(self):
        """Clean up resources."""
        # Close backend if it has cleanup
        if hasattr(self.backend, 'close'):
            await self.backend.close()
