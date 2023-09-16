from datetime import datetime

import requests.exceptions

DT_FORMAT = "%H:%M %d.%m.%Y"

import aiohttp

async def is_valid_link(buttons: list[list[dict]]) -> bool:
    for row in buttons:
        for button in row:
            link = button["link"]
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(link) as response:
                        if 200 <= response.status < 400:
                            return True
                        else:
                            return False
                except aiohttp.ClientError:
                    return False

def deserialize_buttons(text: str) -> list[list[dict]]:
    buttons = []
    if text is None:
        return buttons
    for row in text.split("\n"):
        button_dicts = []
        for button in row.split(" | "):
            caption, link = button.split(" - ")
            link = link.strip()
            if not "https://" not in link and not "http://" in link:
                link = "https://" + link
            # try:
            #     req = requests.get(link)
            # except requests.exceptions.ConnectionError:
            #     raise ValueError
            # if not req.ok:
            #     raise ValueError
            button_dicts.append({"caption": caption.strip(), "link": link})
        buttons.append(button_dicts)
    return buttons


def serialize_buttons(buttons: list[list[dict]]) -> str | None:
    if not buttons:
        return None
    serialized_rows = []
    for button_row in buttons:
        serialized_buttons = [f"{button['caption']} - {button['link']}" for button in button_row]
        serialized_rows.append(" | ".join(serialized_buttons))
    text = "\n".join(serialized_rows)
    return text


def deserialize_reply_buttons(text: str) -> list[list[str]]:
    reply_buttons = []
    for row in text.split("\n"):
        captions = row.split(" | ")
        reply_buttons.append(captions)
    return reply_buttons


def serialize_reply_buttons(buttons: list[list[str]]) -> str:
    rows = []
    for row in buttons:
        row_text = " | ".join(row)
        rows.append(row_text)
    return "\n".join(rows)


class Admin:
    columns = (
        "id",
        "username",
        "first_name",
        "last_name"
    )

    def __init__(self, _id: int, username: str, first_name: str, last_name: str):
        self.id = _id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    def get_tuple(self):
        return (self.id, self.username, self.first_name, self.last_name)


class Bot:
    columns = (
        "id",
        "token",
        "username",
        "admin",
        "status",
        "premium",
        "settings",
        "action"
    )

    def __init__(self, _id: int, token: str, username: str, admin: int, status: int = 1, premium: int = 0,
                settings: int = 2, action: str = None):
        self.id = _id
        self.token = token
        self.username = username
        self.admin = admin
        self.status = status
        self.premium = premium
        self.settings = Settings(settings)
        self.action = action

    def get_tuple(self):
        return self.id, self.token, self.username, self.admin, self.status, self.premium, self.settings.data,  self.action


class User:
    columns = (
        "id",
        "bot",
        "username",
        "first_name",
        "last_name",
        "status",
        "join_dt"
    )

    def __init__(self, _id: int, bot: int, username: str, first_name: str, last_name: str, status: bool, join_dt: str):
        self.id = _id
        self.bot = bot
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.status = status
        self.join_dt = datetime.strptime(join_dt, DT_FORMAT)

    def get_tuple(self):
        return self.id, self.bot, self.username, self.first_name, self.last_name, self.status, self.join_dt.strftime(
            DT_FORMAT)


class Captcha:
    columns = (
        "bot",
        "active",
        "text",
        "photo",
        "video",
        "gif",
        "buttons",
        "del_delay"
    )

    def __init__(
            self,
            _id: int,
            bot: int,
            active: bool = True,
            text: str = None,
            photo: str = None,
            video: str = None,
            gif: str = None,
            buttons: str = None,
            del_delay: int = None
    ):
        self.id = _id
        self.bot = bot
        self.active = active
        self.text = text
        self.photo = photo
        self.video = video
        self.gif = gif
        self.buttons = deserialize_reply_buttons(buttons)
        self.del_delay = del_delay

    def get_tuple(self):
        return self.bot, self.active, self.text, self.photo, self.video, self.gif, serialize_reply_buttons(
            self.buttons), self.del_delay


