JIM = list()

RESPONSE = {
    "response": None,
    "time": None,
    "alert": None,
    "from": "Server",
    "contacts": None
}

PRESENCE = {
    "action": "presence",
    "time": None,
    "type": "status",
    "user": {
        "account_name": "",
        "pubkey": ""
    }
}

MESSAGE = {
    "action": "msg",
    "time": None,
    "to": None,
    "from": None,
    "encoding": "",
    "message": None,
}

MESSAGE_EXIT = {
    "action": "exit",
    "time": None,
    "account_name": "",
}

REQUEST_CONTACTS = {
    "action": "get_contacts",
    "time": None,
    "user": "",
}

ADDING_CONTACT = {
    "action": "add",
    "time": None,
    "account_name": "",
    "user": "",
}

REMOVE_CONTACT = {
    "action": "remove",
    "time": None,
    "account_name": "",
    "user": "",
}

USERS_REQUEST = {
    "action": "get_users",
    "time": None,
    "account_name": "",
}

PUBLIC_KEY_REQUEST = {
    "action": "get_users",
    "time": None,
    "account_name": "",
}

RESPONSE_200 = {"response": 200}
RESPONSE_202 = {
    "response": 202,
    "data_list":None
}
RESPONSE_205 = {"response": 205}
RESPONSE_400 = {
    "response": 400,
    "error": 'Bad Request'
}
RESPONSE_404 = {
    "response": 404}

RESPONSE_511 = {
    "response": 511,
    "bin": None
}