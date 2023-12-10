from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException

import time
from datetime import datetime, date
import sys

options = Options()
#options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

geckodriver_path = "D:\Files\Desktop\gecko\geckodriver.exe"  # specify the path to your geckodriver
driver_service = Service(executable_path=geckodriver_path)

driver = webdriver.Firefox(options=options, service=driver_service)
driver.implicitly_wait(10)

driver.get("https://www.hydro.eaufrance.fr/rechercher/entites-hydrometriques")
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.LINK_TEXT, 'SE CONNECTER'))).click()

WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'login_form__username'))).send_keys("louis.cockenpot@edu.devinci.fr")
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'login_form__password'))).send_keys("X%?,YZfi32Ud+gF")

WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn-block:nth-child(1)'))).click()
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn-outline-primary:nth-child(1)'))).click()
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.col-6:nth-child(1) > div:nth-child(1) > button:nth-child(3)'))).click()

# Cliquer sur chaque étoile
"""
for i in range(43):
    time.sleep(0.01)
    driver.find_element(By.CSS_SELECTOR, 'ul.pagination:nth-child(1) > li:nth-child(6) > a:nth-child(1)').click()
    i+=1
"""

for i in range(10):
    stars = driver.find_elements(By.CLASS_NAME, "favme.fas.fa-star")

    for star in stars:
        star.click()
        time.sleep(1)  # Pause pour simuler un comportement plus naturel

    time.sleep(2)
    driver.find_element(By.CSS_SELECTOR, 'ul.pagination:nth-child(1) > li:nth-child(6) > a:nth-child(1)').click()
    i += 1

driver.quit()



