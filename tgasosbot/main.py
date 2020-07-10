import requests
import config
from bs4 import BeautifulSoup as bs
import json
from lxml import etree
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram import Update
from telegram.ext import Updater
from telegram.ext import MessageHandler
from telegram.ext import Filters


headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
           'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 YaBrowser/20.2.0.1043 Yowser/2.5 Safari/537.36'}


def check_url(link):
    link = str(link)
    link = link.strip()
    if ('https://' or 'http://') not in link:
        link = ''.join(['https://', link])
    session = requests.Session()
    if ('asos' in link):
        request = session.get(link, headers=headers)
        if (request.status_code == 200):
            soup = bs(request.content, 'lxml')

            id = soup.find('link', attrs={'rel': 'alternate'})['href']
            if 'prd' in id:
                T = True
                i = len(id) - 1
                newID = ''
                while '/' not in newID:
                    newID += id[i]
                    i -= 1
                newID = newID[len(newID) - 2::-1]
            else:
                newID = ''
                T = False
        else:
            soup = 'None'
            T = False
    else:
        T = False
        newID = 'None'
        soup = 'None'

    return newID, T, soup, session


def get_all_urls(id):
    asos = 'asos.su/'
    all_urls = []
    valuet = ['RUB', 'GBP', 'AUD', 'TWD', 'HKD', 'ILS', 'CNY', 'TRR', 'EUR', 'SEK', 'CHF', 'EEG']
    for i in range(len(valuet)):
        url = ''.join([asos, valuet[i], id])
        all_urls.append(url)
    return all_urls


def get_urlsJs(id):
    regions = ['RU', 'COM', 'AU', 'ROW', 'ROW', 'ROW', 'ROW', 'ROW', 'DE', 'SE', 'FR', 'ROE']
    valuet = ['RUB', 'GBP', 'AUD', 'TWD', 'HKD', 'ILS', 'CNY', 'RUB', 'EUR', 'SEK', 'CHF', 'GBP']
    linksJs = []
    for i in range(len(regions)):
        NewLinks = ''.join(['https://www.asos.com/api/product/catalogue/v3/stockprice?productIds=', id, '&store=',  regions[i], '&currency=',  valuet[i], '&keyStoreDataversion=ekbycqu-23'])
        linksJs.append(NewLinks)
    return linksJs, valuet


def parser_asos(linksJs, all_urls, valuet, session, soup):
    goods = []
    conuntryList = ['RU', 'GB', 'AU', 'TW', 'HK', 'IL', 'CN', 'TR', 'DE', 'SE', 'FR', 'EE']
    for i in range(len(all_urls)):

        country = conuntryList[i]

        requestPrice = session.get(linksJs[i], headers=headers)
        soupJs = bs(requestPrice.content, 'lxml')
        soupJs = str(soupJs)
        root = etree.fromstring(soupJs)
        price = json.loads(root.xpath('.//p')[0].text)
        price = price[0]['productPrice']['current']['value']

        if i == 1:
            name = soup.find('h1').text
            goods.append({'name': name})

        goods.append({
            'country': country,
            'price': float(price),
            'valuet': valuet[i],
            'url': all_urls[i]
            })

    return goods


def get_course(headers, session):
    url = 'https://pokur.su/gbp/'
    request = session.get(url, headers=headers)
    soup = bs(request.content, 'lxml')
    cours = []
    valuet = ['rub', 'aud', 'twd', 'hkd', 'ils', 'cny', 'eur', 'sek', 'chf']
    for i in range(len(valuet)):
        link = ''.join(['/gbp/', valuet[i], '/1/'])
        a = soup.find('a', attrs={'href': link}).text
        if ',' in a:
            a = float(a.replace(',', '.'))
        cours.append({
            valuet[i].upper(): a
        })
    return cours


def result(cours, goods):
    for i in range(2, len(goods)):
        val = goods[i].get('valuet')
        pr = goods[i].get('price')
        rub = cours[0].get('RUB')
        if val == 'GBP':
            res = float('{:.2f}'.format(pr * rub))
        else:
            for j in range(len(cours)):
                cr = cours[j].get(val)
                if cr != None:
                    a = cr
                    res = float('{:.2f}'.format(pr / a * rub))
        goods[i]['rub'] = res
    goods[0]['rub'] = goods[0].get('price')


def sort(goods):
    name = str(goods[1].get('name'))
    goods.pop(1)
    for i in range(len(goods)):
        for j in range(len(goods)-i-1):
            if goods[j].get('rub') < goods[j+1].get('rub'):
                goods[j], goods[j+1] = goods[j+1], goods[j]
    return goods, name


def prinT(goods,name):
    s = '*'+name+'*'+'\n'
    bl = ' '*24
    for i in range(len(goods)):
        s += ''.join([f'\n {goods[i].get("country")} \t\t {goods[i].get("rub")} \t\t ✔️{goods[i].get("price"):}  ({goods[i].get("valuet")}): \n {bl} {goods[i].get("url")}'])
    s += '👈🏻'
    res = goods[0].get('rub')
    k = 0
    for i in range(len(goods)-1):
        if res > goods[i+1].get('rub'):
            res = goods[i+1].get('rub')
            k = i + 1
    content = ['',
               '',
               f'☝🏻Лучшее предложение в {goods[k].get("country")} - {res} руб, оплата в {goods[k].get("valuet")}.',]

    s += '\n'.join(content)
    return s


def get_url(update: Update, context: CallbackContext):
    link = update.effective_message.text
    if link == '/start':
        text = ['Привет!',
                '',
                'Бот создан для помощи в покупках на ASOS.COM.',
                'Знаешь ли ты, что один и тот же товар',
                'имеет разные цены на сайтах ASOS, относящихся к разным странам',
                'Бот сканирует цены на всех ASOS-сайтах',
                'и сравнивает их в выбраной валюте.',
                'Узнай, где продукт имеет самую низкую цену, и в какой валюте',
                'выгоднее всего совершить покупку!',
                '',
                'Отправь  ссылку на товар, цены на который хочешь сравнить!',
                '']
        update.message.reply_text(
            text='\n'.join(text),
            parse_mode=ParseMode.MARKDOWN,
        )
    elif link == '/help':
        text = ['Бот просматривает цены на сайте ASOS всех регионов',
                'и сравнивает их в выбраной валюте.',
                '',
                'Отправь ссылку на товар, цены на который хочешь сравнить!',
                '']
        update.message.reply_text(
            text='\n'.join(text),
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        id, T, soup, session = check_url(link,)
        if T:
            update.message.reply_text(
                text='Подождите, идет поиск цен...'
            )
            all_urls = get_all_urls(id)
            linksJs, valuet = get_urlsJs(id)
            goods = parser_asos(linksJs, all_urls, valuet, session, soup)
            cours = get_course(headers, session)
            result(cours, goods)
            goods, name = sort(goods)
            end = prinT(goods,name)
            update.message.reply_text(
                text=end,
                parse_mode=ParseMode.MARKDOWN,
               )
        else:
            update.message.reply_text(
                text='Ошибка. Не могу определить эту ссылку.'
            )


def main():
    TG_TOKEN = config.TOKEN
    updater = Updater(
        token=str(TG_TOKEN),
        use_context=True,
    )
    updater.dispatcher.add_handler(MessageHandler(Filters.text, callback=get_url))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
