"""
LLM Committee-based validation for knowledge triple extraction.

Implements a 5-agent committee that validates each extracted triple through
consensus voting, reducing false positives and hallucinations.
"""

import asyncio
import logging
import time
from typing import Tuple, List, Optional, Dict, Any

from .models import ValidationResult, Vote, VoteDecision, ConsensusMetrics
from .agent_pool import ValidatorPool

logger = logging.getLogger(__name__)


class TripleValidationCommittee:
    """
    Committee-based validation for knowledge triples.

    Uses a committee of 5 LLM validators to achieve consensus on triple validity.
    Requires ≥3/5 votes to accept a triple.
    """

    # Known ontology predicates (synchronized with conversation_memory.py)
    KNOWN_PREDICATES = {
        'is_a', 'part_of', 'related_to', 'has_property',
        'improves_upon', 'capable_of', 'trained_on',
        'evaluated_on', 'stated'
    }

    def __init__(
        self,
        validator_pool: Optional[ValidatorPool] = None,
        committee_size: int = 5,
        consensus_threshold: int = 3,
        use_mock: bool = True
    ):
        """
        Initialize committee validation system.

        Args:
            validator_pool: Pool of validators to select from (creates default if None)
            committee_size: Number of validators per committee (default: 5)
            consensus_threshold: Minimum votes needed to accept (default: 3)
            use_mock: Use mock LLM for testing (default: True)
        """
        self.committee_size = committee_size
        self.consensus_threshold = consensus_threshold

        # Initialize validator pool
        if validator_pool is None:
            self.validator_pool = ValidatorPool(
                pool_size=max(10, committee_size * 2),
                use_mock=use_mock
            )
        else:
            self.validator_pool = validator_pool

        # Metrics tracking
        self.metrics = ConsensusMetrics()

        logger.info(
            f"Initialized committee validation: {committee_size} validators, "
            f"{consensus_threshold}/{committee_size} consensus required"
        )

    async def validate(
        self,
        candidate: Tuple[str, str, str],
        context: str,
        include_reasoning: bool = False
    ) -> ValidationResult:
        """
        Validate a candidate triple using committee consensus.

        Args:
            candidate: Triple tuple (subject, predicate, object)
            context: Contextual text from which triple was extracted
            include_reasoning: Include validator reasoning in result

        Returns:
            ValidationResult with consensus decision and confidence
        """
        start_time = time.time()

        subject, predicate, object_ = candidate

        # Pre-validation: Check basic ontology rules
        basic_valid, basic_reason = self._basic_validation(candidate)
        if not basic_valid:
            logger.debug(f"Triple failed basic validation: {basic_reason}")
            # Return early rejection without calling committee
            return ValidationResult(
                accepted=False,
                confidence=0.0,
                votes=[],
                consensus_ratio=0.0,
                total_votes=0,
                yes_votes=0,
                no_votes=1,
                abstain_votes=0,
                duration_ms=0.0
            )

        # Select committee members
        validators = self.validator_pool.select_validators(self.committee_size)
        logger.debug(f"Selected {len(validators)} validators for committee")

        # Create validation prompt
        prompt = self._create_validation_prompt(candidate, context)

        # Collect votes in parallel
        vote_tasks = [validator.judge(prompt) for validator in validators]
        votes: List[Vote] = await asyncio.gather(*vote_tasks)

        # Calculate consensus
        result = self._calculate_consensus(votes)

        # Add duration
        duration_ms = (time.time() - start_time) * 1000
        result.duration_ms = duration_ms

        # Update metrics
        self.metrics.update(result)

        # Log result
        logger.info(
            f"Committee validation: {result.yes_votes}/{result.total_votes} YES votes, "
            f"confidence={result.confidence:.2f}, accepted={result.accepted}, "
            f"duration={duration_ms:.0f}ms"
        )

        # Optionally filter out reasoning
        if not include_reasoning:
            for vote in result.votes:
                vote.reasoning = None

        return result

    def _basic_validation(self, triple: Tuple[str, str, str]) -> Tuple[bool, Optional[str]]:
        """
        Perform basic validation checks before committee review.

        Args:
            triple: Triple tuple (subject, predicate, object)

        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        subject, predicate, object_ = triple

        # Check for empty components
        if not subject or not subject.strip():
            return False, "Empty subject"

        if not object_ or not object_.strip():
            return False, "Empty object"

        # Check predicate is known
        if predicate not in self.KNOWN_PREDICATES:
            return False, f"Unknown predicate: {predicate}"

        return True, None

    def _create_validation_prompt(
        self,
        candidate: Tuple[str, str, str],
        context: str
    ) -> str:
        """
        Create validation prompt for validators.

        Args:
            candidate: Triple tuple (subject, predicate, object)
            context: Contextual text

        Returns:
            Validation prompt string
        """
        subject, predicate, object_ = candidate

        prompt = f"""You are validating a knowledge triple extracted from text.

