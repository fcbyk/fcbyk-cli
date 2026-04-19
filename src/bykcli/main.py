"""CLI entry point."""

import sys
import logging

from bykcli.app import create_cli
from bykcli.core.errors import CliError
from bykcli.runtime import build_runtime

logger = logging.getLogger("bykcli")

main = create_cli()


def _get_log_file_path() -> str:
    """Get the log file path from runtime context."""
    try:
        context = build_runtime()
        return str(context.paths.app_log_file)
    except Exception:
        return "log file"


def _handle_global_exception(exc_type: type, exc_value: BaseException, exc_traceback) -> None:
    """Global exception handler as the last line of defense."""
    if issubclass(exc_type, (SystemExit, KeyboardInterrupt)):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.critical(
        "Uncaught global exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    
    log_file = _get_log_file_path()
    
    from rich.console import Console
    console = Console(stderr=True)
    console.print(f"\n[red]Error:[/red] An unexpected error occurred")
    console.print(f"[yellow]Details have been logged to: {log_file}[/yellow]")
    console.print(f"[dim]For assistance, please provide the following information to developers:[/dim]")
    console.print(f"[dim]  - Exception type: {exc_type.__name__}[/dim]")
    console.print(f"[dim]  - Exception message: {exc_value}[/dim]\n")
    
    sys.exit(1)


if __name__ == "__main__":
    sys.excepthook = _handle_global_exception
    
    try:
        main()
    except CliError as exc:
        logger.warning("cli error: %s", exc)
        from rich.console import Console
        console = Console(stderr=True)
        console.print(f"\n[red]Error:[/red] {exc}\n")
        sys.exit(1)
    except Exception as exc:
        logger.exception("unexpected error in main")
        log_file = _get_log_file_path()
        from rich.console import Console
        console = Console(stderr=True)
        console.print(f"\n[red]Error:[/red] An unexpected error occurred")
        console.print(f"[yellow]Details have been logged to: {log_file}[/yellow]\n")
        sys.exit(1)
