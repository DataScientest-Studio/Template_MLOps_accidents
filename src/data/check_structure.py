import os
import sys


def _is_noconfirm():
    """Check if NOCONFIRM environment variable is set."""
    return os.environ.get("NOCONFIRM", "").lower() in ("1", "true", "yes")


def _is_non_interactive():
    """True when stdin is not a TTY (e.g. Docker, CI, pipes)."""
    return not sys.stdin.isatty()


def check_existing_file(file_path):
    """
    Check if a file already exists. If it does, ask if we want to overwrite it.

    If NOCONFIRM is set or stdin is non-interactive (e.g. Docker), returns True (overwrite).
    """
    if os.path.isfile(file_path):
        if _is_noconfirm():
            print(
                f"File {os.path.basename(file_path)} already exists. Overwriting (NOCONFIRM=1)."
            )
            return True
        if _is_non_interactive():
            print(
                f"File {os.path.basename(file_path)} already exists. Overwriting (non-interactive)."
            )
            return True
        while True:
            response = input(
                f"File {os.path.basename(file_path)} already exists. "
                f"Do you want to overwrite it? (y/n): "
            )
            if response.lower() == "y":
                return True
            elif response.lower() == "n":
                return False
            else:
                print("Invalid response. Please enter 'y' or 'n'.")
    else:
        return True


def check_existing_folder(folder_path):
    """
    Check if a folder already exists. If it doesn't, ask if we want to create it.

    If NOCONFIRM is set or stdin is non-interactive (e.g. Docker), returns True (create).
    """
    if not os.path.exists(folder_path):
        if _is_noconfirm():
            print(
                f"Folder {os.path.basename(folder_path)} doesn't exist. Creating (NOCONFIRM=1)."
            )
            return True
        if _is_non_interactive():
            print(
                f"Folder {os.path.basename(folder_path)} doesn't exist. Creating (non-interactive)."
            )
            return True
        while True:
            response = input(
                f"{os.path.basename(folder_path)} doesn't exists. "
                f"Do you want to create it? (y/n): "
            )
            if response.lower() == "y":
                return True
            elif response.lower() == "n":
                return False
            else:
                print("Invalid response. Please enter 'y' or 'n'.")
    else:
        return False
