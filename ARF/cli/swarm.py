"""
ARF CLI - Swarm subcommands

Pony swarm operations using Recursive Self-Aggregation (RSA).
All commands support --json output mode for scripting.

Examples:
    arf swarm query "What is 47 * 89?" --ponies 4
    arf swarm query "Explain recursion" --iterations 3 --json
    arf swarm run --query "Complex reasoning task" --aggregation-size 2
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pwnies.desktop_pony_swarm.core.swarm import PonySwarm
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False

app = typer.Typer(help="Pony swarm operations")
console = Console()


@app.command()
def query(
    question: str = typer.Argument(..., help="Query for the swarm"),
    ponies: int = typer.Option(4, "--ponies", "-n", help="Number of ponies (N parameter)"),
    aggregation_size: int = typer.Option(2, "--aggregation-size", "-k", help="Aggregation size (K parameter)"),
    iterations: int = typer.Option(3, "--iterations", "-t", help="Number of iterations (T parameter)"),
    mock: bool = typer.Option(True, "--mock/--real", help="Use mock inference (default) or real Horde.AI"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Query the pony swarm using RSA algorithm

    The swarm will use Recursive Self-Aggregation to generate high-quality responses.

    Parameters:
        N (--ponies): Population size (number of ponies)
        K (--aggregation-size): How many responses to aggregate at each iteration
        T (--iterations): Number of refinement iterations

    Examples:
        arf swarm query "What is 47 * 89?"
        arf swarm query "Explain quantum computing" --ponies 6 --iterations 4
        arf swarm query "Write a haiku" --json | jq '.response'
    """
    if not SWARM_AVAILABLE:
        error_msg = "Pony swarm module not available. Install dependencies or check pwnies/ directory."
        if json_output:
            print(json.dumps({"success": False, "error": error_msg}))
        else:
            console.print(f"[red]Error:[/red] {error_msg}")
        sys.exit(1)

    try:
        # Run async query
        result = asyncio.run(_run_swarm_query(
            question=question,
            num_ponies=ponies,
            K=aggregation_size,
            T=iterations,
            use_mock=mock,
            json_output=json_output,
        ))

        if json_output:
            print(json.dumps({
                "success": True,
                "query": question,
                "response": result['response'],
                "parameters": {
                    "N": ponies,
                    "K": aggregation_size,
                    "T": iterations,
                },
                "metrics": result.get('metrics', {}),
                "is_crisis": result.get('is_crisis', False),
            }))
        else:
            console.print(f"\n[bold green]Response:[/bold green]")
            console.print(result['response'])
            console.print()

            if result.get('metrics'):
                metrics = result['metrics']
                console.print(f"[dim]Time: {metrics.get('total_time', 0):.2f}s | "
                            f"Generations: {metrics.get('total_generations', 0)} | "
                            f"Diversity: {metrics.get('avg_diversity', 0):.3f}[/dim]")

        sys.exit(0)

    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


async def _run_swarm_query(
    question: str,
    num_ponies: int,
    K: int,
    T: int,
    use_mock: bool,
    json_output: bool,
):
    """Helper to run swarm query asynchronously"""
    async with PonySwarm(num_ponies=num_ponies, use_mock=use_mock) as swarm:
        if not json_output:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Running RSA with N={num_ponies}, K={K}, T={T}...",
                    total=None
                )
                result = await swarm.recursive_self_aggregation(
                    query=question,
                    K=K,
                    T=T
                )
                progress.remove_task(task)
        else:
            result = await swarm.recursive_self_aggregation(
                query=question,
                K=K,
                T=T
            )

    return result


@app.command()
def info():
    """
    Show swarm configuration and capabilities

    Examples:
        arf swarm info
        arf swarm info --json
    """
    if not SWARM_AVAILABLE:
        console.print("[red]Error:[/red] Pony swarm module not available")
        sys.exit(1)

    info_data = {
        "available": True,
        "default_parameters": {
            "N": 4,
            "K": 2,
            "T": 3,
        },
        "algorithm": "Recursive Self-Aggregation (RSA)",
        "reference": "Research shows 15-30% improvement over single-agent baselines",
    }

    table = Table(title="Pony Swarm Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Algorithm", info_data["algorithm"])
    table.add_row("Default N (ponies)", str(info_data["default_parameters"]["N"]))
    table.add_row("Default K (aggregation)", str(info_data["default_parameters"]["K"]))
    table.add_row("Default T (iterations)", str(info_data["default_parameters"]["T"]))
    table.add_row("Performance", info_data["reference"])

    console.print(table)
    sys.exit(0)


if __name__ == "__main__":
    app()
