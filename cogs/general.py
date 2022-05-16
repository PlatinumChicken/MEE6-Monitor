from click import option
import discord
from discord.ext import commands
from mee6_py_api import API
import json
from discord.ext.commands import has_permissions, CheckFailure
import motor.motor_asyncio
import typing
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option
from numpy import require
import os
from dotenv import load_dotenv

load_dotenv()

class General(commands.Cog, description="General Commands"):

  def __init__(self, client):
    KEY=os.getenv("KEY")
    self.client=client
    self.cluster=motor.motor_asyncio.AsyncIOMotorClient(KEY)

  @cog_ext.cog_slash(
    name='ping',
    description='Get ping',
  )
  async def ping(self, ctx:SlashContext):
    await ctx.send(f"Pong: {round(self.client.latency*1000)}ms")

def setup(client):
  client.add_cog(General(client))
  