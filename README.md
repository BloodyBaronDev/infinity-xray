# ⚡ Infinity Xray

**Серверная сборка Xray: тихие соединения живут дольше, XHTTP отзывчивее под нагрузкой.**
Работает со стандартными клиентами, в основе — официальный [XTLS/Xray-core](https://github.com/XTLS/Xray-core).

![Статус](https://img.shields.io/badge/статус-release%20candidate-orange)
![Версия](https://img.shields.io/badge/версия-0.1.0--rc.1-blue)
![Xray](https://img.shields.io/badge/Xray-v26.10.31-informational)
![Go](https://img.shields.io/badge/Go-1.27.3-00ADD8)
![Лицензия](https://img.shields.io/badge/лицензия-MPL%202.0-green)

> ⚠️ **Это кандидат релиза.** Перед установкой на рабочие ноды объединённой сборке нужны
> полный Linux-прогон и проверка итогового Docker-образа. [Что уже проверено →](TEST_RESULTS.md)

## ✨ Что внутри

| | Функция | Что даёт | Ограничения | Тесты |
|---|---|---|---|---|
| 💓 | **Hysteria keepalive** | Сервер сам шлёт QUIC keepalive в тишине | Мёртвых клиентов по-прежнему закрывают таймауты QUIC | [результаты](TEST_RESULTS.md#keepalive-стенд-3) |
| 🔁 | **Mux keepalive** | Пустые кадры Mux.Cool держат тихий downlink через CDN | Нужен mux на клиенте | [результаты](TEST_RESULTS.md#keepalive-стенд-3) |
| 🧩 | **Mux поверх XHTTP** | Снят серверный запрет | Для MASQUE запрет сохранён | [простой](TEST_RESULTS.md#простой-на-010-rc1-стенд-2) |
| 🚦 | **HTTP/2 governor** | Меньше задержка соседних запросов под нагрузкой | Больше CPU, уступает полосу конкурирующему TCP | [результаты](TEST_RESULTS.md#governor-http2-стенд-1) |
| 🛑 | **Ограниченная остановка** | До 7 с на Close и до 1 с на сообщение об ошибке | Зависший Start не покрыт | [результаты](TEST_RESULTS.md#целостность-и-остановка-стенд-1) |
| 📊 | **icstats** | Счётчики Hysteria и mux без содержимого трафика | Соединения без mux не измеряются | [результаты](TEST_RESULTS.md#диагностика-записей-mux) |
| 🔐 | **Проверка REALITY** | Ошибочные ключи и short ID отклоняются до запуска слушателя | — | — |
| 🧱 | **TCP-only Mux.Cool** | UDP к `v1.mux.cool` идёт обычной маршрутизацией | — | — |

**Не включено:** принудительный отзыв VLESS-пользователей. Remnawave Node 3.4.4 делает
remove/add даже для неизменённого пользователя, и такой патч обрывал бы живые соединения.

## 📈 Коротко о результатах

| Проверка | Без функции | С функцией |
|---|---|---|
| 💓 Простой Hysteria | умирает к 45 с | живо на 330 с |
| 🔁 Простой XHTTP + mux через CDN А | умирает к 90 с | живо на 330 с |
| 🚦 p95 соседних запросов при скачивании, RTT 50 мс | 2411 мс | 309 мс |
| 🚦 Скорость при конкурирующем TCP | 84,9 Мбит/с | **34,2 Мбит/с** (цена governor) |

Замеры сделаны на небольших выборках и частично на более ранних сборках.
Стенды и все оговорки: **[TEST_RESULTS.md](TEST_RESULTS.md)**.

## 🚀 Быстрый старт

Нужны Python 3.11+, git и Go с автозагрузкой toolchain, для образа — Docker.

```bash
bash build.sh                # бинарник linux/amd64
bash build.sh --full-checks  # плюс расширенные тесты governor
bash build.sh image          # плюс локальный образ для Remnawave Node
```

На Windows: `python build.py build`.
Результат: `out/0.1.0-rc.1/linux-amd64/` (`xray`, `SHA256SUMS`, `build-info.json`).
Сценарии ничего не устанавливают и не публикуют.

## ⚙️ Настройки

| Переменная | По умолчанию | Значение |
|---|---|---|
| `XRAY_IC_QUIC_KEEPALIVE` | `10` | Интервал QUIC keepalive, с; ≤0 отключает |
| `XRAY_IC_MUX_KEEPALIVE` | `5` | Тишина перед mux keepalive, с; ≤0 отключает |
| `XRAY_IC_STATS` | `60` | Интервал сводки icstats, с; ≤0 отключает сводку |
| `XRAY_XHTTP_FLOW` | в Docker `on`, у бинарника выключен | Серверный governor |

Явный `xhttpSettings.extra.h2Flow.enabled` важнее `XRAY_XHTTP_FLOW`.

## 🐳 Установка на ноду

В сервисе Remnawave Node меняется только `image`, порты и секреты остаются прежними.
Перезапуск оборвёт текущие соединения. Заранее сохраните compose и ID старого образа:
для отката верните прежний образ и пересоздайте сервис.

## 📌 База

| Xray-core | Commit | Go | Build tags | Remnawave Node | Цели |
|---|---|---|---|---|---|
| `v26.10.31` | `a4a3dff` | `go1.27.3` | `http2legacy` | `3.4.4` | `linux/amd64`, `windows/amd64` для локальных проверок |

Сборка сверяет commit базы и SHA256 патча из [`release.json`](release.json).

## 📚 Документация

- 🧪 [Результаты проверок](TEST_RESULTS.md)
- 🛠 [Сборка, правка патча, настройки и выпуск](docs/DEVELOPMENT.md)
- 📝 [История версий](CHANGELOG.md)
- 🧾 [Происхождение кода](NOTICE.md)

## 📄 Лицензия

[Mozilla Public License 2.0](LICENSE)
