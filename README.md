# ADB APK Installer
![image](https://github.com/user-attachments/assets/991abf71-f241-4bf7-8505-b0a30f71ff71)

Скачайте ADB:
https://developer.android.com/tools/releases/platform-tools

Настройка для Windows 11.

Не забудьте прописать ADB.exe в переменных среды Windows:
1. Найдите в Пуске  "Изменение системных переменных среды"

![image](https://github.com/pulya-na-vullet/apkAutoInstaller/assets/61897393/35ed3028-66c5-45c3-8755-58de6fb48575)

2. Откройте переменные среды:

![image-1](https://github.com/pulya-na-vullet/apkAutoInstaller/assets/61897393/e948b138-d34a-4326-9983-4c4d29d3a2df)

3. Нажмите "Изменить"

![image-3](https://github.com/pulya-na-vullet/apkAutoInstaller/assets/61897393/eb35ea54-6ede-40c3-964d-2da2b6f39b19)

4. Нажмите "Создать"

![image-4](https://github.com/pulya-na-vullet/apkAutoInstaller/assets/61897393/b60ff5a6-0beb-4254-bea6-7677194bbdae)

5. Укажите дирректорию до adb.exe

![image-5](https://github.com/pulya-na-vullet/apkAutoInstaller/assets/61897393/efb33253-6463-4d32-a6c9-0885758471c0)

6. Нажмите "Ок"

# Инструкция по работе с APK Installer:
1. Сохраните APK Installer.exe в дирректорию где есть разрешение на запись файлов
2. Запустите файл APK Installer.exe
3. В текстовом окне отображены устройства и эмуляторы подключенные к ADB.exe (устройства у которых включена отладка по USB. Подробнее тут: https://developer.android.com/tools/adb)
4. При первом запуске содается файл apk_to_unitall.txt в дирректории с файлом APK Installer.exe в котором прописаны тестовые приложения компании Лэтуаль. Вы можете сменить эти
названия на названия своего приложения.
5. Нажмите "Open APK" и выберите apk файл который Вам нужно установить на ваши девайсы.
6. Нажмите "Global Install" программа удалит с Ваших тестовых устройств все APK файлы названия которых зашиты в apk_to_unitall.txt и установит на все подключнные девайсы и эмуляторы Ваше       приложение.

# Дополнительный функционал:
- Каждый новый подключенный девайс или эмулятор отображен в текстовом поле.

# Планы по следующим версиям:
- Создание django сервера который из firebase app distribution будет сохранять сборки в хранилище и устанавливать приложения на подключенные к клиенту устройства.
- Добавление чекбокса "опция автоматической установки новой версии приложеиня"
- Добаввление предвыбранного набора APK на подключенные устройства
- Запуск трансляции устройства
