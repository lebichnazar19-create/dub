"""Мінімальна підробка Kivy для тестів main.py на комп'ютері (Kivy тут
нема). Повторює саме ті правила Kivy, від яких залежить дотик:

  * дотик іде дітям від найновішого до найстарішого (children[0] — останній
    доданий); перший, хто повернув True, забирає його;
  * вимкнений (disabled) віджет ковтає дотик у своїх межах;
  * collide_point — межі включно (x <= px <= right, y <= py <= top);
  * grab: on_touch_move/up спершу йдуть захопленому віджету з
    grab_current = віджет, потім звичайним шляхом від кореня;
  * BoxLayout розкладає дітей: вертикальний — знизу вгору від свого y
    (children[0] — найнижчий), горизонтальний — зліва направо;
  * зміна pos/size віджета викликає зв'язані (bind) обробники.

Малювання не робиться: Color/Rectangle лише записуються в МАЛЮНОК.
"""

import sys
import types

МАЛЮНОК = []     # усе, що «намальовано»: ("колір", rgba) і ("прямокутник", pos, size, texture)


class Дотик:
    def __init__(self, x, y, uid=1):
        self.x, self.y, self.uid = float(x), float(y), uid
        self.grab_current = None
        self.захопили = []

    pos = property(lambda s: (s.x, s.y))

    def grab(self, віджет):
        self.захопили.append(віджет)

    def ungrab(self, віджет):
        self.захопили.remove(віджет)


class _Полотнище:
    def __init__(self):
        self.команд = 0

    def clear(self):
        self.команд = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class Widget:
    def __init__(self, **kw):
        self.x = self.y = 0.0
        self.width = self.height = 100.0
        self.size_hint_x = self.size_hint_y = 1
        self.children, self.parent = [], None
        self._вимкнено = False
        self._обробники = {}
        self.canvas = _Полотнище()
        for к, з in kw.items():
            setattr(self, к, з)

    # -- властивості --
    pos = property(lambda s: (s.x, s.y))
    size = property(lambda s: (s.width, s.height))
    top = property(lambda s: s.y + s.height)
    right = property(lambda s: s.x + s.width)

    @property
    def disabled(self):
        return self._вимкнено or (self.parent is not None and self.parent.disabled)

    @disabled.setter
    def disabled(self, з):
        self._вимкнено = з

    def bind(self, **kw):
        for подія, обробник in kw.items():
            self._обробники.setdefault(подія, []).append(обробник)

    def _сповістити(self, подія, значення):
        for обробник in self._обробники.get(подія, []):
            обробник(self, значення)

    def встановити(self, x, y, ширина, висота):
        """Як Kivy при розкладанні: міняє pos/size і кличе bind-обробники."""
        self.x, self.y, self.width, self.height = float(x), float(y), float(ширина), float(висота)
        self._сповістити("pos", self.pos)
        self._сповістити("size", self.size)
        self.розкласти()

    def розкласти(self):
        pass

    # -- діти --
    def add_widget(self, в):
        в.parent = self
        self.children.insert(0, в)
        self.розкласти()

    def remove_widget(self, в):
        self.children.remove(в)
        в.parent = None

    def clear_widgets(self):
        for в in self.children[:]:
            self.remove_widget(в)

    def collide_point(self, x, y):
        return self.x <= x <= self.right and self.y <= y <= self.top

    # -- дотики, як у kivy.uix.widget.Widget --
    def dispatch(self, подія, touch):
        return getattr(self, подія)(touch)

    def on_touch_down(self, touch):
        if self.disabled and self.collide_point(*touch.pos):
            return True
        for дитина in self.children[:]:
            if дитина.dispatch("on_touch_down", touch):
                return True
        return False

    def on_touch_move(self, touch):
        if self.disabled:
            return False
        for дитина in self.children[:]:
            if дитина.dispatch("on_touch_move", touch):
                return True
        return False

    def on_touch_up(self, touch):
        if self.disabled:
            return False
        for дитина in self.children[:]:
            if дитина.dispatch("on_touch_up", touch):
                return True
        return False


