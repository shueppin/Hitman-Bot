from hitman_secrets import BOT_TOKEN, ALLOWED_DISCORD_SERVERS, SEASONS_ANNOUNCEMENT_CHANNEL_ID, RECORDS_CHANNEL_ID, GENERAL_CHANNEL_ID, MASTERY_CHANNEL_ID
from hitman_monitor import HitmanMonitor

from nextcord.ext import commands, tasks
from nextcord import Interaction, SlashOption
import nextcord
import aiohttp
import io
import json
import asyncio
from pathlib import Path
import os
import random
from typing import TypedDict, Dict, Tuple, List


CHECK_INTERVAL = 600  # seconds

DATA_JSON = Path(__file__).parent / "data.json"

CONTRACTS_LEVELS = [
    "The Showstopper (Paris)",
    "Holiday Hoarders (Paris)",
    "World of Tomorrow (Sapienza)",
    "A Gilded Cage (Marrakesh)",
    "Club 27 (Bangkok)",
    "Freedom Fighters (Colorado)",
    "Situs Inversus (Hokkaido)",
    "Hokkaido Snow Festival (Hokkaido)",
    "The Finish Line (Miami)",
    "Three-Headed Serpent (Santa Fortuna)",
    "Chasing a Ghost (Mumbai)",
    "Another Life (Whittleton Creek)",
    "Shadows in the Water (Ambrose Island)",
    "The Ark Society (Isle of Sgàil)",
    "Golden Handshake (New York)",
    "The Last Resort (Haven Island)",
    "On Top of the World (Dubai)",
    "Death in the Family (Dartmoor)",
    "Apex Predator (Berlin)",
    "End of an Era (Chongqing)",
    "The Farewell (Mendoza)",
]

CONTRACT_CHANCES = [
    60,    # Paris
    60,    # Paris
    100,   # Sapienza
    100,   # Marrakesh
    100,   # Bangkok
    99,    # Colorado, kei Bock uf Colorado (-:
    60,    # Hokkaido
    60,    # Hokkaido
    100,   # Miami
    99,    # Santa Fortuna, kei Bock uf Kolumbie (-:
    100,   # Mumbai
    100,   # Whittleton Creek
    100,   # Ambrose Island
    100,   # Isle of Sgail
    100,   # New York
    100,   # Haven Island
    100,   # Dubai
    100,   # Dartmoor
    99,    # Berlin, kei Bock uf die Dütsche (-:
    100,   # Chongqing
    100    # Mendoza
]


class LocationDataType(TypedDict):
    max_mastery: int
    mastery: Dict[str, int]  # The key is the string of the user id, the value their mastery level.
    levels: Dict[str, Dict[str, Tuple[int, int, str]]]  # The outer key is the level name, the inner key is a string of the user id. The value is minutes, seconds, comment.


'''
Helper functions
'''


def load_json(filename):
    with open(filename) as json_file:
        return json.load(json_file)


def save_json(filename: Path, write_data: dict):
    temp_file = filename.with_suffix(".tmp")
    with open(temp_file, "w") as f:
        json.dump(write_data, f, indent=2)
    os.replace(temp_file, filename)  # Atomic replace to prevent corruption on crash


def get_levels_and_locations() -> Dict[str, str]:
    output = {}
    for location in data:
        for level in data[location]["levels"]:
            output[level] = location

    return output


def get_locations() -> List[str]:
    return list(data.keys())


def get_levels(display_location_in_name=False) -> List[str]:
    if display_location_in_name:
        output = []
        for level, location in get_levels_and_locations().items():
            output.append(f'{level} ({location})')

        return output
    else:
        return list(get_levels_and_locations().keys())


def remove_location_from_level_name(level: str) -> str:
    for location in get_locations():
        level = level.replace(f" ({location})", "")

    return level


def autocomplete_handler(current: str, items: List):
    # Dynamically filter the levels list
    return [
        level for level in items
        if current.lower() in level.lower()
    ][:25]  # Discord Limit


def format_times_and_users(user_times_dictionary: Dict[str, Tuple[int, int, str]]) -> str:
    # Sort the items of the dictionary by lexicographic order of minutes and seconds
    sorted_items = sorted(user_times_dictionary.items(), key=lambda tup: (tup[1][0], tup[1][1]))  # Create a tuple with the minutes and the seconds and let python sort them lexicographically

    output = ""
    for i, item in enumerate(sorted_items):
        # Unpack the values
        user_id_string, value_tuple = item
        user_id = int(user_id_string)
        minutes, seconds, comment = value_tuple

        if comment:
            output += f"\n{i+1}. <@{user_id}> {minutes}:{seconds:02} ({comment})"
        else:
            output += f"\n{i + 1}. <@{user_id}> {minutes}:{seconds:02}"

    return output


