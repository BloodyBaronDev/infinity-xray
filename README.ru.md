# ⚡ Infinity Xray

[English](README.md) · **Русский**

**Серверная сборка Xray: тихие соединения живут дольше, XHTTP отзывчивее под нагрузкой.**
Работает со стандартными клиентами, в основе — официальный [XTLS/Xray-core](https://github.com/XTLS/Xray-core).

![Статус](https://img.shields.io/badge/статус-стабильный-brightgreen)
![Версия](https://img.shields.io/badge/версия-0.2.0-blue)
![Xray](https://img.shields.io/badge/Xray-v26.11.9-informational)
![Go](https://img.shields.io/badge/Go-1.27.3-00ADD8)
![Лицензия](https://img.shields.io/badge/лицензия-MPL%202.0-green)
[![Релиз](https://img.shields.io/github/v/release/BloodyBaronDev/infinity-xray)](https://github.com/BloodyBaronDev/infinity-xray/releases/latest)
[![Звёзды](https://img.shields.io/github/stars/BloodyBaronDev/infinity-xray?style=social)](https://github.com/BloodyBaronDev/infinity-xray/stargazers)

## ✨ Что внутри

| | Функция | Что даёт | Ограничения | Тесты |
|---|---|---|---|---|
| 💓 | **Hysteria keepalive** | Сервер сам шлёт QUIC keepalive в тишине | Мёртвых клиентов по-прежнему закрывают таймауты QUIC | [результаты](TEST_RESULTS.md#keepalive-стенд-3) |
| 🔁 | **Mux keepalive** | Пустые кадры Mux.Cool держат тихий downlink через CDN | Нужен mux на клиенте | [результаты](TEST_RESULTS.md#keepalive-стенд-3) |
| 🧩 | **Mux поверх XHTTP** | Снят серверный запрет | Для MASQUE запрет сохранён | [простой](TEST_RESULTS.md#простой-на-010-rc1-стенд-2) |
| 🚦 | **HTTP/2 governor** | Меньше задержка соседних запросов под нагрузкой | Больше CPU, уступает полосу конкурирующему TCP | [результаты](TEST_RESULTS.md#governor-http2-стенд-1) |
| 🛑 | **Ограниченная остановка** | До 7 с на Close и до 1 с на сообщение об ошибке | — | [результаты](TEST_RESULTS.md#целостность-и-остановка-стенд-1) |
| 📊 | **icstats** | Счётчики Hysteria и mux без содержимого трафика | Соединения без mux не измеряются | [результаты](TEST_RESULTS.md#диагностика-записей-mux) |
| 🔐 | **Проверка REALITY** | Ошибочные ключи и short ID отклоняются до запуска слушателя | — | — |
| 🧱 | **TCP-only Mux.Cool** | UDP к `v1.mux.cool` идёт обычной маршрутизацией | — | — |
| ⏳ | **Отзыв VLESS с отсрочкой** | Соединения удалённого пользователя закрываются, если ключ не вернулся | Выключен; только VLESS | [rc.1](reports/0.2.0-rc.1-test-report.md) |
| 🚧 | **Лимиты на пользователя** | Предел соединений VLESS и общей скорости на email | Выключены; одно значение на всех; Vision без splice | [rc.1](reports/0.2.0-rc.1-test-report.md) |
| 📈 | **Метрики Prometheus** | Агрегаты без пользователей и адресов | Выключены; авторизации нет | [rc.1](reports/0.2.0-rc.1-test-report.md) |
| 🌙 | **Плавная остановка** | Принятые соединения дорабатывают до срока | Выключена; не для QUIC | [rc.1](reports/0.2.0-rc.1-test-report.md) |
| ⏱ | **Сторож запуска** | Зависший Start завершает процесс с кодом 1 | — | — |

Безусловный отзыв не включён: Remnawave Node делает remove/add даже для неизменённого
пользователя, поэтому отзыв работает только с отсрочкой `XRAY_IC_REVOKE_GRACE`.
Режим конкуренции governor (`XRAY_XHTTP_FLOW_COMPETE`) экспериментальный и выключен.

## 📈 Коротко о результатах

| Проверка | Без функции | С функцией |
|---|---|---|
| 💓 Простой Hysteria | умирает к 45 с | живо на 330 с |
| 🔁 Простой XHTTP + mux через CDN А | умирает к 90 с | живо на 330 с |
| 🚦 p95 соседних запросов при скачивании, RTT 50 мс | 2411 мс | 309 мс |
| 🚦 Скорость при конкурирующем TCP | 84,9 Мбит/с | **34,2 Мбит/с** (цена governor) |

0.2.0-rc.3 на рабочей ноде: 0 рестартов, около 32% одного ядра при ~130 Мбит/с,
governor срабатывает на XHTTP + REALITY. Сравнения A/B с прошлой версией нет.

Замеры сделаны на небольших выборках и частично на более ранних сборках.
Стенды и оговорки: **[TEST_RESULTS.md](TEST_RESULTS.md)** и [отчёты](reports/).

## 🚀 Быстрый старт

Нужны Python 3.11+, git и Go с автозагрузкой toolchain, для образа — Docker.

```bash
bash build.sh                # бинарник linux/amd64
bash build.sh --full-checks  # плюс расширенные тесты governor
bash build.sh image          # плюс локальный образ для Remnawave Node
```

На Windows: `python build.py build`.
Результат: `out/0.2.0/linux-amd64/` (`xray`, `SHA256SUMS`, `build-info.json`).
Сценарии ничего не устанавливают и не публикуют.

## ⚙️ Настройки

| Переменная | По умолчанию | Значение |
|---|---|---|
| `XRAY_IC_QUIC_KEEPALIVE` | `10` | Интервал QUIC keepalive, с; ≤0 отключает |
| `XRAY_IC_MUX_KEEPALIVE` | `5` | Тишина перед mux keepalive, с; ≤0 отключает |
| `XRAY_IC_STATS` | `60` | Интервал сводки icstats, с; ≤0 отключает сводку |
| `XRAY_XHTTP_FLOW` | в Docker `on`, у бинарника выключен | Серверный governor |
| `XRAY_XHTTP_FLOW_COMPETE` | выключено | Экспериментальный режим конкуренции governor |
| `XRAY_IC_REVOKE_GRACE` | `0` | Отсрочка отзыва VLESS, с; больше паузы remove/add панели; 0 отключает |
| `XRAY_IC_USER_MAX_CONNS` | `0` | Предел соединений VLESS на email, mux = одно; 0 отключает |
| `XRAY_IC_USER_RATE_DOWN_MBPS` | `0` | Общий лимит скачивания на email, Мбит/с; 0 отключает |
| `XRAY_IC_USER_RATE_UP_MBPS` | `0` | Общий лимит загрузки на email, Мбит/с; 0 отключает |
| `XRAY_IC_METRICS_LISTEN` | не задано | Адрес `/metrics`, например `127.0.0.1:9550`; не публикуйте наружу |
| `XRAY_IC_DRAIN_SECONDS` | `0` | Ожидание соединений при остановке, с; 0 отключает |
| `XRAY_IC_START_TIMEOUT` | `60` | Предел запуска, с; ≤0 отключает |

Явный `xhttpSettings.extra.h2Flow.enabled` важнее `XRAY_XHTTP_FLOW`.

## 🐳 Установка на ноду

Готовый образ на базе `remnawave/node:3.4.5`:

```yaml
services:
  remnanode:
    image: ghcr.io/bloodybarondev/infinity-xray:0.2.0   # вместо remnawave/node
```

```bash
docker compose pull && docker compose up -d
```

В сервисе Remnawave Node меняется только `image`, порты и секреты остаются прежними.
Перезапуск оборвёт текущие соединения. Заранее сохраните compose и ID старого образа:
для отката верните прежний образ и пересоздайте сервис.

## 📌 База

| Xray-core | Commit | Go | Build tags | Remnawave Node | Цели |
|---|---|---|---|---|---|
| `v26.11.9` | `676eaf6` | `go1.27.3` | `http2legacy` | `3.4.5` | `linux/amd64`, `windows/amd64` для локальных проверок |

Сборка сверяет commit базы и SHA256 патча из [`release.json`](release.json).

## 📚 Документация

- 🧪 [Результаты проверок](TEST_RESULTS.md) и [отчёты](reports/)
- 🛠 [Сборка, правка патча, проверки и выпуск](docs/DEVELOPMENT.md)
- 📝 [История версий](CHANGELOG.md)
- 🧾 [Происхождение кода](NOTICE.md)

## 📄 Лицензия

[Mozilla Public License 2.0](LICENSE)
