class UnsupportedStruct(Exception):

    def __init__(self, struct):

        self.message = "{} is invalid struct and not a message".format(str(struct))
        super().__init__(self.message)

def make_icinga_message(struct):
    pass

def make_generic_message(struct):
    pass

def load_struct(struct):
    
    if type(struct) == str:
        return struct
    elif not struct.get("type"):
        raise UnsupportedStruct(struct)

    if struct.get("type") == "icinga":
        return make_icinga_message(struct)
    elif struct.get("type") == "generic":
        return make_generic_message(struct)
    else:
        raise UnsupportedStruct(struct)
