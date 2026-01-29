#!/usr/bin/env python3
"""
Telegram Session String Generator

This script generates a session string that can be used for Telegram authentication
with the Telegram MCP server. The session string allows for portable authentication
without storing session files.

Usage:
    python session_string_generator.py

Requirements:
    - telethon
    - python-dotenv

Note on ID Formats:
When using the MCP server, please be aware that all `chat_id` and `user_id`
parameters support integer IDs, string representations of IDs (e.g., "123456"),
and usernames (e.g., "@mychannel").
"""

import os
import sys
import asyncio

# Check if telethon is installed
try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except ImportError:
    print("❌ Error: 'telethon' module is not installed")
    print("\nPlease install it first:")
    print("  pip install -r requirements.txt")
    print("\nOr install directly:")
    print("  pip install telethon python-dotenv")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: 'python-dotenv' module is not installed")
    print("\nPlease install it first:")
    print("  pip install -r requirements.txt")
    print("\nOr install directly:")
    print("  pip install python-dotenv")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()


def main() -> None:
    API_ID = os.getenv("TELEGRAM_API_ID")
    API_HASH = os.getenv("TELEGRAM_API_HASH")

    if not API_ID or not API_HASH:
        print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
        print("Create an .env file with your credentials from https://my.telegram.org/apps")
        sys.exit(1)

    # Convert API_ID to integer
    try:
        API_ID = int(API_ID)
    except ValueError:
        print("Error: TELEGRAM_API_ID must be an integer")
        sys.exit(1)

    print("\n----- Telegram Session String Generator -----\n")
    print("This script will generate a session string for your Telegram account.")
    print(
        "You will be asked to enter your phone number and the verification code sent to your Telegram app."
    )
    print("The generated session string can be added to your .env file.")
    print(
        "\nYour credentials will NOT be stored on any server and are only used for local authentication.\n"
    )

    try:
        # Run the async session generation
        asyncio.run(generate_session(API_ID, API_HASH))
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        print("Failed to generate session string. Please try again.")
        sys.exit(1)


async def generate_session(api_id: int, api_hash: str) -> None:
    """Generate a Telegram session string asynchronously."""
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start()

    # Get the session string
    session_string = client.session.save()

    await client.disconnect()

    print("\nAuthentication successful!")
    print("\n----- Your Session String -----")
    print(f"\n{session_string}\n")
    print("Add this to your .env file as:")
    print(f"TELEGRAM_SESSION_STRING={session_string}")
    print("\nIMPORTANT: Keep this string private and never share it with anyone!")
    print("WARNING: This session string was printed to your terminal. Consider clearing your terminal history.")

    # Optional: auto-update the .env file
    choice = input(
        "\nWould you like to automatically update your .env file with this session string? (y/N): "
    )
    if choice.lower() == "y":
        try:
            # Read the current .env file
            with open(".env", "r") as file:
                env_contents = file.readlines()

            # Update or add the SESSION_STRING line
            session_string_line_found = False
            for i, line in enumerate(env_contents):
                if line.startswith("TELEGRAM_SESSION_STRING="):
                    env_contents[i] = f"TELEGRAM_SESSION_STRING={session_string}\n"
                    session_string_line_found = True
                    break

            if not session_string_line_found:
                env_contents.append(f"TELEGRAM_SESSION_STRING={session_string}\n")

            # Write back to the .env file
            with open(".env", "w") as file:
                file.writelines(env_contents)

            # Set restrictive permissions (owner read/write only)
            os.chmod(".env", 0o600)

            print("\n.env file updated successfully!")
        except Exception as e:
            print(f"\nError updating .env file: {e}")
            print("Please manually add the session string to your .env file.")


if __name__ == "__main__":
    main()
