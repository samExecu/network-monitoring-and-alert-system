"""
Cross-platform ICMP ping using the OS ping command via subprocess.
No admin/root required. Works on Windows, macOS, and Linux.

Platform differences handled here:
Windows → ping -n 1 -w <ms> (timeout in milliseconds)
macOS → ping -c 1 -W <ms> (timeout in milliseconds)
Linux → ping -c 1 -W <sec> (timeout in seconds)
"""

import subprocess, re, platform
_SYSTEM = platform.system() # "Windows" | "Darwin" | "Linux"
def _build_cmd(host: str, timeout_sec: int) -> tuple[list, str]:
  """
  Return (command_list, rtt_regex_pattern) for the current OS.
  Called once per ping so platform check is always correct.
  """
  if _SYSTEM == "Windows":
    return (
      ["ping", "-n", "1", "-w", str(timeout_sec * 1000), host],
      r"time[=<](\d+)ms",
      )
  elif _SYSTEM == "Darwin": # macOS
    return (
      ["ping", "-c", "1", "-W", str(timeout_sec * 1000), host],
      r"time[=<](\d+\.?\d*)\s*ms",
      )
  else: # Linux (and anything else)
    return (
      ["ping", "-c", "1", "-W", str(timeout_sec), host],
      r"time[=<](\d+\.?\d*)\s*ms",
    )
def ping_host(host: str, timeout: int = 2) -> float | None:
  """
  Ping a host once and return round-trip time in milliseconds.
  Returns None if the host is unreachable or times out.
  Args:
    host — IP address or hostname
    timeout — seconds to wait for a reply
  Returns:
    float — RTT in ms (e.g. 14.0)
    None — host is down or unreachable
  """
  cmd, pattern = _build_cmd(host, timeout)
  try:
    result = subprocess.run(
      cmd,
      capture_output=True,
      text=True,
      timeout=timeout + 3, # subprocess safety net
    )
    match = re.search(pattern, result.stdout, re.IGNORECASE)
    return float(match.group(1)) if match else None
  except subprocess.TimeoutExpired:
    return None
  except FileNotFoundError:
    # ping binary not found - shouldn't happen on any modern OS
    print(f"[PING ERROR] 'ping' command not found on {_SYSTEM}")
    return None
  except Exception as e:
    print(f"[PING ERROR] {host}: {e}")
    return None

"""
Test block for ping_monitor

print(ping_host("8.8.8.8"))       # Google DNS
print(ping_host("1.1.1.1"))       # Cloudflare DNS
print(ping_host("this-host-does-not-exist-12345.local"))

for i in range(5):
  print(ping_host("8.8.8.8"))
"""
