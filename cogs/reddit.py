import discord
import os
import random
from discord import user
from discord.ext import commands 
from discord import Member
from discord.ext.commands import bot, has_permissions, MissingPermissions
import praw
from subreddits import meme_subreddits, nsfw_subreddits

reddit_id=os.getenv('red_id')
reddit_secret=os.getenv('red_sec')

class Reddit(commands.Cog):
    def __init__(self,client):
        self.client=client
        self.reddit=None
        if reddit_id and reddit_secret:
            self.reddit = praw.Reddit(client_id=reddit_id,
                        client_secret=reddit_secret,
                        user_agent="yaameteh:%s:1.0" % reddit_secret,check_for_async=False)
    @commands.command()
    async def meme(self,ctx, subreddit: str=""):
      async with ctx.channel.typing():
          if self.reddit:
            #start working
              chosen_subreddit=meme_subreddits
              if subreddit:
                    if subreddit in chosen_subreddit:
                        chosen_subreddit=subreddit
                    else:
                      list_memes= ",".join(meme_subreddits)
                      await ctx.send("Please choose a subreddit of the following list : %s"%(list_memes))
                      return
                #take user subreddit
              submissions= self.reddit.subreddit(subreddit).hot()
              post_to_pick=random.randint(1,50)
              for i in range(0,post_to_pick):
                submisson=next(x for x in submissions if not x.stickied)
              await ctx.send(submisson.url)
          else:
            await ctx.send("Something is not working. Please contact Administrator")
    @commands.command()
    async def nsfw(self,ctx, subreddit: str=""):
      async with ctx.channel.typing():
          if self.reddit:
            #start working
              nsfw_flag= False
              chosen_subreddit=nsfw_subreddits
              if subreddit:
                    if subreddit in chosen_subreddit:
                        chosen_subreddit=subreddit
                        nsfw_flag=True
                    else:
                      list_nsfw= ",".join(nsfw_subreddits)
                      await ctx.send("Please choose a subreddit of the following list : %s"%(list_nsfw))
                      return
              if nsfw_flag:
                  if not ctx.channel.is_nsfw():
                      await ctx.send('This is not allowed Here')
                      return
                #take user subreddit
              submissions= self.reddit.subreddit(subreddit).hot()
              post_to_pick=random.randint(1,50)
              for i in range(0,post_to_pick):
                submisson=next(x for x in submissions if not x.stickied)
              await ctx.send(submisson.url)

          else:
            await ctx.send("Something is not working. Please contact Administrator")
def setup(client):
    client.add_cog(Reddit(client))