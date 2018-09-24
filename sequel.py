#!/usr/bin/python
#coding=utf-8
import csv
import sys
import re

class Game:
	def __init__(self, name, platform, year, genre, publisher):
		self.name = name
		self.platform = platform
		self.year = year
		self.genre = genre
		self.publisher = publisher
		self.sequel = False
		
	def __repr__(self):
		return "Game(" + self.name + ")"
			
	def __str__(self):
		return "Game():" + "\n\tname=" + self.name + "\n\tplatform=" + self.platform + \
				"\n\tyear=" + str(self.year) + "\n\tgenre=" + self.genre + "\n\tpublisher=" + self.publisher

def isSequel(game, games):
	name = game.name.strip()
	# Does the game have a number at the end?
	pattern = re.compile(r'\s\d*$|\s[IVX]$') # Match any number or roman numeral at the end of the game name
	match = pattern.search(name)
	if match:
		print ("'" + name + "' may be a sequel because of number at end")
	
	# Does the name of the game match the name of any other earlier games?
	for othergame in games:
		othername = othergame.name.strip()
		if len(name) >= len(othername):
			if othername in name and game != othergame:
				if game.year > othergame.year and game.platform == othergame.platform:
					print ("'" + name + " (" + game.year + ")' may be a sequel of '" + othername + " (" + othergame.year + ")'")
					break

	return False
	
reader = csv.reader(open(sys.argv[1]))
next(reader, None) # Skip the headers
games = [Game(row[0], row[1], row[2], row[3], row[4]) for row in reader]

for game in games:
	game.sequel = isSequel(game, games)
	
