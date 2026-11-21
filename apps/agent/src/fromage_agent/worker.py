"""LiveKit Agents worker: joins a Session room and echoes the Candidate's text.

The web app sends Candidate messages as text streams on topic "chat" and shows
text streams from the agent on the same topic.
"""

import asyncio
import logging
from datetime import UTC, datetime

from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from langfuse import Langfuse
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli

from fromage_agent.echo import EchoExaminer
from fromage_agent.llm import HaikuParaphraser
from fromage_agent.store import create_store

TOPIC = "chat"
ERROR_REPLY = "Désolé, une erreur est survenue. Veuillez réessayer."
ROOM_PREFIX = "session-"  # must match roomNameFor in apps/web/lib/livekit/session-token.ts
logger = logging.getLogger("fromage-agent")

load_dotenv()


def session_id_from_room(room_name: str) -> str:
    if not room_name.startswith(ROOM_PREFIX):
        raise ValueError(f"Unexpected room name {room_name!r}")
    return room_name[len(ROOM_PREFIX) :]


async def entrypoint(ctx: JobContext) -> None:
    session_id = session_id_from_room(ctx.room.name)
    langfuse = Langfuse()
    examiner = EchoExaminer(
        session_id,
        HaikuParaphraser(AsyncAnthropic(), langfuse),
        await create_store(),
        lambda: datetime.now(UTC),
    )
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_NONE)

    async def handle(reader: rtc.TextStreamReader, identity: str) -> None:
        try:
            reply = await examiner.on_candidate_message(await reader.read_all())
        except Exception:
            logger.exception("Could not answer Candidate message in Session %s", session_id)
            reply = ERROR_REPLY
        if reply:
            try:
                await ctx.room.local_participant.send_text(reply, topic=TOPIC)
            except Exception:
                logger.exception("Could not send reply in Session %s", session_id)

    # Keep references so tasks are not garbage-collected before they finish.
    tasks: set[asyncio.Task] = set()

    def on_stream(reader: rtc.TextStreamReader, identity: str) -> None:
        task = asyncio.create_task(handle(reader, identity))
        tasks.add(task)
        task.add_done_callback(tasks.discard)

    ctx.room.register_text_stream_handler(TOPIC, on_stream)
    ctx.add_shutdown_callback(lambda: asyncio.to_thread(langfuse.flush))


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
