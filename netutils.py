"""
Сетевые утилиты для NetCheck.
Всё выполняется синхронно — вызывающий код (main.py) обязан
запускать эти функции в отдельном потоке, а не в главном UI-потоке.
"""

import json
import socket
import time
import urllib.error
import urllib.request

DEFAULT_TIMEOUT = 6
USER_AGENT = "Mozilla/5.0 (NetCheckApp; Android)"


def has_internet(timeout=3):
    """
    Проверяет, есть ли у устройства выход в интернет вообще —
    независимо от того, заблокирован ли конкретный сайт.
    Пробуем достучаться до нейтральных публичных адресов (Cloudflare, Google DNS).
    """
    anchors = [("1.1.1.1", 443), ("8.8.8.8", 443)]
    for host, port in anchors:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((host, port))
            s.close()
            return True
        except OSError:
            continue
    return False


def check_site(url, timeout=DEFAULT_TIMEOUT):
    """
    True, если ресурс отвечает (сайт доступен для устройства).
    HTTP-ошибка (404/403/...) всё равно означает, что сайт доступен —
    сервер ведь ответил. Обрыв соединения/таймаут — недоступен.
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False


def get_provider_info():
    """Возвращает (провайдер, регион) через открытый geo/asn-сервис."""
    try:
        req = urllib.request.Request(
            "https://ipapi.co/json/", headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        name = data.get("org") or "Провайдер не определён"
        region = ", ".join(p for p in [data.get("city"), data.get("country_name")] if p)
        return name, region or "—"
    except Exception:
        return "Не удалось определить", "—"


def measure_ping(samples=5, timeout=5):
    """Медиана нескольких быстрых запросов, мс. None при полном отказе."""
    times = []
    for _ in range(samples):
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(
                "https://speed.cloudflare.com/__down?bytes=0",
                headers={"User-Agent": USER_AGENT},
            )
            urllib.request.urlopen(req, timeout=timeout)
            times.append((time.perf_counter() - t0) * 1000)
        except Exception:
            continue
    if not times:
        return None
    times.sort()
    return times[0]


def measure_download(size_bytes=10_000_000, timeout=20):
    """Скорость скачивания в Мбит/с."""
    try:
        req = urllib.request.Request(
            f"https://speed.cloudflare.com/__down?bytes={size_bytes}",
            headers={"User-Agent": USER_AGENT},
        )
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        seconds = time.perf_counter() - t0
        if seconds <= 0:
            return None
        return (len(data) * 8 / 1_000_000) / seconds
    except Exception:
        return None


def measure_upload(size_bytes=4_000_000, timeout=20):
    """Скорость отдачи в Мбит/с."""
    try:
        payload = b"0" * size_bytes
        req = urllib.request.Request(
            "https://speed.cloudflare.com/__up",
            data=payload,
            method="POST",
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/octet-stream",
            },
        )
        t0 = time.perf_counter()
        urllib.request.urlopen(req, timeout=timeout)
        seconds = time.perf_counter() - t0
        if seconds <= 0:
            return None
        return (size_bytes * 8 / 1_000_000) / seconds
    except Exception:
        return None
