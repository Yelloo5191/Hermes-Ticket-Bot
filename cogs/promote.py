import discord, os
from discord.ext import commands
from discord.ext.commands import has_permissions

# - Token Hider
from dotenv import load_dotenv

load_dotenv()

class Promote(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    @has_permissions(administrator=True)
    async def promote(self, ctx, user: discord.Member):
        
        role = discord.utils.get(ctx.guild.roles, name = 'ticket-helper')
        await user.add_roles(role)
        await ctx.send(f"User {user.name} was given the role **ticket-helper** giving them access to all Tickets.")

    @commands.command()
    @has_permissions(administrator=True)
    async def demote(self, ctx, user: discord.Member):

        role = discord.utils.get(ctx.guild.roles, name = 'ticket-helper')
        await user.remove_roles(role)
        await ctx.send(f"User {user.name} was removed of the role **ticket-helper** removing their access to all Tickets.")

def setup(client):
    client.add_cog(Promote(client))