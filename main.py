"""Дуб — візуальне полотно для коду (Kivy, Android).

Перший крок: велике блідо-жовте полотно, що гортається пальцем; фіолетове
ядро «програма» посередині; дотик на порожнє — жовтий квадрат (функція);
дотик на функцію — редактор коду Вужа; функцію можна пересунути пальцем.
Уся логіка (координати, дотик/тягнення, квадрати) — у polotno.py без Kivy;
тут лише малювання на canvas і передача дотиків.

Дотик по всій висоті. Корінь застосунку — BoxLayout з одним-єдиним
віджетом: або полотно, або редактор. Нічого схованого (висота 0, вимкнене
тощо) під полотном не лежить — саме такий схований рядок у Вужі
перехоплював дотики на нижній смузі. Тести: тести/test_дотик_низу.py.
"""

from kivy.app import App
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

import polotno

# Клавіатура не затуляє редактор: вікно стискається над нею.
Window.softinput_mode = "resize"

КОЛІР_ТЕКСТУ = (0.15, 0.1, 0.2, 1)
КОЛІР_ТЕКСТУ_НА_ЯДРІ = (1, 1, 1, 1)


class ПолотноДуб(Widget):
    """Малює polotno.Полотно і віддає їй дотики."""

    def __init__(self, при_відкритті, **kw):
        super().__init__(**kw)
        self.модель = polotno.Полотно(розмір_ядра=dp(polotno.РОЗМІР_ЯДРА),
                                      розмір_функції=dp(polotno.РОЗМІР_ФУНКЦІЇ),
                                      поріг_руху=dp(polotno.ПОРІГ_РУХУ))
        self._при_відкритті = при_відкритті
        self.bind(pos=self._вікно_змінилось, size=self._вікно_змінилось)
        self._вікно_змінилось()

    def _вікно_змінилось(self, *_):
        self.модель.вікно(self.x, self.y, self.width, self.height)
        self.перемалювати()

    # ---- малювання ------------------------------------------------------------

    def перемалювати(self):
        self.canvas.clear()
        with self.canvas:
            Color(*polotno.колір_rgb(polotno.ФОН), 1)
            Rectangle(pos=self.pos, size=self.size)
            for кв in self.модель.квадрати():
                Color(*polotno.колір_rgb(кв["колір"]), 1)
                Rectangle(pos=(кв["x"], кв["y"]), size=(кв["розмір"], кв["розмір"]))
                колір = КОЛІР_ТЕКСТУ_НА_ЯДРІ if кв["тип"] == "ядро" else КОЛІР_ТЕКСТУ
                cx, cy = кв["x"] + кв["розмір"] / 2, кв["y"] + кв["розмір"] / 2
                рядок = polotno.перший_рядок(кв["код"])
                if рядок:
                    self._напис(кв["підпис"], cx, cy + sp(10), sp(16), колір)
                    self._напис(рядок, cx, cy - sp(10), sp(12), колір)
                else:
                    self._напис(кв["підпис"], cx, cy, sp(16), колір)

    def _напис(self, текст, cx, cy, розмір, колір):
        напис = CoreLabel(text=текст, font_size=розмір)
        напис.refresh()
        текстура = напис.texture
        Color(*колір)
        Rectangle(texture=текстура, pos=(cx - текстура.size[0] / 2, cy - текстура.size[1] / 2),
                  size=текстура.size)

    # ---- дотики ---------------------------------------------------------------

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        touch.grab(self)
        self.модель.дотик_униз(touch.x, touch.y)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        if self.модель.дотик_рух(touch.x, touch.y):
            self.перемалювати()
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        touch.ungrab(self)
        дія = self.модель.дотик_вгору(touch.x, touch.y)
        self.перемалювати()
        if дія and дія[0] == "відкрити":
            self._при_відкритті(дія[1])
        return True


class ДубApp(App):
    title = "Дуб"

    def build(self):
        Window.bind(on_keyboard=self._клавіша)
        self.корінь = BoxLayout()
        self.полотно = ПолотноДуб(при_відкритті=self.відкрити_функцію)
        self.редактор = None            # BoxLayout редактора, поки функція відкрита
        self.відкрита = None            # номер відкритої функції
        self.поле_коду = None
        self.корінь.add_widget(self.полотно)
        return self.корінь

    # ---- редактор функції -----------------------------------------------------

    def відкрити_функцію(self, номер):
        if self.редактор is not None:
            return
        self.відкрита = номер
        self.редактор = BoxLayout(orientation="vertical")
        шапка = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(6), padding=dp(4))
        назад = Button(text="← Полотно", size_hint_x=None, width=dp(130), font_size=sp(16))
        назад.bind(on_release=lambda *_: self.закрити_редактор())
        шапка.add_widget(назад)
        шапка.add_widget(Label(text=f"{polotno.ПІДПИС_ФУНКЦІЇ} {номер + 1}", font_size=sp(16)))
        self.редактор.add_widget(шапка)
        self.поле_коду = TextInput(text=self.полотно.модель.код(номер), multiline=True,
                                   font_size=sp(16), font_name="RobotoMono-Regular")
        self.редактор.add_widget(self.поле_коду)
        self.корінь.clear_widgets()
        self.корінь.add_widget(self.редактор)

    def закрити_редактор(self):
        if self.редактор is None:
            return
        self.полотно.модель.записати_код(self.відкрита, self.поле_коду.text)
        self.корінь.clear_widgets()
        self.корінь.add_widget(self.полотно)
        self.редактор = self.поле_коду = self.відкрита = None
        self.полотно.перемалювати()

    def _клавіша(self, вікно, клавіша, *_):
        """Кнопка «Назад» на Android (27) закриває редактор, а не застосунок."""
        if клавіша == 27 and self.редактор is not None:
            self.закрити_редактор()
            return True
        return False


if __name__ == "__main__":
    ДубApp().run()
