#!/usr/bin/env python3

import asyncio
import discord
import logging
import logging.handlers
import os
import shutil
import sqlite3
import time

import modules.import_ships

from discord import emoji
from discord.ext import commands
from fuzzywuzzy import fuzz

_handler = logging.handlers.WatchedFileHandler("/var/log/shrimp.log")
logging.basicConfig(handlers=[_handler], level=logging.INFO)

TOKEN_PATH = "/home/ardaedhel/bin/shrimpbot/privatekey.dsc"
CARD_IMG_PATH = "/home/ardaedhel/bin/shrimpbot/img/"
CARD_LOOKUP = "/home/ardaedhel/bin/shrimpbot/cards.txt"
ACRO_LOOKUP = "/home/ardaedhel/bin/shrimpbot/acronyms.txt"
BOT_OWNER_ID = 236683961831653376


with open(TOKEN_PATH) as t:
    BOT_TOKEN = t.read().strip()

enabled = True
cheating = False  # Changes on login to default to False
special_chars = "~`@#$%^&* ()_-+=|\\{}[]:;\"'<>,.?/!"

cardlookup = {}
with open(CARD_LOOKUP) as cardslist:
    for line in cardslist.readlines():
        filename, key = line.split(";")
        cardlookup[key.rstrip()] = os.path.join(CARD_IMG_PATH, filename)

acronym_dict = {}
with open(ACRO_LOOKUP) as acros:
    for line in acros.readlines():
        acronym, definition = line.split(";")
        acronym_dict[acronym.strip()] = definition.strip()

bot = commands.Bot(command_prefix="&")
note = discord.Game(name="'&' for definitions")


def findIn(findMe, findInMe):
    for word in findMe:
        if word.upper() in findInMe.upper():
            return True
    return False


def equalsAny(findUs, inMe):
    for word in findUs:
        if word.upper() == inMe.upper():
            return True
    return False


def searchFor(search_term, search_set, match_threshold=100):
    ratios = [
        (x, fuzz.token_set_ratio(search_term, x), fuzz.token_sort_ratio(search_term, x))
        for x in search_set
    ]
    matches = sorted(
        [r for r in ratios], key=lambda ratio: ratio[1] + ratio[2], reverse=True
    )
#    if ((int(matches[0][1] + matches[0][2])) > match_threshold) or (int(matches[0][0]) == 100):
    # logging.info(str(matches[0][1]),str(matches[0][2]))
    if ((int(matches[0][1] + matches[0][2])) > match_threshold) or (int(matches[0][1]) == 100):
        logging.info("FOUND MATCHES")
        logging.info(
            str(
                "[+] Card lookup found potential matches for {}. Top 3:".format(
                    search_term
                )
            )
        )
        logging.info(str("[+]   {}".format(str(matches[0:3]))))
        return matches
    logging.info("NO MATCHES")
    logging.info(
        str(
            "[-] Card lookup failed to find matches for {} with fuzzy lookup.".format(
                search_term
            )
        )
    )
    logging.info(str("[*]  {}".format(str(matches[0:3]))))

    return False


@bot.command()
async def list():
    """Lists every word the bot can explain."""
    i = 0
    msg = ""
    for word in acronym_dict:
        if i > 30:
            await bot.say(msg)
            i = 0
            msg = ""
        msg += "\n" + word.upper() + ": " + acronym_dict.get(word.upper(), "ERROR!")
        i += 1
    await bot.say(msg)
    await bot.say("------------------")
    await bot.say(str(len(acronym_dict)) + " words")


@bot.command()
async def status():
    """Checks the status of the bot."""
    await bot.say("Shrimpbot info:")
    await bot.say("Bot name: " + bot.user.name)
    await bot.say("Bot ID: " + str(bot.user.id))
    if enabled:
        await bot.say("The bot is enabled.")
    else:
        await bot.say("The bot is disabled.")


@bot.command()
async def toggle():
    """Toggles if the bot is allowed to explain the stuff."""
    global enabled
    enabled = not enabled
    if enabled:
        await bot.say("The bot is now enabled.")
    else:
        await bot.say("The bot is now disabled.")


