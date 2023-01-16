import re
import socket
import string
import subprocess
import sys
import threading
import asyncio
import os

import discord
import mcpi.minecraft as minecraft
from discord.ext import tasks

intents = discord.Intents(messages=True, message_content=True)

### CONFIG ###
logFile = "/home/pi/server/log.log"
token = "TOKEN HERE"
channelId = 1234567890
serverName = "SERVER NAME"
serverSoftware = "Minecraft Pi: Reborn Server"
world = "world1"
owner = "StevePi"
client = discord.Client(activity = discord.Game(name = ("on "+serverName)), intents=intents)
### END CONFIG ##

# Groups username
joinRe = r"\[INFO\]\: (.*) Has Joined \(IP: \d+\.\d+\.\d+\.\d+\)"
# Groups username and message
chatRe = r"\[CHAT\]\: (<.*?> )(.*)"
# Groups username
deathRe = r"\[CHAT\]\: (.*?) has died"
# Groups username
leaveRe = r"\[CHAT\]\: (.*?) disconnected from the game"
mcpi = minecraft.Minecraft.create()

def getOnlinePlayers():
    try:
        return len(mcpi.getPlayerEntityIds())
    except:
        return 0

def command(message):
    if message[0] == '/':
        if message == '/help':
            mcpi.postToChat('All avaliable commands: /help, /ping, /discord, /rules, /players, /serverinfo')
            return
        if message == '/ping':
            mcpi.postToChat('Pong!')
            return
        if message == '/discord':
            mcpi.postToChat('The Discord is linked here: https://discord.gg/j8CK66Fq6G')
            return
        elif message == '/rules':
            mcpi.postToChat('You are expected to read the full rules linked in the Discord server, if you haven\'t already.')
            mcpi.postToChat('In short: remain respectful, and do not spam, steal, cheat, fly, hack, dupe or post NSFW.')
            mcpi.postToChat('Use /discord to find the Discord link.')
            return
        elif message == '/players':
            if getOnlinePlayers() == 1:
                mcpi.postToChat('There is 1 player online.')
            else:
                mcpi.postToChat('There are ' + str(getOnlinePlayers()) + ' players online.')
            return
        elif message == '/serverinfo':
            mcpi.postToChat(serverName + ', ' + world)
            mcpi.postToChat('Owner is: ' + owner)
            mcpi.postToChat('Running server software: ' + serverSoftware + ' for MCPI & MCPE.')
        else:
            mcpi.postToChat('Unknown command: ' + message)
            return

def joinMessage():
    mcpi.postToChat('Welcome to the official place for the original Pi and Pocket experience! - ThePIs')
    mcpi.postToChat('You are expected to read the full /rules. You can also type /discord to join the server, and /help for all avaliable commands.')
    mcpi.postToChat('Have fun!')

@client.event
async def on_ready():
    print("Now playing on "+serverName)

@client.event
async def on_message(msg):
    """Takes discord messages and outputs them in MCPI"""
    global lastMsg
    if msg.author == client.user or msg.channel.id != channelId:
        return
    # Filters out non-ascii chars
    messageContent = "".join([i for i in msg.content if i in string.printable])
    author = "".join([i for i in str(msg.author) if i in string.printable])
    mcpi.postToChat("[" + author + "] " + messageContent)

async def sendToDiscord(msg):
    chat = re.findall(chatRe, msg)
    if len(chat) == 1:
        if chat[0][0] != '<'+serverName+'> ': message = "```" + chat[0][0] + chat[0][1] + "```"; command(chat[0][1])
        else: return
    else:
        join = re.findall(joinRe, msg)
        if len(join) == 1:
            message = (
                "```ansi\n\033[33m"
                + join[0]
                + " joined the game, bringing the player count to "
                + str(getOnlinePlayers())
                + "/20\n```"
            )

            joinMessage()
        else:
            death = re.findall(deathRe, msg)
            if len(death) == 1:
                message = "```ansi\n\033[33m"+death[0] + " has died```"  # )
            else:
                leave = re.findall(leaveRe, msg)
                if len(leave) == 1:
                    message = (
                        "```ansi\n\033[33m"
                        + leave[0]
                        + " disconnected from the game, leaving the player count at "
                        + str(getOnlinePlayers())
                        + "/20\n```"
                    )
                else: return
    # Add zwj to @ to prevent pings
    message = message.replace("@", "@\u200b")
    channel = client.get_channel(channelId)
    if channel != None:
        await channel.send(message)

async def main():
    global lastMsg
    lastMsg = ""
    while True:
        await asyncio.sleep(0.2)
        oldLastMsg = lastMsg
        lastMsg = subprocess.check_output(["bash", "-c", "grep -v '[INFO]: Saving Game' "+logFile+" | grep -Ev '\[CHAT\]\: .* joined the game' | tail -n1"]).decode('utf-8')
        if lastMsg != oldLastMsg:
            await sendToDiscord(lastMsg)

asyncio.get_event_loop().create_task(main())
client.run(token)
