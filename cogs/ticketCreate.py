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
        if payload.user_id == 849154028890095656: # check if reactioner is bot
            return False

        # query through database for server reaction is triggered in
        query = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id))
        q = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id)).get()
        ticketChannels = json.loads(q.ChannelList) # set the ticket channels list to the list from the database

        # finds the ticket create and ticket logs channels
        guild = self.client.get_guild(payload.guild_id)
        ticketCreateChannel = discord.utils.get(guild.channels, name = 'ticket-creation')
        logsChannel = discord.utils.get(guild.channels, name = 'ticket-logs')

        category = discord.utils.get(guild.categories, name='Tickets')

        # if channel where reaction is triggered in is the create ticket channel 
        if payload.channel_id == ticketCreateChannel.id:

            # query through user info database for user who triggered reaction
            query = database.UInfo.select().where((database.UInfo.UserId == payload.user_id))

            # if it cannot find said user (first ticket), add the user to the database with a ticketcount of 0
            if not query.exists():

                query = database.UInfo.create(UserId = payload.user_id, TicketCount = 0, ChannelList = "[]")
                query.save()


            # otherwise, pull the data from the user and add 1 to their ticketcount
            else:
                query = database.UInfo.select().where(database.UInfo.UserId == payload.user_id).get()
                userTickets = json.loads(query.ChannelList)

                if query.TicketCount >= 3: # if user has 3 or more tickets
                    user = await self.client.fetch_user(payload.user_id)
                    await user.send("You have reached the maximum amount of tickets, close one to open a new one.")
                else:
                    # add one to the users ticket count
                    query.TicketCount += 1
                    query.save()

                    # add one to the servers ticket count
                    query = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id)).get()
                    query.TicketCount += 1
                    query.save()
                    count = query.TicketCount

                    helperRole = discord.utils.get(guild.roles, name = "ticket-helper")
                    botSelf = discord.utils.get(guild.members, id = 849154028890095656)
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(view_channel=False),
                        payload.member: discord.PermissionOverwrite(view_channel=True),
                        helperRole: discord.PermissionOverwrite(view_channel=True),
                        botSelf: discord.PermissionOverwrite(view_channel=True)
                    }
                    ticketChannel = await guild.create_text_channel(name = f"ticket-{count}", overwrites = overwrites, reason = "Needed ticket channel for member", category = category)

                    query = database.Tickets.create(ChannelId = ticketChannel.id, CreatorId = payload.member.id)
                    query.save()

                    opener = await self.client.fetch_user(payload.user_id)
                    embed = discord.Embed(title=f"New ticket opened by: {opener.name}", description=f"Ticket number {count}", color=discord.Colour(0xa7f7a4))
                    await logsChannel.send(embed=embed)

                    ticketChannels.append(ticketChannel.id)
                    query = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id)).get()
                    query.ChannelList = str(ticketChannels)
                    query.save()

                    userTickets.append(ticketChannel.id)
                    query = database.UInfo.select().where((database.UInfo.UserId == payload.user_id)).get()
                    query.ChannelList = str(userTickets)
                    query.save()

                    await(await ticketChannel.send("@ticket-helper")).delete() # pings ticket helper role and deletes

                    embed = discord.Embed(title=f"Welcome to Ticket {count}!", description="A staff member will be with you shortly. React with the 🗑️ emoji to delete this channel!")
                    infoMessage = await ticketChannel.send(embed=embed)
                    await infoMessage.add_reaction("🗑️")
        
        if payload.channel_id in ticketChannels:
            query = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id))
            if not query.exists():
                payload.send("This guild has not been initiated yet.")
            else:
                ticketChannels = json.loads(query.get().ChannelList) # loads in ticket channels from server database to list

                reactor = payload.user_id
                reactorobj = await self.client.fetch_user(reactor)
                guild = self.client.get_guild(payload.guild_id)
                channel = discord.utils.get(guild.channels, id = payload.channel_id)
                if channel.id in ticketChannels:

                    await channel.send("Are you sure you want to delete the chat? (y/n) 10s to respond")
                    def check(ctx):
                        return reactor == ctx.author.id and ctx.content.lower() in responses
                    answerMessage = await self.client.wait_for('message', check=check, timeout=10.0)

                    if answerMessage.content.lower() == 'y':
                        query = database.Tickets.select().where((database.Tickets.ChannelId == payload.channel_id)).get()
                        query = database.UInfo.select().where((database.UInfo.UserId == query.CreatorId)).get()

                        query.TicketCount -= 1
                        channelList = json.loads(query.ChannelList) # set the ticket channels list to the list from the database
                        channelList.remove(channel.id)
                        query.ChannelList = str(channelList)
                        query.save()

                        query = database.TInfo.select().where((database.TInfo.ServerId == payload.guild_id)).get()
                        channelList = json.loads(query.ChannelList)
                        channelList.remove(channel.id)
                        query.ChannelList = str(channelList)
                        count = query.TicketCount
                        query.save()

                        guild = self.client.get_guild(payload.guild_id)
                        logsChannel = discord.utils.get(guild.channels, name = 'ticket-logs')

                        query = database.Tickets.select().where((database.Tickets.ChannelId == channel.id)).get()
                        query.delete_instance()
                        query.save()



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
        if not query.exists():
            ctx.send("This guild has not been initiated yet.")
        else:
            ticketChannels = json.loads(query.get().ChannelList) # loads in ticket channels from server database to list

            reactor = ctx.author.id
            reactorobj = await self.client.fetch_user(reactor)
            channel = discord.utils.get(ctx.guild.channels, id = ctx.channel.id)
            if channel.id in ticketChannels:

                await channel.send("Are you sure you want to delete the chat? (y/n) 10s to respond")
                def check(ctx):
                    return reactor == ctx.author.id and ctx.content.lower() in responses
                answerMessage = await self.client.wait_for('message', check=check, timeout=10.0)

                if answerMessage.content.lower() == 'y':
                    query = database.Tickets.select().where((database.Tickets.ChannelId == ctx.channel.id)).get()
                    query = database.UInfo.select().where((database.UInfo.UserId == query.CreatorId)).get()

                    query.TicketCount -= 1
                    channelList = json.loads(query.ChannelList) # set the ticket channels list to the list from the database
                    channelList.remove(channel.id)
                    query.ChannelList = str(channelList)
                    query.save()

                    query = database.TInfo.select().where((database.TInfo.ServerId == ctx.guild.id)).get()
                    channelList = json.loads(query.ChannelList)
                    channelList.remove(channel.id)
                    query.ChannelList = str(channelList)
                    count = query.TicketCount
                    query.save()


                    logsChannel = discord.utils.get(ctx.guild.channels, name = 'ticket-logs')

                    query = database.Tickets.select().where((database.Tickets.ChannelId == channel.id)).get()
                    query.delete_instance()
                    query.save()

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
        query = database.TInfo.select().where((database.TInfo.ServerId == ctx.guild.id))
        q = database.TInfo.select().where((database.TInfo.ServerId == ctx.guild.id)).get()
        ticketChannels = json.loads(q.ChannelList)

        if ctx.channel.id in ticketChannels:
            channel = ctx.channel
            await channel.edit(name = message)

            await ctx.send("Channel name updated to {}".format(message))

def setup(client):
    client.add_cog(TicketCreate(client))