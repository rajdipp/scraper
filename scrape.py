#!/usr/bin/python
# coding=utf-8
import argparse
import urllib
import datetime
import time
import ucsv as csv  # Ugh. Python CSV module does not handle unicode. This extension works around that.
import sys
import unidecode
from bs4 import BeautifulSoup
from MetaCriticScraper import MetaCriticScraper

# This maps VGChartz Platform names to MetaCritic Platform names
# VGChartz has sales data for nearly every platform (NES, Atari, etc...)
# MetaCritic does not keep track of some of those older platforms, 
# So in that case, the MetaCritic data will be blank
metacritic_platform = {'PS3': 'playstation-3',
                       'X360': 'xbox-360',
                       'PC': 'pc',
                       'WiiU': 'wii-u',
                       '3DS': '3ds',
                       'PSV': 'playstation-vita',
                       'iOS': 'ios',
                       'Wii': 'wii',
                       'DS': 'ds',
                       'PSP': 'psp',
                       'PS2': 'playstation-2',
                       'PS': 'playstation',
                       'XB': 'xbox',  # original xbox
                       'GC': 'gamecube',
                       'GBA': 'game-boy-advance',
                       'DC': 'dreamcast',
                       'PS4': 'playstation-4',
                       'XOne': 'xbox-one'
                       }

# List of platforms that we will include in our final results. All others will be omitted.
include_all_platforms = True
platforms_to_include = ['PS3', 'X360', 'WiiU', '3DS', 'PSV', 'iOS', 'Wii', 'PSP', 'PS4', 'XOne']


# Parses a single row of game information from a VGChartz table.
# Argument must be a BeautifulSoup'ed table row from VGChartz
def vgchartz_parse(row):
    game = {}
    data = row.find_all("td")
    if data:
        game["pos"] = data[0].get_text().strip()
        game["img_url"] = data[1].a.img.get('src')
        game["name"] = data[2].a.get_text().strip()
        game["url"] = data[2].a.get('href')
        if len(game["name"].split(sep="/")) > 1:
            # replace accented chars with ascii
            game["basename"] = unidecode.unidecode(data[2].a.get_text().strip().split(sep="/")[0].strip().lower().replace(' ', '-'))
        else:
            game["basename"] = game["url"].rsplit('/', 2)[1]
        game["platform"] = data[3].img.get('alt')
        game["publisher"] = data[4].get_text().strip()
        game["developer"] = data[5].get_text().strip()
        game["vgchartzscore"] = data[6].get_text().strip()
        game["criticscore"] = data[7].get_text().strip()
        game["userscore"] = data[8].get_text().strip()
        game["global_sales"] = data[9].get_text().strip()
        game["na_sales"] = data[10].get_text().strip()
        game["pal_sales"] = data[11].get_text().strip()
        game["jp_sales"] = data[12].get_text().strip()
        game["rest_sales"] = data[13].get_text().strip()
        game["release_date"] = data[14].get_text().strip()
        game["last_update"] = data[15].get_text().strip()

    return game


# Returns a url to MetaCritic based on game information from VGChartz.
# Returns None if MetaCritic does not support the platform.
# Argument must be a dictionary of game information from VGChartz.
def make_metacritic_url(vg_game_info):
    url = None
    if vg_game_info["platform"] in metacritic_platform:
        url = "http://www.metacritic.com/game/"
        url = url + metacritic_platform[vg_game_info["platform"]] + "/"
        url = url + vg_game_info["basename"]

    return url


# Command-line argument parser.
# You can also specific -h, --help at the command line 
# to see which arguments are supported
parser = argparse.ArgumentParser(description='VGChartz and MetaCritic Game Scraper.')
parser.add_argument('-m', '--max', dest='max_games', type=int, default=0,
                    help='Maximum number of games to scrape (0 to disable).')
parser.add_argument('-s', '--start', dest='start_game', type=int, default=1,
                    help='Start scraping from game N (1 to start at beginning).')
parser.add_argument('-w', '--wait', type=int, default=0,
                    help='Number of seconds to wait before each request to MetaCritc (0 to disable).')
args = parser.parse_args()
# debug
# args.max_games = 50

# Do we have games available to scrape?
# This lets us break out of our loop
games_available = True

current_game = 0  # Specific game we are ready to scrape. Used with start_game
games_scraped = 0  # Count of how many games we have scraped so far
vgchartz_page = 1  # Which VGChartz Page are we on

