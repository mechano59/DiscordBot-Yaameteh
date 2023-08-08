import discord
import os
import random
from discord import user
from discord.ext import commands 
from discord import Member
from discord.ext.commands import bot, has_permissions, MissingPermissions
from webserver import keep_alive
import time
import threading

def run_lavalink():
  os.system("java -jar Lavalink.jar")
threading.Thread(target=run_lavalink).start()
time.sleep(60) #wait until lavalink is ready up
    
client=commands.AutoShardedBot(command_prefix= '$')



@client.event
async def on_ready():
  await client.change_presence(activity=discord.Game(name=f'with Onii-Chan'))
  print('You have logged in as {0.user}'.format(client))
  
@client.event
async def on_message(message, case_insensitive=True):
    if client.user.id != message.author.id:
        if "happy birthday" in message.content.lower():
            await message.channel.send('Happy Birthday! 🎈🎉')

        if message.content.startswith('^botservers'):
          await message.channel.send("I'm in " + str(len(client.guilds)) + " servers!")
    await client.process_commands(message)

@client.event 
async def on_member_join(member):
  print(f'(member) has joined.')
  
@client.event
async def on_member_remove(member):
  print(f'(member) has fucked off.')

#ping command
@client.command() 
async def ping(ctx):
  await ctx.send(f"Don't Ping me you Scum! BTW it's {round(client.latency*1000)}ms. Now get lost.")

#8ball random answer  
@client.command(aliases=['8ball'])
async def _8ball(ctx, * ,question):
  responses =[ 'It is certain',
                'It is decidedly so',
                'Without a doubt',
                'Yes, definitely',
                'You may rely on it',
                'As I see it, yes',
                'Most likely',
                'Outlook good',
                'Yes',
                'Signs point to yes',
                'Reply hazy try again',
                'Ask again later',
                'Better not tell you now',
                'Cannot predict now',
                'Concentrate and ask again',
                "Don't count on it",
                'My reply is no',
                'My sources say no',
                'Outlook not so good',
                'Very doubtful.' ]
  await ctx.send(f'Question: {question}\nAnswer: {random.choice(responses)}')

async def setup():
  await client.wait_until_ready()
  #load cogs
  @client.command()  
  async def load(ctx,extension):
    client.load_extension(f'cogs.{extension}')    #in the cogs folder.
    await ctx.send(" Cogs loaded.")

  #unload cogs
  @client.command()  
  async def unload(ctx,extension):
    client.unload_extension(f'cogs.{extension}')    #in the cogs folder.
    await ctx.send(" Cogs unloaded.")
    
  #reload cogs
  @client.command()  
  async def reload(ctx,extension):
    client.unload_extension(f'cogs.{extension}')    #in the cogs folder.
    client.load_extension(f'cogs.{extension}')    #in the cogs folder.
    await ctx.send(" Cogs reloaded.")
      
  #laoding the python files from cogs folder
  for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            client.load_extension(f'cogs.{filename[:-3]}') #to remove the last 3 characters
client.loop.create_task(setup())
keep_alive()
client.run(os.getenv('gugu'))