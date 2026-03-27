import argparse
import sys
import os
import logging
from pathlib import Path

# Suppress noise from transformers and huggingface
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

from rich.console import Console # type: ignore
from rich.panel import Panel # type: ignore
from rich.table import Table # type: ignore
from rich.columns import Columns # type: ignore
from rich.progress import Progress, SpinnerColumn, TextColumn # type: ignore
from detector.engine import DetectionEngine # type: ignore

console = Console()

def display_results(result):
    """Format and display analysis results in a premium terminal dashboard."""
    if "error" in result:
        console.print(f"\n[bold red]❌ ERROR:[/] {result['error']}\n")
        sys.exit(1)

    pkg = result['package_name']
    reg = result['registry']
    behaviors = result['behaviors']
    rag_match = result['rag_match']
    analysis = result['analysis']
    verdict = analysis['verdict']
    score = analysis['score']
    color = get_verdict_color(verdict)

    # 1. Main Header Dashboard
    verdict_styled = f"[bold {color}]{verdict}[/]"
    score_styled = f"[bold white]{score}/100[/]"
    
    header = Panel(
        f" [cyan]Package:[/] [bold white]{pkg}[/] [dim]({reg})[/]\n"
        f" [cyan]Verdict:[/] {verdict_styled} \n"
        f" [cyan]Risk Score:[/] {score_styled}",
        title="[bold white]🛡️ PD Security Analysis[/bold white]",
        subtitle=f"[dim]Analyzer v0.1.0[/dim]",
        border_style=color,
        padding=(1, 2)
    )
    console.print("\n", header)

    # 2. Behaviors and RAG Match (Side by Side or stacked)
    table = Table(box=None, padding=(0, 2))
    table.add_column("Indicator", style="yellow")
    table.add_column("Level", justify="right")
    
    for b in behaviors:
        if any(x in b for x in ["SENSITIVE", "SHELL", "CRITICAL"]):
            table.add_row(f"• {b}", "[red]CRITICAL[/]")
        elif any(x in b for x in ["URL", "NETWORK", "ENV", "SUSPICIOUS"]):
            table.add_row(f"• {b}", "[orange1]SUSPICIOUS[/]")
        else:
            table.add_row(f"• {b}", "[dim]INFO[/]")
    
    behavior_panel = Panel(
        table,
        title="[bold]🔍 Detected Behaviors[/bold]",
        border_style="dim",
        width=45
    )

    if rag_match:
        rag_content = (
            f"[bold magenta]Topic:[/] {rag_match['pattern']['threat']}\n"
            f"[bold magenta]Similarity:[/] {int(rag_match['score']*100)}%\n"
            f"[dim italic]\"{rag_match['pattern']['description']}\"[/]"
        )
        rag_panel = Panel(
            rag_content,
            title="[bold]🔗 Threat Database Match[/bold]",
            border_style="magenta",
            width=45
        )
        console.print(Columns([behavior_panel, rag_panel]))
    else:
        console.print(behavior_panel)

    # 3. AI Reasoning Dashboard
    reasoning_text = analysis['reasoning'].replace("AI ANALYSIS REPORT:", "").replace("-" * 30, "").strip()
    
    reasoning_panel = Panel(
        f"[white]{reasoning_text}[/]\n\n"
        f"[bold]Confidence:[/] [underline green]{analysis['confidence']}[/]",
        title="[bold cyan]🧠 AI Security Logic[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(reasoning_panel, "\n")

def get_verdict_color(verdict):
    if verdict == "MALICIOUS": return "bright_red"
    if verdict == "SUSPICIOUS": return "orange1"
    return "bright_green"

def main():
    parser = argparse.ArgumentParser(description="Malicious Package Detection CLI")
    parser.add_argument("package_name", nargs='?', help="Package name to scan (legacy)")
    parser.add_argument("--registry", choices=["npm", "pypi"], default="npm", help="Package registry")
    parser.add_argument("--local", help="Path to local package directory for scanning")
    args = parser.parse_args()

    engine = DetectionEngine()

    if args.local:
        package_name = Path(args.local).name
        registry = "local"
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Scanning local directory '{args.local}'...", total=None)
            
            # Simulated engine.run for local
            extract_dir = Path(args.local)
            source_files = engine.downloader.get_source_files(extract_dir)
            all_tokens = []
            for file_path in source_files:
                tokens = engine.ast_parser.parse_file(file_path)
                all_tokens.extend(tokens)
            behaviors = engine.behavior_extractor.extract(all_tokens)
            behavior_description = engine.behavior_extractor.to_natural_language(behaviors)
            rag_results = engine.vector_db.search_similar(behavior_description, top_k=1)
            analysis_result = engine.analyzer.analyze(behaviors, rag_results)
            result = {
                "package_name": package_name,
                "registry": registry,
                "behaviors": behaviors,
                "behavior_description": behavior_description,
                "rag_match": rag_results[0] if rag_results else None,
                "analysis": analysis_result
            }
    elif args.package_name:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Scanning package '{args.package_name}'...", total=None)
            result = engine.run(args.package_name, args.registry)
    else:
        parser.print_help()
        sys.exit(1)

    display_results(result)

if __name__ == "__main__":
    main()
