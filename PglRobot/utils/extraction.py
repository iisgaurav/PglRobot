from aiogram.types import Message

def extract_user_and_reason(message: Message, command_args: str | None = None) -> tuple[int | None, str | None]:
    """
    Extracts the user ID and the reason from a message.
    Supports replies (extracts replied user) or mentions/IDs in the command string.
    Returns (user_id, reason).
    """
    user_id = None
    reason = None
    args = command_args.split() if command_args else []

    # Case 1: Reply to a message
    if message.reply_to_message:
        if message.reply_to_message.from_user:
            user_id = message.reply_to_message.from_user.id
        reason = command_args if command_args else None
        return user_id, reason

    # Case 2: No reply, must provide ID or username in command
    if len(args) == 0:
        return None, None

    target = args[0]
    
    # Check if target is a direct ID or mention in entities
    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                user_id = entity.user.id
                break
            elif entity.type == "mention":
                # Aiogram doesn't auto-resolve @usernames to IDs without API calls or DB lookups.
                # If they passed a username, we might need a separate DB lookup if it's not a text_mention.
                # For simplicity in this basic extractor, we handle numeric IDs.
                pass

    if not user_id:
        try:
            user_id = int(target)
        except ValueError:
            pass

    if len(args) > 1:
        reason = " ".join(args[1:])

    return user_id, reason
