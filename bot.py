from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from tabulate import tabulate
import time

#checking how long it takes to run the script
start_time = time.time()

# supress dev msg
options = Options()
options.add_experimental_option('excludeSwitches', ['enable-logging'])


# Setup Selenium WebDriver with Chrome
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# scrape hoogvliet.com
urls = ["https://www.hoogvliet.com/INTERSHOP/web/WFS/org-webshop-Site/nl_NL/-/EUR/ViewTWParametricSearch-SimpleOfferSearch?PageNumber=0&PageSize=16&SelectedSearchResult=SFProductSearch&SearchTerm=&SelectedItem=&SortingOption=Relevantie&CategoryName=999999-100&CategoryTitle=Aardappelen,%20groente,%20fruit&SearchTermKey=null"
    #   ,"https://www.hoogvliet.com/INTERSHOP/web/WFS/org-webshop-Site/nl_NL/-/EUR/ViewTWParametricSearch-SimpleOfferSearch?PageNumber=0&PageSize=16&SelectedSearchResult=SFProductSearch&SearchTerm=&SelectedItem=&SortingOption=Relevantie&CategoryName=100-10001&CategoryTitle=Producten--Aardappelen&SearchTermKey=null"       
]

# create empty list for tabulate
products = []

for url in urls:
    
    # Open the URL
    driver.get(url)

    #wait for initial load (100% neccesary for explicit wait do NOT remove)
    time.sleep(.5)

    # Explicit wait
    try:
        wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'pagination-total')))
        print("Page is ready!")
    except TimeoutException:
        print("Loading took too much time! OR no 'pagination-total' found")
        driver.quit()
        continue

    # Get the total number of products from the page
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    total_products_div = soup.find('div', class_='pagination-total')
    total_products = int(total_products_div.text.strip().split()[0])
    print("Total number of products:", total_products)
    # Scroll and wait for the page to load more products
    last_height = driver.execute_script("return document.body.scrollHeight")
    products_scraped = 0

    # scroll down wait time to show new products
    scroll_pause_time = 2

    # if the total product is less than products scraped we continue till we have all products or untill new_height is no longer different from last_height
    while products_scraped < total_products:
        # Scroll down to the bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load the page
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

        # Update the number of products scraped
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        title = soup.find_all('h3', {'data-product_id': True})
        products_scraped = len(title)
        print("Products scraped:", products_scraped)

    # Get page source and make soup with it
    page_source = driver.page_source
    

    # html into soup with parse
    soup = BeautifulSoup(page_source, 'html.parser')

    # find titles, euro and cents in HTML with their classes and attributes
    title = soup.find_all('h3', {'data-product_id': True}) # name + product_id
    euro = soup.find_all('span', class_='price-euros') # euro
    cents = soup.find_all('span', class_='price-cents') # cents

    # find category in HTML with class and then find the h1 tag for the category name
    category_div = soup.find('div', class_='col-sm-9 product-list-block col-xs-12')
    category = category_div.find('h1').text.strip()

    #links
    list = soup.find_all('li', class_='filter-item filter-layer2')
    medium_url = []

    filtered_list = [li for li in list if li.find('a', class_='tw-filter')]
    for item in filtered_list:
        category_data = item.find('a')
        data_category = category_data['data-category']
        data_title = category_data['data-title'].replace(' ', '%20')
        data_url = category_data['data-url']
        # Now you have the category, title, and URL for each category
        print(f"Category: {data_category}, Title: {data_title}, URL: {data_url}")
        medium_url.append(f"https://www.hoogvliet.com/INTERSHOP/web/WFS/org-webshop-Site/nl_NL/-/EUR/ViewTWParametricSearch-SimpleOfferSearch?PageNumber=0&PageSize=16&SelectedSearchResult=SFProductSearch&SearchTerm=&SelectedItem=&SortingOption=Relevantie&CategoryName=100-{data_category}&CategoryTitle=Aardappelen,%20groente,%20fruit--{data_title}&SearchTermKey=null")
        

    # add date to use in database
    date = time.strftime("%Y-%m-%d")



    # loop through title, euro and centen and append to products list
    for name, euros, cents in zip(title, euro, cents):

        # make the full price
        full_price = euros.text.strip() + cents.text.strip()

        # remove \n and spaces from full_price so it looks cleaner
        full_price = full_price.replace('\n', '').replace(' ', '')

        # get artikelnumber from title find_all and strip it from the html
        ArtikelNumber = name['data-product_id']

        # make the image url with the artikelnumber
        image = f'https://cdn.hoogvliet.com/Images/Product/L/{ArtikelNumber}.jpg'
        
        #append all the data to the products list so we can tabulate it
        products.append([ArtikelNumber, name.text, full_price, category, image, date])
        print(tabulate(products, headers=['Artikel Nummer', 'Product Name', 'Price (€)', 'category','image url', 'date'], tablefmt='grid'))
        print("\nTotal number of products scraped:", len(products))
    print("Done scraping: ", category, "\n", url)
driver.quit()
# print(medium_url)



# print how long it took to run the script
end_time = time.time()
formatted_duration = "{:.2f}".format(end_time - start_time)
print("\nDuration:", formatted_duration, "seconds")