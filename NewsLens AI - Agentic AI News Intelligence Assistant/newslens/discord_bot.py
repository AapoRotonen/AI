from __future__ import annotations

import logging

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import app_commands
from discord.ext import commands

from newslens.briefings import BriefingService
from newslens.config import Settings
from newslens.pipeline import NewsPipeline
from newslens.research.agent import ResearchAgent, ResearchResult
from newslens.security.access import is_discord_user_allowed
from newslens.security.discord import discord_link_url, escape_discord_text

logger = logging.getLogger(__name__)


def format_research(result: ResearchResult) -> list[str]:
    synthesis = result.synthesis
    lines = [f"**Research summary**\n{escape_discord_text(synthesis.summary)}"]
    summary_refs = [
        (index, item)
        for index, item in enumerate(result.evidence, start=1)
        if item.evidence_id in synthesis.evidence_ids
    ]
    if summary_refs:
        links = []
        for index, item in summary_refs:
            url = discord_link_url(str(item.url))
            if url:
                links.append(f"[{index}]({url})")
        lines[0] += "\n_Sources: " + " ".join(links) + "_"
    if synthesis.supported_claims:
        lines.append("**Evidence-backed claims**")
        for claim in synthesis.supported_claims[:5]:
            ids = claim.get("evidence_ids", "").split(",")
            refs = [item for item in result.evidence if item.evidence_id in ids]
            links = [
                f"[{index + 1}]({url})"
                for index, ref in enumerate(refs)
                if (url := discord_link_url(str(ref.url)))
            ]
            suffix = " " + " ".join(links) if links else ""
            lines.append(f"• {escape_discord_text(claim.get('claim', ''))}{suffix}")
    lines.append("**Sources**")
    for index, item in enumerate(result.evidence[:8], start=1):
        url = discord_link_url(str(item.url))
        source = (
            f"[{index}] **{item.source_type.value}** "
            + (
                f"[{escape_discord_text(item.title)}]({url})"
                if url
                else escape_discord_text(item.title)
            )
            + f" — {escape_discord_text(item.publisher)}"
        )
        lines.append(
            source + (f"\n> {escape_discord_text(item.excerpt[:260])}" if item.excerpt else "")
        )
    if synthesis.uncertain:
        lines.append(
            "**Uncertain / not established**\n"
            + "\n".join(f"• {escape_discord_text(item)}" for item in synthesis.uncertain[:4])
        )
    if synthesis.disagreements:
        lines.append(
            "**Source differences**\n"
            + "\n".join(f"• {escape_discord_text(item)}" for item in synthesis.disagreements[:4])
        )
    if synthesis.why_it_matters:
        lines.append(
            f"**Why it matters (analysis)**\n{escape_discord_text(synthesis.why_it_matters)}"
        )
    lines.append(f"_Sources available: {result.source_count}; types: {result.source_mix}_")
    full = "\n\n".join(lines)
    return [full[i : i + 1850] for i in range(0, len(full), 1850)] or ["No evidence was returned."]


