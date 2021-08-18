# -*- coding: utf-8 -*-
"""
Created on Wed Dec  4 13:36:39 2019

@author: lily1
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import folium
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
import seaborn as sns

#%% this part is used to get the statistics of the given data for the given neighborhood
def getstas(data, neighborhood):
    avg = np.average(data[data["District"] == neighborhood]["Price"] / data[data["District"] == neighborhood]["Beds"])
    maxs = np.max(data[data["District"] == neighborhood]["Price"] / data[data["District"] == neighborhood]["Beds"])
    mins = np.min(data[data["District"] == neighborhood]["Price"] / data[data["District"] == neighborhood]["Beds"])
    cnt = data[data["District"] == neighborhood].shape[0]
    return avg, maxs, mins, cnt

#%% this part is used to get the regresion of the given data
def regression(data):
    
    #get the dependend and independent vairable for the regression
    feature_cols = ["Beds", "Baths", "District", "Size", "Type", "Distance"]
    X = data[feature_cols]
    y = data["Price"]
    
    #change the strings to dummy variables
    dummy_dis = pd.get_dummies(X["District"])
    dummy_type = pd.get_dummies(X["Type"])
    X = pd.concat([X, dummy_dis, dummy_type], axis = 1)
    X = X.drop(["District", "Type"], axis = 1)
    
    test = X
    test["Price"] = y
    
    test = test.rename(columns={"Squirrel Hill": "SquirrelHill"})
    test = test.rename(columns={"North Oakland": "NorthOakland"})
    
    #using smf package to perform ols 
    lm1 = smf.ols(formula = "Price ~ Beds + Baths + Size + Distance + \
                              NorthOakland + Shadyside + SquirrelHill + \
                              Apartment + Condo + House + Townhomes", data = test).fit()
    
    #prints out the result
    print(lm1.summary())
    print("==============================================================================")
    print("Please find the above impact of factors on the housing price, and decide the type of housing you want.")

#%% this part is used to print out the user interface
def printmenu(data):
        
    count = 0
    
    #keep on searching untill the user enters ALLDONE
    while(True):  
        
        #get the user's preference on the district
        print()
        print("Start a new search! Enter ALLDONE to quit.")
        print()
        print("Select the neighborhood:")
        print("1. Shadyside")
        print("2. North Oakland")
        print("3. Squirrel Hill")   
        print("4. All the three areas")
        type_district = input("Please enter your choice: ")
        print()
        if(type_district == "ALLDONE"):
            break
        dict_district = {"1": "Shadyside", "2": "North Oakland", "3": "Squirrel Hill", "4": "All"}
        
        #get the user's preference on the housing type
        print("Select the housing type:")
        print("1. House")
        print("2. Apartments")
        print("3. Condos")
        print("4. Townhomes")
        print("5. All the above types")
        type_housing = input("Please enter your choice: ")
        print()
        if(type_housing == "ALLDONE"):
            break
        dict_type = {"1": "House", "2": "Apartments", "3": "Condos", "4": "Townhomes", "5": "All"}
        
        #get the user's preference on price
        lowest = input("Enter the your acceptable minimum housing price: ")
        if(lowest == "ALLDONE"):
            break
        lowest = int(lowest)
        
        highest = input("Enter the your affordable maximum housing price: ")
        if(highest == "ALLDONE"):
            break
        highest = int(highest)
        
        #get the user's preference on sorting
        print("How do you want to sort the results")
        print("1. Price (high to low)")
        print("2. Price (low to high)")
        print("3. Distance to CMU (in miles)")
        type_choice = input("Please enter your choice: ")    
        if(type_choice == "ALLDONE"):        
            break
        
        #get the data that fits the search, and sort the data as needed
        result = pd.DataFrame({"Address":[],
                               "District": [],
                               "Beds": [], 
                               "Baths": [],
                               "Price": [],
                               "Size": [],
                               "Website": [],
                               "Distance": [],
                               "Longitudes":[],
                               "Latitudes":[],
                               "Type": []})
        
        for i in range(0, len(data)):
            if((type_district == "4" or data["District"].iloc[i] == dict_district[type_district])
               and (type_housing == "5" or data["Type"].iloc[i] == dict_type[type_housing])
               and int(data["Price"].iloc[i]) >= lowest  
               and int(data["Price"].iloc[i]) <= highest):
                result = result.append(data.iloc[i], ignore_index = True)
                
        result = result.round({"Distance": 1})
                
        if(type_choice == "1"):
            result.sort_values(by = "Price", ascending = False)
            
        if(type_choice == "2"):
            result.sort_values(by = "Price", ascending = True)
            
        if(type_choice == "3"):
            result.sort_values(by = "Distance", ascending = True)
            
        print("Find %d places in total. "%result.shape[0])
        print("Here are the top 5 place for you")
        pd.set_option('display.max_colwidth',100)
        pd.set_option('display.width',400)
        pd.set_option('display.max_columns', 9)
        
        prints = result[["Address", "District", 
                      "Beds", "Baths", "Price",
                      "Size", "Website", "Distance", "Type"]]
        
        prints = prints.rename(columns={"Distance": "Distance(miles)"})
        prints = prints.rename(columns={"Size": "Size(sqft)"})
        
        print(prints.head())
        
        # use matplotlib and seaborn packages to picture price-square_footage-beds scatter
        params = {'legend.fontsize': 'x-large',
          'figure.figsize': (15, 5),
         'axes.labelsize': 'x-large',
         'axes.titlesize':'x-large',
         'xtick.labelsize':'x-large',
         'ytick.labelsize':'x-large'}
        pylab.rcParams.update(params)
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x=result['Price'], y=result["Size"], hue=result["Beds"], palette='summer', x_jitter=True, y_jitter=True, s=125, data=result)
        plt.legend(fontsize=12)
        plt.xlabel("Price", fontsize=18)
        plt.ylabel("Square Footage", fontsize=18);
        plt.title("Price vs. Square Footage Colored by Number of Bedrooms", fontsize=18)
        print("Here is a Price vs. Square Footage Colored by Number of Bedrooms Scatter Plot for you!")
        plt.show()
        
        # print the whole sorting sorting list 
        choice = input("Do you want the whole list(y/n): ")
        if (choice == "y"):
            print(prints)
        
        # use folium package to picture the top 5 housing locations relative to CMU on the map
        location=[]
        address=[]
    
        for i in range(0,len(result)):
            location.append((result["Latitudes"][i],result["Longitudes"][i]))
            address.append(result["Address"][i])
            if i==4:
                break

        cmuLatitude=40.4433
        cmuLongitude=-79.9436
        m=folium.Map(location=[cmuLatitude,cmuLongitude])
        for i in range (0,len(result)):
            title='<i>'+address[i]+'</i>'
            folium.Marker(location[i], popup=title).add_to(m)
            if i==4:
                break
        folium.Marker([cmuLatitude,cmuLongitude], popup='<i>Carnegie Mellon University</i>',icon=folium.Icon(color='red')).add_to(m)
        m.save("top5map.html")
        print("We have pictured the top five housing locations relative to CMU on the map, please turn to 'top5map.html' in the folder!")
   
        count += 1
    return count
#%%
def main():
    # read the data from houses.csv
    data = pd.read_csv("houses.csv")
    
    shadyside_avg, shadyside_max, shadyside_min, shadyside_cnt = getstas(data, "Shadyside")
    squirrel_avg, squirrel_max, squirrel_min, squirrel_cnt = getstas(data, "Squirrel Hill")
    northoakland_avg, northoakland_max, northoakland_min, northoakland_cnt = getstas(data, "North Oakland")
    
    # conduct statistic analysis on the total data
    total_avg = np.average(data["Price"] / data["Beds"])
    total_max = np.max(data["Price"] / data["Beds"])
    total_min = np.min(data["Price"] / data["Beds"])
    total_cnt = data.shape[0]
    
    # print the main menu
    print("*********************Welcome to the LIFE SUCKS USE PYTHON********************")
    print("***Find ideal place to live in Shadyside, North Oakland and Squirrel Hills***")
    
    choice = input("Do you want some statistical information on the housing in Pittsburgh?(y/n): ")
    if (choice == "y"):
        print("%-15s%-15s%-15s%-15s%-15s"%("", "Counts", "Average", "Highest", "Lowest"))
        print("=" * 75)  
        print("%-15s%-15d%-15.2f%-15.2f%-15.2f"%("Squirrel Hill", squirrel_cnt, squirrel_avg, squirrel_max, squirrel_min))
        print("%-15s%-15d%-15.2f%-15.2f%-15.2f"%("North Oakland", northoakland_cnt, northoakland_avg, northoakland_max, northoakland_min))
        print("%-15s%-15d%-15.2f%-15.2f%-15.2f"%("Shadyside", shadyside_cnt, shadyside_avg, shadyside_max, shadyside_min))
        print("%-15s%-15d%-15.2f%-15.2f%-15.2f"%("Overall", total_cnt, total_avg, total_max, total_min))
        print()
        
        print("The Boxplots of Prices by District: ")
        # district-price boxplot
        sns.boxplot(x=data["District"], y=data["Price"], data=data,palette="Blues")
        plt.xlabel("District");
        plt.ylabel("Price USD");
        plt.title("Prices by District - Boxplots");
        plt.show()
    
    choice = input("Do you want more details on the effects of the factors?(y/n): ")
    if (choice == "y"):
        regression(data)
        
    count = printmenu(data)
    
    print("You have made %d search with us!"%count)
    print("Hope we have helped!")
    print("Good luck finding your dream house!")
    print("Bye Bye!")
    
#%%
if __name__ == "__main__":
    main()