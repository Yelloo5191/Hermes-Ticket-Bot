import discord, random, os
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.utils import get
from core import database



class Initiate(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases = ['start'])
    @has_permissions(administrator=True)
    async def initiate(self, ctx):

        query = database.TInfo.select().where((database.TInfo.ServerId == ctx.guild.id))

        roles = await ctx.guild.fetch_roles()
        for x in roles: 
            if x == "@everyone":
                everyoneRole = x
        if query.exists():
            await ctx.send("You have already setup Hermes.")
        else:
            helperRole = await ctx.guild.create_role(name = "ticket-helper", colour = discord.Colour(0x91c4eb), reason = "Needed to give mods/staff access to all tickets")
            await ctx.send("Ticket-helper role created <a:loading:849380657863196752>")

            mainCategory = await ctx.guild.create_category(name = "Tickets", reason = "Needed category for holding ticket channels")
            await ctx.send("Tickets category created <a:loading:849380657863196752>")

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                helperRole: discord.PermissionOverwrite(view_channel=True)
            }
            logsChannel = await ctx.guild.create_text_channel(name = "ticket-logs", overwrites = overwrites, reason = "Needed channel for displaying ticket logs", category = mainCategory)
            await ctx.send("Ticket logs channel created <a:loading:849380657863196752>")

            embed = discord.Embed(title="Welcome to TICKET LOGS", description="Every time a ticket is created or deleted, it will be logged here")
            await logsChannel.send(embed=embed)

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
                ctx.guild.default_role: discord.PermissionOverwrite(add_reactions=False)
            }
            startChannel = await ctx.guild.create_text_channel(name = "ticket-creation", overwrites = overwrites, reason = "Needed channel for starting tickets", category = mainCategory)
            await ctx.send("Ticket creation channel created <a:loading:849380657863196752>")

            embed = discord.Embed(title="TICKET CREATION 🎟️", description="React with the 🎫 emoji to start a ticket!")
            ticketCreateEmbed = await startChannel.send(embed=embed)
            await ticketCreateEmbed.add_reaction('🎫')

            q : database.TInfo = database.TInfo.create(ServerId = ctx.guild.id, TicketCount = 0, ChannelList = '[]')
            q.save()

            await ctx.send("Ticket database connected securely <a:loading:849380657863196752>")

            await ctx.send("Hermes bot initiation complete. <:check:849380858535084052>")
    
        database.db.close()

def setup(client):
    client.add_cog(Initiate(client))