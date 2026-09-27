from db.crud import add_message,get_latest_messages
from config import RECENT_MESSAGES_LIMIT
from agent.build_agent import build_executor
from agent.compaction import compact_if_needed,format_chat_history

def chat(connection,client,chat_id,user_input):
    messages=get_latest_messages(connection=connection,chat_id=chat_id,n=RECENT_MESSAGES_LIMIT)

    chat_history=format_chat_history(messages=messages)

    executor=build_executor(client=client,chat_id=chat_id)

    result=executor.invoke({"input":user_input,"chat_history":chat_history})

    answer=result["output"]

    add_message(connection=connection,chat_id=chat_id,role="user",content=user_input)

    add_message(connection=connection,chat_id=chat_id,role="assistant",content=answer)

    compact_if_needed(connection=connection,client=client,chat_id=chat_id)

    return answer
