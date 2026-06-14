"""
TCP port checker and common-port scanner.

How it works:
create_connection() attempts a real TCP handshake (SYN → SYN-ACK → ACK).
If the port is open and listening, the connection succeeds → True.
If closed or filtered, it raises an exception → False.
"""
import socket

COMMON_SERVICES = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
}

def check_port(host: str, port: int, timeout: float = 3.0) -> bool:
    """
    Test whether a TCP port is open on the host.
    Args:
        host — IP or hostname
        port — TCP port number
        timeout — seconds before giving up
    Returns:
        True — port is open (service is listening)
        False — port is closed or filtered
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def scan_common_ports(host: str) -> dict:
    """
    Scan the most common ports on a host.
    Returns a dict: {port: {"service": name, "open": bool}}
    """
    results = {}
    for port, service in COMMON_SERVICES.items():
        results[port] = {
            "service": service,
            "open": check_port(host, port, timeout=1.0),
        }
    return results

"""
Test block for port_monitor
Run this file directly to scan common ports on a given host.
Default: localhost (127.0.0.1)

if __name__ == "__main__":
    host = "127.0.0.1"
    print(f"Scanning common ports on {host}...")
    results = scan_common_ports(host)
    for port, info in results.items():
        status = "OPEN" if info["open"] else "CLOSED"
        print(f"{port} ({info['service']}): {status}")
"""
