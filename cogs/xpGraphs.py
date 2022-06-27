import discord
from discord.ext import commands
from mee6_py_api import API
import os
import matplotlib.pyplot as plt
import numpy as np
import motor.motor_asyncio
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option
import io
from scipy import stats
from dotenv import load_dotenv

load_dotenv()

class XpGraphs(commands.Cog, description='Graphs relating to MEE6 levelling system'):

  def __init__(self, client):
    KEY=os.getenv("KEY")
    self.client=client
    self.cluster=motor.motor_asyncio.AsyncIOMotorClient(KEY)

  @cog_ext.cog_slash(
    name='compare',
    description="Graphs your xp history compared to someone else's",
    options=[
      create_option(
        name='user',
        description='User you want to compare to',
        required=True,
        option_type=6
      ),
      create_option(
        name='interval',
        description='Specify interval',
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
            name='weekly',
            value='weekly'
          )
        ]
      ),
      create_option(
        name='length',
        description='Specify length of graph',
        required=True,
        option_type=4
      ),
      create_option(
        name='usetotalxp',
        description='Use total xp or not',
        required=True,
        option_type=5
      ),
      create_option(
        name='graphtype',
        description='Specify graph type',
        required=True,
        option_type=3,
        choices=[
          create_choice(
            name='Line',
            value='Line'
          ),
          create_choice(
            name='Bar',
            value='Bar'
          )
        ]
      )
    ]
  )
  async def compare(self, ctx:SlashContext, user:str, interval:str, length:int, usetotalxp:bool, graphtype:str):
    data_stream=io.BytesIO()
    db=self.cluster.users
    collection=db[str(ctx.guild.id)]
    person1=await collection.find_one({"_id":str(ctx.author.id)})
    person2=await collection.find_one({"_id":str(user.id)})
    if usetotalxp:
      if interval=="hourly":
        if length<=len(person1['xplist']) and length<=len(person2['xplist']):
          person1_list=person1['xplist'][(-1*length):]
          person2_list=person2['xplist'][(-1*length):]
        else:
          await ctx.send("Length over maximum")
      elif interval=="daily":
        if (length-1)*24<=len(person1['xplist']) and (length-1)*24<=len(person2['xplist']):
          person1_list=person1['xplist'][(-1*length*24)::24]
          person2_list=person2['xplist'][(-1*length*24)::24]
        else:
          await ctx.send("Length over maximum")
      elif interval=="weekly":
        if (length-1)*168<=len(person1['xplist']) and (length-1)*168<=len(person2['xplist']):
          person1_list=person1['xplist'][(-1*length*168)::168]
          person2_list=person2['xplist'][(-1*length*168)::168]
        else:
          await ctx.send("Length over maximum")
    else:
      if length<=len(person1[str(interval+"xp")]) and length<=len(person2[str(interval+"xp")]):
        person1_list=person1[str(interval+"xp")][(-1*length):]
        person2_list=person2[str(interval+"xp")][(-1*length):]
      else:
        await ctx.send("Length over maximum")
    if graphtype=='Line':
      plt.plot(person1_list, label=person1['name'])
      plt.plot(person2_list, label=person2['name'])
      plt.legend(loc='upper left')
    elif graphtype=='Bar':
      x_axis=np.arange(len(person1_list))
      plt.bar(x_axis-0.2, person1_list, 0.4, label=person1['name'])
      plt.bar(x_axis+0.2, person2_list, 0.4, label=person2['name'])
      plt.legend(loc='upper left')
    plt.savefig(data_stream, format='png', bbox_inches='tight', dpi=80)
    plt.close()
    data_stream.seek(0)
    chart=discord.File(data_stream,filename="compare_xp.png")
    embed=discord.Embed(title="XP Compare", description=f"{interval.capitalize()} xp comparison between {person1['name']} and {person2['name']} (Length: {length}, Graph: {graphtype} graph)", color=discord.Color.gold())
    embed.set_image(url='attachment://compare_xp.png')
    await ctx.send(embed=embed, file=chart)

  @cog_ext.cog_slash(
    name='topuserschart',
    description="Breakdown of server top members' xp",
    options=[
     create_option(
        name='graphtype',
        description='Specify graph type',
        required=True,
        option_type=3,
        choices=[
          create_choice(
            name='Pie',
            value='Pie'
          ),
          create_choice(
            name='Bar',
            value='Bar'
          )
        ]
      ),
      create_option(
        name='interval',
        description='Specify interval',
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
        name='length',
        description='Specify number of members shown, defaults to 20 members',
        required=False,
        option_type=4
      )
    ]
  )
  async def topuserschart(self, ctx:SlashContext, graphtype:str, interval:str, length:int = 0):
    data_stream=io.BytesIO()
    db=self.cluster.users
    collection=db[str(ctx.guild.id)]
    people=[]
    totalxp=[]
    people_names=[]
    number=0
    if not length:
      length=20
    async for x in collection.find():
      number+=1
      if number<length+1:
        people.append(x)
    people=sorted(people, key=lambda d: d['totalxp'], reverse=True)
    if graphtype=='Pie':
      for x in people:
        totalxp.append(x['totalxp'])
        people_names.append(f"{x['name']}:\n{x['totalxp']}xp")
      plt.pie(totalxp, labels=people_names)
    elif graphtype=='Bar':
      for x in people:
        totalxp.append(x['totalxp'])
        people_names.append(x['name'])
      plt.bar(people_names, totalxp)
    plt.savefig(data_stream, format='png', bbox_inches='tight', dpi=80)
    plt.close()
    data_stream.seek(0)
    chart=discord.File(data_stream,filename="total_xp.png")
    embed=discord.Embed(title=f"Total XP breakdown", color=discord.Color.green())
    embed.set_image(url='attachment://total_xp.png')
    await ctx.send(embed=embed, file=chart)

  @cog_ext.cog_slash(
    name='xppredict',
    description='Creates a graph showing your predicted xp gain using linear regression',
    options=[
      create_option(
        name='interval',
        description='Specify interval',
        required=True,
        option_type=3,
        choices=[
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
          )
        ]
      ),
      create_option(
        name='length',
        description='amount of predicted xp you want to graph',
        required=True,
        option_type=4
      ),
      create_option(
        name='usetotalxp',
        description='Use total xp or not',
        required=True,
        option_type=5
      )
    ]
  )
  async def xppredict(self, ctx:SlashContext, interval:str, length:int, usetotalxp:bool):
    data_stream=io.BytesIO()
    db=self.cluster.users
    collection=db[str(ctx.guild.id)]
    person1=await collection.find_one({"_id":str(ctx.author.id)})
    if usetotalxp:
      if interval=="daily":
        if (length-1)*24<=len(person1['xplist']):
          person1_list=person1['xplist'][(-1*length*24)::24]
        else:
          await ctx.send("Length over maximum")
      elif interval=="weekly":
        if (length-1)*168<=len(person1['xplist']):
          person1_list=person1['xplist'][(-1*length*168)::168]
        else:
          await ctx.send("Length over maximum")
    else:
      if length<=len(person1[str(interval+"xp")]):
        person1_list=person1[str(interval+"xp")][(-1*length):]
      else:
        await ctx.send("Length over maximum")
    

  @cog_ext.cog_slash(
    name='comparepredict',
    description="Graphs your predicted xp gain compared to someone else's",
    options=[
      create_option(
        name='user',
        description='User you want to compare to',
        required=True,
        option_type=6
      ),
      create_option(
        name='interval',
        description='Specify interval',
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
          )
        ]
      ),
      create_option(
        name='length',
        description='Specify length of graph',
        required=True,
        option_type=4
      ),
      create_option(
        name='usetotalxp',
        description='Use total xp or not',
        required=True,
        option_type=5
      ),
      create_option(
        name='graphtype',
        description='Specify graph type',
        required=True,
        option_type=3,
        choices=[
          create_choice(
            name='Line',
            value='Line'
          ),
          create_choice(
            name='Bar',
            value='Bar'
          )
        ]
      )
    ]
  )
  async def comparepredict(self, ctx:SlashContext, user:str, interval:str, length:int, usetotalxp:bool, graphtype:str):
    pass

def setup(client):
  client.add_cog(XpGraphs(client))