def split_by_lines(text, max_len=1990):
    lines = text.split("\n")
    chunks = []
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            chunks.append(current)
            current = line
        else:
            current += ("\n" if current else "") + line

    if current:
        chunks.append(current)

    return chunks


'''
Init part
'''


bot = commands.Bot(description='HITMAN Helper Bot')

hitman_monitor = HitmanMonitor()

data: Dict[str, LocationDataType] = load_json(DATA_JSON)
data_lock = asyncio.Lock()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    hitman_monitor_task.start()


'''
Automated tasks
'''


@tasks.loop(seconds=CHECK_INTERVAL)
async def hitman_monitor_task():
    try:
        article_name, article_url, roadmap_image_url = await hitman_monitor.check_for_change()

        if article_name:
            channel = bot.get_channel(SEASONS_ANNOUNCEMENT_CHANNEL_ID)
            file = None

            if channel:
                # If image exists, download and attach it
                if roadmap_image_url:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(roadmap_image_url) as resp:
                            if resp.status == 200:
                                image_data = await resp.read()

                                filename = "Roadmap.jpg"
                                file = nextcord.File(fp=io.BytesIO(image_data), filename=filename)

                await channel.send(
                    content=f"# New Hitman Roadmap \n## {article_name} \nCheck out the whole article [here](<{article_url}>) \n\n@everyone",
                    file=file,
                    allowed_mentions=nextcord.AllowedMentions(everyone=True)
                )

    except Exception as e:
        print(f"Error in monitor task: {e}")


'''
Records commands
'''


@bot.slash_command(name="time", description='Add a new Silent Assassin time on difficulty Professional for a level', guild_ids=ALLOWED_DISCORD_SERVERS)
async def time(
        interaction: Interaction,
        level: str = SlashOption(description="Level name", autocomplete=True),
        minutes: int = SlashOption(description="Minutes"),
        seconds: int = SlashOption(description="Seconds (between 0 and 60)"),
        person: nextcord.Member = SlashOption(description="Person who has done this time", required=False),
        comment: str = SlashOption(description='Comment for the time, e.g. "Suit Only"', required=False),
        force: bool = SlashOption(description="Force the new time, even if it is worse than the one already listed", required=False),
):
    # Ensure the correct channel
    if interaction.channel.id != RECORDS_CHANNEL_ID:
        await interaction.response.send_message(f'Please use this command in the `records` channel.', ephemeral=True)
        return

    # Default values
    if person is None:
        person = interaction.user
    person_key = str(person.id)

    if comment is None:
        comment = ""

    clean_level = remove_location_from_level_name(level)

    # Ensure correct values
    if minutes < 0 or seconds < 0 or seconds > 60:
        await interaction.response.send_message(f'Please use only valid minutes and seconds.', ephemeral=True)
        return

    if minutes == 0 and seconds == 0:
        await interaction.response.send_message(f'Please use a valid time.', ephemeral=True)
        return

    if clean_level not in get_levels():
        await interaction.response.send_message(f'Unknown level **{clean_level}**.', ephemeral=True)
        return

    # Set the time
    async with data_lock:
        location = get_levels_and_locations()[clean_level]

        # Check whether there is already a better time
        if person_key in data[location]['levels'].keys():
            old_minutes: int = data[location]['levels'][clean_level][person_key][0]
            old_seconds: int = data[location]['levels'][clean_level][person_key][1]

            if minutes > old_minutes or (minutes == old_minutes and seconds >= old_seconds):
                if not force:
                    await interaction.response.send_message(f'<@{person.id}> already has a better time ({minutes}:{seconds:02}) for **{clean_level}**. \nUse `force = True` to overwrite this.', ephemeral=True)
                    return

        # Add the new time to the JSON and display a message
        data[location]['levels'][clean_level][person_key] = (minutes, seconds, comment)
        save_json(DATA_JSON, data)

    await interaction.response.send_message(f'Added time of {minutes}:{seconds:02} to **{clean_level}** for <@{person.id}>.')  # 02 pad with zeros to a total width of 2 characters


