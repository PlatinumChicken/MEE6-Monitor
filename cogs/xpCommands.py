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
from dotenv import load_dotenv
import os
import numpy as np
from scipy import stats
from datetime import datetime

load_dotenv()

class XpCommands(commands.Cog, description="Commands relating to MEE6 levelling system"):

  def __init__(self, client):
    KEY=os.getenv("KEY")
    self.client=client
    self.cluster=motor.motor_asyncio.AsyncIOMotorClient(KEY)
  
  @cog_ext.cog_slash(
    name="toggleShowSelf",
    description="Toggle whether you show up on xp leaderboard or not",
    options=[
      create_option(
        name='toggle',
        description='Turn on or off',
        required=True,
        option_type=5
      )
    ]
  )
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def toggleShowSelf(self, ctx:SlashContext, toggle: bool):
    db=self.cluster.users
    collection=db[str(ctx.guild.id)]
    filterUser={'_id':str(ctx.author.id)}
    newValue={'$set': {'excluded':toggle}}
    x=await collection.update_one(filterUser, newValue)
    await ctx.send(f"Set `excluded` value to `{toggle}`")
    
  @cog_ext.cog_slash(
    name='leaderboardLength',
    description='Change length of xp leaderboard',
    options=[
      create_option(
        name='length',
        description='Set leaderboard length',
        required=True,
        option_type=4
      )
    ]
  )
  @commands.has_permissions(administrator=True)
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def leaderboardLength(self, ctx: SlashContext, length: int):
    if length>100:
      await ctx.send("Length is too high")
    else:
      db=self.cluster.configs
      collection=db[str(ctx.guild.id)]
      filterGuild={}
      newValue={'$set': {'LeaderboardLength':length}}
      x=await collection.update_one(filterGuild, newValue)
      await ctx.send(f"Changed leaderboard length to {length}")

  @cog_ext.cog_slash(
    name='leaderboardChannel',
    description='Set channel xp leaderboard sends in',
    options=[
      create_option(
        name='channel',
        description='Set channel',
        required=True,
        option_type=7
      )
    ]
  )
  @commands.has_permissions(administrator=True)
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def leaderboardChannel(self, ctx, channel:discord.TextChannel):
    db=self.cluster.configs
    collection=db[str(ctx.guild.id)]
    filterGuild={}
    newValue={'$set': {'CHANNELID':channel.id}}
    x=await collection.update_one(filterGuild, newValue)
    await ctx.send(f"Set leaderboard channel to {channel}")

  @cog_ext.cog_slash(
    name='toggleLeaderboard',
    description='Turn certain parts of leaderboard on and off',
    options=[
      create_option(
        name='type',
        description='Specify type',
        required=True,
        option_type=3,
        choices=[
          create_choice(
            name='hourly',
            value='hourly'
          ),
          create_choice(
            name='daily',
            value='daily'
          ),
          create_choice(
            name='daily',
            value='daily'
          ),
          create_choice(
            name='weekly',
            value='weekly'
          ),
          create_choice(
            name='catch',
            value='catch'
          ),
          create_choice(
            name='all',
            value='all'
          )
        ]
      ),
      create_option(
        name='toggle',
        description='Turn on or off',
        required=True,
        option_type=5
      )
    ]
  )
  @commands.has_permissions(administrator=True)
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def toggleLeaderboard(self, ctx: SlashContext, type:str, toggle: bool):
    db=self.cluster.configs
    collection=db[str(ctx.guild.id)]
    filterGuild={}
    newValue={'$set': {str(type.lower()):toggle}}
    x=await collection.update_one(filterGuild, newValue)
    await ctx.send(f"Set leaderboard `{type}` value to `{toggle}`")

  @cog_ext.cog_slash(
    name='changeNick',
    description='Change displayed username on leaderboard and commands',
    options=[
      create_option(
        name='nickname',
        description='Change nick',
        required=True,
        option_type=3
      )
    ]
  )
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def changeNick(self, ctx: SlashContext, nickname:str):
    db=self.cluster.users
    collection=db[str(ctx.guild.id)]
    person=await collection.find_one({"_id":str(ctx.author.id)})
    await ctx.send(f"Assigned nickname '{str(nickname)}'")
    filterUser={'_id':str(ctx.author.id)}
    newValue={'$set': {'name':str(nickname)}}
    x=await collection.update_one(filterUser, newValue)

  @cog_ext.cog_slash(
    name='getxp',
    description='Get amount of xp',
    options=[
      create_option(
        name='type',
        description='Choose type of xp',
        required=True,
        option_type=3,
        choices=[
          create_choice(
            name='hourly',
            value='hourly'
          ),
          create_choice(
            name='daily',
            value='daily'
          ),
          create_choice(
            name='daily',
            value='daily'
          ),
          create_choice(
            name='weekly',
            value='weekly'
          ),
          create_choice(
            name='total',
            value='total'
          )
        ]
      ),
      create_option(
        name='user',
        description='Choose user',
        required=False,
        option_type=6
      )
    ]
  )
  @commands.cooldown(1, 10, commands.BucketType.user)
  async def getxp(self, ctx: SlashContext, type: str, user: str = None): 
    db=self.cluster.users
    collection=db[str(ctx.guild.id)]
    if user:
      person=await collection.find_one({"_id":str(user.id)})
    else:
      person=await collection.find_one({"_id":str(ctx.author.id)})
    mee6API = API(ctx.guild.id)
    if type=='hourly':
      if user:
        try:
          xp = await mee6API.levels.get_user_xp(user.id, dont_use_cache=True)
          await ctx.send(f"{person['name']}'s hourly xp is {xp-person['xplist'][-1]}")
        except:
          await ctx.send("Error, try again later")
      else:
        try:
          xp = await mee6API.levels.get_user_xp(ctx.author.id, dont_use_cache=True)
          await ctx.send(f"Your hourly xp is {xp-person['xplist'][-1]}")
        except:
          await ctx.send("Error, try again later")
    elif type=='daily':
      if user:
        try:
          xp = await mee6API.levels.get_user_xp(user.id, dont_use_cache=True)
          await ctx.send(f"{person['name']}'s daily xp is {xp-person['xplist'][-24]}")
        except:
          await ctx.send("Error, try again later")
      else:
        try:
          xp = await mee6API.levels.get_user_xp(ctx.author.id, dont_use_cache=True)
          await ctx.send(f"Your daily xp is {xp-person['xplist'][-24]}")
        except:
          await ctx.send("Error, try again later")
    elif type=='weekly':
      if user:
        try:
          xp = await mee6API.levels.get_user_xp(user.id, dont_use_cache=True)
          await ctx.send(f"{person['name']}'s weekly xp is {xp-person['xplist'][-168]}")
        except:
          await ctx.send("Error, try again later")
      else:
        try:
          xp = await mee6API.levels.get_user_xp(ctx.author.id, dont_use_cache=True)
          await ctx.send(f"Your weekly xp is {xp-person['xplist'][-168]}")
        except:
          await ctx.send("Error, try again later")
    elif type=='total':
      if user:
        try:
          xp = await mee6API.levels.get_user_xp(user.id,dont_use_cache=True)
          await ctx.send(f"{person['name']}'s total xp is {xp}")
        except:
          await ctx.send("Error, try again later")
      else:
        try:
          xp = await mee6API.levels.get_user_xp(ctx.author.id, dont_use_cache=True)
          await ctx.send(f"Your total xp is {xp}")
        except:
          await ctx.send("Error, try again later")

  @cog_ext.cog_slash(
    name='stats',
    description='Shows xp stats of user',
    options=[
      create_option(
        name='user',
        description='Choose user',
        required=False,
        option_type=6
      )
    ]
  )
  async def stats(self, ctx:SlashContext, user:str=None):
    mee6API=API(ctx.guild.id)
    db=self.cluster.users
    collection=db[str(ctx.guild.id)]
    people=[]
    async for x in collection.find():
      people.append(x)
    people=sorted(people, key=lambda d: d['totalxp'], reverse=True)
    if user:
      person=await collection.find_one({"_id":str(user.id)})
      index=next((index for (index, d) in enumerate(people) if d["_id"] == str(user.id)), None)
    else:
      person=await collection.find_one({"_id":str(ctx.author.id)})
      index=next((index for (index, d) in enumerate(people) if d["_id"] == str(ctx.author.id)), None)+1
    if user:
      pfp=user.avatar_url
      details=await mee6API.levels.get_user_details(user.id)
    else:
      pfp=ctx.author.avatar_url
      details=await mee6API.levels.get_user_details(ctx.author.id)
    embed=discord.Embed(title=f"Stats of {person['name']}", color=discord.Color.blue())
    embed.set_thumbnail(url=pfp)
    embed.add_field(
      name="General",
      value=f"Total xp is {details['xp']}\nLevel is {details['level']}\nRanked {index} out of {len(people)} people",
      inline=False
    )
    try:
      hourlyxpmean=np.mean(person['hourlyxp'])
      hourlyxpmedian=np.median(person['hourlyxp'])
      hourlyxpmode=stats.mode(person['hourlyxp'])
      embed.add_field(
        name='Hourly XP Stats', 
        value=f"Hourly XP mean is {round(hourlyxpmean, 2)}\nHourly XP median is {hourlyxpmedian}\nHourly XP mode is {hourlyxpmode.mode[0]} with a count of {hourlyxpmode.count[0]}",
        inline=True
        )
    except:
      embed.add_field(
        name='Hourly XP Stats', 
        value=f"Not enough information",
        inline=True
        )
    try:
      dailyxpmean=np.mean(person['dailyxp'])
      dailyxpmedian=np.median(person['dailyxp'])
      dailyxpmode=stats.mode(person['dailyxp'])
      embed.add_field(
        name='Daily XP Stats', 
        value=f"Daily XP mean is {round(dailyxpmean, 2)}\nDaily XP median is {dailyxpmedian}\nDaily XP mode is {dailyxpmode.mode[0]} with a count of {dailyxpmode.count[0]}",
        inline=True
        )
    except:
      embed.add_field(
        name='Daily XP Stats', 
        value=f"Not enough information",
        inline=True
        )
    try:
      weeklyxpmean=np.mean(person['weeklyxp'])
      weeklyxpmedian=np.median(person['weeklyxp'])
      weeklyxpmode=stats.mode(person['weeklyxp'])
      embed.add_field(
        name='Weekly XP Stats', 
        value=f"Weekly XP mean is {round(weeklyxpmean, 2)}\nWeekly XP median is {weeklyxpmedian}\nWeekly XP mode is {weeklyxpmode.mode[0]} with a count of {weeklyxpmode.count[0]}",
        inline=True
        )
    except:
      embed.add_field(
        name='Weekly XP Stats', 
        value=f"Not enough information",
        inline=True
        )
    now=datetime.now()
    hour=int(now.strftime("%H"))-1
    hours=list(np.arange(0,24))
    hourlyxp={}
    person_hourlyxp=person['hourlyxp'][::-1]
    number=0
    for x in hours:
      hourlyxp[x]=[]
    for x in range(hour,24):
      hourlyxp[x].append(person_hourlyxp[number])
      number+=1
    while True:
      if number<len(person_hourlyxp):
        for x in hours:
          if number<len(person_hourlyxp):
            hourlyxp[x].append(person_hourlyxp[number])
            number+=1
          else:
            break
      else:
        break
    means={}
    for x in hourlyxp:
      means[x]=np.mean(hourlyxp[x])
    means=dict(sorted(means.items(), key=lambda item: item[1]))
    embed.add_field(
      name='Most Active Hour',
      value=f"{person['name']}'s most active hour is {list(means)[-1]} (UTC)",
      inline=False
    )
    await ctx.send(embed=embed)

def setup(client):
  client.add_cog(XpCommands(client))
