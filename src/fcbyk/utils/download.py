import os
import requests
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)


def download_file(url: str, dest_path: str) -> None:
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    dest_dir = os.path.dirname(os.path.abspath(dest_path))
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    filename = os.path.basename(dest_path)
    
    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task(f"Downloading {filename}", total=total_size if total_size > 0 else None)
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))
