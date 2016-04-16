import sys
import contextlib

@contextlib.contextmanager
def stdin_replaced_by(new_stdin):
    old_stdin = sys.stdin
    try:
        sys.stdin = new_stdin
        yield
    finally:
        sys.stdin = old_stdin

def get_code(authorize_url):
    """Show authorization URL and return the code that the user wrote."""
    message = "Check this link in your browser: {0}".format(authorize_url)
    print(message + "\n", file=sys.stderr)
    with stdin_replaced_by(open('/dev/tty')):
        return input("Enter verification code: ")
