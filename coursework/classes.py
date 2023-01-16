import json
import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
import os
import re


class Engine(ABC):
    @abstractmethod
    def get_request(self, keyword: str):
        pass

    @staticmethod
    def get_connector(file_name):
        """ Возвращает экземпляр класса Connector """
        connector = Connector(file_name)
        return connector


class HH(Engine):
    def __init__(self):
        self.response_list = []
        self.max_range = 0

    def get_request(self, key: str) -> list:
        """
        Выгружает данные обо всех подходящих вакансиях с сайта HeadHunter.
        """
        key = key.capitalize()
        url = 'https://api.hh.ru/vacancies'

        total_num_response = requests.get(url, {'text': key, 'area': 113})
        total_num = total_num_response.json()['found']
        per_page = 100
        if total_num <= 1000:
            self.max_range = total_num // per_page + 1
        else:
            self.max_range = 11

        for i in range(self.max_range):
            par = {'page': i, 'per_page': per_page, 'text': key, 'area': '113'}
            response = requests.get(url, params=par)
            self.response_list += response.json()['items']

        return self.response_list

    def __len__(self):
        return len(self.response_list)


class SuperJob(Engine):
    def get_request(self, key: str) -> list:
        """
        Выгружает данные обо всех подходящих вакансиях с сайта SuperJob.
        """
        key = key.lower()
        raw_items_list = []

        for i in range(1, 4):
            page = i
            url = f'https://russia.superjob.ru/vacancy/search/?keywords={key}&page={page}'

            response = requests.get(url)
            response_text = response.text

            soup = BeautifulSoup(response_text, 'lxml')
            soup_items = soup.find_all('div', class_='f-test-search-result-item')

            raw_items_list += soup_items

        return raw_items_list


class Vacancy:
    __slots__ = ('__name', '__url', '__description', '__salary', '__refactored_salary')

    def __init__(self, name, url, description, salary):
        self.__name = name
        self.__url = url
        self.__description = description
        self.__salary = salary
        self.__refactored_salary = 0

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, value):
        self.__url = value

    @property
    def description(self):
        return self.__description

    @description.setter
    def description(self, value):
        self.__description = value

    @property
    def salary(self):
        return self.__salary

    @salary.setter
    def salary(self, value):
        self.__salary = value

    def refactor_salary(self):
        """
        Приводит данные о зарплате к одному виду - числовому представлению.
        """
        money = self.__salary
        if isinstance(money, int):
            self.__refactored_salary = self.__salary

        elif isinstance(money, str) and all(word not in money for word in ['По договорённости', 'не указано', 'None']):
            regexp = re.compile(r'(^\d{4,6})|[а-я]{2}(\d{4,6})')
            m = regexp.match(money)
            if m.group(1):
                self.__refactored_salary = int(m.group(1))
            elif m.group(2):
                self.__refactored_salary = int(m.group(2))

    def __lt__(self, other):
        return self.__refactored_salary < other

    def __gt__(self, other):
        return self.__refactored_salary > other

    def __eq__(self, other):
        return self.__refactored_salary == other

    def __ne__(self, other):
        return self.__refactored_salary != other

    def __repr__(self) -> str:
        """
        Возвращает строку, содержащую данные о вакансии.
        """

        return f'Позиция: {self.__name}:\nОписание: {self.__description}\nЗаработная плата от: {self.__refactored_salary}\nСсылка на вакансию: {self.__url}\n\n'


class CountMixin:
    @property
    def get_count_of_vacancy(self):
        """
        Вернуть количество вакансий от текущего сервиса.
        Получать количество необходимо динамически из файла.
        """
        with open('../data/' + self.data_file_name, 'r', encoding='utf-8') as file:
            data = json.load(file)

        return len(data)


class HHVacancy(Vacancy, CountMixin):  # add counter mixin
    """ HeadHunter Vacancy """
    __slots__ = ('data_file_name')

    def __init__(self, __name, __url, __description, __salary):
        self.data_file_name = 'data_hh.json'
        super().__init__(__name, __url, __description, __salary)

    def __str__(self):
        return f'HH: {self.__name}, зарплата: {self.__salary} руб/мес'

    def get_data(self, key: str) -> None:
        hh = HH()
        data_list = hh.get_request(key)
        list_for_vacancies = []
        for i in range(len(hh)):
            self.__name = data_list[i]['name']
            self.__url = data_list[i]['alternate_url']
            description_v_raw = f'{data_list[i]["snippet"]["requirement"] }' + f'{data_list[i]["snippet"]["responsibility"]}'
            description_v_r = description_v_raw.replace('<highlighttext>Python</highlighttext>', '')
            self.__description = description_v_r.replace('<highlighttext>python</highlighttext>', '')
            try:
                self.__salary = data_list[i]['salary']['from']
            except TypeError:
                self.__salary = 'не указано'

            list_for_vacancies.append({'name': self.__name, 'url': self.__url, 'description': self.__description, 'salary': self.__salary})

        connector = hh.get_connector(self.data_file_name)
        connector.insert(list_for_vacancies)

        return connector.data_file


