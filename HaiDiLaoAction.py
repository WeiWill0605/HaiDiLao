# coding=utf-8
import json
import re

import bs4
from Job.Locator.HaiDiLao.HaiDiLaoEntity import *
from Job.Locator.HaiDiLao.HaiDiLaoDao import HaiDiLaoDao
from Core.JobBase import JobBase
from Util import *


class HaiDiLaoAction(JobBase):
    city_dict = {}
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    def initialize(self):
        self.proxy = [self.LOCAL_PROXY_P4]
        # if self.debug():
        #     self.proxy = [self.LOCALHOST]
        self.create_http_manager()
        self._dao = HaiDiLaoDao(run_id=self.run_id, run_date=self.run_date)

    def create_http_manager(self):
        self.http_manager = self.init_http_manager()
        self.http_manager.set_header('Host', 'cater.haidilao.com')
        self.http_manager.set_header('Connection', 'keep-alive')
        self.http_manager.set_header('Accept', 'application/json, text/javascript, */*; q=0.01')
        self.http_manager.set_header('X-Requested-With', 'XMLHttpRequest')
        self.http_manager.set_header('User-Agent', 'Mozilla/5.0 (Linux; Android 8.0.0; MHA-AL00 Build/HUAWEIMHA-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/62.0.3202.84 Mobile Safari/537.36 Html5Plus/1.0')
        self.http_manager.set_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        self.http_manager.set_header('Accept-Encoding', 'gzip, deflate')
        self.http_manager.set_header('Accept-Language', 'zh-CN,en-US;q=0.9')

        self.manager_mobile = self.init_http_manager()
        self.manager_mobile.set_header('X-Device-Id', "XGYWskesLUwDAF/63Sp3Jevc")
        self.manager_mobile.set_header('X-Ca-Key', "60022326")
        self.manager_mobile.set_header('X-OS-Version', "5.1")
        self.manager_mobile.set_header('X-Device-Model', "Phone")
        self.manager_mobile.set_header('X-Ca-Signature-Headers', "X-Ca-Timestamp,X-Ca-Nonce,X-Ca-Key")
        self.manager_mobile.set_header('user-agent',
                                       "XT1077(Android/5.1) Haidilao(Haidilao/6.0.2) Weex/0.18.16.28 720x1184")
        self.manager_mobile.set_header('_HAIDILAO_APP_TOKEN', "")
        self.manager_mobile.set_header('X-Ca-Signature', "9tqLjSm8Zci1pHoB6bF2lbSB2hDl5+FPfTnm82DGnc8=")
        self.manager_mobile.set_header('X-Ca-Nonce', "F4FSHA3idJDh4UX1LpdaIXWr99tKPIjc")
        self.manager_mobile.set_header('X-OS-Type', "Android")
        self.manager_mobile.set_header('X-Source', "app")
        self.manager_mobile.set_header('X-utdid', "")
        self.manager_mobile.set_header('Accept', "application/json; charset=utf-8")
        self.manager_mobile.set_header('Content-Type', "application/json; charset=UTF-8")
        self.manager_mobile.set_header('Host', "superapp.kiwa-tech.com")
        self.manager_mobile.set_header('Connection', "Keep-Alive")
        self.manager_mobile.set_header('Accept-Encoding', "gzip")

    def on_run(self):
        try:
            self.log.info("%s has started" % self.__class__.__name__,
                          "jobID:[%s]" % self.job_id)
            self.initialize()
            self.log.info('start to get home stores')
            self.get_city()
            self.get_store()
            self.log.info('start to get foreign stores')
            self.get_foreign_store()
            if not self.debug():
                send_email(self=self)
            self.log.info("%s has finished" % self.__class__.__name__,
                          "jobID:[%s]" % self.job_id)
        except Exception, e:
            self.log.error("Unexpected/Unhandled Error. %s" % str(e))

    def get_city(self):
        url = 'https://superapp.kiwa-tech.com/app/cityPosition/getCityList'
        post_value = '{"_HAIDILAO_APP_TOKEN":"","customerId":""}'
        page_city = self.download_page(url, self.manager_mobile, post_data=post_value, validate_str='success":true')
        if 'success":true' not in page_city:
            self.log.error('failed to download page city')
            return
        json_page = json.loads(page_city)
        city_list = json_page.get('data').get('cityList')
        if not city_list:
            self.log.error('city list is None')
            return
        for city_block in city_list:
            city_id = city_block.get('cityId')
            city_name = city_block.get('cityName')
            self.city_dict[city_id] = city_name

    def get_store(self):
        url = 'https://superapp.kiwa-tech.com/app/getNearbyStore'
        post_value = '''{"_HAIDILAO_APP_TOKEN":"","customerId":"","latitude":"35.87456","longitude":"120.043743","pageSize":10,"pageNum":1,"country":"CN"}'''
        page = self.download_page(url, self.manager_mobile, post_data=post_value, validate_str='success":true')
        if 'success":true' not in page:
            self.log.error('failed to download store page')
            return
        json_page = json.loads(page)
        store_list = json_page.get('data')
        if not store_list:
            self.log.error('failed to get store list', str())
            return
        index = 0
        for store_block in store_list:
            index += 1
            if index % 10 == 0:
                self.log.info('process', '%s----%s' % (str(index), str(len(store_list))))
            try:
                s = Store()
                coord_str = store_block.get('coordinate')
                if ',' in coord_str:
                    s.longitude = str(coord_str).split(',')[0]
                    s.latitude = str(coord_str).split(',')[1]
                s.hours_of_operation = store_block.get('openTime')
                s.address_raw = store_block.get('address')
                s.loc_name = store_block.get('storeName')
                city_id = store_block.get('city')
                s.store_code = store_block.get('storeId')
                region_mark = store_block.get('regionMark')
                if region_mark == 1 or region_mark == 3:
                    s.country = 'CHN'
                elif region_mark == 2:
                    s.country = None
                    continue
                else:
                    self.log.error('unknown region mark', region_mark)

                s.city = self.city_dict.get(city_id)
                s.city_code = city_id
                phone_raw = self.get_store_details(store_id=s.store_code)
                s.phone_raw = phone_raw
                phone_list = phone_raw.split(',')
                if phone_list:
                    s.phone_1 = phone_list[0]
                    s.phone_2 = phone_list[-1]
                self._dao.save(s)
            except Exception, e:
                self.log.error('failed to process store', '%s---%s' % (str(store_block), str(e)))

    def get_store_details(self, store_id):
        url = 'https://superapp.kiwa-tech.com/app/getStoreById'
        post_data = '{"customerId":"","storeId":"111601"}'.replace('111601', store_id)
        page = self.download_page(url, self.manager_mobile, post_data=post_data, validate_str='success":true')
        if 'success":true' not in page:
            self.log.error('failed to get detail page', str(post_data))
            return
        json_page = json.loads(page)

        phone_raw = json_page.get('data').get('telephone')

        return phone_raw
    # def get_store(self, city_dict):
    #     city_name = city_dict.get('city')
    #     city_id = city_dict.get('cityId')
    #     store_count = str_to_int(city_dict.get('coutStore'))
    #     province_id = city_dict.get('provinceId')
    #     self.log.info('processing city', '%s---%s' % (str(city_name), str(store_count)))
    #     post_value = 'provinceid=%s&cityid=%s' % (province_id, city_id) + '&type=1&cuspoint=120.38442818%2C36.1052149'
    #     url_store = 'http://cater.haidilao.com/Cater/wap/findSelectStoreList.action'
    #     page_store = self.download_page(url_store, self.http_manager, post_data=post_value, validate_str='storeName')
    #     json_page = json.loads(page_store)
    #     if store_count != len(json_page):
    #         self.log.error('store count does not match', post_value)
    #     for store_block in json_page:
    #         try:
    #             s = Store()
    #             coord_str = store_block.get('coordinate')
    #             if ',' in coord_str:
    #                 s.longitude = str(coord_str).split(',')[0]
    #                 s.latitude = str(coord_str).split(',')[1]
    #             s.hours_of_operation = store_block.get('openTime')
    #             s.address_raw = store_block.get('storeAddress')
    #             s.loc_name = store_block.get('storeName')
    #             phone_raw = store_block.get('storetel')
    #             if ',' in phone_raw:
    #                 s.phone_1 = str(phone_raw).split(',')[0]
    #                 s.phone_2 = str(phone_raw).split(',')[1]
    #             else:
    #                 s.phone_1 = phone_raw
    #             s.phone_raw = phone_raw
    #             s.store_code = store_block.get('storeId')
    #             s.country = 'CHN'
    #             s.city = city_name
    #             s.city_code = city_id
    #             self._dao.save(s)
    #         except Exception, e:
    #             self.log.error('failed to process store', '%s---%s' % (str(store_block), str(e)) )

    def get_foreign_store(self):
        self.manager_foreign = self.init_http_manager()
        self.manager_foreign.set_header('Host', 'www.haidilao.com')
        self.manager_foreign.set_header('Connection', 'keep-alive')
        self.manager_foreign.set_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36')
        self.manager_foreign.set_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8')
        self.manager_foreign.set_header('Accept-Encoding', 'gzip, deflate')
        self.manager_foreign.set_header('Accept-Language', 'zh-CN,zh;q=0.9,en;q=0.8')

        url_foreign = 'http://www.haidilao.com/service/foreign'
        page_foreign = self.download_page(url_foreign, self.manager_foreign, validate_str='city_only')
        soup_page = bs4.BeautifulSoup(page_foreign)
        for country_block in soup_page.select('.tab-pane'):
            country_search = re.search(r'id="(.*?)">', str(country_block), re.M)
            if not country_search:
                self.log.error('failed to get country', str(country_block))
                continue
            country = country_search.group(1)
            for store_block in country_block.contents:
                s = Store()
                store_name_search = re.search(r'h3>(.*?)<', str(store_block), re.S)
                if store_name_search:
                    s.loc_name = store_name_search.group(1).strip()
                else:
                    continue
                phone_search = re.search(r'tel_phone">(.*?)<', str(store_block), re.S)
                if phone_search:
                    phone_raw = phone_search.group(1).strip()
                    s.phone_raw = phone_raw
                    if ',' in phone_raw:
                        s.phone_1 = str(phone_raw).split(',')[0]
                        s.phone_2 = str(phone_raw).split(',')[1]
                    else:
                        s.phone_1 = phone_raw
                address_search = re.search(r'address_icon">(.*?)<', str(store_block), re.S)
                if address_search:
                    s.address_raw = address_search.group(1).strip()

                open_time_search = re.search(r'h4>(.*?)<', str(store_block), re.S)
                if open_time_search:
                    s.hours_of_operation = open_time_search.group(1).strip()

                s.country = country
                self._dao.save(s)

    # def get_city(self):
    #     post_value = 'cuspoint=&realname=&source=&type=&mobile=&gender='
    #     url_city = 'http://cater.haidilao.com/Cater/terminus/store/city/list.action'
    #     page_city = self.download_page(url_city, self.http_manager, post_data=post_value,
    #                                    validate_str='"cities":[{"data":[{')
    #     if '"cities":[{"data":[{' not in page_city:
    #         self.log.error('failed to get city page', url_city)
    #         return
    #     json_page = json.loads(page_city)
    #     city_list = json_page.get('resultData').get('body').get('result').get('cities')
    #     for letter_city_block in city_list:
    #         letter_city_list = letter_city_block.get('data')
    #         for city_block in letter_city_list:
    #             self.get_store(city_dict=city_block)









