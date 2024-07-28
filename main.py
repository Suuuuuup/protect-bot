import discord
from discord.ext import commands, tasks
from discord.ui import Select, View
from collections import defaultdict, deque
import time
import asyncio
import json
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='+', intents=intents)

# Initial Settings
default_settings = {
    "anti_link_enabled": False,
    "max_links": 0,
    "anti_spam_enabled": False,
    "spam_threshold": 5,  
    "spam_interval": 10,  
    "owners": []
}

# Load settings from file
if os.path.exists('settings.json'):
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        
        if not settings:
            settings = default_settings
    except json.JSONDecodeError:
        settings = default_settings
else:
    settings = default_settings

# Save settings to file
def save_settings():
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

user_messages = defaultdict(list)
deletion_queue = deque()

# Configuration Commands
@bot.command()
@commands.has_permissions(administrator=True)
async def antilink(ctx, state: str):
    if state.lower() == 'on':
        settings["anti_link_enabled"] = True
        await ctx.send("Anti-lien activé.")
    elif state.lower() == 'off':
        settings["anti_link_enabled"] = False
        await ctx.send("Anti-lien désactivé.")
    else:
        await ctx.send("Utilisation : +antilink [on/off]")
    save_settings()

@bot.command()
@commands.has_permissions(administrator=True)
async def maxlink(ctx, max_links_count: int):
    settings["max_links"] = max_links_count
    await ctx.send(f"Nombre maximal de liens défini à {settings['max_links']}.")
    save_settings()

@bot.command()
@commands.has_permissions(administrator=True)
async def antispam(ctx, state: str):
    if state.lower() == 'on':
        settings["anti_spam_enabled"] = True
        await ctx.send("Anti-spam activé.")
    elif state.lower() == 'off':
        settings["anti_spam_enabled"] = False
        await ctx.send("Anti-spam désactivé.")
    else:
        await ctx.send("Utilisation : +antispam [on/off]")
    save_settings()

@bot.command()
@commands.has_permissions(administrator=True)
async def setmsg(ctx, threshold: int):
    settings["spam_threshold"] = threshold
    await ctx.send(f"Seuil de spam défini à {settings['spam_threshold']} messages.")
    save_settings()

@bot.command()
@commands.has_permissions(administrator=True)
async def settime(ctx, interval: int):
    settings["spam_interval"] = interval
    await ctx.send(f"Intervalle de spam défini à {settings['spam_interval']} secondes.")
    save_settings()

@bot.command()
async def owner(ctx, member: discord.Member):
    if ctx.author.id != 1123002265897279629: # met ton id ! 
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
        return

    if member.id not in settings["owners"]:
        settings["owners"].append(member.id)
        await ctx.send(f"{member.mention} est maintenant un owner.")
    else:
        settings["owners"].remove(member.id)
        await ctx.send(f"{member.mention} n'est plus un owner.")
    save_settings()

@bot.command()
async def config(ctx):
    embed = discord.Embed(title="📜 Commandes", description="Commandes disponibles pour configurer le bot", color=0xff0000)  # Couleur rouge
    embed.set_footer(text="© Suuuuup")
    embed.set_thumbnail(url="https://discord.com/channels/1258757979751059508/1259854501926666320/1267130356268535881")
    embed.add_field(name="+antilink [on/off]", value="Active ou désactive l'anti-lien", inline=False)
    embed.add_field(name="+maxlink [nombre]", value="Définit le nombre maximal de liens avant une action", inline=False)
    embed.add_field(name="+antispam [on/off]", value="Active ou désactive l'anti-spam", inline=False)
    embed.add_field(name="+setmsg [nombre]", value="Définit le seuil de spam en nombre de messages", inline=False)
    embed.add_field(name="+settime [secondes]", value="Définit l'intervalle de temps pour la détection de spam", inline=False)
    embed.add_field(name="+owner [membre]", value="Ajoute ou supprime un owner", inline=False)
    await ctx.send(embed=embed) 


bot.remove_command('help')


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🆘 Aide", description="Utilisez le menu déroulant ci-dessous pour naviguer vers les différentes catégories.", color=0x00ff00)
    view = View()
    select = Select(placeholder="Choisissez une catégorie...", options=[
        discord.SelectOption(label="Configuration", description="Commandes pour configurer le bot", value="config"),
        discord.SelectOption(label="Modération", description="Commandes de modération (ban, kick, mute)", value="moderation")
    ])

    async def callback(interaction):
        if select.values[0] == "config":
            await config(ctx)
        elif select.values[0] == "moderation":
            embed = discord.Embed(title="🔨 Modération", description="Commandes disponibles pour la modération", color=0xff0000)
            embed.set_footer(text="© Suuuuup")
            embed.add_field(name="+ban [membre] [raison]", value="Bannir un membre", inline=False)
            embed.add_field(name="+kick [membre] [raison]", value="Expulser un membre", inline=False)
            embed.add_field(name="+mute [membre] [durée]", value="Muter un membre pour une durée spécifiée (en secondes)", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=False)

    select.callback = callback
    view.add_item(select)
    await ctx.send(embed=embed, view=view)


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} a été banni pour la raison suivante : {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} a été expulsé pour la raison suivante : {reason}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: int, *, reason=None):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)
    await member.add_roles(role)
    await ctx.send(f"{member.mention} a été mute pour {duration} secondes pour la raison suivante : {reason}")
    
    await asyncio.sleep(duration)
    await member.remove_roles(role)
    await ctx.send(f"{member.mention} n'est plus mute.")

@tasks.loop(seconds=1)
async def process_deletion_queue():
    if deletion_queue:
        msg = deletion_queue.popleft()
        try:
            await msg.delete()
        except discord.NotFound:
            print("Message already deleted.")
        except discord.HTTPException as e:
            print(f"Failed to delete message: {e}")

@bot.event
async def on_ready():
    print(f'{bot.user} est connecté!')
    bot.status = discord.Status.dnd
    activity = discord.Activity(type=discord.ActivityType.streaming, url="https://www.twitch.tv/suuuuup_", name="Protect Bot") # Change avec t'es info :)
    await bot.change_presence(activity=activity)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.author.id in settings["owners"]:
        await bot.process_commands(message)
        return

    now = time.time()

    # Anti-Link
    if settings["anti_link_enabled"]:
        if "http://" in message.content or "https://" in message.content:
            deletion_queue.append(message)
            await message.channel.send(f"{message.author.mention}, tu n'es pas autorisé à envoyer un lien.", delete_after=2)
            return

    # Anti-Spam
    if settings["anti_spam_enabled"]:
        user_messages[message.author.id] = [timestamp for timestamp in user_messages[message.author.id] if now - timestamp < settings["spam_interval"]]
        user_messages[message.author.id].append(now)

        if len(user_messages[message.author.id]) > settings["spam_threshold"]:
            # Delete user's messages in the interval
            async for msg in message.channel.history(limit=200):
                if msg.author and (now - msg.created_at.timestamp() < settings["spam_interval"]):
                    deletion_queue.append(msg)

            role = discord.utils.get(message.guild.roles, name='Muted')
            if not role:
                role = await message.guild.create_role(name='Muted')
                for channel in message.guild.channels:
                    await channel.set_permissions(role, send_messages=False, speak=False)
            await message.author.add_roles(role)
            await message.channel.send(f"{message.author.mention} a été muté pour spam.", delete_after=2)
            user_messages[message.author.id] = []

    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
    else:
        await ctx.send(f"Une erreur s'est produite : {str(error)}")
        raise error  

bot.run('') # met le token de ton bot !
