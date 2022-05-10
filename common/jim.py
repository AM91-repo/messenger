from datetime import datetime

TIME = datetime.now().replace(microsecond=0).isoformat(sep=' ')

RESPONSE = {
    "response": None,
    "time": str(TIME),
    "alert": None,
    "from": "Server",
    "contacts": None
}

PRESENCE = {
    "action": "presence",
    "time": str(TIME),
    "type": "status",
    "user": {
        "account_name": "",
        "status": ""
    }
}

MESSAGE = {
    "action": "msg",
    "time": str(TIME),
    "to": None,
    "from": None,
    "encoding": "",
    "message": None
}

MESSAGE_EXIT = {
    "action": "exit",
    "time": str(TIME),
    "account_name": "",
}

RESPONSE_200 = {"response": 200}
RESPONSE_400 = {
    "response": 400,
    "error": 'Bad Request'
}
RESPONSE_404 = {
    "response": 404}