@bot.event
async def on_ready():

    BOT_OWNER = bot.get_user(BOT_OWNER_ID)

    logging.info("Logged in as")
    logging.info(bot.user.name)
    logging.info(bot.user.id)
    logging.info("------")
    logging.info("Owner is")
    logging.info(BOT_OWNER.name)
    logging.info(BOT_OWNER.id)
    logging.info("------")
    logging.info("Servers using Shrimpbot")
    for guild in bot.guilds:
        logging.info(" {}".format(str(guild)))
        logging.info(" - ID: {}".format(str(guild.id)))
        if guild.id == 697833083201650689:
            await guild.leave()
            logging.info(" [!] LEFT {}".format(str(guild)))
        if guild.id != 669698762402299904: # Steel Strat Server are special snowflakes
            await guild.me.edit(nick="Shrimpbot")
    logging.info("======")

    await bot.change_presence(status=discord.Status.online, activity=note)

    # ~ await bot.edit_profile(username="ShrimpBot")


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.channel.type is not discord.ChannelType.private:

        # logging
        logging.info(
            "[{} | {} | {} | {}] {}".format(
                time.ctime(),
                message.guild,
                message.channel.name,
                message.author.name,
                message.content,
            )
        )

    # don't read our own message or do anything if not enabled
    # ONLY the dice roller should respond to other bots

    # if ((message.author.id == bot.user.id) and ("card" not in message.content)):
    #     return
    if not enabled:
        return

    # don't read any bot's messages

    if message.author.bot:
        return


    #   cardLookup(message.content,bot)
    # if findIn(["!LOOKUP", "!CARD"], message.content) and message.content.startswith(
    #     "!"
    # ):
    #     sent = False
    #     searchterm = " ".join(
    #         [x for x in message.content.split() if not x.startswith("!")]
    #     )
    #     for char in special_chars:
    #         searchterm = searchterm.replace(
    #             char, " "
    #         )  # this is super hacky, lrn2regex, scrub
    #     searchterm = searchterm.upper()
    #     logging.info("Looking for {}".format(searchterm))

    #     card_matches = searchFor(searchterm, cardlookup, match_threshold=140)

    #     # maybe return SURPRISE MOTHERFUCKER instead of Surprise Attack
    #     if searchterm == "SURPRISE ATTACK" and random.random() > 0.5:
    #         try:
    #             filepath = os.path.join(CARD_IMG_PATH, "surprisemofo.png")
    #             logging.info(
    #                 "Sending to channel {} - Surprise Motherfucker...".format(
    #                     message.channel
    #                 )
    #             )
    #             await message.channel.send(file=discord.File(filepath))
    #             sent = True
    #         except:
    #             logging.info("Surprise Motherfucker broke.")
    #     elif card_matches:
    #         # Post the image to requested channel
    #         filepath = os.path.join(CARD_IMG_PATH, str(cardlookup[card_matches[0][0]]))
    #         # logging.info("Looking in {}".format(filepath))
    #         logging.info("Sending to channel {} - {}".format(message.channel, filepath))
    #         await message.channel.send(file=discord.File(filepath))
    #         sent = True
    #     else:
    #         logging.info("Didn't find it.  Failing over to wiki search.")
    #         # logging.info(cardlookup)

    #         wikisearchterm = " ".join(
    #             [x for x in message.content.split() if not x.startswith("!")]
    #         )
    #         wiki_img_url = cardpop.autoPopulateImage(wikisearchterm)
    #         if wiki_img_url:
    #             tmp_img_path = CARD_IMG_PATH + "tmp/" + searchterm + ".png"
    #             with requests.get(wiki_img_url, stream=True) as r:
    #                 with open(tmp_img_path, "wb") as out_file:
    #                     shutil.copyfileobj(r.raw, out_file)
    #                     logging.info(
    #                         "Wiki image retrieval - {} - {}".format(
    #                             wikisearchterm, wiki_img_url
    #                         )
    #                     )

    #             logging.info(
    #                 "Sending to channel {} - {}".format(message.channel, tmp_img_path)
    #             )
    #             await message.channel.send(file=discord.File(tmp_img_path))
    #             # await bot.send_message(message.author, "I didn't have that image in my database, so I tried finding it on the Wiki.  Was this the picture you wanted?")
    #             # await bot.send_message(message.author, "[!yes/!no]")
    #             sent = True

    #     if not sent:
    #         await message.author.send(
    #             "Sorry, it doesn't look like that is in my list.  Message Ardaedhel if you think it should be.",
    #         )
    #         await message.author.send(
    #             "Please keep in mind that my search functionality is pretty rudimentary at the moment, so you might re-try using a different common name.  Generally I should recognize the full name as printed on the card, with few exceptions.",
    #         )


bot.run(BOT_TOKEN)