#!/usr/bin/env python3
"""
metal-archives.py - Metal archive utility
author: Telnoratti <telnoratti@gmail.com>
"""

import requests
from bs4 import BeautifulSoup

from lastfm import get_youtube

SEARCH_API = "http://www.metal-archives.com/search/ajax-advanced/searching/"
DISCO_API = "http://www.metal-archives.com/band/discography/id/"

def artist(phenny, input):
    print(input.groups()[1])
    r = requests.get(SEARCH_API + "bands", params={
        "bandName": input.groups()[1],
    }).json()["aaData"]
    if len(r) == 0:
        phenny.say("Couldn't find any bands by that name.")
        return
    elif len(r) > 5:
        r2 = requests.get(SEARCH_API + "bands", params={
            "bandName": input.groups()[1],
            "exactBandMatch": 1,
        }).json()["aaData"]
        if len(r2) == 0 or len(r2) > 5:
            phenny.say("Too many results, try a more exact search")
            return
        r = r2

    bands = [BeautifulSoup(b[0]).find('a').get('href') for b in r]
    mostrecent = bands[0]
    count = albumcount(bands[0])
    bands.pop(0)
    for band in bands:
        newcount = albumcount(band)
        if newcount > count:
            mostrecent = band
            count = newcount

    bandstats = getbandinfo(mostrecent)
    phenny.say("{0}: {1}, {2} ({3} releases), {4} -- {5}".format(bandstats["name"], bandstats["genre"], bandstats["status"], bandstats["album count"], bandstats["country of origin"], mostrecent))

artist.example = '.artist Epica'
artist.name = 'artist'
artist.commands = ['artist', 'artists']

def album(phenny, input):
    r = requests.get(SEARCH_API + "albums", params={
        "releaseTitle": input.groups()[1],
    }).json()["aaData"]
    if len(r) == 0:
        phenny.say("Couldn't find any albums by that name.")
        return
    elif len(r) > 5:
        r2 = requests.get(SEARCH_API + "albums", params={
            "releaseTitle": input.groups()[1],
            "exactReleaseMatch": 1,
        }).json()["aaData"]
        if len(r2) == 0 or len(r2) > 5:
            phenny.say("Too many results, try a more exact search")
            return
        r = r2


    artists = [BeautifulSoup(b[0]).find('a').get('href') for b in r]
    albums  = [BeautifulSoup(b[1]).find('a').get('href') for b in r]
    album_list = [(a, b,) for a, b in zip(albums, artists)]
    mostrecent = album_list[0]
    count = albumcount(album_list[0][1])
    album_list.pop(0)
    for band in album_list:
        newcount = albumcount(band[1])
        if newcount > count:
            mostrecent = band
            count = newcount

    albumstats = getalbuminfo(mostrecent[0])
    if "none" in albumstats["reviews"].lower():
        phenny.say("{0} - {1}, {2} {3} -- {4}".format(
            albumstats["name"],
            albumstats["album"],
            albumstats["release date"],
            albumstats["type"],
            mostrecent[0]))
    else:
        number, _, percent = albumstats["reviews"].strip().rpartition(' ')
        number, _, _ = number.partition(' ')
        phenny.say("{0} - {1} ({2}) {3} [Rating: {4} ({5} reviews)] -- {6}".format(
            albumstats["name"],
            albumstats["album"],
            albumstats["release date"],
            albumstats["type"],
            percent[:-1],
            number,
            mostrecent[0]))

    pass

album.example = '.album The Divine Conspiracy'
album.name = 'album'
album.commands = ['album', 'albums']

def song(phenny, input):
    r = requests.get(SEARCH_API + "songs", params={
        "songTitle": input.groups()[1],
        "releaseType[]": 1,
    }).json()["aaData"]
    if len(r) == 0:
        r = requests.get(SEARCH_API + "songs", params={
            "songTitle": input.groups()[1],
        }).json()["aaData"]
        if len(r) == 0:
            phenny.say("Couldn't find any albums by that name.")
            return
    elif len(r) > 5:
        r2 = requests.get(SEARCH_API + "songs", params={
            "songTitle": input.groups()[1],
            "releaseType[]": 1,
            "exactReleaseMatch": 1,
        }).json()["aaData"]
        if len(r2) == 0:
            r2 = requests.get(SEARCH_API + "songs", params={
                "songTitle": input.groups()[1],
                "exactReleaseMatch": 1,
            }).json()["aaData"]
        if len(r2) == 0 or len(r2) > 5:
            phenny.say("Too many results, try a more exact search")
            return
        r = r2
    print(r)
    song = r[0]

    artist = BeautifulSoup(song[0]).text
    album = BeautifulSoup(song[1]).text
    title = song[2]
    link = get_youtube(title, artist, album)
    phenny.say('{0} - "{1}" from "{2}" -- {3}'.format(
        artist,
        title,
        album,
        link))

song.example = '.song Obsessive Devotion'
song.name = 'song'
song.commands = ['song', 'songs']

def getbandinfo(bandurl):
    r = BeautifulSoup(requests.get(bandurl).text)
    band_info_dd = [item.get_text() for item in r.find('div', attrs={'id': "band_stats"}).find_all("dt")]
    band_info_dt = [item.get_text() for item in r.find('div', attrs={'id': "band_stats"}).find_all("dd")]
    band_info = zip(band_info_dd, band_info_dt)
    bandstats = {}
    for k, v in band_info:
        bandstats[k.lower()[:len(k) - 1]] = v
    bandstats["name"] = r.find('h1', attrs={'class': "band_name"}).get_text()
    bandstats["album count"] = albumcount(bandurl)
    return bandstats

def getalbuminfo(albumurl):
    r = BeautifulSoup(requests.get(albumurl).text)
    album_info_dd = [item.get_text() for item in r.find('div', attrs={'id': "album_info"}).find_all("dt")]
    album_info_dt = [item.get_text() for item in r.find('div', attrs={'id': "album_info"}).find_all("dd")]
    album_info = zip(album_info_dd, album_info_dt)
    albumstats = {}
    for k, v in album_info:
        albumstats[k.lower()[:len(k) - 1]] = v
    albumstats["name"] = r.find('h2', attrs={'class': "band_name"}).get_text()
    albumstats["album"] = r.find('h1', attrs={'class': "album_name"}).get_text()
    return albumstats

def lastalbum(bandurl):
    print(bandurl)
    _, _, band_id = bandurl.rpartition('/')
    r = requests.get(DISCO_API + band_id).text
    r = BeautifulSoup(r)

    largest_year = 0000
    for album in r.find('tbody').find_all('tr'):
        try:
            year = album.find_all('td')[2].get_text()
        except:
            continue
        if int(year) > largest_year:
            largest_year = int(year)
    return largest_year

def albumcount(bandurl):
    print(bandurl)
    _, _, band_id = bandurl.rpartition('/')
    r = requests.get(DISCO_API + band_id).text
    r = BeautifulSoup(r)

    return len(r.find('tbody').find_all('tr'))