# Open our CSV file and write the headers
now = datetime.datetime.now()
csvfilename = "gamedata-" + now.strftime("%Y%m%d-%H_%M_%S") + ".csv"
csvfile = open(csvfilename, "wb")
gamewriter = csv.writer(csvfile)
gamewriter.writerow(['DateTime:', str(now)])
gamewriter.writerow(
    ['vg_name', 'vg_basename', 'vg_platform', 'vg_developer', 'vg_release_date', 'vg_last_update', 'vg_publisher',
     'vg_na_sales', 'vg_pal_sales', 'vg_jp_sales', 'vg_rest_sales', 'vg_global_sales', 'vg_vgchartzscore', 'vg_criticscore',
     'vg_userscore', 'mc_url', 'mc_release_date', 'mc_critic_score', 'mc_critic_outof', 'mc_critic_count',
     'mc_user_score', 'mc_user_count', 'mc_developer', 'mc_rating'])

start_time = time.time()
while games_available:
    # Connect to the VGChartz table. There are 1000 results per page.
    sys.stdout.write("Connecting to VGChartz Page " + str(vgchartz_page) + "...")
    vgchartz_url = "http://www.vgchartz.com/gamedb/games.php?page=" + str(
        vgchartz_page) + "&results=1000&name=&keyword=&console=&region=All&developer=&publisher=&goty_year=&genre=&" \
                         "boxart=Both&banner=Both&ownership=Both&order=Sales&showtotalsales=1&" \
                         "showpublisher=1&showvgchartzscore=1&" \
                         "shownasales=1&showdeveloper=1&showcriticscore=1&" \
                         "showpalsales=1&showreleasedate=1&" \
                         "showuserscore=1&showjapansales=1&showlastupdate=1&" \
                         "showothersales=1"
    # vgchartz_url = "file:vgchartz.htm"	# This is a DEBUG line - pulling vgchartz data from filesystem. Comment it out for production.
    vgchartz_conn = urllib.request.urlopen(vgchartz_url)
    vgchartz_html = vgchartz_conn.read()
    sys.stdout.write("connected.\n")

    vgsoup = BeautifulSoup(vgchartz_html, "lxml")
    rows = vgsoup.find("div", id="generalBody").find("table").find_all("tr")

    # For each row, scrape the game information from VGChartz
    # With that information, make a MetaCritic URL
    # Connect to MetaCritic and scrape more information about the game
    # Save all this information to the CSV file
    for row in rows:
        vg_game_info = vgchartz_parse(row)
        if vg_game_info:
            # Increment current_game counter. If the current game we are about to scrape is less than the start game
            # continue. This stops us from scraping it and contacting MetaCritic until we get to specific game we want
            current_game += 1
            if current_game < args.start_game:
                continue
            try:
                print(current_game, vg_game_info["name"])
            except UnicodeEncodeError:
                print(current_game, vg_game_info["basename"])
            # VGChartz has many thousands of games in its database. A lot are old and have no sales figures.
            # If a game has 0 sales, we are done looking for games. This table is sorted by sales, so all other games will also have 0 sales.
            if (vg_game_info["global_sales"] == "0.00"):
                print("No more games with sales figures. Ending.")
                games_available = False
                break

            if ((~include_all_platforms) & (vg_game_info["platform"] not in platforms_to_include)):
                print("Game not from interesting platform. Skipping.")
                continue

            # Make MetaCritic URL
            metacritic_url = make_metacritic_url(vg_game_info)
            if (args.wait > 0):
                time.sleep(args.wait)  # Option to sleep before connecting so MetaCritic doesn't throttle/block us.
            metacritic_scraper = MetaCriticScraper(metacritic_url)
            # Write everything to the CSV. MetaCritic data will be blank if we could not get it.
            gamewriter.writerow(
                [vg_game_info["name"],
                 vg_game_info["basename"],
                 vg_game_info["platform"],
                 vg_game_info["developer"],
                 vg_game_info["release_date"],
                 vg_game_info["last_update"],
                 vg_game_info["publisher"],
                 vg_game_info["na_sales"],
                 vg_game_info["pal_sales"],
                 vg_game_info["jp_sales"],
                 vg_game_info["rest_sales"],
                 vg_game_info["global_sales"],
                 vg_game_info["vgchartzscore"],
                 vg_game_info["criticscore"],
                 vg_game_info["userscore"],
                 metacritic_url,
                 metacritic_scraper.game["release_date"],
                 metacritic_scraper.game["critic_score"],
                 metacritic_scraper.game["critic_outof"],
                 metacritic_scraper.game["critic_count"],
                 metacritic_scraper.game["user_score"],
                 metacritic_scraper.game["user_count"],
                 metacritic_scraper.game["developer"],
                 metacritic_scraper.game["rating"]])
            # csvfile.flush()

            # We successfully scraped a single game. If we hit max_games, quit. Otherwise, loop to the next game.
            games_scraped += 1
            if (args.max_games > 0 and args.max_games == games_scraped):
                print("Reached max_games limit. Ending.")
                games_available = False
                break
    vgchartz_page += 1

csvfile.close()
elapsed_time = time.time() - start_time
print("Scraped", games_scraped, "games in", round(elapsed_time, 2), "seconds.")
print("Wrote scraper data to", csvfilename)
