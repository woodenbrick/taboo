#!/usr/bin/env python
import re
import urllib
import string
import sqlite3
import time

conn = sqlite3.Connection("tabooDB")
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS `cards` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `word` varchar(50),
                `keyword1` varchar(50),
                `keyword2` varchar(50),
                `keyword3` varchar(50),
                `keyword4` varchar(50),
                `keyword5` varchar(50)
            )""")
cursor.execute("""CREATE TABLE IF NOT exists `stupidcards` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `word` varchar(50),
                `keyword1` varchar(50),
                `keyword2` varchar(50)
            )""")
conn.commit()
total = 5
count = 1
while count <= total:    
    data = urllib.urlopen("http://www.eseonline.net/taboo/taboo.php").read()
    word = re.search("<FONT COLOR=RED>([a-zA-Z ]+)", data)
    if word is None:
        continue
    keywords = string.split(re.search("<font color=#666666>(.+)</font>", data).group(1), "<BR />")
    indb = cursor.execute("""SELECT word FROM cards WHERE word=? and keyword1=? and keyword2=?""",
                          (word.group(1), keywords[0].title(), keywords[1].title())).fetchone()
    if indb:
        print 'card exists, discarding'
        continue
    stupid = cursor.execute("""SELECT word FROM stupidcards WHERE word=? and keyword1=? and
                            keyword2=?""", (word.group(1), keywords[0].title(), keywords[1].title())).fetchone()
    if stupid:
        print 'card has been marked as stupid, discarding'
        continue
    
    cursor.execute("""INSERT INTO cards (word, keyword1, keyword2, keyword3, keyword4,
                   keyword5) VALUES (?, ?, ?, ?, ?, ?)""", (word.group(1).title(), keywords[0].title(),
                                                            keywords[1].title(), keywords[2].title(),
                                                            keywords[3].title(), keywords[4].title()))
    conn.commit()
    print "Card %d of %d" % (count, total)
    time.sleep(2)
    count += 1
conn.close()

