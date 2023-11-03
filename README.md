# RapidChatFlowAPI
A FastAPI project using Socket.IO that connects an assistant and a user within a chat application

##Key Features

• Built using FastAPI and python-socketio
• Uses an AssistantAgent and a UserProxyAgent to facilitate chat communication
• Use of background tasks
• Demonstration of overloaded methods in child classes

## Prerequisites

• Python 3.10 or higher
• FastAPI (pip install fastapi)
• python-socketio (pip install python-socketio[asgi])

##How to Use

1. Clone this repository to your local machine.
2. Install the necessary dependencies.
3. Run the application with command uvicorn main:app

##Usage

Use the /query GET endpoint with a query parameter to send a message as a User.

GET /query?query=YourMessageHere

A socket.io connection is maintained, and the sent message is processed by the Assistant.

The endpoint /query sends a POST request to the UserProxyAgentSocket with your query as a message. This request is then handled by the _process_received_message method, which emits a socket.io message and forwards the request to the superclass for further handling.

##Overloading

For AssistantAgentSocket and UserProxyAgentSocket, an overload has been provided that sends responses over the socket connection. This is a demonstration of how you could customize this project for your individual needs.

##Future Improvements

Feel free to expand on this example app with functionality such as better error handling, additional endpoints, or user authentication.

##Contributing

Contributions are welcome!Please feel free to submit a Pull Request.

## References
1. https://github.com/BimaAdi/fastapi-with-python-socketio-example
2. https://www.reddit.com/r/FastAPI/comments/neds9c/integrate_socketio_with_fastapi/
. https://github.com/tiangolo/fastapi/issues/129
