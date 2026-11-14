<div align="center">

# ⚡ Infinity Xray

**Серверная сборка Xray для Remnawave Node: тихие соединения живут дольше, XHTTP отзывчивее под нагрузкой**

[![Релиз](https://img.shields.io/github/v/release/BloodyBaronDev/infinity-xray?style=flat-square&color=2ea44f&label=релиз)](https://github.com/BloodyBaronDev/infinity-xray/releases/latest)
![Xray](https://img.shields.io/badge/Xray-v26.11.9-informational?style=flat-square)
![Go](https://img.shields.io/badge/Go-1.27.3-00ADD8?style=flat-square&logo=go&logoColor=white)
![Remnawave Node](https://img.shields.io/badge/Remnawave_Node-3.4.5-7c3aed?style=flat-square)
[![Лицензия](https://img.shields.io/badge/лицензия-MPL_2.0-blue?style=flat-square)](LICENSE)

[English](README.md) · **Русский**

[Возможности](#-возможности) · [Результаты](#-результаты) · [Установка](#-установка) · [Настройки](#️-настройки) · [Сборка](#-сборка-из-исходников) · [Документация](#-документация)

</div>

---

Замена Xray внутри [Remnawave Node](https://github.com/remnawave/node) одной строкой в `docker-compose.yml`. Работает со стандартными клиентами, в основе официальный [XTLS/Xray-core](https://github.com/XTLS/Xray-core).

## ✨ Возможности

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

> [!NOTE]
> Безусловный отзыв не включён: Remnawave Node делает remove/add даже для неизменённого пользователя, поэтому отзыв работает только с отсрочкой `XRAY_IC_REVOKE_GRACE`. Режим конкуренции governor (`XRAY_XHTTP_FLOW_COMPETE`) экспериментальный и выключен.

## 📈 Результаты

| Проверка | Без функции | С функцией |
|---|---|---|
| 💓 Простой Hysteria | умирает к 45 с | живо на 330 с |
| 🔁 Простой XHTTP + mux через CDN | умирает к 90 с | живо на 330 с |
| 🚦 p95 соседних запросов при скачивании, RTT 50 мс | 2411 мс | 309 мс |
| 🚦 Скорость при конкурирующем TCP | 84,9 Мбит/с | **34,2 Мбит/с** (цена governor) |

0.2.0-rc.3 на рабочей ноде: 0 рестартов, около 32% одного ядра при ~130 Мбит/с, governor срабатывает на XHTTP + REALITY. Сравнения A/B с прошлой версией нет.

Замеры сделаны на небольших выборках и частично на более ранних сборках. Стенды и оговорки: **[TEST_RESULTS.md](TEST_RESULTS.md)** и [отчёты](reports/).

## 🐳 Установка

Готовый образ `ghcr.io/bloodybarondev/infinity-xray` собран на базе `remnawave/node:3.4.5`. В сервисе ноды меняется только `image`: порты, секрет панели, тома и остальные настройки остаются прежними.

**Требования:** уже работающая Remnawave Node в Docker Compose, `linux/amd64`.

### 1. Сохраните текущее состояние

Перейдите в каталог ноды (обычно `/opt/remnanode`) и запомните, на чём она работает сейчас:

```bash
cd /opt/remnanode
cp docker-compose.yml docker-compose.yml.bak
docker inspect --format '{{.Image}}' remnanode > previous-image.txt
```

### 2. Замените образ

В `docker-compose.yml` поменяйте одну строку:

```diff
 services:
   remnanode:
-    image: remnawave/node:latest
+    image: ghcr.io/bloodybarondev/infinity-xray:0.2.0
```

### 3. Перезапустите ноду

```bash
docker compose pull && docker compose up -d
```

> [!WARNING]
> Перезапуск обрывает текущие соединения клиентов. Делайте это в тихое время.

### 4. Проверьте

```bash
docker exec remnanode xray version        # должно быть Infinity-Xray/v0.2.0
docker logs --tail 50 remnanode           # без ошибок запуска
docker logs remnanode 2>&1 | grep icstats # сводка появляется раз в 60 с
```

Убедитесь, что нода в панели онлайн, и проверьте реальный трафик клиентом.

### 5. Настройте (по желанию)

Переменные из раздела [Настройки](#️-настройки) задаются в `environment` сервиса:

```yaml
services:
  remnanode:
    image: ghcr.io/bloodybarondev/infinity-xray:0.2.0
    environment:
      XRAY_IC_USER_MAX_CONNS: "8"               # предел соединений VLESS на пользователя
      XRAY_IC_METRICS_LISTEN: "127.0.0.1:9550"  # метрики Prometheus, только локально
```

После правки: `docker compose up -d`.

### ↩️ Откат

```bash
cp docker-compose.yml.bak docker-compose.yml
docker compose up -d
```

Если старый тег уже перезаписан, укажите в `image` ID из `previous-image.txt`.

<details>
<summary><b>Отдельный бинарник без Docker</b></summary>

На [странице релиза](https://github.com/BloodyBaronDev/infinity-xray/releases/latest) лежат `xray-linux-amd64`, `xray-windows-amd64.exe`, `SHA256SUMS` и `build-info-*.json`.

```bash
curl -LO https://github.com/BloodyBaronDev/infinity-xray/releases/latest/download/xray-linux-amd64
curl -LO https://github.com/BloodyBaronDev/infinity-xray/releases/latest/download/SHA256SUMS
sha256sum --ignore-missing -c SHA256SUMS
install -m 755 xray-linux-amd64 /usr/local/bin/xray
xray version
```

У отдельного бинарника governor по умолчанию выключен: включите его через `XRAY_XHTTP_FLOW=on`.

</details>

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

## 🛠 Сборка из исходников

Нужны Python 3.11+, git и Go с автозагрузкой toolchain, для образа — Docker.

```bash
bash build.sh                # бинарник linux/amd64
bash build.sh --full-checks  # плюс расширенные тесты governor
bash build.sh image          # плюс локальный образ для Remnawave Node
```

На Windows: `python build.py build`. Результат: `out/0.2.0/linux-amd64/` (`xray`, `SHA256SUMS`, `build-info.json`). Сценарии ничего не устанавливают и не публикуют.

| Xray-core | Commit | Go | Build tags | Remnawave Node |
|---|---|---|---|---|
| `v26.11.9` | `676eaf6` | `go1.27.3` | `http2legacy` | `3.4.5` |

Сборка сверяет commit базы и SHA256 патча из [`release.json`](release.json).

## 📚 Документация

- 🧪 [Результаты проверок](TEST_RESULTS.md) и [отчёты](reports/)
- 🛠 [Сборка, правка патча, проверки и выпуск](docs/DEVELOPMENT.md)
- 📝 [История версий](CHANGELOG.md)
- 🧾 [Происхождение кода](NOTICE.md)

Нашли ошибку или есть вопрос? Откройте [issue](https://github.com/BloodyBaronDev/infinity-xray/issues). Если сборка пригодилась, ⭐ поможет другим её найти.

## 📄 Лицензия

[Mozilla Public License 2.0](LICENSE)
