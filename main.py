import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from core.socket_io import sio
from routes.ws_no_prefix import NoPrefixNamespace
from config import config_list
from autogen import AssistantAgent, UserProxyAgent
import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from autogen import Agent

# from queue import Empty
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

    async def _process_received_message(self, message, sender, silent):
        msg_lines = [f"{sender.name.capitalize()}: {message}"]
        # await self.async_enqueue(msg_lines)
        await self.sio.emit("message", "\n".join(msg_lines))

        return super()._process_received_message(message, sender, silent)

    async def a_receive(
        self,
        message: Union[Dict, str],
        sender: Agent,
        request_reply: Optional[bool] = None,
        silent: Optional[bool] = False,
    ):
        await self._process_received_message(message, sender, silent)  # await
        if (
            request_reply is False
            or request_reply is None
            and self.reply_at_receive[sender] is False
        ):
            return
        reply = await self.a_generate_reply(sender=sender)
        if reply is not None:
            await self.a_send(reply, sender, silent=silent)


class UserProxyAgentSocket(UserProxyAgent):
    def __init__(self, sio, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sio = sio

    async def _process_received_message(self, message, sender, silent):
        msg_lines = [f"{sender.name.capitalize()}: {message}"]
        # await self.async_enqueue(msg_lines)
        await self.sio.emit("message", "\n".join(msg_lines))

        return super()._process_received_message(message, sender, silent)

    async def a_receive(
        self,
        message: Union[Dict, str],
        sender: Agent,
        request_reply: Optional[bool] = None,
        silent: Optional[bool] = False,
    ):
        await self._process_received_message(message, sender, silent)  # await
        if (
            request_reply is False
            or request_reply is None
            and self.reply_at_receive[sender] is False
        ):
            return
        reply = await self.a_generate_reply(sender=sender)
        if reply is not None:
            await self.a_send(reply, sender, silent=silent)


assistant = AssistantAgentSocket(
    name="assistant",
    llm_config=llm_config,
    sio=sio,
    system_message="you are a software engineer",
)
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
    # await sio.emit("response", f"question: {query}")
    await user_proxy.a_initiate_chat(assistant, message=query)
    # result = extract_messages(user_proxy.chat_messages)
    # await sio.emit("response", result)
    return {"message": "query sent"}
