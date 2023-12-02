import pyautogui as pag
import time
from PIL import Image


class Rect:
    def __init__(self, l, t, w, h):
        # l = left, t = top, r = right, b = bottom, w = width, h = height
        self.l = int(l)
        self.t = int(t)
        self.w = int(w)
        self.h = int(h)
        self.r = int(l + w)
        self.b = int(t + h)

    @staticmethod
    def rect_by_ltwh(l, t, w, h):
        return Rect(l, t, w, h)

    @staticmethod
    def rect_by_ltrb(l, t, r, b):
        return Rect(l, t, r - l, b - t)

    def to_abs(self, mother_rect):
        # переводит координаты прямоугольника в абсолютные значения
        # например если координаты rect1           - это координаты внутри screenshot.rect,
        #             а координаты screenshot.rect - это кординаты на экране,
        # то этот метод вернет координаты rect1 на экране
        return self + mother_rect.pos()

    def get_ltwh(self):
        return self.l, self.t, self.w, self.h

    def get_ltrb(self):
        return self.l, self.t, self.r, self.b

    def pos(self):
        return self.l, self.t

    def center(self):
        return int((self.l + self.r) / 2), int((self.t + self.b) / 2)

    def __add__(self, other):
        if isinstance(other, tuple) and len(other) == 2:
            return Rect(self.l + other[0], self.t + other[1], self.w, self.h)
        raise NotImplementedError("прибавлять к прямоугольнику можно только двухэлементные кортежи")

    @staticmethod
    def are_rectangles_intersecting(rect1, rect2):
        l1, t1, r1, b1 = rect1.get_ltrb()
        l2, t2, r2, b2 = rect2.get_ltrb()
        return max(l1, l2) <= min(r1, r2) and max(t1, t2) <= min(b1, b2)

    def __repr__(self):
        return f"Rect{self.get_ltwh()}"


class Screen_part:
    def __init__(self, rect: Rect, take_a_screenshot=False):
        self.rect = rect
        self.im = None
        if take_a_screenshot:
            self.update_image()

    def update_image(self):
        self.im = pag.screenshot(region=self.rect.get_ltwh())

    def update_rect(self, search_area, grayscale, confidence):
        self.rect = Rect(*pag.locate(self.im, search_area.im, grayscale=grayscale, confidence=confidence)) + \
                    search_area.rect.pos()


def filter_out_intersecting_rectangles(rects):
    result = []
    for r in rects:
        if any([Rect.are_rectangles_intersecting(r, old_r) for old_r in result]): continue
        result.append(r)
    return result


def filter_out_all_before_bookmark(rects, bookmark_rect):
    result = []
    for r in rects:
        if r.b < bookmark_rect.t: continue
        result.append(r)
    return result


def componentwise_sum_of_tuple(t1, t2):
    if len(t1) != len(t2): raise Exception('суммируются кортежи разной длины')
    return tuple([t1[i] + t2[i] for i in range(len(t1))])


def find_green(screenshot):
    color = (233, 243, 235)
    w, h = screenshot.size
    for y in range(h):
        for x in range(w):
            if screenshot.getpixel((x, y)) == color:
                return x, y
    raise Exception("зеленый не найден")

    # # ищем самую широкую полоску зеленого цвета
    # # эта штука работает слишком медленно
    # color = (233, 243, 235)
    # w, h = screenshot.size
    # max_w = 0
    # crd_of_max = None
    # fr = None
    # for y in range(h):
    #     for x in range(w):
    #         if screenshot.getpixel((x, y)) == color and fr is None:
    #             fr = x
    #         if screenshot.getpixel((x, y)) != color and fr is not None:
    #             to = x
    #             if max_w < to - fr:
    #                 max_w = to - fr
    #                 crd_of_max = (fr, y)
    #             break
    # if crd_of_max is None:
    #     raise Exception("зеленый не найден")
    # return crd_of_max


def get_bookmark(screenshot: Screen_part):  # возвращает нижнюю часть главного скриншота (без панели задач)
    color = (231, 243, 245)
    y_to = None
    x = int(screenshot.im.size[0] / 2)
    for y in range(screenshot.im.size[1] - 1, 0, -1):
        if screenshot.im.getpixel((x, y)) == color:
            y_to = y - 5
            break
    y_from = y_to - 50
    return Screen_part(Rect(0, y_from, int(screenshot.im.size[0] / 2), y_to - y_from)
                       .to_abs(screenshot.rect), take_a_screenshot=True)


