Гайд по развертке проекта
*Глава 1 установка Unreal Engine*
<Плейсхолдер для гайда по установки анрил энжен>
*Глава 2 установка SITL px4 в WSL *
1) Установить wsl2
2) Склонировать репозиторий в wsl коммандой (git clone https://github.com/PX4/PX4-Autopilot.git --recursive)
3) В терминале windows с помощью команды ipconfig узнать ip адресс wsl
4) С помощью команды *nano ~/.bashrc* добавить системную переменную PX4_SIM_HOST_ADDR комаандой *export PX4_SIM_HOST_ADDR=* присвоить значение найденное на шаге 3
5) Перейти в дерикторию */PX4-Autopilot* и использовать команду  make px4_sitl_default none_iris

*Глава 3 Python код для автономного управления дроном  в WSL *
1) Скопировать репозиторий в wsl командой (git clone https://github.com/ildimas/Aerohack_Beverly_Hills_Misis_4.git)
2) Cоздать виртуальное окружение с помощью команды python3 -m venv envi (!Вы можете выбрать другое название)
3) Активировать виртуальное окжуение командой *source envi/bin/activate*
4) Запустить энтрипоинт файл mavsdk_test.py командой *python3 mavsdk_test.py*

Порядок запуска: Unreal Engine -> SITL PX4 -> Python код 