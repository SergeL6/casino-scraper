from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

def can_fetch(url, agent='*'):
    root = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    rp = RobotFileParser()
    rp.set_url(f"{root}/robots.txt")
    rp.read()
    return rp.can_fetch(agent, url)

urls = [
    "https://www.livescore.com/en-za/online-casinos/",
    "https://www.worldsportsbetting.co.za/promotions",
    "https://www.casino.org/en-za/minimum-deposit/",
]

for u in urls:
    try:
        print(can_fetch(u), u)
    except Exception as e:
        print(f"Error checking {u}: {e}")