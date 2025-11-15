"""
ARF CLI - Ontology subcommands

Ontology validation and inference operations.
All commands support --json output mode for scripting.

Examples:
    arf ontology validate "(GPT-4, is_a, LLM)"
    arf ontology infer --triple "(GPT-4.5, improves_upon, GPT-4)"
    arf ontology list-predicates --json
"""

import sys
import json
import re
from pathlib import Path
from typing import Optional, Tuple

import typer
from rich.console import Console
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_memory import ConversationMemory

app = typer.Typer(help="Ontology operations")
console = Console()


def parse_triple(triple_str: str) -> Tuple[str, str, str]:
    """
    Parse a triple string like "(subject, predicate, object)"

    Returns:
        Tuple of (subject, predicate, object)

    Raises:
        ValueError if parsing fails
    """
    # Match pattern: (subject, predicate, object)
    pattern = r'\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)'
    match = re.match(pattern, triple_str.strip())

    if not match:
        raise ValueError(f"Invalid triple format: {triple_str}. Expected: (subject, predicate, object)")

    return (
        match.group(1).strip(),
        match.group(2).strip(),
        match.group(3).strip(),
    )


@app.command()
def validate(
    triple: str = typer.Argument(..., help="Triple to validate: (subject, predicate, object)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Validate a knowledge triple against the ontology

    The triple format is: (subject, predicate, object)

    Examples:
        arf ontology validate "(GPT-4, is_a, LLM)"
        arf ontology validate "(Claude-4, improves_upon, Claude-3.5)"
        arf ontology validate "(AI, has_property, reasoning)" --json
    """
    try:
        # Parse triple
        subject, predicate, obj = parse_triple(triple)

        # Create a temporary memory instance for validation
        memory = ConversationMemory(agent_id="validator", validate_ontology=True)

        # Validate using the internal method
        is_valid, error_msg = memory._validate_triple((subject, predicate, obj))

        if json_output:
            print(json.dumps({
                "success": True,
                "valid": is_valid,
                "triple": {
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                },
                "error": error_msg,
            }))
        else:
            if is_valid:
                console.print(f"[green]✓ Valid triple[/green]")
                console.print(f"  Subject: {subject}")
                console.print(f"  Predicate: {predicate}")
                console.print(f"  Object: {obj}")
            else:
                console.print(f"[red]✗ Invalid triple[/red]")
                console.print(f"  Error: {error_msg}")
                console.print(f"  Triple: ({subject}, {predicate}, {obj})")

        sys.exit(0 if is_valid else 1)

    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command()
def infer(
    triple: str = typer.Argument(..., help="Triple for inference: (subject, predicate, object)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Perform inference on a knowledge triple

    Note: Full inference engine implementation is planned for Phase 7.
    This command currently validates and stores the triple.

    Examples:
        arf ontology infer "(GPT-4.5, improves_upon, GPT-4)"
        arf ontology infer "(Claude-4, is_a, LLM)" --json
    """
    try:
        # Parse triple
        subject, predicate, obj = parse_triple(triple)

        # For now, just validate (full inference in Phase 7)
        memory = ConversationMemory(agent_id="inference", validate_ontology=True)
        is_valid, error_msg = memory._validate_triple((subject, predicate, obj))

        if not is_valid:
            if json_output:
                print(json.dumps({
                    "success": False,
                    "error": f"Invalid triple: {error_msg}",
                }))
            else:
                console.print(f"[red]✗ Cannot infer from invalid triple[/red]")
                console.print(f"  Error: {error_msg}")
            sys.exit(1)

        # Store as understanding (inference engine will process later)
        content = f"{subject} {predicate.replace('_', ' ')} {obj}"
        ref = memory.transmit({"content": content})

        if json_output:
            print(json.dumps({
                "success": True,
                "triple": {
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                },
                "stored_ref": ref,
                "note": "Full inference engine coming in Phase 7",
            }))
        else:
            console.print(f"[green]✓ Triple validated and stored[/green]")
            console.print(f"  ({subject}, {predicate}, {obj})")
            console.print(f"  [dim]Note: Full inference engine coming in Phase 7[/dim]")

        sys.exit(0)

    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command(name="list-predicates")
def list_predicates(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    List all known predicates in the ontology

    Examples:
        arf ontology list-predicates
        arf ontology list-predicates --json | jq '.predicates[]'
    """
    # Known predicates (synchronized with ontology_integrity/src/lib.rs)
    predicates = [
        "is_a",
        "part_of",
        "related_to",
        "has_property",
        "improves_upon",
        "capable_of",
        "trained_on",
        "evaluated_on",
        "stated",
    ]

    if json_output:
        print(json.dumps({
            "success": True,
            "count": len(predicates),
            "predicates": predicates,
        }))
    else:
        table = Table(title="Known Ontology Predicates")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Predicate", style="green")

        for i, pred in enumerate(predicates, 1):
            table.add_row(str(i), pred)

        console.print(table)

    sys.exit(0)


@app.command()
def info():
    """
    Show ontology information

    Examples:
        arf ontology info
    """
    table = Table(title="Ontology System Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Backend", "File (Holochain integration in progress)")
    table.add_row("Validation", "Active")
    table.add_row("Predicates", "9 base predicates")
    table.add_row("Inference Engine", "Phase 7 (planned)")

    console.print(table)
    console.print("\n[dim]For full symbolic reasoning, see Phase 7 roadmap[/dim]")

    sys.exit(0)


if __name__ == "__main__":
    app()
