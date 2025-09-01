import discord
from discord.ext import commands

class Embeds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Comando básico para enviar un embed
    @commands.command()
    async def embed(self, ctx, title: str, *, description: str = " "):
        """
        Crea un embed simple: .embed <titulo> <descripcion>
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Pedido por {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

        await ctx.send(embed=embed)

    # Ejemplo: embed de anuncio
    @commands.command()
    async def announce(self, ctx, *, message: str):
        """
        Anuncio en embed: .announce <mensaje>
        """
        embed = discord.Embed(
            title="📢 Anuncio",
            description=message,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Anunciado por {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

        await ctx.send(embed=embed)

    # Ejemplo: embed con campos
    @commands.command()
    async def info(self, ctx):
        """
        Muestra un embed con varios campos
        """
        embed = discord.Embed(
            title="ℹ️ Información del Servidor",
            description=f"Servidor: {ctx.guild.name}",
            color=discord.Color.green()
        )
        embed.add_field(name="Miembros", value=ctx.guild.member_count, inline=True)
        embed.add_field(name="Dueño", value=ctx.guild.owner, inline=True)
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Embeds(bot))
