import socket
import subprocess
import sys
import logging
import time

def is_port_available(port: int, host: str = "localhost", timeout: float = 0.5) -> bool:
    """Check if a port is available by attempting to bind to it."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        sock.close()
        return result != 0  # Non-zero means port is not in use
    except Exception:
        return True


def force_close_port(port: int) -> None:
    """Force close any process using the specified port."""
    try:
        if sys.platform == "win32":
            # Windows: use netstat and taskkill
            subprocess.run(
                f'netstat -ano | findstr ":{port}" | findstr "LISTENING"',
                shell=True,
                capture_output=True,
                text=True,
            )
            # Alternative: use Get-Process on PowerShell
            subprocess.run(
                f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Stop-Process -Force"',
                shell=True,
                capture_output=True,
            )
        else:
            # Linux/Mac: use lsof or fuser
            try:
                subprocess.run(
                    f"kill -9 $(lsof -t -i :{port})",
                    shell=True,
                    capture_output=True,
                    timeout=2,
                )
                logging.debug(f"Forcefully closed port {port}")
            except subprocess.TimeoutExpired:
                logging.warning(f"Timeout while trying to close port {port}")
    except Exception as e:
        logging.debug(f"Could not force close port {port}: {e}")


def wait_for_port_available(port: int, host: str = "localhost", max_retries: int = 10, retry_delay: float = 0.5) -> bool:
    """Wait for a port to become available, with retries."""
    for attempt in range(max_retries):
        if is_port_available(port, host):
            return True
        logging.debug(f"Port {port} still in use, waiting... (attempt {attempt + 1}/{max_retries})")
        time.sleep(retry_delay)
    return False