class BoxLayout(Widget):
    def __init__(self, **kw):
        self.orientation = "horizontal"
        self.spacing = 0
        self.padding = 0
        super().__init__(**kw)

    def розкласти(self):
        if not self.children:
            return
        п = self.padding if isinstance(self.padding, (int, float)) else self.padding[0]
        діти = self.children
        if self.orientation == "vertical":
            сталі = sum(д.height for д in діти if д.size_hint_y is None)
            гнучких = sum(1 for д in діти if д.size_hint_y is not None)
            залишок = max(0.0, self.height - 2 * п - сталі - self.spacing * (len(діти) - 1))
            y = self.y + п
            for д in діти:                      # children[0] — останній доданий — унизу
                в = д.height if д.size_hint_y is None else залишок / max(гнучких, 1)
                д.встановити(self.x + п, y, self.width - 2 * п, в)
                y += в + self.spacing
        else:
            сталі = sum(д.width for д in діти if д.size_hint_x is None)
            гнучких = sum(1 for д in діти if д.size_hint_x is not None)
            залишок = max(0.0, self.width - 2 * п - сталі - self.spacing * (len(діти) - 1))
            x = self.x + п
            for д in reversed(діти):            # перший доданий — ліворуч
                ш = д.width if д.size_hint_x is None else залишок / max(гнучких, 1)
                д.встановити(x, self.y + п, ш, self.height - 2 * п)
                x += ш + self.spacing


class Label(Widget):
    def __init__(self, **kw):
        self.text = ""
        super().__init__(**kw)


class Button(Label):
    """Увімкнена кнопка бере дотик у своїх межах; натиснути() — як відпускання."""

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.disabled:
            self.торкнуто = True
            return True
        return super().on_touch_down(touch)

    def натиснути(self):
        for обробник in self._обробники.get("on_release", []):
            обробник(self)


class TextInput(Widget):
    def __init__(self, **kw):
        self.text = ""
        self.focus = False
        super().__init__(**kw)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.disabled:
            self.focus = True
            return True
        return super().on_touch_down(touch)


class App:
    title = ""
    user_data_dir = "."

    def run(self):
        self.root = self.build()


class _Вікно:
    def __init__(self):
        self.softinput_mode = ""
        self.size = (400, 800)
        self.обробники = {}

    def bind(self, **kw):
        for подія, обробник in kw.items():
            self.обробники.setdefault(подія, []).append(обробник)

    def клавіша(self, код):
        """Як Android-кнопка «Назад» (27): перший обробник, що повернув True, зупиняє."""
        for обробник in self.обробники.get("on_keyboard", []):
            if обробник(self, код, None, None, None):
                return True
        return False


Window = _Вікно()


class _Текстура:
    def __init__(self, ш, в):
        self.size = (ш, в)


class CoreLabel:
    def __init__(self, text="", font_size=12, **kw):
        self.text, self.font_size = text, font_size
        self.texture = None

    def refresh(self):
        self.texture = _Текстура(len(self.text) * self.font_size * 0.6, self.font_size * 1.2)


def Color(*rgba):
    МАЛЮНОК.append(("колір", rgba))


def Rectangle(pos=(0, 0), size=(0, 0), texture=None, **kw):
    МАЛЮНОК.append(("прямокутник", tuple(pos), tuple(size), texture))


def встановити(monkeypatch):
    """Підставити підробку в sys.modules (через monkeypatch — зникає після тесту)."""
    def модуль(назва, **вміст):
        м = types.ModuleType(назва)
        м.__dict__.update(вміст)
        monkeypatch.setitem(sys.modules, назва, м)

    for назва in ("kivy", "kivy.core", "kivy.uix"):
        модуль(назва)
    модуль("kivy.app", App=App)
    модуль("kivy.core.text", Label=CoreLabel)
    модуль("kivy.core.window", Window=Window)
    модуль("kivy.graphics", Color=Color, Rectangle=Rectangle)
    модуль("kivy.metrics", dp=lambda x: x, sp=lambda x: x)
    модуль("kivy.uix.boxlayout", BoxLayout=BoxLayout)
    модуль("kivy.uix.button", Button=Button)
    модуль("kivy.uix.label", Label=Label)
    модуль("kivy.uix.textinput", TextInput=TextInput)
    модуль("kivy.uix.widget", Widget=Widget)
    МАЛЮНОК.clear()
    Window.обробники.clear()


# ---- дотик, як його розсилає Kivy Window ----------------------------------------

def натиснути(корінь, дотик):
    return корінь.dispatch("on_touch_down", дотик)


def _після_натискання(корінь, подія, дотик):
    for віджет in дотик.захопили[:]:
        дотик.grab_current = віджет
        віджет.dispatch(подія, дотик)
    дотик.grab_current = None
    корінь.dispatch(подія, дотик)


def рухати(корінь, дотик, x, y):
    дотик.x, дотик.y = float(x), float(y)
    _після_натискання(корінь, "on_touch_move", дотик)


def відпустити(корінь, дотик, x=None, y=None):
    if x is not None:
        дотик.x, дотик.y = float(x), float(y)
    _після_натискання(корінь, "on_touch_up", дотик)


def торкнутись(корінь, x, y, uid=1):
    """Натиснути й одразу відпустити в одній точці (дотик без руху)."""
    дотик = Дотик(x, y, uid)
    натиснути(корінь, дотик)
    відпустити(корінь, дотик)
    return дотик
