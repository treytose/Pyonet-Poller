from rich.console import Console


class Logger:
  def __init__(self):
    self.console = Console()
    
  def log_warning(self, message):
    self.console.print(f"[yellow underline]WARNING: {message}")
    
  def log_error(self, message):
    self.console.print(f"[red underline]ERROR: {message}")