class NewsLensBot(commands.Bot):
    def __init__(
        self,
        settings: Settings,
        pipeline: NewsPipeline,
        briefing: BriefingService,
        researcher: ResearchAgent,
    ) -> None:
        super().__init__(command_prefix="!", intents=discord.Intents.none())
        self.settings = settings
        self.pipeline = pipeline
        self.briefing_service = briefing
        self.researcher = researcher
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.tree.add_command(self._brief_command())
        self.tree.add_command(self._ask_command())
        self.tree.add_command(self._investigate_command())
        self.tree.add_command(self._finland_command())

    async def setup_hook(self) -> None:
        await self.tree.sync()
        self.scheduler.add_job(
            self._scheduled_run,
            "interval",
            minutes=self.settings.brief_interval_minutes,
            id="news_brief",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()

    async def close(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        await super().close()

    def _brief_command(self) -> app_commands.Command:
        @app_commands.command(
            name="brief", description="Discover news and generate the latest AI briefing"
        )
        async def brief(interaction: discord.Interaction) -> None:
            if not self._is_authorized(interaction.user.id):
                await self._deny_command(interaction)
                return
            await interaction.response.defer(thinking=True)
            try:
                stats = await self.pipeline.run_once()
                result = await self.briefing_service.generate()
                for index, message in enumerate(result.to_discord_messages()):
                    prefix = (
                        f"Discovery: {stats.discovered} candidates, {stats.stored} stored.\n"
                        if index == 0
                        else ""
                    )
                    await interaction.followup.send(
                        (prefix + message)[:2000],
                        allowed_mentions=discord.AllowedMentions.none(),
                    )
            except Exception as exc:
                logger.error("Discord /brief failed (%s)", type(exc).__name__)
                await interaction.followup.send(
                    "The briefing could not be generated. Check application logs.",
                    allowed_mentions=discord.AllowedMentions.none(),
                )

        return brief

    def _ask_command(self) -> app_commands.Command:
        @app_commands.command(name="ask", description="Research an AI/software news question")
        @app_commands.describe(question="A question about recent or historical AI news")
        async def ask(
            interaction: discord.Interaction, question: app_commands.Range[str, 3, 500]
        ) -> None:
            if not self._is_authorized(interaction.user.id):
                await self._deny_command(interaction)
                return
            await interaction.response.defer(thinking=True)
            await self._send_research(interaction, question)

        return ask

    def _investigate_command(self) -> app_commands.Command:
        @app_commands.command(
            name="investigate", description="Investigate a public news article URL"
        )
        @app_commands.describe(url="An HTTP(S) article URL")
        async def investigate(
            interaction: discord.Interaction, url: app_commands.Range[str, 8, 1000]
        ) -> None:
            if not self._is_authorized(interaction.user.id):
                await self._deny_command(interaction)
                return
            await interaction.response.defer(thinking=True)
            await self._send_research(interaction, f"Investigate this article: {url}")

        return investigate

    def _finland_command(self) -> app_commands.Command:
        @app_commands.command(
            name="finland", description="Research recent AI developments in Finland"
        )
        async def finland(interaction: discord.Interaction) -> None:
            if not self._is_authorized(interaction.user.id):
                await self._deny_command(interaction)
                return
            await interaction.response.defer(thinking=True)
            await self._send_research(
                interaction,
                "What important artificial intelligence, AI agents, coding-agent, company, product, or research developments are happening in Finland recently? Distinguish Finnish primary sources from independent reporting.",
            )

        return finland

    async def _send_research(self, interaction: discord.Interaction, request: str) -> None:
        try:
            result = await self.researcher.research(request)
            for message in format_research(result):
                await interaction.followup.send(
                    message[:2000],
                    allowed_mentions=discord.AllowedMentions.none(),
                )
        except Exception as exc:
            logger.error("Discord research command failed (%s)", type(exc).__name__)
            await interaction.followup.send(
                "Research could not be completed. Check application logs.",
                allowed_mentions=discord.AllowedMentions.none(),
            )

    def _is_authorized(self, user_id: int) -> bool:
        return is_discord_user_allowed(
            user_id,
            self.settings.discord_allowed_user_ids,
            self.settings.discord_allow_public_commands,
        )

    @staticmethod
    async def _deny_command(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "This command is not enabled for your account. Ask the NewsLens administrator.",
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )


async def _scheduled_run(self) -> None:
    try:
        stats = await self.pipeline.run_once()
        if self.settings.discord_brief_channel_id is None:
            logger.info(
                "Scheduled discovery ran without a publication channel",
                extra={"stored": stats.stored},
            )
            return
        channel = self.get_channel(self.settings.discord_brief_channel_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            logger.error("Configured brief channel is not available to the bot")
            return
        briefing = await self.briefing_service.generate()
        for message in briefing.to_discord_messages():
            await channel.send(message[:2000], allowed_mentions=discord.AllowedMentions.none())
    except Exception as exc:
        logger.error("Scheduled NewsLens pipeline failed (%s)", type(exc).__name__)
