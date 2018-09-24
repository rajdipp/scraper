import sys
from MetaCriticScraper import MetaCriticScraper
import time
# Do we want to handle movies, tv shows, etc...?
# FIXME: Handle URL better

start_time = time.time()
scraper = MetaCriticScraper(sys.argv[1])
elapsed_time = time.time() - start_time
print("URL: " + scraper.game['url'])
print("Title: " + scraper.game['title'])
print("Platform: " + scraper.game['platform'])
print("Publisher: " + scraper.game['publisher'])
print("Release Date: " + scraper.game['release_date'])
print("Critic Score: " + scraper.game['critic_score'] + "/" + scraper.game['critic_outof'] + " (" + scraper.game['critic_count'] + " critics)")
print("User Score: " + scraper.game['user_score'] + " (" + scraper.game['user_count'] + " users)")
print("Developer: " + scraper.game['developer'])
print("Genre: " + scraper.game['genre'])
print("Rating: " + scraper.game['rating'])
print("Time to scrape: ", round(elapsed_time, 2), "secs")