def get_main_screenshot(im_left_side, im_right_side):
    rect_left_side = Rect(*pag.locateOnScreen(im_left_side, grayscale=False))
    rect_right_side = Rect(*pag.locateOnScreen(im_right_side, grayscale=False))
    screenshot = Screen_part(
        Rect.rect_by_ltrb(
            int(rect_left_side.l),
            150,  # отступ сверху (там где всякие вкладки в браузере)
            rect_right_side.r,
            pag.size()[1],
        )
    )
    return screenshot


def find_magics(screenshot, im_magic, bookmark):
    rects = pag.locateAll(im_magic, screenshot.im, grayscale=True, confidence=0.9)
    rects = [Rect(*r) for r in rects]  # перегоняем найденые боксы в прямоугольники
    rects = [r.to_abs(screenshot.rect) for r in rects]  # переводим их координаты в абсолютные
    rects = filter_out_intersecting_rectangles(rects)
    if bookmark is not None:
        rects = filter_out_all_before_bookmark(rects, bookmark.rect)
    return rects


def main():
    im_magic = Image.open('buttons/magic.png')
    im_left_side = Image.open('buttons/leftSide.png')
    im_right_side = Image.open('buttons/rightSide.png')
    im_recs = Image.open('buttons/reks_mini.png')
    # im_stat = Image.open('buttons/stat.png')
    im_next = Image.open('buttons/nextTask2.png')
    im_finish = Image.open('buttons/finishTest2.png')

    # инициализация:
    # находим область с тестом
    screenshot = get_main_screenshot(im_left_side, im_right_side)
    # перед пролистыванием создается закладка - кусок скриншота из его нижней части
    # после пролистывания на новом скрине ищется эта закладка и все палочки выше нее уже не прокликиваются
    bookmark = None

    while True:
        # план такой:
        # - делаем скрин
        # - ищем на нем не прокликаные палочки
        # - прокликиваем их
        # - если есть копка перехода - переходим
        # - если нет - скроллим и возвращаемя к шагу 1

        # делаем скрин
        screenshot.update_image()

        # если есть закладка - то находим ее на скрине
        if bookmark is not None:
            bookmark.update_rect(screenshot, grayscale=True, confidence=0.9)

        # ищем на скрине палочки
        try:
            rects = find_magics(screenshot, im_magic, bookmark)
        except:
            rects = []

        # протыкиваем их
        for r in rects:
            pag.moveTo(r.center())
            pag.click()

            # делаем скрин и ищем "рекомендации"
            try:
                screenshot2 = Screen_part(Rect(*pag.position(), 30, 30), take_a_screenshot=True)
                r2 = Rect(*pag.locate(im_recs, screenshot2.im, grayscale=True, confidence=0.9)) + screenshot2.rect.pos()
                pag.moveTo(r2.center())
                # # делаем скрин и ищем "статистику"
                # screenshot2 = Screen_part(Rect(*pag.position(), 40, 60), take_a_screenshot=True)
                # r2 = Rect(*pag.locate(im_stat, screenshot2.im, grayscale=True, confidence=0.7)) + screenshot2.rect.pos()
                # pag.moveTo(r2.center())
            except:
                continue  # скорее всего рекомендации за нижней границей экрана

            # делаем скрин и ищем зеленый цвет
            # screenshot3 = Screen_part(Rect(int(pag.position().x) - 60, int(pag.position().y) - 200, 400, 400),
            screenshot3 = Screen_part(Rect(int(pag.position().x) - 50, int(pag.position().y) - 20, 400, 50),
                                      take_a_screenshot=True)
            pag.moveTo(componentwise_sum_of_tuple(screenshot3.rect.pos(), find_green(screenshot3.im)))
            pag.click()

        # если есть копка завершения - завершаем
        try:
            r_finish = Rect(*pag.locate(im_finish, screenshot.im, grayscale=True, confidence=0.8)) \
                .to_abs(screenshot.rect)
            pag.moveTo(r_finish.center())
            pag.click()
            print("success!")
            return
        except:
            pass

        # если есть копка перехода - переходим
        try:
            r_next = Rect(*pag.locate(im_next, screenshot.im, grayscale=True, confidence=0.8)).to_abs(screenshot.rect)
            pag.moveTo(r_next.center())
            pag.click()
            time.sleep(2)  # время на загрузку следующего задания

            bookmark = None  # после перехода на следующее задания текущая закладка уже не нужна
            continue
        except:
            pass

        # если этих кнопок нет - сохраняем закладку, скроллим и возвращаемя к шагу 1
        bookmark = get_bookmark(screenshot)
        pag.scroll(-950)


if __name__ == '__main__':
    main()
