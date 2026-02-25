"""
Discord Interactive Labeling Bot
---------------------------------
Run in WSL2 via OpenClaw. Fetches pending LabelingTasks from the FastAPI server
and sends them to Discord with interactive buttons for human labeling.

Usage:
    python scripts/discord_labeling_bot.py

Required env vars (in .env or shell):
    DISCORD_BOT_TOKEN          - Your Discord bot token
    DISCORD_LABELING_CHANNEL_ID - Channel ID to post labeling tasks
    API_BASE_URL               - FastAPI server URL (default: http://localhost:8000)
"""
import os
import discord
from discord import app_commands
from discord.ui import Button, View
import httpx
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_LABELING_CHANNEL_ID = int(os.getenv("DISCORD_LABELING_CHANNEL_ID", "0"))
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

if not DISCORD_BOT_TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN 未設定，請在 .env 檔案中設定")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# ── API helpers ────────────────────────────────────────────

async def fetch_next_task() -> dict | None:
    async with httpx.AsyncClient() as http:
        resp = await http.get(f"{API_BASE_URL}/api/labeling/pending?limit=1", timeout=5.0)
        tasks = resp.json()
        return tasks[0] if tasks else None


async def submit_label(task_id: int, human_label: str, status: str) -> None:
    async with httpx.AsyncClient() as http:
        await http.post(
            f"{API_BASE_URL}/api/labeling/{task_id}/submit",
            json={"human_label": human_label, "status": status},
            timeout=5.0,
        )


# ── Discord UI ─────────────────────────────────────────────

class LabelingView(View):
    def __init__(self, task_id: int):
        super().__init__(timeout=600)  # 10 分鐘內有效
        self.task_id = task_id

    @discord.ui.button(label="✅ 真實", style=discord.ButtonStyle.green)
    async def btn_real(self, interaction: discord.Interaction, button: Button):
        await self._submit(interaction, human_label="real", status="labeled", label_text="✅ 標記為真實")

    @discord.ui.button(label="❌ 假評論", style=discord.ButtonStyle.red)
    async def btn_fake(self, interaction: discord.Interaction, button: Button):
        await self._submit(interaction, human_label="fake", status="labeled", label_text="❌ 標記為假評論")

    @discord.ui.button(label="⏭️ 跳過", style=discord.ButtonStyle.grey)
    async def btn_skip(self, interaction: discord.Interaction, button: Button):
        await self._submit(interaction, human_label="skipped", status="skipped", label_text="⏭️ 已跳過")

    async def _submit(
        self,
        interaction: discord.Interaction,
        human_label: str,
        status: str,
        label_text: str,
    ):
        for item in self.children:
            item.disabled = True

        await submit_label(self.task_id, human_label, status)
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(label_text, ephemeral=True)

        next_task = await fetch_next_task()
        if next_task:
            await send_task(interaction.channel, next_task)
        else:
            await interaction.channel.send("🎉 所有待標記評論已完成！")


def build_embed(task: dict) -> discord.Embed:
    pre_label = task.get("pre_label") or "unknown"
    pre_conf = task.get("pre_confidence") or 0.0
    content = task.get("content_json") or {}
    text = content.get("text", "（無評論文字）")
    rating = content.get("rating") or 0
    author = content.get("author") or "匿名"
    date = content.get("date") or ""

    verdict_emoji = "❌" if pre_label == "fake" else "✅"
    verdict_zh = "假評論" if pre_label == "fake" else "真實"
    stars = "★" * int(rating) + "☆" * (5 - int(rating)) if rating else "—"
    color = discord.Color.red() if pre_label == "fake" else discord.Color.green()

    embed = discord.Embed(
        title=f"📋 待標記 #{task['id']}",
        description=f'"{text}"',
        color=color,
    )
    embed.add_field(name="評分", value=stars, inline=True)
    embed.add_field(name="作者", value=author, inline=True)
    embed.add_field(name="日期", value=date, inline=True)
    embed.add_field(
        name="🤖 LLM 建議",
        value=f"{verdict_emoji} {verdict_zh}（{pre_conf:.0%}）",
        inline=False,
    )
    return embed


async def send_task(channel: discord.TextChannel, task: dict) -> None:
    embed = build_embed(task)
    view = LabelingView(task["id"])
    await channel.send(embed=embed, view=view)


# ── Slash commands ─────────────────────────────────────────

@tree.command(name="labeling", description="開始標記待審評論")
async def cmd_labeling(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    task = await fetch_next_task()
    if task:
        await send_task(interaction.channel, task)
        await interaction.followup.send("已推送第一筆待標記評論 👆", ephemeral=True)
    else:
        await interaction.followup.send("目前沒有待標記的評論 🎉", ephemeral=True)


@tree.command(name="status", description="查詢系統狀態")
async def cmd_status(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with httpx.AsyncClient() as http:
        resp = await http.get(f"{API_BASE_URL}/api/status", timeout=5.0)
        data = resp.json()
    ollama = "✅" if data.get("ollama") == "ok" else "❌"
    msg = (
        f"**Review Trust Analyzer 狀態**\n"
        f"伺服器: ✅\n"
        f"Ollama ({data.get('ollama_model')}): {ollama}\n"
        f"待標記: {data.get('labeling_pending')} 筆\n"
        f"SerpAPI 剩餘: {data.get('serpapi_credits')} 次"
    )
    await interaction.followup.send(msg, ephemeral=True)


# ── Bot events ─────────────────────────────────────────────

@client.event
async def on_ready():
    await tree.sync()
    print(f"Bot 上線: {client.user}")
    print(f"API: {API_BASE_URL}")
    print(f"頻道 ID: {DISCORD_LABELING_CHANNEL_ID}")
    print("指令已同步，可在 Discord 使用 /labeling 和 /status")


if __name__ == "__main__":
    client.run(DISCORD_BOT_TOKEN)
