import ldap
import sys

class Person:

    def __init__(self, cn, username, name, email, phone):

        self.cn = cn
        self.username = username
        self.name = name
        self.email = email
        self.phone = phone

    def __eq__(self, other):
        return other.cn == self.cn

    def __hash__(self):
        return hash(self.cn)

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

def get_user_by_uid(username, ldap_args, uid_is_cn=False):

    if not username:
        print("WARNING: get_user_by_uid called with empty username", file=sys.stderr)
        return None

    if uid_is_cn:
        username = username.split(",")[0].split("=")[1]

    search_filter = "(&(objectClass=inetOrgPerson)(uid={username}))".format(username=username)
    results = ldap_query(search_filter, ldap_args)
    
    if not results or len(results) < 1:
        print("WARNING: {} not found, no dispatch saved".format(username), file=sys.stderr)
        return None

    cn, p = results[0]
    return _person_from_search_result(cn, p)


def get_members_of_group(group, ldap_args):

    if not group:
        return []

    search_filter = "(&(objectClass=groupOfNames)(cn={group_name}))".format(group_name=group)

    # TODO wtf is this btw??
    groups_dn = ",".join([ s.replace("People","groups") for s in base_dn.split(",")])
    results = ldap_query(search_filter, ldap_args, alt_base_dn=groups_dn)

    if not results:
        return []
    
    group_dn, entry = results[0]
    members = entry.get("member", [])

    persons = []
    for member in members:

        user_cn = member.decode("utf-8")
        person_obj = get_user_by_uid(user_cn, ldap_args, uid_is_cn=True)

        if not person_obj:
            continue

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
            persons += get_members_of_group(group, ldap_args)
    else:
        # send to administrators #
        persons += get_members_of_group(admin_group, ldap_args)

    return set(persons)
