#!/usr/bin/env python3
import datetime
import logging
import os
import sys
import configurator

sys.path.insert(1, (os.path.dirname(os.path.dirname(__file__))))
from functools import reduce
from discord.ext import commands
from src import tkfinder, util
from src.resources import embed, const
from github import Github
from discord_components import DiscordComponents

base_path = os.path.dirname(__file__)
config = configurator.Configurator(os.path.abspath(os.path.join(base_path, "resources", "config.json")))
prefix = '§'
description = 'The premier Tekken 7 Frame bot, made by Baikonur#4927, continued by Tib#1303'
bot = commands.Bot(command_prefix=prefix, description=description)
buttons = DiscordComponents(bot)

# Set logger to log errors
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

logfile_directory = os.path.abspath(os.path.join(base_path, "..", "log"))
logfile_path = logfile_directory + "\\logfile.log"

# Create logfile if not exists
if not os.path.exists(logfile_directory):
    os.makedirs(logfile_directory)

if not os.path.isfile(logfile_path):
    open(logfile_path, "w")

file_handler = logging.FileHandler(logfile_path)
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

discord_token = config.read_config()['DISCORD_TOKEN']
feedback_channel_id = config.read_config()['FEEDBACK_CHANNEL_ID']
github_token = config.read_config()['GITHUB_TOKEN']
gh = Github(login_or_token=github_token)


@bot.event
async def on_ready():
    print(datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.author.id == bot.user.id and user.id != bot.user.id and reaction.count < 3:
        item_index = const.EMOJI_LIST.index(reaction.emoji) if reaction.emoji in const.EMOJI_LIST else -1

        if item_index > -1:
            delete_after = config.get_auto_delete_duration(reaction.message.channel.id)
            content = reaction.message.embeds[0].description.replace('\n', '\\n').split("\\n")
            character_name = util.get_character_name_from_content(content)
            character = tkfinder.get_character_detail(character_name)
            move_list = util.get_moves_from_content(content)
            move = move_list[item_index]

            result = util.display_moves_by_input(character, move)
            if "components" in result:
                await reaction.message.channel.send(embed=result["embed"], delete_after=delete_after,
                                                    components=result["components"])
            else:
                await reaction.message.channel.send(embed=result["embed"], delete_after=delete_after)
            await reaction.remove(bot.user)


@bot.event
async def on_message(message):
    """This has the main functionality of the bot. It has a lot of
    things that would be better suited elsewhere but I don't know
    if I'm going to change it."""
    try:
        channel = message.channel
        author_name = str.strip(str(message.author))
        author_id=message.author.id

        if author_name in const.BLACKLIST or author_id in const.ID_BLACKLIST:
            return
        else:
            if message.content.startswith('!random'):
                howMany = message.content.split(' ', 1)[1]
                await channel.send("preparing to random "+howMany+" characters for " + author_name)
                character_list = (tkfinder.generate_character_list(howMany))
                # inc = 0
                # for character in charList:
                #     inc = inc + 1
                #     await channel.send("[" + str(inc) + "] - " + character)
                result = util.display_randomized_characters(character_list, author_name)
                print("hej!")
                await channel.send(embed=result["embed"])
                print("hej!")

            elif message.content == '!maliniak':
                await channel.send("maliniak to noob")

            elif message.content == '!server-list':
                serverlist = list(map(lambda x: x.name, bot.guilds))

                serverlist.sort()
                step = 60
                for begin in range(0, len(serverlist), step):
                    end = begin + step
                    if end > len(serverlist):
                        end = len(serverlist)
                    servers = reduce(util.do_sum, serverlist[begin:end])
                    await channel.send(servers)
                msg = "Number of servers in: " + str(len(serverlist))
                await channel.send(msg)

            elif message.content == '!last-updates':
                try:
                    messages = util.get_latest_commits_messages(gh, 5)
                    result = {"embed": embed.success_embed(messages)}
                except Exception as e:
                    result = {"embed": embed.error_embed(e)}
                await channel.send(embed=result["embed"])

            elif message.content.startswith("!auto-delete"):

                if message.author.permissions_in(channel).manage_messages:
                    duration = message.content.split(' ', 1)[1]
                    if duration.isdigit() or duration == "-1":
                        config.save_auto_delete_duration(channel.id, duration)
                        result = {"embed": embed.success_embed("Saved")}
                    else:
                        result = {"embed": embed.error_embed("Duration needs to be a number in seconds")}
                else:
                    result = {"embed": embed.error_embed("You need the permission <manage_messages> to do that")}

                await channel.send(embed=result["embed"])

            elif message.content.startswith('!clear-messages'):
                # delete x of the bot last messages
                number = int(message.content.split(' ', 1)[1])
                messages = []
                async for m in channel.history(limit=100):
                    if m.author == bot.user:
                        messages.append(m)

                to_delete = [message]
                for i in range(number):
                    to_delete.append(messages[i])

                await channel.delete_messages(to_delete)

            elif message.content == '!help':
                await channel.send(embed=embed.help_embed())

            elif message.content.startswith('?feedback'):

                print(message.content)
                print(author_name)
                print(const.BLACKLIST)
                print(author_name in const.BLACKLIST)
                print(author_id in const.ID_BLACKLIST)

                today = datetime.datetime.now()
                age = today - message.author.created_at
                if age.days < 120:
                    return
                else:
                    user_message = message.content.split(' ', 1)[1].replace("\n", "")
                    server_name = str(message.channel.guild)
                    feedback_channel = bot.get_channel(feedback_channel_id)
                    try:
                        feedback_message = "{} ;{} ;{} ;{}\n".format(str(message.author), message.author.id, server_name, user_message)
                        await feedback_channel.send(feedback_message)
                        result = {"embed": embed.success_embed("Feedback sent")}
                    except Exception as e:
                        result = {"embed": embed.error_embed("Feedback couldn't be sent caused by: " + e)}

                    await channel.send(embed=result["embed"])

            elif message.content.startswith('!') and len(message.content[1:].split(' ', 1)) > 1:

                delete_after = config.get_auto_delete_duration(channel.id)
                user_message_list = message.content[1:].split(' ', 1)

                original_name = user_message_list[0].lower()
                original_move = user_message_list[1]

                character_name = tkfinder.correct_character_name(original_name)

                if character_name is not None:
                    character = tkfinder.get_character_detail(character_name)
                    move_type = util.get_move_type(original_move.lower())

                    if move_type:
                        result = util.display_moves_by_type(character, move_type)
                    else:
                        result = util.display_moves_by_input(character, original_move)
                else:
                    result = {"embed": embed.error_embed(f'Character {original_name} does not exist.')}
                    delete_after = 5
                if "components" in result:
                    bot_message = await channel.send(embed=result["embed"], delete_after=delete_after,
                                                     components=result["components"])
                else:
                    bot_message = await channel.send(embed=result["embed"], delete_after=delete_after)
                if embed.MOVE_NOT_FOUND_TITLE == bot_message.embeds[0].title:

                    content = bot_message.embeds[0].description.replace('\n', '\\n').split("\\n")
                    movelist = util.get_moves_from_content(content)
                    for i in range(len(movelist)):
                        await bot_message.add_reaction(const.EMOJI_LIST[i])

            await bot.process_commands(message)

    except Exception as e:
        time_now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        error_msg = f'{time_now} | Message: {message.content} from {message.author.name} in {message.channel.guild.name}.' \
                    f'\n Error: {e}'
        #print(error_msg)
        logger.error(error_msg)


bot.run(discord_token)
