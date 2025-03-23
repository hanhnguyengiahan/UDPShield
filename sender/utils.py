import sys

def parse_run_time(run_time_str, min_run_time=1, max_run_time=60):
    """Parse and validate the runtime argument."""
    try:
        return float(run_time_str) / 1000.0
    except ValueError:
        sys.exit(f"Invalid run_time argument, must be numerical: {run_time_str}")

def parse_port(port_str, min_port=49152, max_port=65535):
    """Parse and validate the port number."""
    try:
        port = int(port_str)
        if not (min_port <= port <= max_port):
            raise ValueError()
        return port
    except ValueError:
        sys.exit(f"Invalid port argument, must be between {min_port} and {max_port}: {port}")
