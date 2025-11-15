"""
Parameter Sweep for RSA Algorithm Optimization.

Performs grid search over N, K, T parameters to find optimal configurations
for different query complexities.

Phase 4.1: Performance Optimization
"""

import asyncio
import time
import logging
import json
import itertools
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.benchmark_suite import BenchmarkSuite, BenchmarkQuery, BenchmarkResult

logger = logging.getLogger(__name__)


@dataclass
class ParameterConfig:
    """Single parameter configuration to test."""
    N: int  # Number of ponies
    K: int  # Aggregation size
    T: int  # Number of iterations

    def __str__(self):
        return f"N={self.N},K={self.K},T={self.T}"

    def is_valid(self) -> bool:
        """Check if parameter combination is valid."""
        # K must be <= N
        if self.K > self.N:
            return False
        # All must be positive
        if self.N < 1 or self.K < 1 or self.T < 1:
            return False
        return True


@dataclass
class SweepResult:
    """Results from testing a single parameter configuration."""
    config: ParameterConfig
    complexity: str
    avg_latency: float
    avg_diversity: float
    avg_quality: float
    total_time: float
    num_queries: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'N': self.config.N,
            'K': self.config.K,
            'T': self.config.T,
            'complexity': self.complexity,
            'avg_latency': self.avg_latency,
            'avg_diversity': self.avg_diversity,
            'avg_quality': self.avg_quality,
            'total_time': self.total_time,
            'num_queries': self.num_queries
        }


