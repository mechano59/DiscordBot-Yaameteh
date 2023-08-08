import discord
import os
import random
from discord import user
from discord.ext import commands 
from discord import Member
from discord.ext.commands import bot, has_permissions, MissingPermissions


class Moderation(commands.Cog):
    def __init__(self,client):
        self.client=client
    #kick command
    @commands.command(name="kick", pass_context=True)
    @has_permissions(kick_members=True)
    async def kick(self,ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f'User {member} has kicked.')
  
    @kick.error
    async def kick_error(ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send("Sorry, you are not allowed to do that!")

    #ban command
    @commands.command(name="ban", pass_context=True)
    @has_permissions(ban_members=True)
    async def ban(ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f'User {member} has been banned.')
  
    @ban.error
    async def ban_error(ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send("Sorry, you are not allowed to do that!")

    #unban command  
    @commands.command()
    async def unban(ctx,*,member):
        banned_users=await ctx.guild.bans()
        member_name,member_discriminator= member.split('#')
  
        for ban_entry in banned_users:
            user=ban_entry.user
    
            if (user.name, user.discriminator) == (member_name,member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'{user.mention} Nii-Chan is allowed here from now on.')
                return
        
    #clear or delete message  
    @commands.command(name="clear", pass_context=True)
    @has_permissions(manage_messages=True)
    async def clear(self,ctx, amount=5):
        await ctx.channel.purge(limit=amount)
        if(amount<=0):
            await ctx.send('Your PP is too small to fit. Make it bigger.')

    @clear.error
    async def clear_error(self,ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send("Sorry, you are not allowed to do that!")
    
    #mute members  
    @commands.command(name="mute")
    @has_permissions(manage_messages=True)
    async def mute(ctx, member: discord.Member,*,reason=None):
        guild= ctx.message.server
        mutedRole=discord.utils.get(guild.roles, name='Muted')
        
        if not mutedRole:
            mutedRole=await guild.create_role(name='Muted')
            
            for channel in guild.channels: 
                await channel.set_permissions(mutedRole, speak=False, send_messages=True, read_message_history=True, read_messages=True)
                
        await member.add_roles(mutedRole, reason=reason)
        await ctx.send(f'Muted{member.mention} for a {reason}')
        
        await ctx.send("I taped {member.mention}Nii-Chan's cakehole shut for a {reason}.")
        await member.send("You were muted in the server.")
           

    @mute.error
    async def mute_error(self,ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send("Sorry, you are not allowed to do that!")
        else:
            raise error
        
def setup(client):
    client.add_cog(Moderation(client))