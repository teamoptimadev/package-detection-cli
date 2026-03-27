import os
import sys
import shutil
import subprocess
import typer # type: ignore
import questionary # type: ignore
from pathlib import Path
from rich.console import Console # type: ignore
from rich.panel import Panel # type: ignore
from rich.table import Table # type: ignore
from rich.progress import Progress, SpinnerColumn, TextColumn # type: ignore
from typing import Optional, List

# Core logic imports (relative to project root)
sys.path.append(str(Path(__file__).parent.parent))
from detector.engine import DetectionEngine # type: ignore
from main import get_verdict_color, display_results # type: ignore

app = typer.Typer(help="🛡️ Package Detector - Security gatekeeper for package installations.")
console = Console()

BANNER = r"""
[bold cyan]██████╗  █████╗  ██████╗██╗  ██╗ █████╗  ██████╗ ███████╗
██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██╔════╝ ██╔════╝
██████╔╝███████║██║     █████╔╝ ███████║██║  ███╗█████╗  
██╔═══╝ ██╔══██║██║     ██╔═██╗ ██╔══██║██║   ██║██╔══╝  
██║     ██║  ██║╚██████╗██║  ██╗██║  ██║╚██████╔╝███████╗
╚═╝     ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝[/]

[bold blue]██████╗ ███████╗████████╗███████╗ ██████╗████████╗ ██████╗ ██████╗ 
██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
██║  ██║█████╗     ██║   █████╗  ██║        ██║   ██║   ██║██████╔╝
██║  ██║██╔══╝     ██║   ██╔══╝  ██║        ██║   ██║   ██║██╔══██╗
██████╔╝███████╗   ██║   ███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║
╚═════╝ ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝[/]
"""

def display_banner():
    console.print(BANNER)

@app.callback()
def main_callback():
    display_banner()

def detect_registry(package_name: str) -> str:
    """Heuristic to detect if it's an NPM or PyPI package."""
    cwd = Path.cwd()
    if (cwd / "package.json").exists():
        return "npm"
    if (cwd / "requirements.txt").exists() or (cwd / "setup.py").exists() or (cwd / "pyproject.toml").exists():
        return "pypi"
    
    # Check if package name looks like a typical python package (snake_case) or npm (kebab-case)
    if "_" in package_name and "-" not in package_name:
        return "pypi"
    
    return "npm" # Default to npm

def perform_security_check(package_name: str, registry: str, yes: bool = False) -> bool:
    """
    Runs the security scan and prompts if malicious.
    Returns True if safe to proceed, False to abort.
    """
    engine = DetectionEngine()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=f"🔍 Analyzing package '{package_name}' from {registry}...", total=None)
        result = engine.run(package_name, registry)
    
    if "error" in result:
        console.print(f"[bold red]ERROR Scanning {package_name}:[/bold red] {result['error']}")
        return questionary.confirm(f"Scan failed for '{package_name}'. Do you still want to install it?").ask()
    
    analysis = result["analysis"]
    verdict = analysis["verdict"]
    score = analysis["score"]
    
    # Show report
    # Import display_results here to avoid circular dependencies if any
    display_results(result)

    if verdict in ["MALICIOUS", "SUSPICIOUS"] and not yes:
        console.print(f"[bold red]WARNING:[/] This package shows [bold {get_verdict_color(verdict)}]{verdict}[/] behavior.")
        return questionary.confirm(f"Do you want to proceed with installing '{package_name}'?").ask()
    
    return True

@app.command("install", help="Safely install a package after analysis.")
@app.command("i", help="Safely install a package after analysis.")
def install(
    packages: List[str] = typer.Argument(..., help="Package(s) to install."),
    npm: bool = typer.Option(False, "--npm", help="Force NPM registry."),
    pip: bool = typer.Option(False, "--pip", help="Force PyPI registry."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt.")
):
    """
    Intercepts installation commands and checks safety.
    """
    registry = "npm"
    if npm:
        registry = "npm"
    elif pip:
        registry = "pypi"
    else:
        registry = detect_registry(packages[0])
    
    for pkg in packages:
        if perform_security_check(pkg, registry, yes):
            console.print(f"📦 Installing '{pkg}' using {registry}...")
            try:
                if registry == "npm":
                    bin_path = shutil.which("npm")
                    if not bin_path:
                        console.print("[bold red]ERROR: npm binary not found.[/bold red]")
                        continue
                    cmd = [bin_path, "install", pkg]
                else: # pypi
                    bin_path = shutil.which("pip") or shutil.which("pip3")
                    if not bin_path:
                        console.print("[bold red]ERROR: pip binary not found.[/bold red]")
                        continue
                    cmd = [bin_path, "install", pkg]
                
                subprocess.run(cmd, check=True)
                console.print(f"[bold green]Successfully installed '{pkg}'.[/bold green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[bold red]ERROR:[/] Actual installation failed for '{pkg}': {e}")
        else:
            console.print(f"[bold yellow]Aborted installation of '{pkg}'.[/bold yellow]")

@app.command("scan", help="Only scan a package without installing.")
def scan(
    package: str,
    registry: str = typer.Option("npm", "--registry", "-r", help="Registry to scan (npm or pypi)")
):
    perform_security_check(package, registry, yes=True)

# Support subcommands like 'pg npm install react'
@app.command("npm", help="Force npm context for the command.")
def npm_cmd(
    ctx: typer.Context,
    command: str = typer.Argument(...),
    packages: List[str] = typer.Argument(...)
):
    if command in ["install", "i", "add"]:
        # Use our install logic
        install(packages, npm=True)
    else:
        # Pass through (if we want to support other npm commands, but let's stick to install)
        console.print(f"[dim]Passing through npm command: {command}...[/dim]")
        subprocess.run(["npm", command] + packages)

@app.command("pip", help="Force pip context for the command.")
def pip_cmd(
    ctx: typer.Context,
    command: str = typer.Argument(...),
    packages: List[str] = typer.Argument(...)
):
    if command in ["install"]:
        # Use our install logic
        install(packages, pip=True)
    else:
        console.print(f"[dim]Passing through pip command: {command}...[/dim]")
        subprocess.run(["pip", command] + packages)

if __name__ == "__main__":
    app()
