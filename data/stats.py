from .models import *


def gen_stats(users: list[User]):
    all_users = len(users)
    active = len([user for user in users if user.status])
    dead = len([user for user in users if not user.status])
    return all_users, active, dead
