import discord, os, json
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.utils import get
from core import database


responses = ['y', 'n']

class TicketCreate(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        query = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id))
        q : database.TInfo = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id)).get()
        ticketChannels = json.loads(q.ChannelList)

        guild = self.client.get_guild(payload.guild_id)
        ticketCreateChannel = discord.utils.get(guild.channels, name = 'ticket-creation')
        logsChannel = discord.utils.get(guild.channels, name = 'ticket-logs')

        category = discord.utils.get(guild.categories, name='Tickets')


        if payload.channel_id == ticketCreateChannel.id:

            query = database.UInfo.select().where((database.UInfo.UserId == payload.user_id))

            if not query.exists():

                q : database.UInfo = database.UInfo.create(UserId = payload.user_id, TicketCount = 0)
                q.save()

            else:
                q: database.UInfo = database.UInfo.select().where(database.UInfo.UserId == payload.user_id).get()

                q.TicketCount += 1
                q.save()
            
            if q.TicketCount > 3:
                user = await self.client.fetch_user(payload.user_id)
                await user.send("You have reached the maximum amount of tickets, close one to open a new one.")
            else:

                q = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id)).get()
                q.TicketCount += 1
                q.save()
                count = q.TicketCount


                helperRole = discord.utils.get(guild.roles,name="ticket-helper")
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    payload.member: discord.PermissionOverwrite(view_channel=True),
                    helperRole: discord.PermissionOverwrite(view_channel=True)
                }
                ticketChannel = await guild.create_text_channel(name = f"ticket-{count}", overwrites = overwrites, reason = "Needed ticket channel for member", category = category)

                opener = await self.client.fetch_user(payload.user_id)
                embed = discord.Embed(title=f"New ticket opened by: {opener.name}",description=f"Ticket number {count}",color=discord.Colour(0xa7f7a4))
                await logsChannel.send(embed=embed)

                ticketChannels.append(ticketChannel.id)
                q : database.TInfo = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id)).get()
                q.ChannelList = str(ticketChannels)
                q.save()

                await(await ticketChannel.send("@everyone")).delete()
                
                embed = discord.Embed(title=f"Welcome to Ticket {count}!", description="A staff member will be with you shortly. React with the 🗑️ emoji to delete this channel!")
                infoMessage = await ticketChannel.send(embed=embed)
                await infoMessage.add_reaction("🗑️")


        if payload.channel_id in ticketChannels:
            q = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id)).get()
            count = q.TicketCount

            if payload.user_id != 849154028890095656:
                reactor = payload.user_id
                reactorobj = await self.client.fetch_user(reactor)

                channel = discord.utils.get(guild.channels, id = payload.channel_id)
                await channel.send("Are you sure you want to delete the chat? (y/n) 10s to respond")
                def check(ctx):
                    return reactor == ctx.author.id and ctx.content.lower() in responses
                answerMessage = await self.client.wait_for('message', check=check, timeout=10.0)

                if answerMessage.content.lower() == 'y':

                    query = database.UInfo.select().where((database.UInfo.UserId == reactor)).get()
                    query.TicketCount -= 1
                    query.save

                    ticketChannels.remove(channel.id)
                    q : database.TInfo = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id)).get()
                    q.ChannelList = str(ticketChannels)
                    q.save()
                    await channel.delete()
                    embed = discord.Embed(title=f"Ticket closed by: {reactorobj.name}",description=f"Ticket number {count}",color=discord.Colour(0xfc6e6e))
                    await logsChannel.send(embed=embed)

                elif answerMessage.content.lower() == 'n':
                    await ctx.send("Cancelled")
                else:
                    await ctx.send("Unexpected response")

        database.db.close()
    
    @commands.command(aliases = ["delete"])
    async def end(self, ctx):
        query = database.TInfo.select().where((database.TInfo.ServerId == ctx.guild.id))
        q : database.TInfo = database.TInfo.select().where((database.TInfo.ServerId == ctx.guild.id)).get()
        ticketChannels = json.loads(q.ChannelList)

        reactor = ctx.author.id
        reactorobj = await self.client.fetch_user(reactor)
        channel = discord.utils.get(ctx.guild.channels, id = ctx.channel.id)
        if channel.id in ticketChannels:
        
            await channel.send("Are you sure you want to delete the chat? (y/n) 10s to respond")
            def check(ctx):
                return reactor == ctx.author.id and ctx.content.lower() in responses
            answerMessage = await self.client.wait_for('message', check=check, timeout=10.0)

            if answerMessage.content.lower() == 'y':
                
                query = database.UInfo.select().where((database.UInfo.UserId == reactor)).get()
                query.TicketCount -= 1
                query.save()

                query = database.TInfo.select().where((database.TInfo.ServerId == ctx.guild.id)).get()
                count = query.TicketCount

                logsChannel = discord.utils.get(ctx.guild.channels, name = 'ticket-logs')

                await channel.delete()
                embed = discord.Embed(title=f"Ticket closed by: {reactorobj.name}",description=f"Ticket number {count}",color=discord.Colour(0xfc6e6e))
                await logsChannel.send(embed=embed)

            elif answerMessage.content.lower() == 'n':
                await ctx.send("Cancelled")
            else:
                await ctx.send("Unexpected response")
        
        database.db.close()
    
    @commands.command()
    async def rename(self, ctx, *, message):

        if ctx.channel.id in ticketChannels:
            channel = ctx.channel
            await channel.edit(name = message)

            await ctx.send("Channel name updated to {}".format(message))

def setup(client):
    client.add_cog(TicketCreate(client))