class UnsupportedStruct(Exception):

    def __init__(self, struct):

        self.message = "{} is invalid struct and not a message".format(str(struct))
        super().__init__(self.message)

def make_icinga_message(struct):

    first_line  = "{state} - {service} ({host})".format(state=struct.get("state"),
                    service=struct.get("service_name"), host=struct.get("service_host"))
    second_line = struct.get("service_output") or ""
    third_line  = "Direkt-Link: {link}".format(link=struct.get("icingaeweb_url"))

    if not struct.get("owners") and not struct.get("owner-groups"):
        fourth_line = "Notification to: admins (default)"
    else:
        owners = struct.get("owners") or []
        groups = struct.get("owner-groups") or []
        groups_strings = [ g + "-group" for g in groups ]
        fourth_line = "Notification to: " + ", ".join(owners) + " " + ", ".join(groups_strings)

    return "\n".join([first_line, second_line, third_line, fourth_line])

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
