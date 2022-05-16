from datetime import datetime
import asyncio
from mee6_py_api import API
import discord
from discord.ext import tasks
from discord.ext import commands
import os
from pymongo import MongoClient
from discord_slash import SlashCommand
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents().all()

def get_prefix(client,message):
  KEY=os.getenv("KEY")
  cluster=MongoClient(KEY)
  collection=cluster['configs'][str(message.guild.id)]
  dict=collection.find_one()

  return dict['prefix']

client = commands.Bot(intents=intents, command_prefix = get_prefix)
slash = SlashCommand(client, sync_commands=True, override_type=True)

for filename in os.listdir('./cogs'):
  if filename.endswith('py'):
    client.load_extension(f"cogs.{filename[:-3]}")

TOKEN=os.getenv("TOKEN")
client.run(TOKEN)
