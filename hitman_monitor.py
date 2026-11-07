import aiohttp
import re
import typing


ROADMAP_JSON_URL = "https://ioi.dk/api/articles?type.group=type&type.tags=Roadmaps&universe.group=universe&universe.tags=HITMAN&location.group=location&location.tags=%23%23all_location%23%23&pagination.limit=20"
BASE_ARTICLE_URL = "https://ioi.dk"


class HitmanMonitor:
    def __init__(self):
        self.newest_image_url = None

    async def check_for_change(self) -> typing.Tuple[str, str, str]:
        """
        Checks whether there is a new article.
        If yes, it returns the name of the article, the article url and the Roadmap image URL, otherwise returns empty strings.
        """
        async with aiohttp.ClientSession() as session:
            # Fetch JSON
            async with session.get(ROADMAP_JSON_URL) as response:
                response.raise_for_status()
                json_data = await response.json()

            # Extract article name and link
            try:
                article_name = json_data["cards"][0]["title"]
                article_url = json_data["cards"][0]["link"]["url"]
            except KeyError as e:
                print("Could not extract name or URL:", e)
                return '', '', ''

            # Fetch article HTML
            if not "http" in article_url:
                # Make sure the url is valid
                article_url = BASE_ARTICLE_URL + article_url

            async with session.get(article_url) as response:
                response.raise_for_status()
                html = await response.text()

            # Extract image URL
            # Find first occurrence of "data-srcset"
            match = re.search(r'srcset="([^"]+)"', html)
            if not match:
                print("Could not find image")
                return '', '', ''

            srcset = match.group(1)
            # srcset may contain multiple URLs, take the first one
            roadmap_image_url = srcset.split(",")[0].strip().split(" ")[0]

            if not roadmap_image_url:
                print("No image URL")
                return '', '', ''

            # Compare with last seen image
            if self.newest_image_url == roadmap_image_url:
                return '', '', ''

            self.newest_image_url = roadmap_image_url
            return article_name, article_url, roadmap_image_url
