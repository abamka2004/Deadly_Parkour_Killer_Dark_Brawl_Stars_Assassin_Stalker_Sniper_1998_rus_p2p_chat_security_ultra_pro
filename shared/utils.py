import time


def format_message(msg):
    return f"[{time.strftime('%H:%M:%S', time.localtime(msg['timestamp']))}] {msg['sender_name']}: {msg['text']}"
