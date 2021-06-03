import discord, os
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.utils import get
from pymongo import MongoClient

# - Token Hider
from dotenv import load_dotenv

load_dotenv()

# - Mongo Setup
cluster = MongoClient(os.getenv("MONGO"))
db = cluster["hermes"]
collection = db["tickets"]

ticketChannels = []
responses = ['y', 'n']

class TicketCreate(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        guild = self.client.get_guild(payload.guild_id)
        ticketCreateChannel = discord.utils.get(guild.channels, name = 'ticket-creation')
        logsChannel = discord.utils.get(guild.channels, name = 'ticket-logs')

        category = discord.utils.get(guild.categories, name='Tickets')


        if payload.channel_id == ticketCreateChannel.id:
            results = collection.find_one({"_id":payload.user_id})
            if results == None:
                post = {"_id":payload.user_id, "amount":0}
                collection.insert_one(post)
            else:
                collection.update_one({"_id":payload.user_id}, {"$set": {"amount":results["amount"] + 1}})
                results = collection.find_one({"_id":payload.user_id})
            
            if results["amount"] > 3:
                user = await self.client.fetch_user(payload.user_id)
                await user.send("You have reached the maximum amount of tickets, close one to open a new one.")
            else:

                results = collection.find_one({"_id":payload.guild_id})
                collection.update_one({"_id":payload.guild_id}, {"$set": {"tickets": results["tickets"] + 1}})
                results = collection.find_one({"_id":payload.guild_id})
                count = results["tickets"]


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

                await(await ticketChannel.send("@everyone")).delete()
                
                embed = discord.Embed(title=f"Welcome to Ticket {count}!", description="A staff member will be with you shortly. React with the 🗑️ emoji to delete this channel!")
                infoMessage = await ticketChannel.send(embed=embed)
                await infoMessage.add_reaction("🗑️")


        if payload.channel_id in ticketChannels:
            results = collection.find_one({"_id":payload.guild_id})
            count = results["tickets"]

            if payload.user_id != 849154028890095656:
                reactor = payload.user_id
                reactorobj = await self.client.fetch_user(reactor)

                channel = discord.utils.get(guild.channels, id = payload.channel_id)
                await channel.send("Are you sure you want to delete the chat? (y/n) 10s to respond")
                def check(ctx):
                    return reactor == ctx.author.id and ctx.content.lower() in responses
                answerMessage = await self.client.wait_for('message', check=check, timeout=10.0)

                if answerMessage.content.lower() == 'y':
                    results = collection.find_one({"_id": reactor})
                    collection.update_one({"_id": reactor}, {"$set":{"amount": results["amount"] - 1}})

                    await channel.delete()
                    embed = discord.Embed(title=f"Ticket closed by: {reactorobj.name}",description=f"Ticket number {count}",color=discord.Colour(0xfc6e6e))
                    await logsChannel.send(embed=embed)

                elif answerMessage.content.lower() == 'n':
                    await ctx.send("Cancelled")
                else:
                    await ctx.send("Unexpected response")
    
    @commands.command(aliases = ["delete"])
    async def end(self, ctx):
        
        reactor = ctx.author.id
        reactorobj = await self.client.fetch_user(reactor)
        channel = discord.utils.get(ctx.guild.channels, id = ctx.channel.id)
        if channel.id in ticketChannels:
        
            await channel.send("Are you sure you want to delete the chat? (y/n) 10s to respond")
            def check(ctx):
                return reactor == ctx.author.id and ctx.content.lower() in responses
            answerMessage = await self.client.wait_for('message', check=check, timeout=10.0)

            if answerMessage.content.lower() == 'y':
                results = collection.find_one({"_id": reactor})
                collection.update_one({"_id": reactor}, {"$set":{"amount": results["amount"] - 1}})

                results = collection.find_one({"_id":ctx.guild.id})
                count = results["tickets"]
                logsChannel = discord.utils.get(ctx.guild.channels, name = 'ticket-logs')

                await channel.delete()
                embed = discord.Embed(title=f"Ticket closed by: {reactorobj.name}",description=f"Ticket number {count}",color=discord.Colour(0xfc6e6e))
                await logsChannel.send(embed=embed)

            elif answerMessage.content.lower() == 'n':
                await ctx.send("Cancelled")
            else:
                await ctx.send("Unexpected response")
    
    @commands.command()
    async def rename(self, ctx, *, message):

        if ctx.channel.id in ticketChannels:
            channel = ctx.channel
            await channel.edit(name = message)

            await ctx.send("Channel name updated to {}".format(message))

def setup(client):
    client.add_cog(TicketCreate(client))