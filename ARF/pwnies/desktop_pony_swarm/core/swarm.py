"""
Recursive Self-Aggregation (RSA) orchestrator for pony swarm.

Implements Algorithm 1 from paper (Appendix B).
Research: RSA achieves 15-30% improvement over single-agent baselines.

Phase 4.1 Optimizations:
- Parallel generation requests (async/await)
- Adaptive parameter selection
- Optimized embedding computation
"""

import asyncio
import random
import logging
import time
from typing import List, Dict, Any, Optional
from .pony_agent import DesktopPonyAgent
from .embedding import SwarmEmbeddingManager
from .adaptive_params import AdaptiveParameterSelector, RSAParams

logger = logging.getLogger(__name__)

class PonySwarm:
    """
    RSA-based pony swarm coordinator.
    
    Parameters match paper recommendations:
    - N=4 ponies (population size)
    - K=2 aggregation size
    - T=3 iterations
    """
    
    def __init__(
        self,
        num_ponies: int = 4,
        pony_names: Optional[List[str]] = None,
        use_mock: bool = True,
        use_adaptive_params: bool = True
    ):
        self.num_ponies = num_ponies
        self.use_mock = use_mock
        self.use_adaptive_params = use_adaptive_params

        # Default pony names
        if not pony_names:
            pony_names = ["Pinkie Pie", "Rainbow Dash", "Twilight Sparkle", "Fluttershy"]

        # Initialize ponies
        self.ponies: List[DesktopPonyAgent] = []
        for i in range(num_ponies):
            name = pony_names[i] if i < len(pony_names) else f"Pony {i+1}"
            pony = DesktopPonyAgent(
                pony_id=f"pony_{i}",
                pony_name=name,
                role="generalist",
                use_mock=use_mock
            )
            self.ponies.append(pony)

        # Embedding manager
        self.embedding_manager = SwarmEmbeddingManager()

        # Adaptive parameter selector
        self.param_selector = AdaptiveParameterSelector() if use_adaptive_params else None

        # Performance metrics
        self.metrics: Dict[str, Any] = {
            'total_queries': 0,
            'avg_diversity': [],
            'iteration_times': [],
            'param_selections': []
        }

        mode = "MOCK" if use_mock else "REAL"
        adaptive = " + ADAPTIVE" if use_adaptive_params else ""
        logger.info(f"Initialized swarm with {num_ponies} ponies [{mode}{adaptive} inference]")
    
    async def __aenter__(self):
        """Async context manager entry."""
        for pony in self.ponies:
            await pony.__aenter__()
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit."""
        for pony in self.ponies:
            await pony.__aexit__(*args)
    
    # ============================================================
    # RSA CORE ALGORITHM
    # ============================================================
    
    async def recursive_self_aggregation(
        self,
        query: str,
        K: Optional[int] = None,
        T: Optional[int] = None,
        user_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recursive Self-Aggregation (RSA) - Algorithm 1 from paper.

        Args:
            query: User question/task
            K: Aggregation size (None for adaptive selection)
            T: Number of refinement iterations (None for adaptive selection)
            user_state: User context for wellbeing checks

        Returns:
            Dict with final response, metrics, and iteration history
        """
        N = self.num_ponies
        user_state = user_state or {}

        # Adaptive parameter selection
        if self.use_adaptive_params and (K is None or T is None):
            params = self.param_selector.select_parameters(query)
            K = K or params.K
            T = T or params.T
            self.metrics['param_selections'].append({
                'query': query[:50],
                'params': {'N': N, 'K': K, 'T': T}
            })
        else:
            # Use defaults if not specified
            K = K or 2
            T = T or 3

        start_time = time.time()
        self.metrics['total_queries'] += 1

        logger.info(f"Starting RSA: query='{query[:50]}...', N={N}, K={K}, T={T}")
        
        # Priority 1: Check for crisis indicators
        crisis_alert = self._check_all_ponies_for_crisis(query, user_state)
        if crisis_alert:
            return {
                'response': crisis_alert,
                'is_crisis': True,
                'iterations': []
            }
        
        # ============================================================
        # STEP 1: INITIALIZATION - Generate initial population
        # ============================================================

        logger.info(f"Step 1: Generating initial population ({N} responses)")

        population = []

        # OPTIMIZATION: Generate responses and embeddings in parallel
        response_tasks = [pony.generate_response(query) for pony in self.ponies]
        responses = await asyncio.gather(*response_tasks)

        # OPTIMIZATION: Generate all embeddings in parallel
        embedding_tasks = [
            self.ponies[i].generate_embedding(responses[i])
            for i in range(len(responses))
        ]
        embeddings = await asyncio.gather(*embedding_tasks)

        for i, (response, embedding) in enumerate(zip(responses, embeddings)):
            population.append(response)

            # Store embedding
            self.embedding_manager.add_pony_response(
                pony_id=self.ponies[i].pony_id,
                iteration=1,
                response=response,
                vector=embedding,
                metadata={'timestamp': time.time()}
            )
        
        # Aggregate to community level
        self.embedding_manager.aggregate_to_community(
            iteration=1,
            pony_ids=[p.pony_id for p in self.ponies]
        )
        
        iteration_history = [{
            'iteration': 1,
            'population': population.copy(),
            'diversity': self.embedding_manager.get_diversity_metric(1)
        }]
        
        # ============================================================
        # STEPS 2-T: RECURSIVE AGGREGATION
        # ============================================================
        
        for t in range(2, T + 1):
            iter_start = time.time()
            logger.info(f"Step {t}: Recursive aggregation (K={K})")

            # OPTIMIZATION: Generate all aggregation prompts first
            aggregation_data = []
            for i in range(N):
                # Subsampling: Sample K indices WITHOUT replacement
                subset_indices = random.sample(range(N), K)
                subset = [population[idx] for idx in subset_indices]

                # Build aggregation prompt
                agg_prompt = self._build_aggregation_prompt(query, subset, K)

                aggregation_data.append({
                    'pony_index': i,
                    'prompt': agg_prompt,
                    'subset_indices': subset_indices
                })

            # OPTIMIZATION: Generate all improved responses in parallel
            response_tasks = [
                self.ponies[data['pony_index']].generate_response(data['prompt'])
                for data in aggregation_data
            ]
            new_population = await asyncio.gather(*response_tasks)

            # OPTIMIZATION: Generate all embeddings in parallel
            embedding_tasks = [
                self.ponies[i].generate_embedding(new_population[i])
                for i in range(len(new_population))
            ]
            embeddings = await asyncio.gather(*embedding_tasks)

            # Store all embeddings
            for i, (improved, embedding) in enumerate(zip(new_population, embeddings)):
                self.embedding_manager.add_pony_response(
                    pony_id=self.ponies[i].pony_id,
                    iteration=t,
                    response=improved,
                    vector=embedding,
                    metadata={
                        'timestamp': time.time(),
                        'aggregated_from': aggregation_data[i]['subset_indices']
                    }
                )
            
            # Update population
            population = new_population
            
            # Aggregate to community
            self.embedding_manager.aggregate_to_community(
                iteration=t,
                pony_ids=[p.pony_id for p in self.ponies]
            )
            
            # Track metrics
            diversity = self.embedding_manager.get_diversity_metric(t)
            iter_time = time.time() - iter_start
            
            iteration_history.append({
                'iteration': t,
                'population': population.copy(),
                'diversity': diversity
            })
            
            self.metrics['avg_diversity'].append(diversity)
            self.metrics['iteration_times'].append(iter_time)
            
            logger.info(f"  Iteration {t} complete: diversity={diversity:.4f}, time={iter_time:.2f}s")
        
        # ============================================================
        # STEP 4: TERMINATION - Select final response
        # ============================================================
        
        # Random sample from final population (as recommended in paper)
        final_response = random.choice(population)
        
        total_time = time.time() - start_time
        
        result = {
            'response': final_response,
            'is_crisis': False,
            'iterations': iteration_history,
            'final_population': population,
            'metrics': {
                'total_time': total_time,
                'avg_diversity': sum(self.metrics['avg_diversity']) / len(self.metrics['avg_diversity']) if self.metrics['avg_diversity'] else 0,
                'total_generations': N * T
            }
        }
        
        logger.info(f"RSA complete: time={total_time:.2f}s, final_diversity={iteration_history[-1]['diversity']:.4f}")
        
        return result
    
    # ============================================================
    # AGGREGATION PROMPTS
    # ============================================================
    
    def _build_aggregation_prompt(
        self,
        query: str,
        candidates: List[str],
        K: int
    ) -> str:
        """
        Build aggregation prompt following paper's template (Appendix F).
        
        Different prompts for K=1 (self-refinement) vs K>1 (aggregation).
        """
        if K == 1:
            # Self-refinement prompt
            return f"""You are given a problem and a candidate solution.
The candidate may be incomplete or contain errors.
Refine this solution and produce an improved, higher-quality response.
If it is entirely wrong, attempt a new strategy.

Problem:
{query}

Candidate solution:
{candidates[0]}

Now refine the candidate into an improved solution with clear reasoning:"""
        
        else:
            # Multi-candidate aggregation prompt
            candidates_text = "\n\n".join([
                f"---- Solution {i+1} ----\n{cand}"
                for i, cand in enumerate(candidates)
            ])
            
            return f"""You are given a problem and several candidate solutions.
Some candidates may be incorrect or contain errors.
Aggregate the useful ideas and produce a single, high-quality solution.
Reason carefully; if candidates disagree, choose the correct path.
If all are incorrect, attempt a different strategy.

Problem:
{query}

Candidate solutions:
{candidates_text}

Now write a single improved solution with clear reasoning:"""
    
    def _check_all_ponies_for_crisis(
        self,
        query: str,
        user_state: Dict[str, Any]
    ) -> Optional[str]:
        """
        Priority 1: Check all ponies for crisis indicators.
        
        Returns alert if any pony detects crisis.
        """
        for pony in self.ponies:
            alert = pony.check_crisis_indicators(query, user_state)
            if alert:
                return alert
        return None
    
    # ============================================================
    # ALTERNATIVE: SINGLE-STEP AGGREGATION
    # ============================================================
    
    async def single_step_aggregation(
        self,
        query: str,
        K: int = 4
    ) -> Dict[str, Any]:
        """
        Single-step aggregation (RSA with T=1).
        
        Equivalent to Best-of-N with aggregation instead of selection.
        Useful for quick queries without full RSA overhead.
        """
        logger.info(f"Single-step aggregation: K={K}")
        
        # Generate K responses
        tasks = [self.ponies[i % self.num_ponies].generate_response(query) for i in range(K)]
        candidates = await asyncio.gather(*tasks)
        
        # Aggregate using first pony
        agg_prompt = self._build_aggregation_prompt(query, candidates, K)
        final_response = await self.ponies[0].generate_response(agg_prompt)
        
        return {
            'response': final_response,
            'is_crisis': False,
            'candidates': candidates,
            'method': 'single_step_aggregation'
        }