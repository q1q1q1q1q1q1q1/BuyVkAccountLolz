from bs4 import BeautifulSoup as BS
from selenium import webdriver
import pickle
import os
import time
import datetime
import vk_api


PATH_TO_CHROMEDRIVER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'chromedriver')
PATH_TO_COOKIES_LOLZ = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cookiesLolz.pkl')
PATH_TO_COOKIES_VK = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cookiesVk.pkl')


SET_FRIENDS_COUNT = 100
SET_MAX_PRICE_ACCOUNT = 14
SET_MIN_PRICE_ACCOUNT = 0
LAST_SIGN_IN_AGO = 2
CURRENT_MONTH = "авг"

NEW_PASSWORD = "k2fm2m2flk23mwqe"

MAIN_URL_LOLZTEAM = "https://lolz.guru/"
URL_TO_BUY_VK_ACCOUNTS = MAIN_URL_LOLZTEAM + f"market/vkontakte/page-3?pmin={str(SET_MIN_PRICE_ACCOUNT)}&pmax={str(SET_MAX_PRICE_ACCOUNT)}&order_by=price_to_up&group_follower_min=0&group_follower_max=0&groups_min=0&groups_max=0&admin_level=0&reg=0&page="

UNLIKE_KEY_WORDS = ['online', 'сегодня', 'три', 'часа', 'назад', 'час', 'минуту', 'минут' 'только', 'что', 'вчера', 'недавно', 'этой', 'неделе']


class FindVkAccount:
    def start(self, i=1):

        driver = self.openLolzPage()
        try:
            while i <= getLastPage(driver.page_source):
                balance = self.checkBalance(driver.page_source)

                linksToAccount = self.checkAcoountsOnPage(driver, balance)
                self.checkLastSignIn(linksToAccount, driver)
                i += 1

                driver.get(URL_TO_BUY_VK_ACCOUNTS + str(i))
        except AttributeError:
            print("[INF] Scan is ended")

    def openLolzPage(self):
        driver = webdriver.Chrome(executable_path=PATH_TO_CHROMEDRIVER)
        driver.get(URL_TO_BUY_VK_ACCOUNTS + str(1))
        cookies = pickle.load(open(PATH_TO_COOKIES_LOLZ, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)

        cookies = pickle.load(open(PATH_TO_COOKIES_VK, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)

        time.sleep(5)
        return driver

    def checkBalance(self, html):
        soup = parsHtml(html)
        return int(soup.find("span", class_="balanceValue").text)

    def checkAcoountsOnPage(self, driver, balance):
        linksToAccount = []
        soup = parsHtml(driver.page_source)
        marketItems = soup.find_all("div", class_="marketIndexItem")
        for item in marketItems:
            #price = int(item.find("div", class_="marketIndexItem--Price").text) ### For compare with balance ###
            friendsCount = int(item.find("div", class_="marketIndexItem--Stats").text.strip().split("\n")[0].split(" ")[0])

            if friendsCount > SET_FRIENDS_COUNT:
                urlPrefix = item.find("a", class_="marketIndexItem--Title").get("href")

                if not self.checkForRepeat(urlPrefix):
                    continue

                linksToAccount.append(MAIN_URL_LOLZTEAM + urlPrefix)
        return linksToAccount

    def checkForRepeat(self, urlPrefix):
        with open("TryingPost.txt") as file:
            ids = file.read().split("\n")

        FLAG_ = 0
        for idd in ids:
            if idd == urlPrefix:
                FLAG_ += 1

        if FLAG_ == 0:
            with open("TryingPost.txt", "a") as file:
                file.write(urlPrefix + "\n")

            return True
        return False

    def checkLastSignIn(self, linksToAccount, driver):
        for link in linksToAccount:
            driver.get(link)
            soup = parsHtml(driver.page_source)
            try:
                linkToVk = soup.find("span", class_="data").text
            except AttributeError:
                continue

            driver.get(linkToVk)
            soup = parsHtml(driver.page_source)
            try:
                activity = soup.find("div", class_="profile_online_lv").text
            except AttributeError:
                continue

            FLAG_ = 0

            for keyWord in UNLIKE_KEY_WORDS:
                if keyWord in activity:
                    FLAG_ += 1

            if FLAG_ == 0:
                if CURRENT_MONTH in activity:
                    lastSignIn = int(activity.split(" ")[1])
                    if int(str(datetime.datetime.today()).split(" ")[0].split("-")[-1]) - lastSignIn < LAST_SIGN_IN_AGO:
                        continue
                print(linkToVk)
                print(activity)
                print(link)
                self.buyAccount(link, driver)

    def buyAccount(self, link, driver):
        driver.get(link)
        try:
            driver.find_element_by_xpath('//a[@class="button primary OverlayTrigger marketViewItem--buyButton "]').click()
            time.sleep(8)
        except Exception as e:
            print(e)
            return

        soup = parsHtml(driver.page_source)
        try:
            loginAndPass = soup.find("span", id="loginData--login_and_password").text
        except AttributeError:
            return
        print(loginAndPass)
        self.changePassword(loginAndPass)

    def changePassword(self, loginAndPass):
        login = loginAndPass.split(":")[0]
        password = loginAndPass.split(":")[1]
        vk_session = vk_api.VkApi(login, password)
        try:
            vk_session.auth()
        except Exception as e:
            print(e)
            print("[INF] Bad salesman")
            return

        vk = vk_session.get_api()
        infoProf = vk.account.getProfileInfo()
        vk.account.changePassword(old_password=password, new_password=NEW_PASSWORD)
        name = infoProf["first_name"]
        lastName = infoProf["last_name"]
        print("[INF] Password Changed")
        self.saveAccountData(login, NEW_PASSWORD, name, lastName)

    def saveAccountData(self, login, password, name, lastName):
        with open("accounts.txt", 'a') as file:
            file.write(login + ":" + password + ":" + name + ":" + lastName + "\n")


def parsHtml(html):
    return BS(html, 'lxml')


def getLastPage(html):
    soup = parsHtml(html)
    return int(soup.find("div", class_="PageNav").get("data-last"))


if __name__ == '__main__':
    acc = FindVkAccount()
    acc.start()