class SJVacancy(Vacancy, CountMixin):  # add counter mixin
    """ SuperJob Vacancy """
    __slots__ = ('data_file_name')

    def __init__(self, __name, __url, __description, __salary):
        self.data_file_name = 'data_sj.json'
        super().__init__(__name, __url, __description, __salary)

    def __str__(self):
        return f'SJ: {self.__name}, зарплата: {self.__salary} руб/мес'

    def get_data(self, key: str):
        sj = SuperJob()
        data_list = sj.get_request(key)

        list_for_vacancies = []
        for data in data_list:
            basic_path_description = ''
            basic_path_others = ''
            salary_v_r = ''
            is_ad = False
            try:
                basic_path_description = data.contents[0].contents[0].contents[0].contents[0]
                basic_path_others = basic_path_description.contents[0].contents[0].contents[1].contents[0].contents[0]
                salary_v_r = basic_path_others.contents[1].text

            except IndexError:
                try:
                    basic_path_description = data.contents[1].contents[0].contents[0].contents[0]
                    basic_path_others = basic_path_description.contents[0].contents[0].contents[1].contents[0].contents[0]
                    salary_v_r = basic_path_others.contents[1].text
                except (IndexError, AttributeError) as e:
                    print('Пропускаю рекламу...')
                    is_ad = True

            finally:
                if is_ad:
                    continue

                self.__salary = salary_v_r.replace('\xa0', '')
                self.__name = basic_path_others.contents[0].text
                self.__description = basic_path_description.contents[2].text
                self.__url = 'https://russia.superjob.ru' + basic_path_others.contents[0].contents[0].contents[0].contents[0].attrs['href']
                list_for_vacancies.append({'name': self.__name, 'url': self.__url, 'description': self.__description, 'salary': self.__salary})

        connector = sj.get_connector('data_sj.json')
        connector.insert(list_for_vacancies)

        return connector.data_file


class Connector:
    """
    Класс-коннектор к файлу, обязательно файл должен быть в json формате
    не забывать проверять целостность данных, что файл с данными не подвергся
    внешней деградации
    """
    __data_file = None

    def __init__(self, df):
        self.__data_file = '../data/' + df
        self.__connect()

    @property
    def data_file(self):
        return self.__data_file

    @data_file.setter
    def data_file(self, value):
        if value[-5:-1] == '.json':
            self.__data_file = '../data/' + value
        else:
            self.__data_file = '../data/' + value + '.json'
        self.__connect()

    def __connect(self):
        """
        Проверка на существование файла с данными и
        создание его при необходимости
        Также проверить на деградацию и возбудить исключение
        если файл потерял актуальность в структуре данных
        """
        if os.path.isfile(self.__data_file):
            try:
                with open(self.__data_file, encoding='utf-8') as file:
                    value_from_file = json.load(file)[0]['name']
                capitalized_check = value_from_file.capitalize()
            except AttributeError:
                raise AttributeError('файл поврежден')
        else:
            new_file = open(self.__data_file, 'x')
            new_file.close()

    def insert(self, data):
        """
        Запись данных в файл с сохранением структуры и исходных данных
        """
        with open(self.__data_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False)

    def select(self, query, strong=True):
        """
        Выбор данных из файла с применением фильтрации
        query содержит словарь, в котором ключ - это поле для
        фильтрации, а значение - это искомое значение, например:
        {'price': 1000}, должно отфильтровать данные по полю price
        и вернуть все строки, в которых цена 1000
        """
        with open(self.__data_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        if query:
            key, value = list(query.items())[0]
            if strong:
                selected_data = [data_item for data_item in data if data_item[key] == value]
            else:
                selected_data = [data_item for data_item in data if value in data_item[key]]
            return selected_data
        return data

    def delete(self, query):
        """
        Удаление записей из файла, которые соответствуют запросу,
        как в методе select. Если в query передан пустой словарь, то
        функция удаления не сработает
        """
        if query:
            with open(self.__data_file, 'r', encoding='utf-8') as file_r:
                data = json.load(file_r)

            key, value = query.items()[0]
            saved_data = [data_item for data_item in data if data_item[key] != value]
            with open(self.__data_file, 'w', encoding='utf-8') as file_w:
                json.dump(saved_data, file_w)
                