@bot.slash_command(name="records", description="Display all records, or just the ones for a specific level", guild_ids=ALLOWED_DISCORD_SERVERS)
async def records(
        interaction: Interaction,
        location: str = SlashOption(description="Location", autocomplete=True, required=False),
        level: str = SlashOption(description="Level name", autocomplete=True, required=False)
):
    # Output the whole message. If we get a level, we display only this, if we get a location we display all its levels and otherwise every level.
    async with (data_lock):
        output = "# Records - Difficulty Professional, Silent Assassin\n"

        if level:
            clean_level = remove_location_from_level_name(level)
            location = get_levels_and_locations()[clean_level]

            output += f"\n**{level}**"
            output += format_times_and_users(data[location]['levels'][clean_level]) + "\n"

        else:
            # If we don't get a location we show all
            if location is None:
                wanted_locations = get_locations()
            else:
                wanted_locations = [location]

            for location in get_locations():
                if location in wanted_locations:
                    output += f"\n## {location}"

                    for lvl in data[location]['levels']:
                        output += f"\n**{lvl}**"

                        if data[location]['levels'][lvl]:
                            output += format_times_and_users(data[location]['levels'][lvl])
                        else:
                            output += "\nNo times recorded"

                        output += "\n"

    # Send the message as chunks
    chunks = split_by_lines(output)
    await interaction.response.send_message(chunks[0], ephemeral=True)

    for chunk in chunks[1:]:
        await interaction.followup.send("\n" + chunk, ephemeral=True)


@bot.slash_command(name="add_level", description="Add a new level in a location", guild_ids=ALLOWED_DISCORD_SERVERS)
async def add_level(
        interaction: Interaction,
        level_name: str = SlashOption(description="Level name (without the location)"),
        location: str = SlashOption(description="Location name"),
):
    # Ensure the correct channel
    if interaction.channel.id != RECORDS_CHANNEL_ID:
        await interaction.response.send_message(f'Please use this command in the `records` channel.', ephemeral=True)
        return

    # Ensure correct values
    if location not in get_locations():
        await interaction.response.send_message(f'Unknown location **{location}**.', ephemeral=True)
        return

    # Add the new level
    async with data_lock:
        if level_name in data[location]['levels']:
            await interaction.response.send_message(f"A level with that name already exists for **{location}**.", ephemeral=True)
            return

        data[location]['levels'][level_name] = {}
        save_json(DATA_JSON, data)

    await interaction.response.send_message(f'Added new level **{level_name}** to **{location}**.')


@bot.slash_command(name="rename_level", description="Rename a level", guild_ids=ALLOWED_DISCORD_SERVERS)
async def rename_level(
        interaction: Interaction,
        old_level_name: str = SlashOption(description="Actual level name", autocomplete=True),
        new_level_name: str = SlashOption(description="New level name"),
):
    # Ensure the correct channel
    if interaction.channel.id != RECORDS_CHANNEL_ID:
        await interaction.response.send_message(f'Please use this command in the `records` channel.', ephemeral=True)
        return

    location = get_levels_and_locations()[old_level_name]

    # Ensure correct values
    if old_level_name not in data[location]['levels']:
        await interaction.response.send_message(f'Level **{old_level_name}** does not exist.', ephemeral=True)
        return

    # Get and remove the old data and write it where under the new data
    async with data_lock:
        if new_level_name in data[location]['levels']:
            await interaction.response.send_message(f"A level with that name already exists for **{location}**.", ephemeral=True)
            return

        level_data = data[location]['levels'].pop(old_level_name)
        data[location]['levels'][new_level_name] = level_data
        save_json(DATA_JSON, data)

    await interaction.response.send_message(f"Level **{old_level_name}** has been renamed to **{new_level_name}**.")


@bot.slash_command(name="list_levels", description="List all levels for all or a specific location", guild_ids=ALLOWED_DISCORD_SERVERS)
async def list_levels(
        interaction: Interaction,
        location: str = SlashOption(description="Location", autocomplete=True, required=False)
):
    # Ensure the correct channel
    if interaction.channel.id != RECORDS_CHANNEL_ID:
        await interaction.response.send_message(f'Please use this command in the `records` channel.', ephemeral=True)
        return

    # If we don't get a location we show all
    if location is None:
        wanted_locations = get_locations()
    else:
        wanted_locations = [location]

    # Output the whole message
    async with (data_lock):
        output = "# Available levels"

        for location in get_locations():
            if location in wanted_locations:
                output += f"\n\n**{location}**"
                for level in data[location]['levels']:
                    output += f"\n- {level}"

    await interaction.response.send_message(f"{output}", ephemeral=True)


