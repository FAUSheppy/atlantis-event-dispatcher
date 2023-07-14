import ldap

# LDAP server details
ldap_server = "ldap://localhost:5005"
base_dn = "ou=People,dc=atlantishq,dc=de"
manager_dn = "cn=Manager,dc=atlantishq,dc=de"
manager_password = "flanigan"

class Person:

    def __init__(self, cn, username, name, email, phone):

        self.cn = cn
        self.username = username
        self.name = name
        self.email = email
        self.pohon = phone

def ldap_query(search_filter, ldap_args, alt_base_dn=None):
    
    ldap_server = ldap_args["LDAP_SERVER"]
    manager_dn = ldap_args["LDAP_BIND_DN"]
    manager_pw = ldap_args["LDAP_BIND_PW"]
    base_dn = ldap_args["LDAP_BASE_DN"]

    # for example a specific user dn #
    if alt_base_dn:
        base_dn = alt_base_dn

    # estabilish connection
    conn = ldap.initialize(ldap_server)
    conn.simple_bind_s(manager_dn, manager_password)

    # search in scope #
    search_scope = ldap.SCOPE_SUBTREE
    search_results = conn.search_s(base_dn, search_scope, search_filter)
   
    # unbind from connection and return #
    conn.unbind_s()
    return search_results

def _person_from_search_result(cn, entry):

    username = entry.get("uid", [None])[0]
    name = entry.get("firstName", [None])[0]
    email = entry.get("email", [None])[0]
    phone = entry.get("telephoneNumber", [None])[0]

    return Person(cn, username, name, email, phone)

def get_user_by_uid(username, ldap_args):

    if not username:
        return None

    search_filter = "(&(objectClass=inetOrgPerson)(uid={username}))".format(username=username)
    results = ldap_query(search_filter, ldap_args)
    
    if not results or len(results) < 1:
        return None

    cn, p = results[0]
    return _person_from_search_result(cn, p)


def get_members_of_group(group, ldap_args):

    if not group:
        return []

    search_filter = "(&(objectClass=groupOfNames)(cn={group_name})".format(group)
    results = ldap_query(search_filter, ldap_args)

    if not results:
        return []
    
    group_dn, entry = results[0]
    members = entry.get("member", [])

    persons = []
    for member in members:

        user_dn = member.decode("utf-8")
        user_filter = "(objectClass=inetOrgPerson)"
        results = ldap_query(user_filter, ldap_args, alt_base_dn=user_dn)

        if not results:
            continue

        cn, entry = results[0]
        person_obj = _person_from_search_result(cn, entry)
        persons.append(person_obj)

    return persons


def select_targets(users, groups, ldap_args, admin_group="pki"):
    '''Returns a list of persons to send notifications to'''

    persons = []
    if users:
        for username in users:
            persons.append(get_user_by_uid(username, ldap_args))
    elif groups:
        for group in groups:
            persons.append(get_members_of_group(group, ldap_args))
    else:
        # send to administrators #
        persons.append(get_members_of_group())

    return persons
