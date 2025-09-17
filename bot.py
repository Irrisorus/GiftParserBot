import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
from motor.motor_asyncio import AsyncIOMotorClient

# =============== НАСТРОЙКИ ==================
API_ID = 27224361      # мой api_id
API_HASH = "4cddd4d0e539e13017347d07a17eb935"

SESSION_NAME = "tg_bot"

MONGO_URI = "mongodb+srv://kitsunyaroslav_db_user:w6mcBrrab6Wkx6uL@cluster0.xvsqm4j.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "GiftMessagesDB"

GROUP_A = -1002535658591 # исходная группа
GROUP_B = -1002931751866  # наша группа

from telethon.tl.functions.channels import GetForumTopicsRequest



# # Маппинг тем: topic_id в А -> topic_id в Б
# TOPIC_MAP = {
#     1196970: 2,
#     1196967: 3,
#     1196953: 4,
#     1196973: 5,
# }

CHECK_INTERVAL = 30  # секунд между проверками очереди
DELAY_DAYS = 21
# ============================================

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo[DB_NAME]
messages = db["messages"]

# # ======  СООБЩЕНИЯ В ГРУППЕ А ==========


@client.on(events.NewMessage(chats=GROUP_A))
async def handler(event):
    
   
    doc = {
         "chat_id": event.chat_id,
         "message_id": event.id,
         "text":event.text,
        #  "thread_id": thread_id,
         "target_chat_id": GROUP_B,
        # "target_thread_id": TOPIC_MAP[thread_id],
         "send_at": datetime.utcnow() + timedelta(days=DELAY_DAYS),#  datetime.utcnow() + timedelta(seconds=20) datetime.utcnow() + timedelta(days=DELAY_DAYS)
         "done": False,
     }
    await messages.insert_one(doc)
    print(f"💾 Сохранено сообщение {event.id} (thread_id=)")

    # print("📩 Новое сообщение!")
    # print("chat_id:", event.chat_id)
    # print("thread_id:", getattr(event.message, "message_thread_id", None))
    # print("text:", event.text)

# ====== ФОНОВЫЙ ПЛАНИРОВЩИК =================
async def scheduler():
    while True:
        now = datetime.utcnow()
        docs = messages.find({"send_at": {"$lte": now}, "done": False})
        async for doc in docs:
            try:
                msg = await client.get_messages(doc["chat_id"], ids=doc["message_id"])
                msg.text=msg.text.replace("New Gifts were Recently Upgraded","Прошёл 21 день")
                if msg.media:  # если есть фото/файл/видео
                    file_bytes = await msg.download_media(file=bytes)
                    await client.send_file(
                        entity=doc["target_chat_id"],
                        file=file_bytes,
                        caption=msg.text if msg.text else None,
                        # message_thread_id=doc["target_thread_id"]
                    )
                else:  # если только текст
                    await client.send_message(
                        entity=doc["target_chat_id"],
                        message=msg.text,
                        # message_thread_id=doc["target_thread_id"]
                    )

                await messages.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"done": True}}
                )
                print(f"✅ Отправлено сообщение {doc['message_id']} ")
                print(datetime.now)

            except Exception as e:
                print(f"❌ Ошибка при отправке {doc['message_id']}: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


# # ====== СТАРТ ================================
async def main():
    await client.start()
    asyncio.create_task(scheduler())
    print("🚀 Бот запущен и слушает группу А в реальном времени")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())

# # from telethon import TelegramClient, events
# # API_ID = 27224361
# # API_HASH = "4cddd4d0e539e13017347d07a17eb935"
# # SESSION_NAME = "get_ids"

# # client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# # @client.on(events.NewMessage)
# # async def p(event):
# #     print("chat_id:", event.chat_id,
# #           "msg_id:", event.id,
# #           "thread_id:", getattr(event.message, "message_thread_id", None),
# #           "text:", (event.text or "")[:80])

# # async def main():
# #     await client.start()
# #     print("Listening — отправь сообщение в тему")
# #     await client.run_until_disconnected()

# # import asyncio
# # asyncio.run(main())