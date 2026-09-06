"""
NetCheck — проверка доступности сайтов из белого списка (Ozon, Max, Yandex, VK)
и базовый тест скорости интернета (провайдер, регион, пинг, загрузка, отдача).

Запуск на компьютере для проверки перед сборкой APK:
    pip install kivy
    python main.py

Сборка APK: см. README.md (buildozer или GitHub Actions).
"""

import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ColorProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

from netutils import (
    check_site,
    get_provider_info,
    has_internet,
    measure_download,
    measure_ping,
    measure_upload,
)

SITES = [
    {"name": "Ozon", "domain": "ozon.ru", "url": "https://www.ozon.ru/favicon.ico"},
    {"name": "Max", "domain": "max.ru", "url": "https://max.ru/favicon.ico"},
    {"name": "Yandex", "domain": "ya.ru", "url": "https://ya.ru/favicon.ico"},
    {"name": "VK", "domain": "vk.com", "url": "https://vk.com/favicon.ico"},
]

STATUS_TEXT = {
    "checking": "Проверка…",
    "ok": "Есть доступ",
    "blocked": "Нет доступа",
    "offline": "Нет связи",
}
STATUS_COLOR = {
    "checking": (0.34, 0.65, 1, 1),
    "ok": (0.25, 0.75, 0.5, 1),
    "blocked": (0.9, 0.28, 0.3, 1),
    "offline": (0.43, 0.47, 0.51, 1),
}


class SiteRow(BoxLayout):
    site_name = StringProperty("")
    site_domain = StringProperty("")
    status_text = StringProperty(STATUS_TEXT["checking"])
    status_color = ColorProperty(STATUS_COLOR["checking"])


class SitesScreen(Screen):
    rows = []

    def on_pre_enter(self):
        if not self.rows:
            self._build_rows()
            self.run_checks()

    def _build_rows(self):
        self.ids.site_list.clear_widgets()
        self.rows = []
        for site in SITES:
            row = SiteRow(site_name=site["name"], site_domain=site["domain"])
            self.ids.site_list.add_widget(row)
            self.rows.append(row)

    def run_checks(self):
        self.ids.recheck_btn.disabled = True
        self.ids.recheck_btn.text = "Проверяем…"
        for row in self.rows:
            row.status_text = STATUS_TEXT["checking"]
            row.status_color = STATUS_COLOR["checking"]
        threading.Thread(target=self._check_all_thread, daemon=True).start()

    def _check_all_thread(self):
        online = has_internet()
        results = []
        for site in SITES:
            if not online:
                results.append("offline")
                continue
            results.append("ok" if check_site(site["url"]) else "blocked")
        Clock.schedule_once(lambda dt: self._apply_results(results))

    def _apply_results(self, results):
        for row, result in zip(self.rows, results):
            row.status_text = STATUS_TEXT[result]
            row.status_color = STATUS_COLOR[result]
        self.ids.recheck_btn.disabled = False
        self.ids.recheck_btn.text = "Проверить заново"


class SpeedScreen(Screen):
    provider_loaded = False

    def on_pre_enter(self):
        if not self.provider_loaded:
            self.provider_loaded = True
            threading.Thread(target=self._provider_thread, daemon=True).start()

    def _provider_thread(self):
        name, region = get_provider_info()
        Clock.schedule_once(lambda dt: self._apply_provider(name, region))

    def _apply_provider(self, name, region):
        self.ids.isp_name.text = name
        self.ids.isp_region.text = region

    def run_speed_test(self):
        self.ids.speed_btn.disabled = True
        self.ids.m_ping.text = "—"
        self.ids.m_down.text = "—"
        self.ids.m_up.text = "—"
        threading.Thread(target=self._speed_thread, daemon=True).start()

    def _speed_thread(self):
        Clock.schedule_once(lambda dt: setattr(self.ids.speed_btn, "text", "Измеряем пинг…"))
        ping = measure_ping()
        Clock.schedule_once(
            lambda dt: setattr(self.ids.m_ping, "text", f"{ping:.0f}" if ping else "н/д")
        )

        Clock.schedule_once(lambda dt: setattr(self.ids.speed_btn, "text", "Измеряем загрузку…"))
        down = measure_download()
        Clock.schedule_once(
            lambda dt: setattr(self.ids.m_down, "text", f"{down:.1f}" if down else "н/д")
        )

        Clock.schedule_once(lambda dt: setattr(self.ids.speed_btn, "text", "Измеряем отдачу…"))
        up = measure_upload()
        Clock.schedule_once(
            lambda dt: setattr(self.ids.m_up, "text", f"{up:.1f}" if up else "н/д")
        )

        Clock.schedule_once(lambda dt: self._finish())

    def _finish(self):
        self.ids.speed_btn.disabled = False
        self.ids.speed_btn.text = "Запустить тест скорости"


class RootWidget(BoxLayout):
    pass


class NetCheckApp(App):
    # Kivy автоматически подгружает netcheck.kv (имя класса без "App", в нижнем регистре)
    def build(self):
        return RootWidget()


if __name__ == "__main__":
    NetCheckApp().run()
