from calendar import week
from datetime import datetime
import asyncio
from mee6_py_api import API
import discord
from discord.ext import tasks
from discord.ext import commands
import os
import motor.motor_asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class Leaderboard(commands.Cog):

  def __init__(self, client):
    KEY=os.getenv("KEY")
    self.client=client
    self.cluster=motor.motor_asyncio.AsyncIOMotorClient(KEY)
    self.leaderboardUpdate.start()
    self.ran=False

  @tasks.loop(seconds=40.0)
  async def leaderboardUpdate(self):
    now=datetime.now()
    current_minute=now.strftime("%M")
    current_hour=now.strftime("%H")
    if current_minute!='26':
      self.ran=False
    elif current_minute=='26' and not self.ran:
      for guild in self.client.guilds:
        if guild.id==928762387874582648:
          #getting xp values
          mee6API = API(guild.id)
          leaderboard_page = await mee6API.levels.get_leaderboard_page(0)
          db=self.cluster.users
          collection=db[str(guild.id)]
          for x in range(len(leaderboard_page['players'])):
            try:
              filterUser={'_id':str(leaderboard_page['players'][x]['id'])}
              person=await collection.find_one({"_id":str(leaderboard_page['players'][x]['id'])})
              newXpList=person['xplist']
              newXpList.append(leaderboard_page['players'][x]['xp'])
              newValue={'$set': {'xplist':newXpList}}
              y=await collection.update_one(filterUser, newValue)
              newValue={'$set': {'totalxp':leaderboard_page['players'][x]['xp']}}
              y=await collection.update_one(filterUser, newValue)
            except:
              print(f"Error with {leaderboard_page['players'][x]['id']}")

          #sending leaderboard
          db=self.cluster.configs
          collection= db[str(guild.id)]
          config=await collection.find_one()
          channel=self.client.get_channel(id=int(config['CHANNELID']))
          print(channel)
          db=self.cluster.users
          collection=db[str(guild.id)]
          people=[]
          async for x in collection.find():
            people.append(x)
          for person in people:
            equalsHourly=False
            equalsDaily=False
            equalsWeekly=False
            hourlyMessage=""
            dailyMessage=""
            weeklyMessage=""
            dailyDaysToCatchMessage=""
            weeklyDaysToCatchMessage=""
            if len(person['xplist'])%24==0:
              person['dailyxp'].append(person['xplist'][-1]-person['xplist'][-24])
              y=await collection.update_one({'_id':person['_id']}, {'$set':{'dailyxp':person['dailyxp']}})
              equalsDaily=True
            if len(person['xplist'])>1:
              person['hourlyxp'].append(person['xplist'][-1]-person['xplist'][-2])
              y=await collection.update_one({'_id':person['_id']}, {'$set':{'hourlyxp':person['hourlyxp']}})
              equalsHourly=True
            if len(person['xplist'])%168==0:
              person['weeklyxp'].append(person['xplist'][-1]-person['xplist'][-168])
              y=await collection.update_one({'_id':person['_id']}, {'$set':{'weeklyxp':person['weeklyxp']}})
              equalsWeekly=True
          #messages
          if config['all']:
            if equalsHourly:
              length=0
              for person in sorted(people, key=lambda d: d['hourlyxp'][-1], reverse=True):
                if not person['excluded'] and person['hourlyxp'][-1]!=0 and length<int(config['LeaderboardLength']):
                  hourlyMessage+=f"{person['name']}'s hourly xp is {person['hourlyxp'][-1]}\n"
                  length+=1
              if hourlyMessage and config['hourly']:
                embed=discord.Embed(title=f'Hourly XP', description=hourlyMessage, color=discord.Colour.blue())
                await channel.send(embed=embed)
              elif not hourlyMessage and config['hourly']:
                embed=discord.Embed(title=f'Hourly XP', description="No one gained xp in the past hour\n", color=discord.Colour.red())
                await channel.send(embed=embed)
            if equalsDaily:
              length=0
              for person in sorted(people, key=lambda d: d['dailyxp'][-1], reverse=True):
                if not person['excluded'] and person['dailyxp'][-1]!=0 and length<int(config['LeaderboardLength']):
                  dailyMessage+=f"{person['name']}'s daily xp is {person['dailyxp'][-1]}\n"
                  length+=1
              if dailyMessage and config['daily']:
                embed=discord.Embed(title=f'Daily XP', description=dailyMessage, color=discord.Colour.green())
                await channel.send(embed=embed)
              elif not dailyMessage and config['daily']:
                embed=discord.Embed(title=f'Daily XP', description="No one gained xp in the past day\n", color=discord.Colour.red())
                await channel.send(embed=embed)
              #catch
              totalXpList=sorted(people, key=lambda d: d['totalxp'], reverse=True)
              for x in range(len(totalXpList)-1):
                p1=totalXpList[x]
                p2=totalXpList[x+1]
                length=0
                if p1['dailyxp'][-1]<p2['dailyxp'][-1] and length<int(config['LeaderboardLength']):
                  daysToCatch=(int(p1['totalxp'])-int(p2['totalxp']))//(int(p2['dailyxp'][-1])-int(p1['dailyxp'][-1]))
                  dailyDaysToCatchMessage+=f"{p2['name']} will pass {p1['name']} in {daysToCatch} at the current xp gain rate.\n"
                  length+=1
              if dailyDaysToCatchMessage and config['catch']:
                embed=discord.Embed(title=f'Days to Catch (Daily)', description=dailyDaysToCatchMessage, color=discord.Colour.dark_green())
                await channel.send(embed=embed)
              elif not dailyDaysToCatchMessage and config['catch']:
                embed=discord.Embed(title=f'Days to Catch (Daily)', description="No one will catch up at the current xp gain rate", color=discord.Colour.dark_red())
                await channel.send(embed=embed)
            if equalsWeekly:
              length=0
              for person in sorted(people, key=lambda d: d['weeklyxp'][-1], reverse=True):
                if not person['excluded'] and person['weeklyxp'][-1]!=0 and length<int(config['LeaderboardLength']):
                  weeklyMessage+=f"{person['name']}'s daily xp is {person['weeklyxp'][-1]}\n"
                  length+=1
              if weeklyMessage and config['weekly']:
                embed=discord.Embed(title=f'Weekly XP', description=weeklyMessage, color=discord.Colour.orange())
                await channel.send(embed=embed)
              elif not weeklyMessage and config['weekly']:
                embed=discord.Embed(title=f'Weekly XP', description="No one gained xp in the past week\n", color=discord.Colour.red())
                await channel.send(embed=embed)
              #catch
              totalXpList=sorted(people, key=lambda d: d['totalxp'], reverse=True)
              for x in range(len(totalXpList)-1):
                p1=totalXpList[x]
                p2=totalXpList[x+1]
                length=0
                if p1['weeklyxp'][-1]<p2['weeklyxp'][-1] and length<int(config['LeaderboardLength']):
                  daysToCatch=(int(p1['totalxp'])-int(p2['totalxp']))//(int(p2['weeklyxp'][-1])-int(p1['weeklyxp'][-1]))
                  weeklyDaysToCatchMessage+=f"{p2['name']} will pass {p1['name']} in {daysToCatch} at the current xp gain rate.\n"
                  length+=1
              if weeklyDaysToCatchMessage and config['catch']:
                embed=discord.Embed(title=f'Days to Catch (Weekly)', description=weeklyDaysToCatchMessage, color=discord.Colour.dark_orange())
                await channel.send(embed=embed)
              elif not weeklyDaysToCatchMessage and config['catch']:
                embed=discord.Embed(title=f'Days to Catch (Weekly)', description="No one will catch up at the current xp gain rate", color=discord.Colour.dark_red())
                await channel.send(embed=embed)
      self.ran=True

  @leaderboardUpdate.before_loop
  async def before_leaderboardUpdate(self):
    await self.client.wait_until_ready()

def setup(client):
  client.add_cog(Leaderboard(client))