'''
Mastery commands
'''


@bot.slash_command(name="mastery", description="Show the mastery of all players for all or for a specific location", guild_ids=ALLOWED_DISCORD_SERVERS)
async def mastery(
        interaction: Interaction,
        location: str = SlashOption(description="Location", autocomplete=True, required=False)
):
    # If we don't get a location we show all
    if location is None:
        wanted_locations = get_locations()
    else:
        wanted_locations = [location]

    # Output the whole message
    async with (data_lock):
        output = "# Mastery levels"

        for location in get_locations():
            if location in wanted_locations:
                output += f"\n\n**{location}**"
                for person_id in data[location]['mastery']:
                    output += f"\n- <@{person_id}>: Mastery {data[location]['mastery'][person_id]}/{data[location]['max_mastery']}"

        # Send the message as chunks
        chunks = split_by_lines(output)
        await interaction.response.send_message(chunks[0], ephemeral=True)

        for chunk in chunks[1:]:
            await interaction.followup.send("\n" + chunk, ephemeral=True)


@bot.slash_command(name="set_mastery", description='Set the mastery level for a location', guild_ids=ALLOWED_DISCORD_SERVERS)
async def set_mastery(
        interaction: Interaction,
        location: str = SlashOption(description="Location", autocomplete=True),
        mastery_level: int = SlashOption(description="Mastery level"),
):
    # Ensure the correct channel
    if interaction.channel.id != MASTERY_CHANNEL_ID:
        await interaction.response.send_message(f'Please use this command in the `mastery` channel.', ephemeral=True)
        return

    # Ensure correct values
    if location not in get_locations():
        await interaction.response.send_message(f'Unknown location **{location}**.', ephemeral=True)
        return

    if mastery_level < 1 or mastery_level > data[location]['max_mastery']:
        await interaction.response.send_message(f"Mastery ranges from 1 to {data[location]['max_mastery']} in {location}.", ephemeral=True)
        return

    # Set the data
    async with data_lock:
        person_key = str(interaction.user.id)
        data[location]['mastery'][person_key] = mastery_level

        save_json(DATA_JSON, data)

    await interaction.response.send_message(f'<@{interaction.user.id}> reached **Mastery {mastery_level}** in **{location}**.')  # 02 pad with zeros to a total width of 2 characters


'''
General commands
'''


@bot.slash_command(name="contracts", description="List random locations for contracts", guild_ids=ALLOWED_DISCORD_SERVERS)
async def contracts(
        interaction: Interaction,
        number_of_contracts: int = SlashOption(description="How many maps to generate (default 2)", default=2, required=False),
):
    # Ensure the correct channel
    if interaction.channel.id != GENERAL_CHANNEL_ID:
        await interaction.response.send_message(f'Please use this command in the `general` channel.', ephemeral=True)
        return

    # Ensure correct data
    if number_of_contracts < 1:
        await interaction.response.send_message('Please specify a valid number.', ephemeral=True)
        return

    retry : bool = True
    attempts : int = 0
    while retry:
        retry = False
        result = random.choices(CONTRACTS_LEVELS, weights=CONTRACT_CHANCES, k=number_of_contracts)

        # Check if result contains no duplicates
        for contract_possibility in CONTRACTS_LEVELS:
            if result.count(contract_possibility) >= 2:
                retry = True  
                attempts += 1

        # Some exit-possibilities such that the loop is not infinite (/ very long)
        # This will allow duplicates
        if number_of_contracts >= len(CONTRACTS_LEVELS)//2:
            retry = False
        if attempts >= 100:
            retry = False
    

    await interaction.response.send_message("\n".join(result))


'''
Discord Autocomplete functions
'''


@time.on_autocomplete("level")
@records.on_autocomplete("level")
async def extended_level_autocomplete(interaction: Interaction, current: str):
    return autocomplete_handler(current, get_levels(display_location_in_name=True))


@rename_level.on_autocomplete("old_level_name")
async def simple_level_autocomplete(interaction: Interaction, current: str):
    return autocomplete_handler(current, get_levels())


@add_level.on_autocomplete("location")
@list_levels.on_autocomplete("location")
@mastery.on_autocomplete("location")
@records.on_autocomplete("location")
@set_mastery.on_autocomplete("location")
async def location_autocomplete(interaction: Interaction, current: str):
    return autocomplete_handler(current, get_locations())


bot.run(BOT_TOKEN)
