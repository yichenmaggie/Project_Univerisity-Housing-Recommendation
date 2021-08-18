# -*- coding: utf-8 -*-
"""
@explanation: this file is used for scraping data from the two website, 
https://www.apartments.com/ and pittsburgh.craigslist.org
for user interation part, please refer to the menu.py
"""
import numpy as np
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from time import sleep
from random import randint #avoid throttling by not sending too many requests one after the other
from geopy.distance import geodesic

#%%
#create a function to scarpe all the attributes from apartments.com
def parse(types,district):
  headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
  #form the url by the housing types and scrape the page
  type_url='https://www.apartments.com/'+types+'/'+district+'-pa/'
  r = requests.get(type_url,headers=headers)
  c = r.content
  soup = BeautifulSoup(c,'html.parser')
  #find the maximam pages in the page turning bar of the housing type in order to change the url based on the page
  if(soup.find('div', class_='placardContainer').find('nav',class_='paging')!=None):
    paging = soup.find('div', class_='placardContainer').find('nav',class_='paging').find_all('li')
    page=[]
    #get all possible pages in the bar
    for item in paging:
        if item.find('a') is None: continue   
        page.append(item.find('a').get('data-page'))
    
    # To extract the first and last page numbers
    start_page = page[1]
    last_page = page[-2]
  else:
    start_page = last_page = 0
    
  cmuLatitude=40.4433
  cmuLongitude=-79.9436
  cmu=(cmuLongitude,cmuLatitude)
  #create the dataframe to store the information we want to get
  housing=pd.DataFrame(columns=['Address', 'District','Beds', 'Baths', \
                                'Longitudes', 'Latitudes', \
                              'Price', 'Size', 'Website','Distance', 'Type'])
  
  if district=='squirrel-hill':
          district='Squirrel Hill'
  else:
      district='Shadyside'
  
  
  for page_number in range(int(start_page),int(last_page) + 1):
      # To form the url based on page numbers
      if(last_page==0):
        url=type_url
      else:
        url = type_url+str(page_number)+"/"
      r = requests.get(url, headers=headers)
      c = r.content
      soup = BeautifulSoup(c,'html.parser')
      
      # To extract the information in each page based on the title
      placard_content =soup.find(id="placardContainer" ,class_="placardContainer")
      panel = placard_content.ul
      Title=panel.findAll('a', class_=re.compile('js-placardTitle'))
      Address= panel.findAll('div', class_='location')
      Price = panel.findAll('span',class_='altRentDisplay')
      
      #run a for loop to find all the information of the items in one page
      for i in (range(len(Price))):
          #for each house, click into the house to get detail information of the house
          #i.e. longitude, latitude 
          if Price[i] is not None:
              childUrl = Title[i]['href']
              childResponse = requests.get(childUrl, headers=headers)
              if childResponse.status_code == 200:
                childSoup = BeautifulSoup(childResponse.content, 'html.parser')
              else:
                print('parsing error: code temporarily unavailable')
              latitude = childSoup.find('meta',property="place:location:latitude")["content"]
              longitude = childSoup.find('meta',property="place:location:longitude")["content"]
              location=(longitude,latitude)
              distance=(geodesic(cmu,location).km)
              childPanel = childSoup.find('table', class_=re.compile("availabilityTable"))
              rows = childPanel.tbody.findAll('tr', class_=re.compile("rentalGridRow"))
              
              #in a given house's page, fetch each unit's information
              for j in range(len(rows)):
                #clean the price befroe inserting it into the dataframe
                price = rows[j].find('td',class_="rent").get_text().strip()
                #skip the unit which does not have exact price
                if(price.find("Call for Rent")!=-1):
                  continue
                price = price.replace("$","").replace(",","").strip()
                if(price.find("Person")):
                  price = price.split("/")[0].strip()
                #if the price displayed is a range
                #compute the average of the min and max to replace the price
                if(price.find("-")!=-1):
                  highPrice,lowPrice = price.split("-")
                  lowPrice = int(lowPrice.strip())
                  highPrice = int(highPrice.strip())
                  price = (lowPrice+highPrice)/2
                price = float(price)
                #clean the outliers
                if(price>10000):
                  continue
                
                #strip the 'sq ft' from the size 
                sizeStr = (rows[j].find('td',class_="sqft").get_text().strip()).replace(',','').split(' ')
                #if no size recorded, drop this house record
                if(len(sizeStr)==1 or len(sizeStr)==0):
                  continue
                #if the size displayed is a range
                #compute the average of the min and max to replace the size
                if('-' in sizeStr):
                  lowSize = float(sizeStr[0])
                  highSize = float(sizeStr[2])
                  size = (lowSize+highSize)/2
                try:
                  #transform the size from string to float
                  size = float(sizeStr[0].strip())
                except ValueError:
                  print("error of transforming size:"+sizeStr)
                
                #extract the bedroom number in a correct way
                #if it is studio, return 1 for number of bedrooms
                numBeds = rows[j].find('td',class_="beds").find('span').get_text().strip().split(" ")[0][0]
                if numBeds=='S':
                  numBeds = 1
                if numBeds == '0':
                  numBeds = 1
                housing = housing.append \
                ({'Address':Title[i].get_text().replace("\r","").replace("\n","") \
                            +', '+Address[i].get_text(), \
                  'District': district, \
                  'Beds':int(numBeds), \
                  'Baths':int(rows[j].find('td',class_="baths").find('span').get_text().strip().split(" ")[0][0]),\
                  'Longitudes':longitude, \
                  'Latitudes': latitude, \
                  'Price':price,\
                  'Size': size, \
                  'Website':childUrl,\
                  'Distance':distance,\
                  'Type':types},\
                  ignore_index = True)
  return housing
