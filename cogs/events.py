import discord
from discord.ext import commands
from discord.ext.commands import MissingPermissions, CheckFailure
import motor.motor_asyncio
import os
import asyncio
from mee6_py_api import API
from discord.ext.commands import BucketType, CooldownMapping
from discord_slash import cog_ext, SlashContext, manage_commands
from discord.ext.commands.errors import MissingPermissions
from dotenv import load_dotenv

load_dotenv()

  
async def setupUsers(guild_id, db):
  try:
    collection=db[str(guild_id)]
    people={}
    mee6API = API(guild_id)
    leaderboard_page = await mee6API.levels.get_leaderboard_page(0)
    for x in range(len(leaderboard_page['players'])):
      people={
        '_id':leaderboard_page['players'][x]['id'],
        'name':leaderboard_page['players'][x]['username'],
        'userid':leaderboard_page['players'][x]['id'],
        'xplist':[],
        'hourlyxp':[],
        'dailyxp':[],
        'weeklyxp':[],
        'totalxp':leaderboard_page['players'][x]['xp'],
        'excluded':False
      }
      await collection.insert_one(people)
  except:
    print(f"Error in server {guild_id}")

async def setupConfig(guild_id, db):
  try:
    collection=db[str(guild_id)]
    configs={
        "_id":guild_id,
        "API": guild_id,
        "CHANNELID": 0,
        "LeaderboardLength": 0,
        "all": True,
        "hourly": True,
        "daily": True,
        "weekly": True,
        "catch": True,
        "prefix":"."
      }
    await collection.insert_one(configs)
  except:
    print(f"Error in server {guild_id}")

class Events(commands.Cog):

  def __init__(self, client):
    KEY=os.getenv("KEY")
    self.client=client
    self.cluster=motor.motor_asyncio.AsyncIOMotorClient(KEY)

  @commands.Cog.listener()
  async def on_command_error(self, ctx, error): 
    if isinstance(error, commands.CommandOnCooldown):
      jour = round(error.retry_after/86400)
      heure = round(error.retry_after/3600)
      minute = round(error.retry_after/60)
      if jour > 0:
        await ctx.send('This command has a cooldown, be sure to wait for '+str(jour)+ "day(s)")
      elif heure > 0:
        await ctx.send('This command has a cooldown, be sure to wait for '+str(heure)+ " hour(s)")
      elif minute > 0:
        await ctx.send('This command has a cooldown, be sure to wait for '+ str(minute)+" minute(s)")
      else:
        await ctx.send(f'This command has a cooldown, be sure to wait for {error.retry_after:.2f} second(s)')
    if isinstance(error, MissingPermissions):
        await ctx.send(error)

  @commands.Cog.listener()
  async def on_slash_command_error(self, ctx:SlashContext, error): 
    if isinstance(error, commands.CommandOnCooldown):
      jour = round(error.retry_after/86400)
      heure = round(error.retry_after/3600)
      minute = round(error.retry_after/60)
      if jour > 0:
        await ctx.send('This command has a cooldown, be sure to wait for '+str(jour)+ "day(s)")
      elif heure > 0:
        await ctx.send('This command has a cooldown, be sure to wait for '+str(heure)+ " hour(s)")
      elif minute > 0:
        await ctx.send('This command has a cooldown, be sure to wait for '+ str(minute)+" minute(s)")
      else:
        await ctx.send(f'This command has a cooldown, be sure to wait for {error.retry_after:.2f} second(s)')
    if isinstance(error, MissingPermissions):
        await ctx.send(f"Missing permissions: `{','.join(error.missing_perms)}`")
    print(error)

  @commands.Cog.listener()
  async def on_guild_join(self, ctx, guild):
    db=self.cluster.users
    collections= await db.list_collection_names()
    if str(guild.id) not in collections:
      await setupUsers(guild.id, db)
    db=self.cluster.configs
    collections= await db.list_collection_names()
    if str(guild.id) not in collections:
      await setupConfig(guild.id, db)

  @commands.Cog.listener()
  async def on_ready(self):
    print('Logged in as {0.user}'.format(self.client))
    await self.client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name =f".help"))
    db=self.cluster.users
    collections= await db.list_collection_names()
    for guild in self.client.guilds:
      if str(guild.id) not in collections:
        await setupUsers(guild.id, db)
    db=self.cluster.configs
    collections= await db.list_collection_names()
    for guild in self.client.guilds:
      if str(guild.id) not in collections:
        await setupConfig(guild.id, db)

def setup(client):
  client.add_cog(Events(client))
