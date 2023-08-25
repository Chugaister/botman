from data import models

from html.parser import HTMLParser
import html
class CustomHTMLParser(HTMLParser):
    def init(self):
        super().init()
        self.result = []

    def handle_starttag(self, tag, attrs):
        self.result.append(f"<{tag}>")

    def handle_endtag(self, tag):
        self.result.append(f"</{tag}>")

    def handle_data(self, data):
        self.result.append(html.escape(data))

def replace_invalid_elements(html_markup):
    parser = CustomHTMLParser()
    parser.feed(html_markup)
    return ''.join(parser.result)




def gen_dynamic_text(text: str, user: models.User) -> str:
    any = user.first_name if user.first_name else user.username
    text = text.replace("[username]", str(user.username))
    text = text.replace("[first_name]", str(user.first_name))
    text = text.replace("[last_name]", str(user.last_name))
    text = text.replace("[any]", any)
    return text
