import discord, os
from discord.ext import commands
from discord.ext.commands import has_permissions
from pymongo import MongoClient
from peewee import *
from core import database


# - Token Hider
from dotenv import load_dotenv

load_dotenv()

prefix = ','
client = commands.Bot(command_prefix=prefix, help_command=None, case_insensitive=True)
client.remove_command('help')

# - Cog Loader
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')



# - On Bot Startup Event
@client.event
async def on_ready():
    activity = discord.Game(name='Writing Tickets :0 | ,help')
    await client.change_presence(status=discord.Status.idle, activity=activity)
    print('Hermes is online')


# - Ping Command
@client.command()
@has_permissions(administrator=True)
async def ping(ctx):
    embed = discord.Embed(title="Pong!", description=f"{ctx.author.mention} pong!\nThe response time for your ping was ``{round(client.latency * 1000)}ms``")
    await ctx.send(embed=embed)

# - Error Handling
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"{ctx.author.name}, you are lacking the permissions required for running this command. If you believe this is an error, message an Admin or Dev.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"{ctx.author.name}, you are lacking a required parameter/argument. Please enter all the required args or refer to ,help.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"{ctx.author.name}, this command was not found, check your spelling and capitalization and try again or refer to ,help.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(f"{ctx.author.name}, you entered an extra/incorrect paramater, try again or refer to ,help")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"{ctx.author.name}, you entered an extra/incorrect paramater, try again or refer to ,help")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"{ctx.author.name}, that command is on cooldown, please wait ``{round(error.retry_after)} seconds``!")
    else:
        await ctx.send("An unexpected error occurred.")
        raise error

# - Help Command
@client.group(invoke_without_command=True)
async def help(ctx):
    embed = discord.Embed(title="Hermes Tickets Help", description="Use ,help <command> for more help on each specific command")

    embed.add_field(name = "Main", value = "start, promote, demote, \nrename, end")
    embed.add_field(name = "Misc", value = "ping")

    await ctx.send(embed=embed)

@help.command()
async def start(ctx):
    embed = discord.Embed(title = "Start [Initiate]", description = "Initializes the bot, creating all the necessary channels, roles, and db instances.")

    embed.add_field(name = "Usage", value = ",start")
    await ctx.send(embed=embed)

@help.command()
async def promote(ctx):
    embed = discord.Embed(title = "Promote", description = "Gives mentioned member 'ticket-helper' role and allows them to view all tickets")

    embed.add_field(name = "Usage", value = ",promote <@user> | ,promote <user id>")
    await ctx.send(embed=embed)

@help.command()
async def demote(ctx):
    embed = discord.Embed(title = "Demote", description = "Removes 'ticket-helper' role from mentioned member and disallows them from viewing all tickets")

    embed.add_field(name = "Usage", value = ",demote <@user> | ,demote <user id>")
    await ctx.send(embed=embed)

@help.command()
async def rename(ctx):
    embed = discord.Embed(title = "Rename", description = "Renames title of ticket channel")

    embed.add_field(name = "Usage", value = ",rename <name>")
    await ctx.send(embed=embed)

@help.command()
async def end(ctx):
    embed = discord.Embed(title = "End [Delete]", description = "Deletes ticket channel upon confirmation")

    embed.add_field(name = "Usage", value = ",end")
    await ctx.send(embed=embed)



client.run(os.getenv('TOKEN'))


