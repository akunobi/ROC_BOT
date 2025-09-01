import discord
from discord.ext import commands
import aiohttp
import json
import os
import random
import string

LINKS_FILE = "roblox_links.json"

class Roblox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.links = self.load_links()

    def load_links(self):
        if os.path.exists(LINKS_FILE):
            with open(LINKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_links(self):
        with open(LINKS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.links, f, indent=4, ensure_ascii=False)

    def generate_code(self, length=6):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    # ✅ .connect → genera código
    @commands.command()
    async def connect(self, ctx):
        user_id = str(ctx.author.id)
        if user_id in self.links:
            return await ctx.send("✅ Ya tienes vinculada una cuenta. Usa `.check` para verla.")

        code = self.generate_code()
        if "pending" not in self.links:
            self.links["pending"] = {}

        self.links["pending"][user_id] = code
        self.save_links()

        await ctx.send(
            f"🔗 Para vincular tu cuenta Roblox:\n"
            f"1. Ve a tu perfil de Roblox.\n"
            f"2. Pon este código en tu **Descripción** o **Estado**: `{code}`\n"
            f"3. Luego escribe `.verify <usuario_roblox>`"
        )

    # ✅ .verify <usuario> → comprueba si el código está en su perfil
    @commands.command()
    async def verify(self, ctx, username: str):
        user_id = str(ctx.author.id)
        if "pending" not in self.links or user_id not in self.links["pending"]:
            return await ctx.send("❌ No tienes ninguna verificación pendiente. Usa `.connect` primero.")

        code = self.links["pending"][user_id]

        async with aiohttp.ClientSession() as session:
            # Obtener datos del usuario por username
            async with session.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}) as resp:
                data = await resp.json()
                if not data["data"]:
                    return await ctx.send("❌ Usuario de Roblox no encontrado.")
                roblox_id = data["data"][0]["id"]

            # Obtener biografía
            async with session.get(f"https://users.roblox.com/v1/users/{roblox_id}") as resp:
                profile = await resp.json()

        bio = profile.get("description", "") or ""
        if code in bio:
            # Guardar relación Discord ↔ Roblox
            self.links[user_id] = {"roblox_id": roblox_id, "roblox_name": username}
            del self.links["pending"][user_id]
            self.save_links()
            await ctx.send(f"✅ {ctx.author.mention} tu cuenta de Roblox ha sido vinculada como **{username}**.")
        else:
            await ctx.send("❌ No encontré tu código en la biografía. Asegúrate de haberlo puesto y vuelve a intentar.")

    # ✅ .check @user → muestra Roblox info
    @commands.command()
    async def check(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        user_id = str(member.id)
        if user_id not in self.links:
            return await ctx.send(f"❌ {member.mention} no tiene vinculada ninguna cuenta. Usa `.connect`.")

        roblox_data = self.links[user_id]
        roblox_id = roblox_data["roblox_id"]
        roblox_name = roblox_data["roblox_name"]

        async with aiohttp.ClientSession() as session:
            # Avatar
            async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={roblox_id}&size=150x150&format=Png") as resp:
                avatar_data = await resp.json()
                avatar_url = avatar_data["data"][0]["imageUrl"]

        embed = discord.Embed(
            title=f"Roblox Info: {roblox_name}",
            description=f"🔗 [Perfil Roblox](https://www.roblox.com/users/{roblox_id}/profile)",
            color=0x00a2ff
        )
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Username", value=roblox_name, inline=True)
        embed.add_field(name="User ID", value=roblox_id, inline=True)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Roblox(bot))
