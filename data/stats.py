from .models import *
from datetime import datetime

def gen_stats(users: list[User]):
    all_users = len(users)
    active = len([user for user in users if user.status])
    dead = len([user for user in users if not user.status])
    joined_today = len([user for user in users if (user.join_dt.date() - datetime.now().date()).days <= 1])
    joined_week = len([user for user in users if (user.join_dt.date() - datetime.now().date()).days <= 7])
    joined_month = len([user for user in users if (user.join_dt.date() - datetime.now().date()).days <= 30])

    return all_users, active, dead, joined_today, joined_week, joined_month