**Context:**
{context}

**Proposed Triple:**
Subject: {subject}
Predicate: {predicate}
Object: {object_}

**Validation Criteria:**

1. **Factual Correctness**: Is the triple factually correct given the context?
   - The relationship must be explicitly stated or strongly implied in the context
   - Do not accept triples based on external knowledge not present in the context

2. **Ontology Compliance**: Does the triple follow ontology rules?
   - Predicate '{predicate}' must be used appropriately
   - Subject and object must be well-formed (no empty strings)

3. **No Hallucination**: Is this triple actually supported by the text?
   - Reject if the triple makes unsupported claims
   - Reject if the relationship is invented or assumed

**Your Task:**
Evaluate the triple and respond in this format:

Vote: YES or NO
Confidence: [0.0-1.0]
Reasoning: [Brief explanation of your decision]

**Guidelines:**
- Vote YES only if all three criteria are satisfied
- Vote NO if any criterion fails
- Confidence should reflect your certainty (0.0 = very uncertain, 1.0 = very certain)
- Be conservative: when in doubt, vote NO
"""
        return prompt

    def _calculate_consensus(self, votes: List[Vote]) -> ValidationResult:
        """
        Calculate consensus from committee votes.

        Args:
            votes: List of validator votes

        Returns:
            ValidationResult with consensus decision
        """
        total_votes = len(votes)
        yes_votes = sum(1 for v in votes if v.decision == VoteDecision.YES)
        no_votes = sum(1 for v in votes if v.decision == VoteDecision.NO)
        abstain_votes = sum(1 for v in votes if v.decision == VoteDecision.ABSTAIN)

        # Calculate consensus
        accepted = yes_votes >= self.consensus_threshold

        # Calculate confidence (mean of YES votes, or 0 if rejected)
        yes_vote_list = [v for v in votes if v.decision == VoteDecision.YES]
        if yes_vote_list and accepted:
            confidence = sum(v.confidence for v in yes_vote_list) / len(yes_vote_list)
        else:
            confidence = 0.0

        # Calculate consensus ratio
        if yes_votes + no_votes > 0:
            consensus_ratio = max(yes_votes, no_votes) / (yes_votes + no_votes)
        else:
            consensus_ratio = 0.0

        return ValidationResult(
            accepted=accepted,
            confidence=confidence,
            votes=votes,
            consensus_ratio=consensus_ratio,
            total_votes=total_votes,
            yes_votes=yes_votes,
            no_votes=no_votes,
            abstain_votes=abstain_votes
        )

    async def validate_batch(
        self,
        candidates: List[Tuple[Tuple[str, str, str], str]],
        include_reasoning: bool = False
    ) -> List[ValidationResult]:
        """
        Validate a batch of triples in parallel.

        Args:
            candidates: List of (triple, context) tuples
            include_reasoning: Include validator reasoning in results

        Returns:
            List of ValidationResults
        """
        tasks = [
            self.validate(triple, context, include_reasoning)
            for triple, context in candidates
        ]
        return await asyncio.gather(*tasks)

    def get_metrics(self) -> ConsensusMetrics:
        """Get current validation metrics."""
        return self.metrics

    def reset_metrics(self):
        """Reset validation metrics."""
        self.metrics = ConsensusMetrics()
        logger.info("Reset committee validation metrics")

    async def close(self):
        """Clean up resources."""
        await self.validator_pool.close()
        logger.info("Closed committee validation system")
