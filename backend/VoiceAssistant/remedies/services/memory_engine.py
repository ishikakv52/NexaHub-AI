from collections import defaultdict

USER_MEMORY = defaultdict(list)

def save_message(user_id, role, message):
    USER_MEMORY[user_id].append({
        "role": role,
        "message": message
    })

def get_history(user_id):
    return USER_MEMORY[user_id][-10:]  # last 10 messages

def clear_memory(user_id):
    USER_MEMORY[user_id] = []