import os
import logging
import asyncio
import aiohttp

from dotenv import load_dotenv

import discord
from discord.ext import commands


# =========================
# CONFIG
# =========================

load_dotenv()

TOKEN = os.getenv("TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000")
BACKEND_TOKEN = os.getenv("PRIVILEGE_TOKEN")

if TOKEN is None:
    raise ValueError("no se encontró el TOKEN en el archivo .env")


# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("discord_bot")


# =========================
# INTENTS
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True


# =========================
# BOT
# =========================

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# poll_id -> { "message_id": int, "options": [str], "votes": {user_id: int} }
active_polls: dict = {}


# =========================
# BACKEND HELPERS
# =========================

async def backend_post(endpoint: str, payload: dict) -> dict | None:
    """Envía un POST al backend. Retorna el JSON o None si falla."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": BACKEND_TOKEN or ""
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}{endpoint}",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                return await resp.json()
    except Exception as e:
        logger.error(f"error llamando al backend ({endpoint}): {e}")
        return None


# =========================
# EVENTS
# =========================

@bot.event
async def on_ready():
    logger.info(f"bot conectado como {bot.user}")
    logger.info("servidores conectados:")

    for guild in bot.guilds:
        logger.info(f"  {guild.name} (id: {guild.id})")

        for channel in guild.channels:
            logger.info(f"    └─ {channel.name} (id: {channel.id})")

    logger.info("listo.")


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    logger.info(
        f"mensaje en #{message.channel} "
        f"por {message.author}: {message.content}"
    )

    if message.content.lower() == "hola":
        await message.channel.send("q onda 😭")

    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    """Registra votos cuando alguien reacciona a un mensaje de poll."""
    if user.bot:
        return

    # Buscar si la reacción pertenece a algún poll activo
    poll = next(
        (p for p in active_polls.values() if p["message_id"] == reaction.message.id),
        None
    )
    if poll is None:
        return

    emoji = str(reaction.emoji)
    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

    if emoji not in number_emojis:
        return

    option_index = number_emojis.index(emoji)
    if option_index >= len(poll["options"]):
        return

    # Un voto por usuario
    if user.id in poll["votes"]:
        # Quitar reacción anterior si ya votó
        prev_index = poll["votes"][user.id]
        if prev_index != option_index:
            prev_emoji = number_emojis[prev_index]
            try:
                await reaction.message.remove_reaction(prev_emoji, user)
            except discord.HTTPException:
                pass

    poll["votes"][user.id] = option_index
    logger.info(f"{user} votó opción {option_index + 1} en poll {reaction.message.id}")


@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"falta un argumento: `{error.param.name}`")
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("no tenés permisos para usar este comando.")
        return

    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send("este comando solo funciona en un servidor.")
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send(f"argumento inválido: {error}")
        return

    logger.error(f"error en comando: {error}")
    await ctx.send("algo explotó internamente 💀")


@bot.event
async def on_error(event, *args, **kwargs):
    logger.exception(f"error inesperado en evento: {event}")


# =========================
# CHECKS
# =========================

def is_admin():
    """Check: solo usuarios con el rol 'Admin'."""
    async def predicate(ctx):
        role = discord.utils.get(ctx.guild.roles, name="Admin")
        if role is None or role not in ctx.author.roles:
            raise commands.MissingPermissions(["Admin role"])
        return True
    return commands.check(predicate)


# =========================
# COMMANDS - GENERALES
# =========================

@bot.command()
async def ping(ctx):
    await ctx.send(f"pong 🏓 ({round(bot.latency * 1000)}ms)")


@bot.command()
@commands.guild_only()
async def server(ctx):
    await ctx.send(
        f"servidor: {ctx.guild.name}\n"
        f"miembros: {ctx.guild.member_count}"
    )


@bot.command()
@commands.guild_only()
@commands.has_permissions(manage_messages=True)
async def say(ctx, *, mensaje):
    await ctx.send(mensaje)


# =========================
# COMMANDS - POLLS
# =========================

@bot.command()
@commands.guild_only()
async def poll(ctx, pregunta: str, *opciones: str):
    """
    Crea un poll con 2 a 5 opciones.
    Uso: !poll "¿Pregunta?" "Opción 1" "Opción 2" ...
    """
    if len(opciones) < 2:
        await ctx.send("necesitás al menos 2 opciones.")
        return
    if len(opciones) > 5:
        await ctx.send("máximo 5 opciones.")
        return

    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

    description = "\n".join(
        f"{number_emojis[i]} {opcion}"
        for i, opcion in enumerate(opciones)
    )

    embed = discord.Embed(
        title=f"📊 {pregunta}",
        description=description,
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"creado por {ctx.author.display_name}")

    msg = await ctx.send(embed=embed)

    for i in range(len(opciones)):
        await msg.add_reaction(number_emojis[i])

    active_polls[msg.id] = {
        "message_id": msg.id,
        "question": pregunta,
        "options": list(opciones),
        "votes": {},
        "author_id": ctx.author.id,
        "channel_id": ctx.channel.id,
    }

    logger.info(f"poll creado: '{pregunta}' (msg_id={msg.id})")


@bot.command()
@commands.guild_only()
async def endpoll(ctx, message_id: int):
    """
    Cierra un poll, muestra el resumen y lo notifica al backend.
    Uso: !endpoll <message_id>
    """
    poll = active_polls.get(message_id)

    if poll is None:
        await ctx.send("no encontré ese poll.")
        return

    # Solo el creador o alguien con manage_messages puede cerrarlo
    is_creator = ctx.author.id == poll["author_id"]
    has_perms = ctx.author.guild_permissions.manage_messages
    if not is_creator and not has_perms:
        await ctx.send("solo el creador del poll o un moderador puede cerrarlo.")
        return

    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    options = poll["options"]
    votes = poll["votes"]

    # Contar votos por opción
    counts = [0] * len(options)
    for option_index in votes.values():
        counts[option_index] += 1

    total = sum(counts)

    results_lines = []
    for i, option in enumerate(options):
        pct = round((counts[i] / total) * 100) if total > 0 else 0
        results_lines.append(f"{number_emojis[i]} **{option}** — {counts[i]} voto(s) ({pct}%)")

    winner_index = counts.index(max(counts)) if total > 0 else None
    winner_text = f"🏆 ganador: **{options[winner_index]}**" if winner_index is not None else "sin votos."

    embed = discord.Embed(
        title=f"📊 resultados: {poll['question']}",
        description="\n".join(results_lines) + f"\n\n{winner_text}",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"total de votos: {total}")

    await ctx.send(embed=embed)

    # Notificar al backend (endpoint imaginario)
    payload = {
        "question": poll["question"],
        "options": options,
        "results": [
            {"option": options[i], "votes": counts[i]}
            for i in range(len(options))
        ],
        "total_votes": total,
        "winner": options[winner_index] if winner_index is not None else None,
        "guild_id": ctx.guild.id,
        "channel_id": poll["channel_id"],
        "message_id": message_id,
    }

    result = await backend_post("/api/polls/result", payload)
    if result:
        logger.info(f"poll {message_id} enviado al backend correctamente.")
    else:
        logger.warning(f"no se pudo notificar al backend sobre el poll {message_id}.")

    del active_polls[message_id]


# =========================
# COMMANDS - EMBEDS (Admin)
# =========================

@bot.command()
@commands.guild_only()
@is_admin()
async def embed(
    ctx,
    titulo: str,
    descripcion: str,
    color: str = "blurple"
):
    """
    Crea un embed personalizado. Solo para el rol Admin.
    Uso: !embed "Título" "Descripción" [color]
    Colores: blurple, green, red, yellow, orange, purple
    """
    color_map = {
        "blurple": discord.Color.blurple(),
        "green":   discord.Color.green(),
        "red":     discord.Color.red(),
        "yellow":  discord.Color.yellow(),
        "orange":  discord.Color.orange(),
        "purple":  discord.Color.purple(),
    }

    embed_color = color_map.get(color.lower(), discord.Color.blurple())

    embed_msg = discord.Embed(
        title=titulo,
        description=descripcion,
        color=embed_color
    )
    embed_msg.set_footer(text=f"publicado por {ctx.author.display_name}")

    await ctx.message.delete()
    await ctx.send(embed=embed_msg)


# =========================
# RUN
# =========================

bot.run(TOKEN)