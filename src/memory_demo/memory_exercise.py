from __future__ import annotations
import asyncio
import uuid
import typer
import logging
import random
import os
from memory_demo.driver import ChatWithMemory
from memory_demo.llm_config import build_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer()

load_dotenv()
llm = build_chat_model()

async def generate_message(history) -> str:
    message_types = [
        "set a durable preference or stable trait (e.g., 'I love drinking green tea', 'I prefer traveling by train')",
        "provide a scheduled event or an important episodic fact (e.g., 'I'm traveling to the Swiss Alps next week departing on Monday', 'I went to the Italian Dolomites last year')",
    ]
    selected_type = random.choice(message_types)
    
    prompt = f"""Generate a single short sentence or question from a user to an AI assistant. 
    The message should {selected_type}. Do not include any other text or quotes. Try not to repeat the same message."""

    prompt_messages = history + [HumanMessage(content=prompt)]
    response = await llm.ainvoke(prompt_messages)
    synthetic_message = response.content.strip()
    history.append(HumanMessage(content=synthetic_message))
    return synthetic_message

async def run_exercise(user_count: int, question_count: int):
    ams_url = os.getenv("AGENT_MEMORY_SERVER_URL", "http://localhost:8080")
    chat = ChatWithMemory(ams_url=ams_url)
    iterations = user_count * question_count
    error_count = 0
    for i in range(1, user_count + 1):
        user_id = f"user{i}"
        
        def get_new_session_id():
            return str(uuid.uuid4())
            
        session_id = get_new_session_id()
        messages_until_session_change = random.randint(2, 5)
        message_counter = 0
        history = [SystemMessage(content="You are a helpful assistant.")]
        
        typer.echo(f"\n--- Processing for {user_id} ---")
        
        for _ in range(question_count):
            if message_counter >= messages_until_session_change:
                session_id = get_new_session_id()
                typer.echo(f"\n--- Session ID changed to {session_id} ---")
                messages_until_session_change = random.randint(2, 5)
            
            question = await generate_message(history)

            typer.echo(f"User (Session: {session_id}): {question}")
            async for response in chat.process_input_async(question, session_id, user_id):
                if not response:
                    error_count += 1
                    continue
                typer.echo(f"Assistant: {response.content}")

            typer.echo("-" * 20)
            message_counter += 1
            progress = (i - 1) * question_count + message_counter
            percentage = progress / iterations
            typer.echo(f"Progress: {percentage:.0%} User: {i} ({message_counter} of {question_count})")
            typer.echo("-" * 20)
    
    typer.echo(f"Generator error count: {error_count}")


@app.command()
def main(
    users: int = typer.Option(1, help="Number of users to process"),
    questions: int = typer.Option(100, help="Number of questions to ask per user"),
):
    typer.echo(f"Running Dynamic Memory Exercise with {users} users and {questions} questions each")
    if questions < 1:
        typer.echo("Error: questions parameter must be at least 1")
        raise typer.Exit(code=1)
    asyncio.run(run_exercise(users, questions))

if __name__ == "__main__":
    app()
