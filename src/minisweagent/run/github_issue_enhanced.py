#!/usr/bin/env python3
import os
from pathlib import Path

import requests
import typer
import yaml
from rich.console import Console
import json

from minisweagent.agents.interactive import InteractiveAgent
from minisweagent.config import builtin_config_dir, get_config_path
from minisweagent.environments.docker import DockerEnvironment
from minisweagent.models import get_model
from minisweagent.run.extra.config import configure_if_first_time
from minisweagent.run.utils.save import save_traj
from typing import Tuple

DEFAULT_CONFIG = Path(os.getenv("MSWEA_GITHUB_CONFIG_PATH", builtin_config_dir / "github_issue.yaml"))
console = Console(highlight=False)
app = typer.Typer(rich_markup_mode="rich", add_completion=False)


def get_owner_repo_issue_number(issue_url: str) -> Tuple[str, str, str]:
    """
    Extracts owner, repo name, and issue number from a GitHub issue URL.
    
    Example:
        https://github.com/containerd/fifo/issues/56
        returns ('containerd', 'fifo', '56')
    """
    # Strip trailing slashes and split by '/'
    parts = issue_url.rstrip('/').split('/')
    
    # GitHub issue URLs follow the pattern:
    # https://github.com/[owner]/[repo]/issues/[number]
    # After splitting, the relevant parts are at the end:
    # index -4: owner
    # index -3: repo
    # index -1: issue number
    
    try:
        owner = parts[-4]
        repo = parts[-3]
        issue_number = parts[-1]
        return owner, repo, issue_number
    except IndexError:
        raise ValueError("Invalid GitHub issue URL format.")


# def ensure_folder_exists(folder_path: str):
#     """
#     Checks if a folder exists at the given path; if not, creates it.
#     Includes parents=True to create any missing parent directories.
#     """
#     Path(folder_path).mkdir(parents=True, exist_ok=True)


def fetch_github_issue(issue_url: str) -> str:
    """Fetch GitHub issue text from the URL."""
    # Convert GitHub issue URL to API URL
    api_url = issue_url.replace("github.com", "api.github.com/repos").replace("/issues/", "/issues/")

    headers = {}
    if github_token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {github_token}"

    response = requests.get(api_url, headers=headers)
    issue_data = response.json()

    title = issue_data["title"]
    body = issue_data["body"] or ""

    return f"GitHub Issue: {title}\n\n{body}"


# fmt: off
@app.command()
def main(
    issue_url: str = typer.Option(prompt="Enter GitHub issue URL", help="GitHub issue URL"),
    config: Path = typer.Option(DEFAULT_CONFIG, "-c", "--config", help="Path to config file"),
    model: str | None = typer.Option(None, "-m", "--model", help="Model to use"),
    model_class: str | None = typer.Option(None, "--model-class", help="Model class to use (e.g., 'anthropic' or 'minisweagent.models.anthropic.AnthropicModel')", rich_help_panel="Advanced"),
    yolo: bool = typer.Option(False, "-y", "--yolo", help="Run without confirmation"),
) -> InteractiveAgent:
    # fmt: on
    """Run mini-SWE-agent on a GitHub issue"""
    configure_if_first_time()

    _config = yaml.safe_load(get_config_path(config).read_text())
    _agent_config = _config.setdefault("agent", {})
    if yolo:
        _agent_config["mode"] = "yolo"
    if model_class is not None:
        _config.setdefault("model", {})["model_class"] = model_class

    task = fetch_github_issue(issue_url)

    agent = InteractiveAgent(
        get_model(model, _config.get("model", {})),
        DockerEnvironment(**_config.get("environment", {})),
        **_agent_config,
    )

    repo_url = issue_url.split("/issues/")[0]
    if github_token := os.getenv("GITHUB_TOKEN"):
        repo_url = repo_url.replace("https://github.com/", f"https://{github_token}@github.com/") + ".git"

    agent.env.execute(f"git clone {repo_url} /testbed", cwd="/")

    exit_status, result = None, None
    try:
        exit_status, result = agent.run(task)
    except KeyboardInterrupt:
        console.print("\n[bold red]KeyboardInterrupt -- goodbye[/bold red]")
    finally:
        owner, repo, issue_number = get_owner_repo_issue_number(issue_url)
        output_path = f"deliverables_final/open_github_issues/{owner}_{repo}_{issue_number}/traj.json"
        save_traj(agent, Path(output_path), exit_status=exit_status, result=result)
        """
            Write fix.patch
        """
        with open(f"deliverables_final/open_github_issues/{owner}_{repo}_{issue_number}/fix.patch", "w") as outfile:
            json.dump({
                "model_name_or_path": "vertex_ai/gemini-2.5-flash",
                "github issue url": issue_url,
                "model_patch": result
                }, outfile, indent=4)
        print(f"Saved fix.patch to deliverables_final/open_github_issues/{owner}_{repo}_{issue_number}/fix.patch")
    return agent


if __name__ == "__main__":
    app()
