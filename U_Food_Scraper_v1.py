from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
import time
import os
from datetime import datetime
import pandas as pd
import warnings
import sys
import xlsxwriter
from multiprocessing import freeze_support
warnings.filterwarnings('ignore')

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--headless')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.page_load_strategy = 'eager'
    # disable location prompts & disable images loading
    prefs = {"profile.default_content_setting_values.geolocation": 2, "profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(300)

    return driver

def scrape_posts(driver, output1, page, settings):

    
    print('-'*75)
    print('Scraping The Posts Links ...')
    # getting the full posts list
    links = []
    nposts = 0
    limit = settings["Number of Posts"]
    end = False
    for i in range(100):
        driver.get(page + f'/{i+1}')
        # scraping posts urls
        posts = wait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card")))      
        for post in posts:
            try:
                nposts += 1
                print(f'Scraping the url for post {nposts}')
                link = wait(post, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a"))).get_attribute('href')
                links.append(link)
                if nposts == limit:
                    end = True
                    break
            except:
                pass

        if end: break

    # scraping posts details
    print('-'*75)
    print('Scraping Posts Details...')
    print('-'*75)
    n = len(links)
    data = pd.DataFrame()
    for i, link in enumerate(links):
        try:
            driver.get(link)           
            details = {}
            print(f'Scraping the details of post {i+1}\{n}')

            # Post title
            title = ''             
            try:
                title = wait(driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).get_attribute('textContent').strip()
            except:
                print(f'Warning: failed to scrape the name for post: {link}')               
                
            details['Post_Title'] = title
                                    
            # Categories 
            cat1, cat2 = '', ''
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.section-categ-tag")))
                lis = wait(div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
                ncats = len(lis)
                if ncats == 2:
                    cat1 = lis[0].get_attribute('textContent').strip()
                    cat2 = lis[1].get_attribute('textContent').strip()
                elif ncats == 1:
                    cat1 = lis[0].get_attribute('textContent').strip()
            except:
                pass
                    
            details['Category1'] = cat1            
            details['Category2'] = cat2            
             
            # author 
            author = ''
            try:
                author = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='author-name text15 text-weight-300']"))).get_attribute('textContent').split(':')[-1].strip()
            except:
                pass          
                
            details['Author'] = author            
            
            # article date
            date = ''
            try:
                date = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='publish-time text15 text-weight-300']"))).get_attribute('textContent').split(':')[-1].strip()
                if '小時前' in date or '分鐘前' in date:
                    date = datetime.today().strftime('%Y.%m.%d')
            except:
                pass          
                
            details['Article_Date'] = date           
                                      
            # content
            content = ''
            text_tags = ['p', 'h2', 'h3', 'h4']
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.lazy")))
                elems = wait(div, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "*")))
                for elem in elems:
                    try:
                        if elem.tag_name not in text_tags:
                            continue
                        else:
                            text = elem.text.replace('Play Video', '').strip()
                            if len(text) > 0:
                                content += text + '\n'
                    except:
                        pass
            except Exception as err:
                pass
                
            details['Article_Content'] = content                        
            # tags
            tags = ''
            try:
                div = wait(driver, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.section-article-tag")))[-1]
                lis = wait(div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
                for li in lis:
                    tags += li.get_attribute('textContent').strip() + ', '
                tags = tags[:-2]
            except:
                pass          
                
            details['Article_Tags'] = tags                  
            details['Article_Link'] = link                                    
            # appending the output to the datafame       
            data = data.append([details.copy()])
        except Exception as err:
            pass
            #print(str(err))
           
    # output to excel
    data.to_excel(output1, index=False)
 
def get_inputs():

    # assuming the inputs to be in the same script directory
    path = os.getcwd()
    if '\\' in path:
        path += '\\food_settings.xlsx'
    else:
        path += '/food_settings.xlsx'

    if not os.path.isfile(path):
        print('Error: Missing the settings file "food_settings.xlsx"')
        input('Press any key to exit')
        sys.exit(1)
    try:
        settings = {}
        #with open(path, "r") as f:
        #    reader = csv.reader(f)
        #    for line in reader:
        #        settings[line[0]] = int(line[1])
        df = pd.read_excel(path)
        cols = df.columns
        settings[cols[0]] = int(cols[1])
    except:
        print('Error: Failed to process the settings sheet')
        input('Press any key to exit')
        sys.exit(1)

    # checking the settings dictionary
    keys = ["Number of Posts"]
    for key in keys:
        if key not in settings.keys():
            print(f"Warning: the setting '{key}' is not present in the settings file")
            settings[key] = 3000

    if settings["Number of Posts"] < 1:
        settings[key] = 3000

    return settings

def initialize_output():

    stamp = datetime.now().strftime("%d_%m_%Y_%H_%M")
    path = os.getcwd() + '\\Scraped_Data\\' + stamp
    if os.path.exists(path):
        os.remove(path) 
    os.makedirs(path)

    file1 = f'U_Food_{stamp}.xlsx'

    # Windws and Linux slashes
    if os.getcwd().find('/') != -1:
        output1 = path.replace('\\', '/') + "/" + file1
    else:
        output1 = path + "\\" + file1  

    # Create an new Excel file and add a worksheet.
    workbook1 = xlsxwriter.Workbook(output1)
    workbook1.add_worksheet()
    workbook1.close()    

    return output1

def main():
    print('Initializing The Bot ...')
    freeze_support()
    start = time.time()
    settings = get_inputs()
    output1 = initialize_output()
    homepages = ["https://food.ulifestyle.com.hk/restaurant/news/%E6%9C%80Hit%E9%A3%9F%E8%A8%8A"]
   
    try:
        driver = initialize_bot()
    except Exception as err:
        print('Failed to initialize the Chrome driver due to the following error:\n')
        print(str(err))
        print('-'*75)
        input('Press any key to exit.')
        sys.exit()
    for page in homepages:
        try:
            scrape_posts(driver, output1, page, settings)
        except Exception as err: 
            driver.quit()
            time.sleep(5)
            driver = initialize_bot()

    driver.quit()
    print('-'*100)
    elapsed_time = round(((time.time() - start)/60), 2)
    input(f'Process is completed in {elapsed_time} mins, Press any key to exit.')

if __name__ == '__main__':

    main()