housing=pd.DataFrame(columns=['Address', 'District','Beds', 'Baths', \
                                'Longitudes', 'Latitudes', \
                              'Price', 'Size', 'Website','Distance', 'Type'])
types_list = ['apartments','houses','condos','townhomes']
district_list = ['squirrel-hill', 'shadyside']
for district in district_list:
  for types in types_list:
    #concat all the units of different types and districts into one table
    housing = pd.concat([housing, parse(types,district)])
print("Apartments.com Scrape complete!")
#%%concat tables from craiglis and apartments.com
def getdata(get_num, get_web, housetype):
    
    #set the latitude and longtitude of CMU
    cmuLatitude = 40.4433
    cmuLongitude = -79.9436
    cmu = (cmuLongitude,cmuLatitude)
    
    #build a empty dataframe
    title_texts = []
    links = []
    latitudes = []
    longitudes = []
    bedrooms = []
    bathrooms = []
    area = []
    prices = []
    address = []
    distances = []
    
    ans = pd.DataFrame({"Address": address,
                        "Beds": bedrooms,
                        "Baths": bathrooms,
                        "Longitudes":longitudes,
                        "Latitudes":latitudes,
                        "Price": prices,
                        "Size": area,                       
                        "Website": links,                        
                        "Distance": distances})
    
    #get the total number of posting for the corresponding search
    response = requests.get(get_num + "&housing_type=" + str(housetype))
    html_soup = BeautifulSoup(response.text, "html.parser")
    results_num = html_soup.find("div", class_= "search-legend")
    
    #if there is no posting find, then return the empty dataframe
    if results_num.find("span", class_ = "totalcount") is None:
        return ans        
    
    results_total = int(results_num.find("span", class_ = "totalcount").text) 
    
    #generate the page index used in the URL
    pages = np.arange(0, results_total + 1, 120)
    
    #count the times of iteration
    iterations = 0    
    
    #go through each page
    for page in pages:
        
        #get the URL
        web = get_web + str(page) + "&housing_type=" + str(housetype)
        response = requests.get(web)
        
        #sleep for some random time to avoid being caught
        sleep(randint(1,5))
        
        #check the status of the response
        if response.status_code != 200:
            continue;
        
        #get all the listings
        page_html = BeautifulSoup(response.text, "html.parser")
        
        posts = page_html.find_all("li", class_ = "result-row")
        
        #iterate on all the listings in that page
        for post in posts:
                
            #get the title of the listing
            post_title = post.find("a", class_ = "result-title hdrlnk")
            post_title_text = post_title.text
            
            #get the price of the listing, and exclude some abnormal pricing
            post_price = float(post.find("span", class_ = "result-price").text.strip().replace("$", "")) 
            if(post_price > 10000):
                  continue
            
            #get the detailed URL of the detailed link page, and get into that page
            post_link = post_title["href"]        
            lists_html = requests.get(post_link)
            
            #check the status of the response
            if lists_html.status_code != 200:
                continue;
            
            lists = BeautifulSoup(lists_html.text, "html.parser")   
            
            #ignore the listing with no address
            if lists.find("div", id = "map") is None:
                continue
            
            #get the longtitude, latitude of the listing, and calculate the distance to CMU
            post_latitude = lists.find("div", id = "map")["data-latitude"]
            post_longitude = lists.find("div", id = "map")["data-longitude"]
            location = (post_longitude, post_latitude)
            distance = (geodesic(cmu,location).km)
            
            #get the number of bedroom, bathroom, and size of the listing
            post_bedbathsize = lists.find_all(lambda tag: tag.name == "span" and tag.get("class") == ["shared-line-bubble"])
            
            #if there are less than two class "shared-line-bubble" find, then it does not include both of the bed and bath information
            #ignore the listing with incomplete information
            if post_bedbathsize is None or len(post_bedbathsize) < 2:
                continue
            
            post_bedbath = post_bedbathsize[0].find_all("b")
            post_size = post_bedbathsize[1].find("b")  
            
            #ignore the listing with shared bedrooms or bathrooms
            try:
                bedroom_count = float(post_bedbath[0].text[:-2])
                if (bedroom_count == 0):
                  bedroom_count = 1
                bathroom_count = float(post_bedbath[1].text[:-2])
                size = int(post_size.text)
            except Exception:
                #pass the records which share the bedroom with the landowner
                continue
            
            #ignore the listing without mapaddress
            if lists.find("div", class_ = "mapaddress") is None:
                continue
            
            post_address = lists.find("div", class_ = "mapaddress").text            
            
            #append the new information to the lists
            title_texts.append(post_title_text)
            links.append(post_link)
            latitudes.append(post_latitude)
            longitudes.append(post_longitude)
            prices.append(post_price)
            bedrooms.append(bedroom_count)
            bathrooms.append(bathroom_count)
            area.append(size) 
            address.append(post_address)
            distances.append(distance)
        
        #iterations added
        iterations += 1
    
    #transform data into dataframe
    ans = pd.DataFrame({"Address": address,
                        "Beds": bedrooms,
                        "Baths": bathrooms,
                        "Longitudes":longitudes,
                        "Latitudes":latitudes,
                        "Price": prices,
                        "Size": area,                       
                        "Website": links,                        
                        "Distance": distances})

    #drop the duplicate records based on their website
    ans = ans.drop_duplicates(subset = "Website")
    
    #return the final dataframe
    return ans

