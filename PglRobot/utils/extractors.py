from aiogram.types import Message

async def extract_user_and_reason(message: Message) -> tuple[int | None, str]:
    """
    Extracts the target user_id and reason from a command message.
    Handles replies and direct mentions/IDs.
    Returns: (user_id, reason)
    """
    user_id = None
    reason = ""

    args = message.text.split(None, 1) if message.text else []
    
    # Check if replied to a user
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        if len(args) > 1:
            reason = args[1]
    # Check if a user ID/mention was provided in the command
    elif len(args) > 1:
        command_args = args[1].split(None, 1)
        target = command_args[0]
        
        if len(command_args) > 1:
            reason = command_args[1]

        # Extract by entities (Mentions)
        if message.entities:
            for entity in message.entities:
                if entity.type == "text_mention" and entity.user:
                    user_id = entity.user.id
                    break
                elif entity.type == "mention":
                    # For @username, we'd normally have to resolve it. 
                    # If it's a known username, getting the ID requires additional work or MTProto.
                    # For now, we will rely on replies or numeric IDs or text_mentions if they didn't reply.
                    pass

        # If not found via entity, maybe it's a numeric ID
        if not user_id and target.lstrip('-').isdigit():
            user_id = int(target)

    return user_id, reason