class Greeting:
    columns = (
        "bot",
        "active",
        "text",
        "photo",
        "video",
        "gif",
        "buttons",
        "send_delay",
        "del_delay"
    )

    def __init__(
            self,
            _id: int,
            bot: int,
            active: bool = False,
            text: str = None,
            photo: str = None,
            video: str = None,
            gif: str = None,
            buttons: str = None,
            send_delay: int = None,
            del_delay: int = None
    ):
        self.id = _id
        self.bot = bot
        self.active = active
        self.text = text
        self.photo = photo
        self.video = video
        self.gif = gif
        self.buttons = deserialize_buttons(buttons)
        self.send_delay = send_delay
        self.del_delay = del_delay

    def get_tuple(self):
        return (
            self.bot,
            self.active,
            self.text,
            self.photo,
            self.video,
            self.gif,
            serialize_buttons(self.buttons),
            self.send_delay,
            self.del_delay
        )


class Mail:
    columns = (
        "sender",
        "bot",
        "active",
        "text",
        "photo",
        "video",
        "gif",
        "buttons",
        "send_dt",
        "del_dt",
        "status",
        "sent_num",
        "blocked_num",
        "error_num",
        "file_id",
        "multi_mail",
        "start_time",
        "duration"
    )

    def __init__(
            self,
            _id: int,
            sender: int,
            bot: int,
            active: bool = False,
            text: str = None,
            photo: str = None,
            video: str = None,
            gif: str = None,
            buttons: str = None,
            sched_dt: str = None,
            del_dt: str = None,
            status: bool = False,
            sent_num: int = 0,
            blocked_num: int = 0,
            error_num: int = 0,
            file_id: str = None,
            multi_mail: int = None,
            start_time: int = None,
            duration: str = None
    ):
        self.id = _id
        self.sender = sender
        self.bot = bot
        self.active = active
        self.text = text
        self.photo = photo
        self.video = video
        self.gif = gif
        self.buttons = deserialize_buttons(buttons)
        self.send_dt = datetime.strptime(sched_dt, DT_FORMAT) if sched_dt else None
        self.del_dt = datetime.strptime(del_dt, DT_FORMAT) if del_dt else None
        self.status = status
        self.sent_num = sent_num
        self.blocked_num = blocked_num
        self.error_num = error_num
        self.file_id = file_id
        self.multi_mail = multi_mail
        self.start_time = start_time
        self.duration = duration

    def get_tuple(self):
        return (
            self.sender,
            self.bot,
            self.active,
            self.text,
            self.photo,
            self.video,
            self.gif,
            serialize_buttons(self.buttons),
            self.send_dt.strftime(DT_FORMAT) if self.send_dt else None,
            self.del_dt.strftime(DT_FORMAT) if self.del_dt else None,
            self.status,
            self.sent_num,
            self.blocked_num,
            self.error_num,
            self.file_id,
            self.multi_mail,
            self.start_time,
            self.duration
        )


class AdminNotification:
    columns = (
        "text",
        "photo",
        "video",
        "gif"
    )

    def __init__(
            self,
            _id: int,
            text: str = None,
            photo: str = None,
            video: str = None,
            gif: str = None,
    ):
        self.id = _id
        self.text = text
        self.photo = photo
        self.video = video
        self.gif = gif

    def get_tuple(self):
        return (
            self.text,
            self.photo,
            self.video,
            self.gif
        )


class Purge:
    columns = (
        "sender",
        "bot",
        "active",
        "sched_dt",
        "status",
        "deleted_msgs_num",
        "cleared_chats_num",
        "error_num",
        "mail_id",
        "start_time",
        "duration"
    )

    def __init__(
            self,
            _id: int,
            sender: int,
            bot: int,
            active: bool = False,
            sched_dt: str = None,
            status: bool = False,
            deleted_msgs_num: int = 0,
            cleared_chats_num: int = 0,
            error_num: int = 0,
            mail_id: int = None,
            start_time: int = None,
            duration: str = None
    ):
        self.id = _id
        self.sender = sender
        self.bot = bot
        self.active = active
        self.sched_dt = datetime.strptime(sched_dt, DT_FORMAT) if sched_dt else None
        self.status = status
        self.deleted_msgs_num = deleted_msgs_num
        self.cleared_chats_num = cleared_chats_num
        self.error_num = error_num
        self.mail_id = mail_id if mail_id else None
        self.start_time = start_time
        self.duration = duration

    def get_tuple(self):
        return (
            self.sender,
            self.bot,
            self.active,
            self.sched_dt.strftime(DT_FORMAT) if self.sched_dt else None,
            self.status,
            self.deleted_msgs_num,
            self.cleared_chats_num,
            self.error_num,
            self.mail_id,
            self.start_time,
            self.duration
        )


