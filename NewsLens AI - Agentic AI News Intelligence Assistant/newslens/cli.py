from __future__ import annotations

import argparse
import asyncio
import json
import logging
from dataclasses import asdict
from pathlib import Path

from alembic import command
from alembic.config import Config as AlembicConfig

from newslens.briefings import BriefingService
from newslens.config import Settings
from newslens.discord_bot import NewsLensBot, format_research
from newslens.persistence.database import make_session_factory
from newslens.persistence.repository import NewsRepository
from newslens.pipeline import NewsPipeline
from newslens.research.agent import ResearchAgent


def _runtime(settings: Settings):
    sessions = make_session_factory(settings)
    repository = NewsRepository(sessions)
    pipeline = NewsPipeline(settings, repository)
    briefing = BriefingService(settings, repository)
    researcher = ResearchAgent(settings, sessions)
    return sessions, pipeline, briefing, researcher


async def _run(args: argparse.Namespace, settings: Settings) -> None:
    sessions, pipeline, briefing, researcher = _runtime(settings)
    try:
        if args.command == "ingest":
            print(json.dumps(asdict(await pipeline.run_once(limit=args.limit)), indent=2))
        elif args.command == "brief":
            print("\n\n".join((await briefing.generate()).to_discord_messages()))
        elif args.command == "ask":
            result = await researcher.research(args.question)
            print("\n\n".join(format_research(result)))
        elif args.command == "bot":
            if not settings.discord_bot_token:
                raise RuntimeError("DISCORD_BOT_TOKEN is required for the bot command")
            bot = NewsLensBot(settings, pipeline, briefing, researcher)
            try:
                await bot.start(settings.discord_bot_token)
            finally:
                await bot.close()
    finally:
        engine = sessions.kw.get("bind")
        if engine is not None:
            await engine.dispose()


def _migrate() -> None:
    root = Path(__file__).resolve().parent.parent
    config = AlembicConfig(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    command.upgrade(config, "head")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="newslens", description="NewsLens AI news intelligence PoC"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-db", help="Apply database migrations")
    subparsers.add_parser("brief", help="Generate a briefing from stored stories")
    subparsers.add_parser("bot", help="Run the Discord bot and scheduled pipeline")
    ingest = subparsers.add_parser("ingest", help="Discover and store relevant stories")
    ingest.add_argument("--limit", type=int, default=100)
    ask = subparsers.add_parser("ask", help="Research a question")
    ask.add_argument("question")
    args = parser.parse_args()
    settings = Settings()
    logging.basicConfig(
        level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    if args.command == "init-db":
        _migrate()
        return
    asyncio.run(_run(args, settings))


if __name__ == "__main__":
    main()
