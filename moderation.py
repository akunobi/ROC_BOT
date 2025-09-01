import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta

WARNS_FILE = "warns.json"
MUTES_FILE = "mutes.json"

WARN_DURATION_DAYS = 30
LOG_CHANNEL_NAME = "logs"

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warns = self.load_json(WARNS_FILE)
        self.mutes = self.load_json(MUTES_FILE)
        self.clear_expired_warns.start()
        self.check_mutes.start()  # Tarea automática para revisar mutes

    # 📂 Manejo de JSON
    def load_json(self, file):
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_json(self, file, data):
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # 🔁 Limpiar warns expirados
    @tasks.loop(hours=24)
    async def clear_expired_warns(self):
        changed = False
        for user_id in list(self.warns.keys()):
            new_list = []
            for warn in self.warns[user_id]:
                warn_time = datetime.fromisoformat(warn["date"])
                if datetime.utcnow() - warn_time < timedelta(days=WARN_DURATION_DAYS):
                    new_list.append(warn)
            if new_list != self.warns[user_id]:
                self.warns[user_id] = new_list
                changed = True
        if changed:
            self.save_json(WARNS_FILE, self.warns)

    # 🔁 Revisar expiración de mutes
    @tasks.loop(minutes=1)
    async def check_mutes(self):
        for guild in self.bot.guilds:
            muted_role = discord.utils.get(guild.roles, name="Muted")
            if not muted_role:
                continue
            for user_id, data in list(self.mutes.items()):
                unmute_time = datetime.fromisoformat(data["until"])
                if datetime.utcnow() >= unmute_time:
                    member = guild.get_member(int(user_id))
                    if member and muted_role in member.roles:
                        await member.remove_roles(muted_role, reason="Mute expirado")
                        log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
                        if log_channel:
                            await log_channel.send(f"🔊 {member} fue desmuteado automáticamente (mute expirado).")
                    del self.mutes[user_id]
                    self.save_json(MUTES_FILE, self.mutes)

    # 📌 Obtener canal de logs
    async def get_log_channel(self, guild):
        return discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)

    # ✅ Comando: mute temporal
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, time: str, *, reason="No especificado"):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            return await ctx.send("❌ No existe el rol `Muted`. Créalo y quítale permisos de escribir/hablar.")

        # ⏳ Convertir duración (ej: 10m, 1h, 1d)
        amount = int(time[:-1])
        unit = time[-1]
        if unit == "m":
            duration = timedelta(minutes=amount)
        elif unit == "h":
            duration = timedelta(hours=amount)
        elif unit == "d":
            duration = timedelta(days=amount)
        else:
            return await ctx.send("❌ Formato inválido. Usa `m`=minutos, `h`=horas, `d`=días. Ej: `.mute @user 10m spam`")

        until = datetime.utcnow() + duration

        await member.add_roles(muted_role, reason=reason)
        self.mutes[str(member.id)] = {"until": until.isoformat(), "reason": reason}
        self.save_json(MUTES_FILE, self.mutes)

        await ctx.send(f"🔇 {member.mention} fue muteado por {time}. Razón: {reason}")

        log_channel = await self.get_log_channel(ctx.guild)
        if log_channel:
            await log_channel.send(f"🔇 {member} muteado por {time}. Razón: {reason}")

    # ✅ Comando: unmute manual
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            return await ctx.send("❌ No existe el rol `Muted`.")

        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            self.mutes.pop(str(member.id), None)
            self.save_json(MUTES_FILE, self.mutes)
            await ctx.send(f"🔊 {member.mention} fue desmuteado.")
            log_channel = await self.get_log_channel(ctx.guild)
            if log_channel:
                await log_channel.send(f"🔊 {member} fue desmuteado manualmente por {ctx.author}.")
        else:
            await ctx.send(f"✅ {member.mention} no está muteado.")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
