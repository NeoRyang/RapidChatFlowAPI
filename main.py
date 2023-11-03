import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from core.socket_io import sio
from routes.ws_no_prefix import NoPrefixNamespace
from config import config_list
from autogen import AssistantAgent, UserProxyAgent
import asyncio
from queue import Empty
import time

from queue import Queue

import autogen

current_time = time.strftime("%H:%M:%S", time.localtime())

task = None  # 全局变量task

app = FastAPI()

sio.register_namespace(NoPrefixNamespace("/"))

sio_asgi_app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=app)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_route("/socket.io/", route=sio_asgi_app, methods=["GET", "POST"])
app.add_websocket_route("/socket.io/", sio_asgi_app)

background_queue = asyncio.Queue()


# async def send_from_queue():
#     while True:
#         try:
#             data = await background_queue.get()  # 异步等待队列中有数据
#             print(data)
#             await sio.emit("response", data)
#         except asyncio.QueueEmpty:  # 队列为空时进行处理
#             await asyncio.sleep(0.1)


# @app.on_event("startup")
# def startup_event():
#     global task  # 使用全局变量task
#     # 添加后台任务并在FastAPI启动时运行
#     task = asyncio.create_task(send_from_queue())


# @app.on_event("shutdown")
# async def shutdown_event():
#     global task  # 使用全局变量task
#     # 取消任务
#     task.cancel()
#     try:
#         await task
#     except asyncio.CancelledError:
#         pass
#     sio.disconnect()  # 关闭所有sockets


def extract_messages(de):
    signal = "TERMINATE"
    manager = list(de.keys())[0]
    dicts = de[manager]
    messages = [d["content"].strip() for d in dicts]
    cleaned_messages = [msg for msg in messages if msg and msg != signal]
    return cleaned_messages


llm_config = {
    "config_list": config_list,
    "request_timeout": 220,
    "temperature": 0.0,
}


class AssistantAgentSocket(AssistantAgent):
    def __init__(self, sio, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sio = sio

    # async def async_enqueue(self, msg):
    #     await background_queue.put(msg)

    async def _process_received_message(self, message, sender, silent):
        msg_lines = [f"{sender.name.capitalize()}: {message}"]
        # await self.async_enqueue(msg_lines)
        await self.sio.emit("message", "\n".join(msg_lines))

        # loop = asyncio.get_event_loop()
        # loop.call_soon_threadsafe(asyncio.create_task, self.async_enqueue(msg_lines))
        return super()._process_received_message(message, sender, silent)


class UserProxyAgentSocket(UserProxyAgent):
    def __init__(self, sio, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sio = sio

    # async def async_enqueue(self, msg):
    #     await background_queue.put(msg)

    async def _process_received_message(self, message, sender, silent):
        msg_lines = [f"{sender.name.capitalize()}: {message}"]
        # await self.async_enqueue(msg_lines)
        await self.sio.emit("message", "\n".join(msg_lines))

        # loop = asyncio.get_event_loop()
        # loop.call_soon_threadsafe(asyncio.create_task, self.async_enqueue(msg_lines))
        return super()._process_received_message(message, sender, silent)


# assistant = autogen.AssistantAgent(
assistant = AssistantAgentSocket(
    name="assistant",
    llm_config=llm_config,
    sio=sio,
    system_message="you are a software engineer",
)
# user_proxy = autogen.UserProxyAgent(
user_proxy = UserProxyAgentSocket(
    name="user",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    llm_config=llm_config,
    sio=sio,
    system_message="you are a user",
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,  # set to True or image name like "python:3" to use docker
    },
)


@app.get("/query")
async def query(query: str):
    await sio.emit("response", f"question: {query}")  # 发送 "message" 事件和 "haha" 数据到所有客户端
    await user_proxy.a_initiate_chat(assistant, message=query)
    # result = extract_messages(user_proxy.chat_messages)
    # await sio.emit("response", result)  # 发送 "message" 事件和 "haha" 数据到所有客户端
    return {"message": "query sent"}