#get the data using getdata function
#set the type of the housing(craigslist use code for that)
get_num_squirrel = "https://pittsburgh.craigslist.org/search/apa?availabilityMode=0&query=squirrel+hill"
get_web_squirrel = "https://pittsburgh.craigslist.org/search/apt?availabilityMode=0&query=squirrel+hill&s="
squirrelhill_apt = getdata(get_num_squirrel, get_web_squirrel, 1)
squirrelhill_apt["Type"] = "Apartment"
squirrelhill_house = getdata(get_num_squirrel, get_web_squirrel, 6)
squirrelhill_house["Type"] = "House"
squirrelhill_condo = getdata(get_num_squirrel, get_web_squirrel, 2)
squirrelhill_condo["Type"] = "Condo"
squirrelhill_townhouse = getdata(get_num_squirrel, get_web_squirrel, 9)
squirrelhill_townhouse["Type"] = "Townhomes"
squirrelhill = pd.concat([squirrelhill_apt, squirrelhill_house, squirrelhill_condo, squirrelhill_townhouse], axis = 0)
squirrelhill.insert(1, "District", "Squirrel Hill")

get_num_shadyside = "https://pittsburgh.craigslist.org/search/apa?availabilityMode=0&query=shadyside"
get_web_shadyside = "https://pittsburgh.craigslist.org/search/apt?availabilityMode=0&query=shadyside&s="
shadyside_apt = getdata(get_num_shadyside, get_web_shadyside, 1)
shadyside_apt["Type"] = "Apartment"
shadyside_house = getdata(get_num_shadyside, get_web_shadyside, 6)
shadyside_house["Type"] = "House"
shadyside_condo = getdata(get_num_shadyside, get_web_shadyside, 2)
shadyside_condo["Type"] = "Condo"
shadyside_townhouse = getdata(get_num_shadyside, get_web_shadyside, 9)
shadyside_townhouse["Type"] = "Townhomes"
shadyside = pd.concat([shadyside_apt, shadyside_house, shadyside_condo, shadyside_townhouse], axis = 0)
shadyside.insert(1, "District", "Shadyside")

get_num_northoakland = "https://pittsburgh.craigslist.org/search/apa?query=north+oakland&availabilityMode=0"
get_web_northoakland = "https://pittsburgh.craigslist.org/search/apa?availabilityMode=0&query=north%20oakland&s="
northoakland_apt = getdata(get_num_northoakland, get_web_northoakland, 1)
northoakland_apt["Type"] = "Apartment"
northoakland_house = getdata(get_num_northoakland, get_web_northoakland, 6)
northoakland_house["Type"] = "House"
northoakland_condo = getdata(get_num_northoakland, get_web_northoakland, 2)
northoakland_condo["Type"] = "Condo"
northoakland_townhouse = getdata(get_num_northoakland, get_web_northoakland, 9)
northoakland_townhouse["Type"] = "Townhomes"
northoakland = pd.concat([northoakland_apt, northoakland_house, northoakland_condo, northoakland_townhouse], axis = 0)
northoakland.insert(1, "District", "North Oakland")

result = pd.concat([squirrelhill, shadyside, northoakland], axis = 0)
print("Craigslist Scrape complete!")
#%%
#append the result from two websites
result = pd.concat([result,housing])
result = result.reset_index(drop=True)
print(result.info())
#%%   
#write the data into csv 
result.to_csv('houses.csv', index = False) 

#%%