class ParameterSweep:
    """
    Grid search over RSA parameters to find optimal configurations.
    """

    def __init__(self, use_mock: bool = True):
        """
        Initialize parameter sweep.

        Args:
            use_mock: If True, use mock inference for fast testing
        """
        self.use_mock = use_mock
        self.suite = BenchmarkSuite(use_mock=use_mock)
        self.results: List[SweepResult] = []
        logger.info(f"Initialized ParameterSweep [{'MOCK' if use_mock else 'REAL'} mode]")

    def generate_configs(
        self,
        N_values: List[int] = None,
        K_values: List[int] = None,
        T_values: List[int] = None
    ) -> List[ParameterConfig]:
        """
        Generate all valid parameter combinations.

        Default values from roadmap:
        - N ∈ {2,4,6,8}
        - K ∈ {1,2,3}
        - T ∈ {1,2,3,4}

        Args:
            N_values: List of N values to test (default: [2,4,6,8])
            K_values: List of K values to test (default: [1,2,3])
            T_values: List of T values to test (default: [1,2,3,4])

        Returns:
            List of valid ParameterConfig objects
        """
        if N_values is None:
            N_values = [2, 4, 6, 8]
        if K_values is None:
            K_values = [1, 2, 3]
        if T_values is None:
            T_values = [1, 2, 3, 4]

        # Generate all combinations
        all_combos = itertools.product(N_values, K_values, T_values)

        # Filter to valid configurations
        configs = []
        for N, K, T in all_combos:
            config = ParameterConfig(N=N, K=K, T=T)
            if config.is_valid():
                configs.append(config)

        logger.info(f"Generated {len(configs)} valid parameter configurations")
        return configs

    async def test_config(
        self,
        config: ParameterConfig,
        queries: List[BenchmarkQuery]
    ) -> SweepResult:
        """
        Test a single parameter configuration on a set of queries.

        Args:
            config: ParameterConfig to test
            queries: List of benchmark queries to run

        Returns:
            SweepResult with aggregate metrics
        """
        logger.info(f"Testing config: {config}")

        results = []
        start_time = time.time()

        async with self.suite.__class__(use_mock=self.use_mock) as suite:
            for query in queries:
                result = await suite.run_single_benchmark(
                    query,
                    N=config.N,
                    K=config.K,
                    T=config.T
                )
                results.append(result)

        total_time = time.time() - start_time

        # Compute aggregate metrics
        avg_latency = sum(r.latency for r in results) / len(results)
        avg_diversity = sum(r.diversity for r in results) / len(results)

        # Quality score based on keyword matching
        quality_scores = [
            r.quality_score(q.expected_keywords)
            for r, q in zip(results, queries)
        ]
        avg_quality = sum(quality_scores) / len(quality_scores)

        sweep_result = SweepResult(
            config=config,
            complexity=queries[0].complexity if queries else "unknown",
            avg_latency=avg_latency,
            avg_diversity=avg_diversity,
            avg_quality=avg_quality,
            total_time=total_time,
            num_queries=len(results)
        )

        self.results.append(sweep_result)

        logger.info(
            f"  Config {config}: "
            f"latency={avg_latency:.2f}s, "
            f"diversity={avg_diversity:.4f}, "
            f"quality={avg_quality:.2%}"
        )

        return sweep_result

    async def run_sweep(
        self,
        complexity: str = "micro",
        N_values: List[int] = None,
        K_values: List[int] = None,
        T_values: List[int] = None,
        max_configs: int = None
    ) -> List[SweepResult]:
        """
        Run full parameter sweep for a specific complexity level.

        Args:
            complexity: "micro", "medium", or "large"
            N_values, K_values, T_values: Parameter ranges to test
            max_configs: Maximum number of configs to test (for quick testing)

        Returns:
            List of SweepResult objects
        """
        logger.info(f"Starting parameter sweep for {complexity} queries")

        # Get queries for this complexity
        queries = self.suite.get_queries_by_complexity(complexity)

        # Generate configurations
        configs = self.generate_configs(N_values, K_values, T_values)

        # Limit if requested
        if max_configs and len(configs) > max_configs:
            logger.info(f"Limiting to {max_configs} configurations")
            configs = configs[:max_configs]

        # Test each configuration
        results = []
        for i, config in enumerate(configs, 1):
            logger.info(f"Progress: {i}/{len(configs)}")
            result = await self.test_config(config, queries)
            results.append(result)

        return results

    def find_pareto_frontier(
        self,
        results: List[SweepResult] = None
    ) -> List[SweepResult]:
        """
        Find Pareto-optimal configurations (best trade-off between latency and quality).

        A configuration is Pareto-optimal if no other configuration is better
        in both latency (lower is better) and quality (higher is better).

        Args:
            results: List of SweepResult to analyze (default: self.results)

        Returns:
            List of Pareto-optimal configurations
        """
        if results is None:
            results = self.results

        pareto_frontier = []

        for candidate in results:
            is_dominated = False

            # Check if any other config dominates this one
            for other in results:
                if other == candidate:
                    continue

                # Other dominates if it's better in latency AND quality
                if (other.avg_latency <= candidate.avg_latency and
                    other.avg_quality >= candidate.avg_quality and
                    (other.avg_latency < candidate.avg_latency or
                     other.avg_quality > candidate.avg_quality)):
                    is_dominated = True
                    break

            if not is_dominated:
                pareto_frontier.append(candidate)

        logger.info(f"Found {len(pareto_frontier)} Pareto-optimal configurations")
        return pareto_frontier

    def find_best_config(
        self,
        metric: str = "latency",
        results: List[SweepResult] = None
    ) -> SweepResult:
        """
        Find best configuration by a specific metric.

        Args:
            metric: "latency", "diversity", or "quality"
            results: List of SweepResult to analyze (default: self.results)

        Returns:
            Best SweepResult by the specified metric
        """
        if results is None:
            results = self.results

        if not results:
            raise ValueError("No results to analyze")

        if metric == "latency":
            return min(results, key=lambda r: r.avg_latency)
        elif metric == "diversity":
            return max(results, key=lambda r: r.avg_diversity)
        elif metric == "quality":
            return max(results, key=lambda r: r.avg_quality)
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def save_results(self, filename: str = "sweep_results.json"):
        """Save sweep results to JSON file."""
        output_path = Path(__file__).parent / filename

        data = {
            'timestamp': time.time(),
            'mode': 'mock' if self.use_mock else 'real',
            'total_configs': len(self.results),
            'results': [r.to_dict() for r in self.results]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved results to {output_path}")
        return output_path

    def generate_report(self, results: List[SweepResult] = None) -> str:
        """Generate human-readable sweep report."""
        if results is None:
            results = self.results

        if not results:
            return "No results to report"

        report = []
        report.append("\n" + "="*80)
        report.append("PARAMETER SWEEP REPORT")
        report.append("="*80)
        report.append(f"Mode: {'MOCK' if self.use_mock else 'REAL INFERENCE'}")
        report.append(f"Total Configurations: {len(results)}")

        # Best by latency
        best_latency = self.find_best_config("latency", results)
        report.append(f"\n✓ BEST LATENCY: {best_latency.config}")
        report.append(f"  Latency: {best_latency.avg_latency:.2f}s")
        report.append(f"  Quality: {best_latency.avg_quality:.2%}")
        report.append(f"  Diversity: {best_latency.avg_diversity:.4f}")

        # Best by quality
        best_quality = self.find_best_config("quality", results)
        report.append(f"\n✓ BEST QUALITY: {best_quality.config}")
        report.append(f"  Quality: {best_quality.avg_quality:.2%}")
        report.append(f"  Latency: {best_quality.avg_latency:.2f}s")
        report.append(f"  Diversity: {best_quality.avg_diversity:.4f}")

        # Pareto frontier
        pareto = self.find_pareto_frontier(results)
        report.append(f"\n✓ PARETO FRONTIER ({len(pareto)} configurations):")
        for config_result in sorted(pareto, key=lambda r: r.avg_latency):
            report.append(
                f"  {config_result.config}: "
                f"latency={config_result.avg_latency:.2f}s, "
                f"quality={config_result.avg_quality:.2%}"
            )

        report.append("\n" + "="*80)

        return "\n".join(report)


async def main():
    """Run parameter sweep from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Run parameter sweep for Pony Swarm")
    parser.add_argument(
        "--complexity",
        choices=["micro", "medium", "large"],
        default="micro",
        help="Complexity level to test"
    )
    parser.add_argument(
        "--max-configs",
        type=int,
        help="Limit number of configs (for quick testing)"
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real Horde.AI (slow)"
    )
    parser.add_argument(
        "--output",
        default="sweep_results.json",
        help="Output JSON file"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    sweep = ParameterSweep(use_mock=not args.real)

    # Run sweep
    results = await sweep.run_sweep(
        complexity=args.complexity,
        max_configs=args.max_configs
    )

    # Save results
    sweep.save_results(args.output)

    # Print report
    print(sweep.generate_report(results))


if __name__ == "__main__":
    asyncio.run(main())