class Msg:
    columns = (
        "id",
        "user",
        "bot",
        "mail_id",
    )

    def __init__(self, _id: int, user: int, bot: int, mail_id: int = 0):
        self.id = _id
        self.user = user
        self.bot = bot
        self.mail_id = mail_id

    def get_tuple(self):
        return self.id, self.user, self.bot, self.mail_id


class MailsQueue:
    columns = (
        "bot",
        "user",
        "mail_id",
        "admin_status"
    )

    def __init__(
            self,
            _id: int,
            bot: int,
            user: int,
            mail_id: int,
            admin_status: bool = False,
    ):
        self.id = _id
        self.bot = bot
        self.user = user
        self.mail_id = mail_id
        self.admin_status = admin_status

    def get_tuple(self):
        return (
            self.bot,
            self.user,
            self.mail_id,
            self.admin_status,
        )


class Settings:

    def __init__(self, data: int):
        self.data = data

    def read_bit(self, index: int) -> bool:
        mask = 1 << index
        bit = (self.data & mask) >> index
        return bool(bit)

    def write_bit(self, index: int, value: bool) -> None:
        mask = 1 << index
        cleared_integer = self.data & ~mask
        self.data = cleared_integer | (int(value) << index)

    def get_autoapprove(self) -> bool:
        return self.read_bit(0)

    def set_autoapprove(self, value: bool) -> None:
        self.write_bit(0, value)

    def get_users_collect(self) -> bool:
        return self.read_bit(1)

    def set_users_collect(self, value: bool) -> None:
        self.write_bit(1, value)

    def get_force_captcha(self) -> bool:
        return self.read_bit(2)

    def set_force_captcha(self, value: bool) -> None:
        self.write_bit(2, value)


class MultiMail:
    columns = (
        "sender",
        "bots",
        "active",
        "text",
        "photo",
        "video",
        "gif",
        "buttons",
        "send_dt",
        "del_dt",
        "status",
        "sent_num",
        "blocked_num",
        "error_num"
    )

    def __init__(
            self,
            _id: int,
            sender: int,
            bots: str = "",
            active: bool = False,
            text: str = None,
            photo: str = None,
            video: str = None,
            gif: str = None,
            buttons: str = None,
            sched_dt: str = None,
            del_dt: str = None,
            status: bool = False,
            sent_num: int = 0,
            blocked_num: int = 0,
            error_num: int = 0
    ):
        self.id = _id
        self.sender = sender
        self.bots = []
        for bot_id in bots.split(" "):
            if bot_id != "":
                self.bots.append(int(bot_id))
        self.active = active
        self.text = text
        self.photo = photo
        self.video = video
        self.gif = gif
        self.buttons = deserialize_buttons(buttons)
        self.send_dt = datetime.strptime(sched_dt, DT_FORMAT) if sched_dt else None
        self.del_dt = datetime.strptime(del_dt, DT_FORMAT) if del_dt else None
        self.status = status
        self.sent_num = sent_num
        self.blocked_num = blocked_num
        self.error_num = error_num

    def get_tuple(self):
        return (
            self.sender,
            " ".join([str(bot) for bot in self.bots]),
            self.active,
            self.text,
            self.photo,
            self.video,
            self.gif,
            serialize_buttons(self.buttons),
            self.send_dt.strftime(DT_FORMAT) if self.send_dt else None,
            self.del_dt.strftime(DT_FORMAT) if self.del_dt else None,
            self.status,
            self.sent_num,
            self.blocked_num,
            self.error_num
        )
