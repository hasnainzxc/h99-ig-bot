def delay(seconds):
    """Pause the execution for a specified number of seconds."""
    import time
    time.sleep(seconds)

def log(message):
    """Log a message to the console with a timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp} - {message}")

def validate_username(username):
    """Check if the username meets the required criteria."""
    if len(username) < 5:
        raise ValueError("Username must be at least 5 characters long.")
    if not username.isalnum():
        raise ValueError("Username must be alphanumeric.")
    return True

def validate_password(password):
    """Check if the password meets the required criteria."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    return True