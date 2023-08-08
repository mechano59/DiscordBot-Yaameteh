import re
import discord
from discord.ext import commands
import lavalink
from lavalink import utils
from discord import utils
from discord import Embed
import datetime as dt
import math

url_rx = re.compile(r'https?://(?:www\.)?.+')

class Music(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.client.music = lavalink.Client(self.client.user.id)
    self.client.music.add_node('127.0.0.1', 2333, 'youshallnotpass', 'eu', 'default-node')
    self.client.add_listener(self.client.music.voice_update_handler, 'on_socket_response')
    self.client.music.add_event_hook(self.track_hook)

  def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.client.music._event_hooks.clear()

  async def cog_before_invoke(self, ctx):
      """ Command before-invoke handler. """
      guild_check = ctx.guild is not None
      #  This is essentially the same as `@commands.guild_only()`
      #  except it saves us repeating ourselves (and also a few lines).

      if guild_check:
          await self.ensure_voice(ctx)
          #  Ensure that the bot and command author share a mutual voicechannel.

      return guild_check

  async def cog_command_error(self, ctx, error):
      if isinstance(error, commands.CommandInvokeError):
          await ctx.send(error.original)
          # The above handles errors thrown in this cog and shows them to the user.
          # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
          # which contain a reason string, such as "Join a voicechannel" etc. You can modify the above
          # if you want to do things differently.

  async def ensure_voice(self, ctx):
      """ This check ensures that the bot and command author are in the same voicechannel. """
      player = self.client.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
      # Create returns a player if one exists, otherwise creates.
      # This line is important because it ensures that a player always exists for a guild.

      # Most people might consider this a waste of resources for guilds that aren't playing, but this is
      # the easiest and simplest way of ensuring players are created.

      # These are commands that require the bot to join a voicechannel (i.e. initiating playback).
      # Commands such as volume/skip etc don't require the bot to be in a voicechannel so don't need listing here.
      should_connect = ctx.command.name in ('play','join',)

      if not ctx.author.voice or not ctx.author.voice.channel:
          # Our cog_command_error handler catches this and sends it to the voicechannel.
          # Exceptions allow us to "short-circuit" command invocation via checks so the
          # execution state of the command goes no further.
          raise commands.CommandInvokeError('Join a voicechannel first.')

      if not player.is_connected:
          if not should_connect:
              raise commands.CommandInvokeError('Not connected.')

          permissions = ctx.author.voice.channel.permissions_for(ctx.me)

          if not permissions.connect or not permissions.speak:  # Check user limit too?
              raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')

          player.store('channel', ctx.channel.id)
          await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
      else:
          if int(player.channel_id) != ctx.author.voice.channel.id:
              raise commands.CommandInvokeError('You need to be in my voicechannel.')

  async def cog_check(self, ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("Music commands are not available in DMs.")
        return False

    return True

  # @commands.Cog.listener()
  # async def on_voice_state_update(self, ctx, member, before, after):
  #   if not member.client and after.channel is None:
  #     if not [m for m in before.channel.members if not m.client]:
  #       await self.client.music.player_manager.get(ctx.guild.id)(member.guild).teardown()

  @commands.command(name='join')
  async def join(self, ctx):
    member = utils.find(lambda m: m.id == ctx.author.id, ctx.guild.members)
    if member is not None and member.voice is not None:
      vc = member.voice.channel
      player = self.client.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
      if not player.is_connected:
        player.store('channel', ctx.channel.id)
        await self.connect_to(ctx.guild.id, str(vc.id))

  @commands.command(aliases=['dc'])
  async def disconnect(self, ctx):
      """ Disconnects the player from the voice channel and clears its queue. """
      player = self.client.music.player_manager.get(ctx.guild.id)

      if not player.is_connected:
          # We can't disconnect, if we're not connected.
          return await ctx.send('Not connected.')
      if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
          # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
          # may not disconnect the bot.
          return await ctx.send('You\'re not in my voicechannel!')

      # Clear the queue to ensure old tracks don't start playing
      # when someone else queues something.
      player.queue.clear()
      # Stop the current track so Lavalink consumes less resources.
      await player.stop()
      # Disconnect from the voice channel.
      await ctx.guild.change_voice_state(channel=None)
      await ctx.send('*⃣ | Disconnected.')

  @commands.command(aliases=['p'])
  async def play(self, ctx, *, query):
    try:
      player = self.client.music.player_manager.get(ctx.guild.id)
      query = query.strip('<>')
      if not url_rx.match(query):

        query = f'ytsearch:{query}'
      results = await player.node.get_tracks(query)

      # if not results or not results['tracks']:
      #     return await ctx.send('Nothing found!')

      embed = discord.Embed(colour=ctx.guild.me.top_role.colour)

      if results['loadType'] == 'TRACK_LOADED':
        tracks = results['tracks']

        for track in tracks:

            player.add(requester=ctx.author.id, track=track)

        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='The Track Has Been Added!', timestamp=dt.datetime.utcnow(),description=f'[{track["info"]["title"]}]({track["info"]["uri"]})')
        embed.set_footer(text=f"Added by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
      
      elif results['loadType'] == 'PLAYLIST_LOADED':
        tracks = results['tracks']

        for track in tracks:
            # Add all of the tracks from the playlist to the queue.
            player.add(requester=ctx.author.id, track=track)
        
        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='The Playlist Has Been Added!', timestamp=dt.datetime.utcnow(),description=f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks')
        embed.set_footer(text=f"Added by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)
      
      elif results['loadType'] == 'SEARCH_RESULT': 
        tracks = results['tracks'][0:10]
        i = 0
        query_result = ''
        for track in tracks:
          i = i + 1
          query_result = query_result + f'{i}) {track["info"]["title"]} - {track["info"]["uri"]}\n'
        
        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Please Select The Song You Would Like To Play (1-10)',description=query_result)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

        def check(m):
          return m.author.id == ctx.author.id
          
        response = await self.client.wait_for('message', check=check)
        track = tracks[int(response.content)-1]

        player.add(requester=ctx.author.id, track=track)

        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='The Track Has Been Added!', timestamp=dt.datetime.utcnow(),description=f'[{track["info"]["title"]}]({track["info"]["uri"]})')
        embed.set_footer(text=f"Added by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

      elif results['loadType'] == 'NO_MATCHES':
        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Could Not Find Anything!', timestamp=dt.datetime.utcnow())
        embed.description='Please Check The Link and Try Again...'
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

      else:
        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Error! Something Went Wrong.', timestamp=dt.datetime.utcnow())
        embed.description='The Link Might Be Region Restricted or Unavailable Right Now.'
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

      if not player.is_playing:
        await player.play()

    except Exception as error:
      print(error)

  @commands.command(aliases=['loop', 'l'])
  async def repeat(self, ctx):
      player = self.client.music.player_manager.get(ctx.guild.id)

      if not player.is_playing:
          return await ctx.send('Nothing playing.')

      player.repeat = not player.repeat

      await ctx.send('🔁 | Repeat ' + ('enabled' if player.repeat else 'disabled'))

  @commands.command(aliases=['s'])
  async def stop(self, ctx):
    player = self.client.music.player_manager.get(ctx.guild.id)
    if not player.is_playing:
      return await ctx.send('Not playing.')
    player.queue.clear()
    await player.stop()
    await ctx.send('⏹ | Stopped.')

  @commands.command(aliases=['np', 'n'])
  async def now(self, ctx):
    player = self.client.music.player_manager.get(ctx.guild.id)
    song='Nothing'

    if player.current:
        pos = lavalink.utils.format_time(player.position)
        if player.current.stream:
          dur = 'LIVE'
        else:
          dur = lavalink.utils.format_time(player.current.duration)
          song = f'**[{player.current.title}]({player.current.uri})**\n({pos}/{dur})'

    embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Now Playing', timestamp=dt.datetime.utcnow(),description=song)
    embed.add_field(name="Artist", value=player.current.author, inline=False)
    embed.set_author(name="Playback Information")
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)
  
  @commands.command(aliases=['resume'])
  async def pause(self, ctx):
    player = self.client.music.player_manager.get(ctx.guild.id)

    if not player.is_playing:
        return await ctx.send('Not playing.')

    if player.paused:
        await player.set_pause(False)
        await ctx.send('⏯ | Resumed')
    else:
        await player.set_pause(True)
        await ctx.send(' ⏯ | Paused')

  @commands.command(aliases=['forceskip', 'fs'])
  async def skip(self, ctx):
    player = self.client.music.player_manager.get(ctx.guild.id)

    if not player.is_playing:
        return await ctx.send('Not playing.')

    await ctx.send('⏭ | Skipped.')
    await player.skip()

  @commands.command(aliases=['q'])
  async def queue(self, ctx, page: int=1):
    player = self.client.music.player_manager.get(ctx.guild.id)
    if not player.queue:
        return await ctx.send('There\'s nothing in the queue! Why not queue something?')
    
    items_per_page = 10
    pages = math.ceil(len(player.queue) / items_per_page)

    start = (page - 1) * items_per_page
    end = start + items_per_page

    queue_list = ''

    for i, track in enumerate(player.queue[start:end], start=start):
        queue_list += f'`{i + 1}.` [**{track.title}**]({track.uri})\n'

    embed = discord.Embed(colour=ctx.guild.me.top_role.colour,
                          description=f'**Queue Information: {len(player.queue)} tracks**\n\n{queue_list}')
    embed.set_footer(text=f'Viewing page {page}/{pages}')
    await ctx.send(embed=embed)

  async def track_hook(self, event):
    if isinstance(event, lavalink.events.QueueEndEvent):
      guild_id = int(event.player.guild_id)
      await self.connect_to(guild_id, None)
      
  async def connect_to(self, guild_id: int, channel_id: str):
    ws = self.client._connection._get_websocket(guild_id)
    await ws.voice_state(str(guild_id), channel_id)

def setup(client):
  client.add_cog(Music(client))