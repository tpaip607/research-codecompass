"""notify.py — macOS notification wrapper using osascript."""
import subprocess


def notify(title: str, message: str = "", urgent: bool = False) -> None:
    """Send a macOS notification via osascript.

    Args:
        title: Notification title
        message: Notification body text
        urgent: If True, play the Sosumi alert sound
    """
    sound = ' sound name "Sosumi"' if urgent else ""
    escaped_msg = message.replace('"', '\\"')
    escaped_title = title.replace('"', '\\"')
    script = f'display notification "{escaped_msg}" with title "{escaped_title}"{sound}'
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=False,
            timeout=5,
            capture_output=True,
        )
    except Exception:
        pass  # Notifications are best-effort; never crash the runner
