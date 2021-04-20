from selenium import webdriver
import scrapy
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait  # for implicit and explict waits
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


class SpiderDriver:

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--enable-javascript")
        self.driver = webdriver.Chrome(options=options, executable_path="/usr/local/bin/chromedriver")
        self.driver.implicitly_wait(30)

    def get(self, url):
        """
        directs driver to url, sleeps for a few seconds as a throttle and then returns the html for that url
        :param url:
        :return: html of the url location
        """
        self.driver.get(url)
        sleep(5)
        return self.driver.execute_script("return document.documentElement.outerHTML")

    def getNext(self, xpath):
        """
        hits button of the given xpath, sleeps, then returns the html of the desired button click
        :param xpath:
        :return: html of the next page
        """
        next_button = WebDriverWait(self.driver, 20).until(
            ec.presence_of_element_located((By.XPATH, xpath)))
        ActionChains(self.driver).move_to_element(next_button).perform()
        next_button.click()
        sleep(5)
        return self.driver.execute_script("return document.documentElement.outerHTML")

    def current_url(self):

        return self.driver.current_url

    def close(self):
        self.driver.close()
