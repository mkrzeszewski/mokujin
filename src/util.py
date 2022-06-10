import datetime

from src import tkfinder
from src.resources import const, embed
from discord_components import Button, ActionRow

def display_randomized_characters(characters, player):
    print("hej - in utils!")
    result = {}
    result["embed"] = embed.character_randomized_embed(characters, player)
    print("hej - exiting utils!")
    return result

def get_character_name_from_content(content):
    first_line = content[0]
    return first_line.split("Similar moves from ")[1]


def get_moves_from_content(content):
    content.pop(0)
    for i in range(len(content)):
        content[i] = content[i][7:]
    return content


def get_latest_commits_messages(gh, numbers: int):
    commits = gh.get_user().get_repo("mokujin").get_commits()
    message = ""
    for i in range(0, numbers, 1):
        new_date = datetime.datetime.strptime(str(commits[i].commit.committer.date), '%Y-%m-%d %H:%M:%S').strftime(
            '%Y-%m-%d')
        message += f'{commits[i].commit.message} on {new_date}\n'
    return message


def get_move_type(original_move: str):
    for k in const.MOVE_TYPES.keys():
        if original_move in const.MOVE_TYPES[k]:
            return k


def do_sum(x1, x2):
    return x1 + "\n" + x2


def display_moves_by_type(character, move_type):
    move_list = tkfinder.get_by_move_type(character, move_type)
    result = {}
    if len(move_list) < 1:
        result["embed"] = embed.error_embed(
            'No ' + move_type.lower() + ' for ' + character['proper_name'])
    elif len(move_list) == 1:
        character_move = tkfinder.get_move(character, move_list[0])
        if character_move and "Tags" in character_move:
            result["components"] = ActionRow(create_components(character_move))
        result["embed"] = embed.move_embed(character, character_move)
    elif len(move_list) > 1:
        result["embed"] = embed.move_list_embed(character, move_list, move_type)

    return result


def create_components(character_move):
    tags = character_move["Tags"]
    components = []
    for tag in tags:
        if tag == "Rage Art" or tag == "Rage Drive":
            components.append(Button(label=tag, disabled=True, style=4))
        else:
            components.append(Button(label=tag, disabled=True, style=3))
    components.sort(key=lambda val: const.SORT_ORDER[val.label])
    return components


def display_moves_by_input(character, original_move):
    character_move = tkfinder.get_move(character, original_move)
    character_name = character["name"]
    result = {}
    if character_move is not None:
        result["embed"] = embed.move_embed(character, character_move)

    else:
        generic_move = tkfinder.get_generic_move(original_move)
        if generic_move is not None:
            generic_character = tkfinder.get_character_detail("generic")
            result["embed"] = embed.move_embed(generic_character, generic_move)
        else:
            similar_moves = tkfinder.get_similar_moves(original_move, character_name)
            result["embed"] = embed.similar_moves_embed(similar_moves, character_name)
    if character_move and "Tags" in character_move and len(character_move["Tags"]) > 0:
        result["components"] = ActionRow(create_components(character_move))

    return result
