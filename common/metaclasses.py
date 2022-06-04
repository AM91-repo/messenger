import dis


class ServerMaker(type):
    # Metaclass for checking server compliance:
    def __init__(self, clsname, bases, clsdict):
        methods = []
        attrs = []

        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        # print(methods)
        if 'connect' in methods:
            raise TypeError(
                'Using the connect method is not allowed in the server class')
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Incorrect socket initialization')
        super().__init__(clsname, bases, clsdict)


class ClientMaker(type):
    # Metaclass for checking client:
    def __init__(self, clsname, bases, clsdict):
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError(
                    'The use of a prohibited method was detected in the class')
        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError(
                'There are no calls to functions that work with sockets.')
        super().__init__(clsname, bases, clsdict)
