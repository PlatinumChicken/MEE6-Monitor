import discord
from discord.ext import commands
from mee6_py_api import API
from discord.ext.commands import has_permissions, CheckFailure
import motor.motor_asyncio
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option
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
  
  @cog_ext.cog_slash(
    name='whois',
    description='Shows xp stats of user',
    options=[
      create_option(
        name='user',
        description='Choose user',
        required=True,
        option_type=6
      )
    ]
  )
  async def whois(self, ctx:SlashContext, user:str):
    db=self.cluster.users
    collection=db[str(ctx.guild.id)]
    person=await collection.find_one({"_id":str(user.id)})
    await ctx.send(f"{user}'s nick is {person['name']}")

def setup(client):
  client.add_cog(General(client))
