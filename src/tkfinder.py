# -*- coding: utf-8 -*-
import json
import os

from random import randrange
from difflib import SequenceMatcher
from heapq import nlargest as _nlargest

from src.resources import const

base_path = os.path.dirname(__file__)

def generate_character_list(howMany):
    chara_misc_json = load_characters_config()
    chara_misc_json.pop()
    tempList = []
    for x in range (0, int(howMany)):
        tempVal = randrange(len(chara_misc_json))
        tempList.append(chara_misc_json[tempVal]["name"])
        del chara_misc_json[tempVal]
    return tempList


def load_characters_config():
    filepath = os.path.abspath(os.path.join(base_path, "resources", "character_misc.json"))
    with open(filepath) as chara_misc_file:
        contents = chara_misc_file.read()

    chara_misc_json = json.loads(contents)
    return chara_misc_json


def correct_character_name(alias: str):
    # check if input in dictionary or in dictionary values
    if alias in const.CHARACTER_ALIAS:
        return alias

    for key, value in const.CHARACTER_ALIAS.items():
        if alias in value:
            return key

    return None


def get_character_movelist(character):
    os.path.abspath(os.path.join(base_path, "..", "json", character.get('local_json')))
    filepath = os.path.abspath(os.path.join(base_path, "..", "json", character.get('local_json')))
    with open(filepath) as move_file:
        move_file_contents = move_file.read()
    move_json = json.loads(move_file_contents)

    return move_json


def get_commands_from(chara_name: str) -> list:
    character = get_character_detail(chara_name)
    movelist = get_character_movelist(character)
    result = []
    for move in movelist:
        result.append(move["Command"])

    return list(result)


def get_close_matches_indexes(word, possibilities, n=3, cutoff=0.6):
    """Use SequenceMatcher to return a list of the indexes of the best
    "good enough" matches. word is a sequence for which close matches
    are desired (typically a string).
    possibilities is a list of sequences against which to match word
    (typically a list of strings).
    Optional arg n (default 3) is the maximum number of close matches to
    return.  n must be > 0.
    Optional arg cutoff (default 0.6) is a float in [0, 1].  Possibilities
    that don't score at least that similar to word are ignored.
    """

    if not n > 0:
        raise ValueError("n must be > 0: %r" % (n,))
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError("cutoff must be in [0.0, 1.0]: %r" % (cutoff,))
    result = []
    s = SequenceMatcher()
    s.set_seq2(word)
    for idx, x in enumerate(possibilities):
        s.set_seq1(x)
        if s.real_quick_ratio() >= cutoff and \
                s.quick_ratio() >= cutoff and \
                s.ratio() >= cutoff:
            result.append((s.ratio(), idx))

    # Move the best scorers to head of list
    result = _nlargest(n, result)

    # Strip scores for the best n matches
    return [x for score, x in result]


def get_similar_moves(move: str, chara_name: str) -> list:
    move_list = get_commands_from(chara_name)
    moves_indexes = get_close_matches_indexes(move_simplifier(move), map(move_simplifier, move_list), 5, 0.5)

    result = []
    for index in moves_indexes:
        result.append(move_list[index])

    return result


def get_character_detail(chara_name: str) -> dict:
    """Gets character details from character_misc.json, if character exists
    returns character details as dict if exists, else None"""

    chara_misc_json = load_characters_config()
    chara_details = list(filter(lambda x: (x['name'] == chara_name), chara_misc_json))

    if chara_details:
        return chara_details[0]
    else:
        return None


def get_generic_move(move_command: str) -> dict:
    character = get_character_detail("generic")
    move = get_move(character, move_command)
    return move


def get_move(character: dict, move_command: str) -> dict:
    """Gets move from local_json, if exists
    returns move if exists, else None"""

    movelist = get_character_movelist(character)

    move = list(filter(lambda x: (move_simplifier(x['Command'].replace("\\",""))
                                  == move_simplifier(move_command)), movelist))
    if not move:
        move = list(filter(lambda x: (is_command_in_alias(move_command, x)), movelist))

    if move:
        move[0]['Command'] = move[0]['Command'].replace("\\","")
        return move[0]
    else:
        return None


def get_by_move_type(character: dict, move_type: str) -> list:
    """Gets a list of moves that match move_type from local_json
    returns a list of move Commands if finds match(es), else empty list"""

    move_json = get_character_movelist(character)
    moves = list(filter(lambda x: (move_type in x["Tags"]), move_json))

    if moves:
        move_list = []
        for move in moves:
            move_list.append(move['Command'])
        return list(set(move_list))
    else:
        return []


def is_command_in_alias(command: str, item: dict) -> bool:
    if 'Alias' in item:
        aliases = item['Alias']
        for alias in aliases:
            if move_simplifier(command) == move_simplifier(alias):
                return True
    return False


def move_simplifier(move_input) -> str:
    """Removes bells and whistles from the move_input"""
    short_input = move_input.strip().lower()
    short_input = short_input.replace("in rage", "")

    for old, new in const.REPLACE.items():
        short_input = short_input.replace(old, new)

    # cd works, ewgf doesn't, for some reason
    if short_input[:2].lower() == 'cd' and short_input[:3].lower() != 'cds':
        short_input = short_input.lower().replace('cd', 'fnddf')
    if short_input[:2].lower() == 'wr':
        short_input = short_input.lower().replace('wr', 'fff')
    return short_input
