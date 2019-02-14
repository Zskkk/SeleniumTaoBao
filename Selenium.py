from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from pyquery import PyQuery as pq
from urllib.parse import quote
import pymongo

KEYWORD = 'macbook'
MONGO_URL = 'localhost'
MONGO_DB = 'taobao'
MONGO_COLLECTION = 'products'

chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options)
wait = WebDriverWait(browser, 10)
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

def index_page(page):
    """
    抓取索引页
    :param page: 页码
    """
    print('正在爬取第', page, '页')
    try:
        url = 'https://s.taobao.com/search?q=' + quote(KEYWORD)
        browser.get(url)
        if page > 1:
            input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager div.form > input')))
            subimt = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager div.form .btn')))
            input.clear()
            subimt.send_keys(page)
            subimt.click()
        #判断下面页码是否高亮
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager li.item.active > span'), str(page)))
        #等待页面加载
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager .items .item')))
        get_products()
    except TimeoutException:
        index_page(page)

def get_products():
    """
    提取商品数据
    """
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-pager .items .item').items()
    for item in items:
        products = {
            'image': item.find('.pic img').attr('data-src'),
            'price': item.find('.row .price strong').text(),
            'deal': item.find('.row .deal-cnt').text(),
            'title': item.find('.ctx-box .title').text(),
            'shopname': item.find('.shop .shopname').text(),
            'location': item.find('.location').text()
        }
        print(products)
        save_to_mongo(product)

def save_to_mongo(result):
    """
    保存至MongoDB
    :param result: 结果
    """
    try:
        if db[MONGO_COLLECTION].insert(result):
            print('存储到MongoDB成功')
    except Exception:
        print('存储到MongoDB失败')

def main():
    for page in range(1, 101):
        index_page(page)
    browser.close()

if __name__ == '__main__':
    main()