import logging
import sys

class Colors:
    RESET = "\033[0m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BOLD = "\033[1m"

class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        logging.INFO: f"{Colors.GREEN}%(asctime)s - %(name)s - %(levelname)s - %(message)s{Colors.RESET}",
        logging.WARNING: f"{Colors.YELLOW}%(asctime)s - %(name)s - %(levelname)s - %(message)s{Colors.RESET}",
        logging.ERROR: f"{Colors.RED}%(asctime)s - %(name)s - %(levelname)s - %(message)s{Colors.RESET}",
        logging.CRITICAL: f"{Colors.BOLD}{Colors.RED}%(asctime)s - %(name)s - %(levelname)s - %(message)s{Colors.RESET}"
    }

    def format(self, record):
        log_format = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_format)
        return formatter.format(record)

def configure_logging(level=logging.INFO):
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())

    logging.basicConfig(
        level=level,
        handlers=[console_handler],
        force=True
    )