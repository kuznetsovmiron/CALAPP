import asyncio
import uuid
import logging

# Import all ORM models to ensure they're registered with SQLAlchemy metadata
# This must happen before any database operations
import app.orm.user  # noqa: F401
import app.orm.session  # noqa: F401
import app.orm.token  # noqa: F401

from app.services.orchestrator.runner import AssistantRunner
from app.schemas.orchestrator.assistant import AssistantOutput

logging.basicConfig(level=logging.WARNING)

USER_ID = uuid.UUID("a49d8405-ad71-498f-b7d9-0b979c712e5d")  # temp user for testing


async def main():
    print("Calendar AI Assistant (type 'exit' to quit)\n")

    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                break
            output: AssistantOutput = await AssistantRunner.run(
                user_id=USER_ID,
                message=user_input,
            )
            if output.text:
                print(output.text)
            elif output.tool:
                print(f"[tool:{output.tool}] {output.arguments}")
            else:
                print("[empty output]")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    print("\nBye!")


if __name__ == "__main__":
    asyncio.run(main())