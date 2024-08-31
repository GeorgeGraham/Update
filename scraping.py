from bs4 import BeautifulSoup
import requests
import re
import time

def scrape_list(list_url):
    x = 1
    listDictionary = {}
    listDictionary["movies"] = []
    listDictionary["url"] = list_url
    while True:
        print("URL URL URL")
        #print(f"{list_url}/page/{x}")
        r = requests.get(f"{list_url}page/{x}")
        print(r.text)
        soup = BeautifulSoup(r.text, 'lxml')
        #print(soup.text)
        # change to title-1 prettify (remove has notes , optional i guess)
        listDictionary["title"] = soup.find("h1", class_="title-1 prettify").get_text()
        #print(listDictionary)

        films = soup.find_all('ul', class_='js-list-entries poster-list -p125 -grid film-list')
        films2 = films[0].find_all('div', class_='film-poster')
        #print(films2[0])
        for element in films2:
            imgElement = element.find('img')
            url = 'https://letterboxd.com'+element.get('data-target-link')
            listDictionary['movies'].append(scrape_film(url))
        x+=1
        if len(films2) == 0:
            break
    #print(listDictionary)
    return listDictionary


def scrape_film(url):
    linkname = url.removeprefix('https://letterboxd.com/')
    linkname = 'https://letterboxd.com/csi/'+linkname+'stats/'
    #print(linkname)
    filmdictionary = {}
    r = requests.get(url)
    r2 = requests.get(linkname)
    soup = BeautifulSoup(r.text, 'lxml')
    soup2 = BeautifulSoup(r2.text, 'lxml')
    #print(r.text)

    films = soup.find_all('span', class_='name js-widont prettify')
    #Get Title
    filmdictionary['title'] = films[0].text
    #Get Genres
    ratingsDiv = soup.find(id='tab-genres')
    genres = [a.text for a in ratingsDiv.find_all('a')]
    filmdictionary['genres'] = genres
    #Get Watches
    watches = soup2.find_all('li', class_='stat filmstat-watches')
    if len(watches) > 0:
        x = watches[0].find('a').get('title')
        x2 = x.lstrip("Watched by ")
        x2 = x2.rstrip(" members")
        x2 = x2.replace(",", "")
        x2 = x2.replace(u'\xa0', u' ')
        x2 = x2.rstrip(" ")
        filmdictionary["watches"] = x2
    #Get ReleaseDate
    releaseDate = soup.find('h5',class_='date').text
    releaseDateSplit = releaseDate.split(" ");
    filmdictionary["releaseyear"] = releaseDateSplit[len(releaseDateSplit)-1]
    #Get runtime
    runtime = soup.find('section',class_='section col-10 col-main').find('p',class_='text-link text-footer')
    runtimeSplit = runtime.text.split(" ")
    cleaned = runtimeSplit[0].strip()
    cleaned2 = cleaned.split('\xa0')[0]
    filmdictionary["runtime"] = cleaned2
    return filmdictionary

#y = scrape_film("https://letterboxd.com/film/koji-shiraishis-never-send-me-please/")
#print(y)

#scrape_list("https://letterboxd.com/ur_mom_lol/list/letterboxds-1000-most-watched-films/")
#scrape_list("https://letterboxd.com/eyesack2007/list/bad-boys-1/")