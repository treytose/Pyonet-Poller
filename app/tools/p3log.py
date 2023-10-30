import os, logging, time, traceback
from logging.handlers import RotatingFileHandler
from rich.console import Console

console = Console()

class P3Log:
    def __init__(self, filename="app", path="app/logs", debug=False):
        self.debug = debug
        
        # ensure path exists
        if not os.path.exists(path):
            os.makedirs(path)

        # ensure filename ends with .log
        if not filename.endswith(".log"):
            filename = filename + ".log"
                
        self.log_path = os.path.join(path, filename)
        self.logger = logging.getLogger(__name__)
        
        max_bytes = 50 * (2**20) # 50Mb 
        handler = RotatingFileHandler(self.log_path, maxBytes=max_bytes, backupCount=2)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO) # Will not log normal logs without this

    def add_timestamp(self, message):
        return f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}"

    def log(self, message):       
        if self.debug:
            print(message)
        self.logger.info(self.add_timestamp(message))    

    def log_info(self, message):        
        message = f"[INFO] {message}"
        console.print(f"[bold blue]{message}")
        self.logger.info(self.add_timestamp(message))

    def log_success(self, message):        
        message = f"[SUCCESS] {message}"
        console.print(f"[bold green]{message}")
        self.logger.info(self.add_timestamp(message))

    def log_warning(self, message):        
        message = f"[WARNING] {message}"
        console.print(f"[bold yellow]{message}")
        self.logger.warning(self.add_timestamp(message))

    def log_error(self, message):  
        message = f"[ERROR] {message}"      
        console.print(f"[bold red]{message}")
        self.logger.error(self.add_timestamp(message))


if __name__ == '__main__':
    oLog = P3Log("test.log")
    oLog.log("TEST Info")
    oLog.log_warning("TEST WARNING")
    oLog.log_error("TEST ERROR")