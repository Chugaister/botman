from data import models


def gen_dynamic_text(text: str, user: models.User) -> str:
    any = user.first_name if user.first_name else user.username
    text = text.replace("[username]", str(user.username))
    text = text.replace("[first_name]", str(user.first_name))
    text = text.replace("[last_name]", str(user.last_name))
    text = text.replace("[any]", any)
    return text
