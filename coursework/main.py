from utils import *
from classes import SJVacancy, HHVacancy


def main():
    while True:
        user_key = input('Привет! Введите ключевое слово на английском языке для поиска вакансий (например, python или java): >> ')
        print(f'Ищем вакансии по ключевому слову "{user_key}" на сайтах HH и SuperJob. Нужно немного подождать.')

        file_1 = collect_data(HHVacancy, user_key)
        file_2 = collect_data(SJVacancy, user_key)

        all_data = upload_data_to_file(file_1, file_2)

        print('Нашли!')

        user_choice = input('Выберите действие и введи соответствующую цифру:\n1 - чтобы загрузить в файл 1000 вакансий по выбранному ключевому слову.\n2 - чтобы загрузить в файл топ вакансий по зарплатам.\n3 - чтобы загрузить в файл вакансии по выбранному ключевому слову с дополнительным параметром.\n4 - завершить работу программы. >> ')
        if user_choice == '1':
            print(upload_1000(all_data))

        elif user_choice == '2':
            num = int(input('Введите необходимое число вакансий в списке: >> '))
            sorted_data = sorting(all_data)
            print(get_top(sorted_data, num))

        elif user_choice == '3':
            num_key = input('Введите параметр, который хотите задать: 1 - название, 2 - описание или 3 - зарплата. >> ')
            if num_key == '1':
                key = 'name'
                value = input('Введите ключевое слово, которое должно содержаться в названии вакансии на сайте. >> ')
                print(select_data_from_all_data(all_data, {key: value}, strong=False))
            elif num_key == '2':
                key = 'description'
                value = input('Введите ключевое слово, которое должно содержаться в описании вакансии на сайте. >> ')
                print(select_data_from_all_data(all_data, {key: value}, strong=False))
            elif num_key == '3':
                key = 'salary'
                value = input('Введите число. >> ')
                try:
                    int_value = int(value)
                except ValueError:
                    print('Необходимо ввести число.')
                else:
                    print(select_data_from_all_data(all_data, {key: int_value}, strong=True))
            else:
                print('По такому параметру поиск невозможен.')

        elif user_choice == '4':
            print('Пока!')
            break

        else:
            print('Кажется, вы ввели что-то другое. Попробуйте еще раз.')


if __name__ == '__main__':
    main()
    