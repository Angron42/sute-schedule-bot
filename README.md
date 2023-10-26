<div align="center">

<img src="https://user-images.githubusercontent.com/81159301/193612153-e085ffb7-230b-413c-a7b2-c450536cd397.png" alt="Логотип бота" width="200"><br><br>

# Розклад ДТЕУ
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
## [English version](README.en.md)

Телеграм-бот для зручного перегляду розкладу пар у Державному Торговельно-Економісному Університеті ([ДТЕУ](https://knute.edu.ua)).<br>
Бот доступний для використання: [@dteubot](https://t.me/dteubot).

</div><br>


# Функції

- ✅ Перегляд розкладу пар
- ✅ Нагадування про пари
- ✅ Посилання на профілі викладачів
- ✅ Стабільна робота при недоступності сайту
- Та інші функції, такі як перегляд розкладу дзвінків, списку студентів групи та часу до перерви.


# Скріншоти

![Скріншот взаємодії](https://github.com/cubicbyte/dteubot/assets/81159301/554f4df6-9812-4a65-b06e-9a6fd47df889)


# Команди

* **/today**<br>
  пари сьогодні
* **/tomorrow**<br>
  пари завтра
* **/left**<br>
  час до кінця/початку пари
* **/calls**<br>
  розклад дзвінків
* **/settings**<br>
  відкрити налаштування
* **/group \<groupId?: `number`\>**<br>
  вибрати групу
* **/lang \<lang?: `[en/uk/ru]`\>**<br>
  вибрати мову

? - необов'язковий параметр
<br><br>


# Запуск

Бота можна запустити трьома способами:
- Через виконуваний файл (.exe для Windows)
- Через Docker-контейнер
- З ручною компіляцією

## 1. Звичайний спосіб

1. Завантажте [останню версію бота](https://github.com/cubicbyte/dteubot/releases/latest)
2. Розмістіть файл `dteubot` в будь-якій директорії, в якій ви хочете зберігати дані бота
3. Запустіть файл цією командою: (після першого запуску буде створено файл конфігурації)
   ```shell
   ./dteubot
   ```
4. Відкрийте файл `.env` та заповніть **BOT_TOKEN**. Інші налаштування опціональні.
5. Запустіть бота цією командою:
   ```shell
   ./dteubot
   ```

Готово!

## 2. Docker

На даний момент у розробці.

## 3. Ручна компіляція

> :warning: Для цього способу вам потрібен **Go** версії **1.21.1+** - [завантажити](https://golang.org/dl/)

1. Завантажте цей репозиторій та відкрийте в ньому командний рядок.<br>
   Для завантаження, нажміть зелену кнопку **<span style="color: lightgreen;"><> Code</span> > Download ZIP**<br>
   або виконайте команду
   ```shell
   git clone https://github.com/cubicbyte/dteubot
   ```
2. Переконайтесь, що маєте встановлений компілятор **Go** та виконайте команду
   ```shell
   go build
   ```

Тепер ви маєте виконуваний файл `dteubot`. Перейдіть до розділу **1. Звичайний спосіб**
