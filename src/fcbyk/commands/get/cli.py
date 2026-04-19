import click
import webbrowser
import os
from rich.console import Console
from rich.table import Table
from fcbyk.utils.download import download_file

# 资源映射表
RESOURCES = {
    "vscode": {
        "home": "https://code.visualstudio.com/",
        "download": "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user",
        "filename": "VSCodeUserSetup-x64.exe"
    },
    "py": {
        "home": "https://www.python.org/",
        "download": "https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe",
        "filename": "python-3.12.1-amd64.exe"
    }
}

@click.command()
@click.argument("resource", required=False)
@click.option("-d", "--download", is_flag=True, help="Download the package. Optional: provide a path after -d.")
@click.argument("download_dir", required=False)
@click.option("-l", "--list", "list_resources", is_flag=True, help="List all supported resources")
def get(resource, download, download_dir, list_resources):
    """Get resources: opens the official website by default, or downloads the package with -d."""
    
    if list_resources:
        console = Console()
        table = Table(title="Supported Resources")
        table.add_column("Name", style="cyan")
        table.add_column("Home Page", style="green")
        
        for name, info in RESOURCES.items():
            table.add_row(name, info["home"])
        
        console.print(table)
        return

    if not resource:
        click.echo(click.get_current_context().get_help())
        return

    # Handle download logic
    if download:
        # If no download_dir provided after -d, default to current directory
        if not download_dir:
            download_dir = "."
        
        res_key = resource.lower()
        if res_key not in RESOURCES:
            click.secho(f"Resource not found: {resource}", fg="red")
            click.echo(f"Currently supported resources: {', '.join(RESOURCES.keys())}")
            return

        res = RESOURCES[res_key]
        
        # Trigger download
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
            except Exception as e:
                click.secho(f"Failed to create directory: {e}", fg="red")
                return
        
        dest_path = os.path.join(download_dir, res["filename"])
        click.echo(f"Starting download for {resource} to {dest_path}...")
        try:
            download_file(res["download"], dest_path)
            click.secho(f"\nDownload completed: {dest_path}", fg="green")
        except Exception as e:
            click.secho(f"\nDownload failed: {e}", fg="red")
    else:
        # Open official website
        res_key = resource.lower()
        if res_key not in RESOURCES:
            click.secho(f"Resource not found: {resource}", fg="red")
            click.echo(f"Currently supported resources: {', '.join(RESOURCES.keys())}")
            return
            
        res = RESOURCES[res_key]
        click.echo(f"Opening {resource} official website: {res['home']}")
        webbrowser.open(res["home"])
