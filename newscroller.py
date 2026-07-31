#!/usr/bin/env python
# Name: newscroller.py
# Gathers news headlines from RSS feeds then sends to RGB matrix newscroller
# https://feedparser.readthedocs.io/en/latest/
# Commmon RSS Elements: https://feedparser.readthedocs.io/en/latest/common-rss-elements/

import feedparser
import time
from bs4 import BeautifulSoup
import html
import re
import subprocess
import random
from datetime import datetime

DEBUG_MODE = False  # set to True to enable single feed debugging and to output debug print statements
DUMMY_HEADLINES = False  # set to true to feed dummy headlines for debugging purposes

basedir = "/home/pi/projects/led-matrix"  # location of script
news_filename = f"{basedir}/headlines.txt"  # local file to save news headlines

filter_keywords = r"apocalypse|chupacabra"  # regex patterns used for filtering out unwanted keywords in headlines
replacement_text = "Cats everywhere!"  # headliner text to replace unwanted headlines

# -------------- Setup For RGB Matrix ---------------- #
speed = 12  # The higher the number, the faster the scroll
rotation = "--led-pixel-mapper rotate:0"  # Screen rotation: replace :0 with :180 to rotate 180 degrees
fontpath = "/home/pi/rpi-rgb-led-matrix/fonts/clR6x12.bdf"
led_chain = 4  # the number of RGB panels chained together
y_positions = [
    0,
    4,
    8,
    12,
    16,
    20,
]  # the positions available on Y axis for scrolling text
scroller = (
    f"{basedir}/scrolling-text-example"  # executable for scrolling on the RGB matrix
)
number_of_loops = 1  # use -1 to infinite looping of scrolling text

# --------------- List of RSS sources --------------- #
if DEBUG_MODE:
    # test single URL
    newsurls = {"yahoonews": "http://news.yahoo.com/rss/"}

else:
    newsurls = {
        "nprnews": "http://www.npr.org/rss/rss.php?id=1001",
        "googletop": "https://news.google.com/news/headlines?ned=us",
        "googleworld": "https://news.google.com/news/headlines/section/topic/WORLD?ned=us",
        "googleus": "https://news.google.com/news/headlines/section/topic/NATION?ned=us",
        "googletech": "https://news.google.com/news/headlines/section/topic/TECHNOLOGY?ned=us",
        "googlewbiz": "https://news.google.com/news/headlines/section/topic/BUSINESS?ned=us",
        "googlescience": "https://news.google.com/news/headlines/section/topic/SCIENCE?ned=us",
        "googleent": "https://news.google.com/news/headlines/section/topic/ENTERTAINMENT?ned=us",
        "googlehealth": "https://news.google.com/news/headlines/section/topic/HEALTH?ned=us",
        "yahoonews": "http://news.yahoo.com/rss/",
        "sciencedailyenv": "https://www.sciencedaily.com/rss/top/environment.xml",
        "scifi": "https://www.scifinow.co.uk/feed/",
        "googlesyfy": "https://www.google.com/alerts/feeds/10241725619013902659/5279783658638593448",
        "marketwatch": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "theatlantic": "https://theatlantic.com/feed/all/",
    }


def dprint(*args, **kwargs):
    if DEBUG_MODE:
        print(*args, **kwargs)


def parse_feed(rss_link):
    # Run the RSS news source through feed parser
    return feedparser.parse(rss_link)


def get_headlines(rss_link):
    # Extracts headlines from parsed rss feed (item --> title) and returns as list
    headlines = []
    feed = parse_feed(rss_link)
    for item in feed["items"]:
        # For each title, remove HTML tags like <b> </b>, &nbsp;, &amp; etc. for pretty format
        pretty_title = BeautifulSoup(item["title"], "html.parser").get_text(
            " ", strip=True
        )
        pretty_title = html.unescape(pretty_title)
        headlines.append(pretty_title)
    return headlines


def suppress_news(lines):
    # I don't want to know about these topics, so suppress them
    # Replace these headlines with something more calm
    pattern = re.compile(filter_keywords, re.IGNORECASE)
    new_list = [replacement_text if pattern.search(line) else line for line in lines]
    return new_list


def save_to_file(filename, list):
    # Save all headlines to a file
    # add newline after each headline
    file = open(filename, "w")
    for i in list:
        file.write(i)
        file.write("\n")
    file.close()
    print(f"Headlines saved to {filename}")


def random_color():
    # generate random RGB values for text color
    color = [  # 0-255
        random.randint(0, 255),
        random.randint(0, 255),
        random.randrange(256),  # alternate way for the same thing
    ]
    return color


def scroll(text):
    # Scroll text on the RGB matrix using the scroller executable
    dprint(text)  # DEBUG
    color = ",".join(
        str(i) for i in random_color()
    )  # comma-separated rgb values like 255,0,255
    # choose a random Y position for scrolling text
    pos = random.choice(y_positions)
    # Escape all quotes inside the text string so that they are processed as literal quotes rather than the start/stop of a quoted string
    textstr = text.replace('"', '\\"')
    cmd = f'sudo {scroller} -s {speed} --led-chain={led_chain} -f {fontpath} -l {number_of_loops} -C {color} -y {pos} {rotation} "{textstr}"'
    dprint(cmd + "\n")  # DEBUG
    try:
        # subprocess.run(cmd, shell=True, capture_output=False, stdout=subprocess.DEVNULL)
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print("Command failed:")
        print(e.stderr)


def main():
    while True:
        if not DUMMY_HEADLINES:
            # Collate all headlines from news sources and save to a master list
            dprint("Collating all headlines...")
            all_headlines = []
            for source in newsurls:
                all_headlines.extend(get_headlines(newsurls[source]))
            save_to_file(filename=news_filename, list=all_headlines)
        else:
            with open(f"{basedir}/dummy_headlines.txt") as file:
                all_headlines = [
                    line.strip() for line in file
                ]  # strips whitespace and newlines from each line

        # Filter out unwanted headlines
        suppressed_headlines = suppress_news(all_headlines)
        if DEBUG_MODE:
            save_to_file(
                filename="/home/pi/projects/led-matrix/suppressed_headlines.txt",
                list=suppressed_headlines,
            )

        # scroll the current date and time before scrolling the headlines
        today = datetime.now().astimezone()
        date = today.strftime(  # Date format: Wednesday, July 29, 2026 09:17:23 PM MDT
            "%A  %B %d, %Y  %I:%M %p %Z"
        )
        scroll(date)

        # scroll the headlines
        for headline in suppressed_headlines:
            scroll(headline)
            time.sleep(1)  # delay before displaying next headline


if __name__ == "__main__":
    main()
