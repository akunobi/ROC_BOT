import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Cargar el token desde el archivo .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents para que el bot pueda leer mensajes, usuarios, etc.
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Prefijo del bot
bot = commands.Bot(command_prefix=".", intents=intents)

# Evento al iniciar
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# Comando simple: ping
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# Cargar cogs (comandos organizados)
initial_extensions = [
    "cogs.moderation",
    "cogs.fun",
    "cogs.utility",
    "cogs.embeds"
]

if __name__ == "__main__":
    for ext in initial_extensions:
        try:
            bot.load_extension(ext)
            print(f"✅ Cog cargado: {ext}")
        except Exception as e:
            print(f"❌ Error cargando {ext}: {e}")

bot.run(TOKEN)
