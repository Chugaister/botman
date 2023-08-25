from data import models
import re


def clean_string_double_tags(input_string: str):
    pattern = r'<[^>]+>'
    words_with_angle_brackets = re.findall(pattern, input_string)
    matching_tags = []
    for word in words_with_angle_brackets:
        
        tag_name = word.split(' ')[0].strip('<').strip('>').strip('/')
        closing_tag_pattern = fr'</{tag_name}>'
        
        if re.search(closing_tag_pattern, input_string):
            matching_tags.append(word)
            words_with_angle_brackets.remove(word)
            words_with_angle_brackets.remove(closing_tag_pattern)
    for word in words_with_angle_brackets:
        if '/' in word:
            if word[-2] == '/':
                words_with_angle_brackets.remove(word)
    string_arr =input_string.split(" ")
    for index, word in enumerate(string_arr):
        for tag in words_with_angle_brackets:
            if tag in word:
                string_arr[index] = word.replace('<', '').replace('>', '')
    return ' '.join(string_arr)

def clean_string_single_tag(input_string: str):
    string_arr = input_string.split(' ')
    for index, word in enumerate(string_arr):
        if ('<' in word) != ('>' in word):
            string_arr[index] = word.replace('<', '') if '<' in word else word.replace('>')
    return ' '.join(string_arr)

def clean_string(input_string: str):
    cleaned1 = clean_string_single_tag(input_string)
    cleaned2 = clean_string_double_tags(cleaned1)
    return cleaned2

def gen_dynamic_text(text: str, user: models.User) -> str:
    any = user.first_name if user.first_name else user.username
    text = text.replace("[username]", clean_string(str(user.username)))
    text = text.replace("[first_name]", clean_string(str(user.first_name)))
    text = text.replace("[last_name]", clean_string(str(user.last_name)))
    text = text.replace("[any]", clean_string(str(any)))
    return text
