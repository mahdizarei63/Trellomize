def log_message(message):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{message}\n")
