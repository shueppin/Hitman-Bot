# Hitman Bot

A Discord bot for a single small server with some features for Hitman World of Assassination:
- Announcements for new seasons
- Random map selector for contract creation
- Internal level leaderboard for Silent Assassin records (with support for addition of new levels)
- Internal mastery tracker for maps

This project is designed for usage with Python 3.14.  
You need to bring your own discord server, discord bot and server to run this script on.

## Installation
1. Create a Discord Server  
2. Create a Discord application (bot) and install it in your server with the necessary permissions
3. Clone this repository to your server which will be running the Python script
4. Download the requirements from the requirements file
5. Create a `.env` file inside this directory with your data. It should look like the following template (the channel_ids can be the same if you want):
    ```dotenv
    BOT_TOKEN=your_discord_token
    ALLOWED_DISCORD_SERVER=your_discord_server_id

    GENERAL_CHANNEL_ID=channel_id_for_contracts_map_selection
    RECORDS_CHANNEL_ID=channel_id_for_level_time_changes_and_level_additions
    MASTERY_CHANNEL_ID=channel_id_for_level_mastery_changes
    SEASONS_ANNOUNCEMENT_CHANNEL_ID=channel_id_where_the_bot_posts_season_announcments
    ```
6. Start the discord bot using the script `discord_bot.py`. The bot will only run, wherever this script is running.