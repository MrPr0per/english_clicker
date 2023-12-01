import pyautogui as pag
import time
from PIL import Image


def are_rectangles_intersecting(rect1, rect2):
    # l = left, t = top, r = right, b = bottom
    l1, t1, w1, h1 = rect1
    l2, t2, w2, h2 = rect2
    r1, b1 = l1 + w1, t1 + h1
    r2, b2 = l2 + w2, t2 + h2
    return max(l1, l2) <= min(r1, r2) and max(t1, t2) <= min(b1, b2)


def filter_out_intersecting_rectangles(rects):
    history = []
    for r in rects:
        if any([are_rectangles_intersecting(r, old_r) for old_r in history]): continue
        history.append(r)
    return history


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


def main():
    im_magic = Image.open('buttons/magic.png')
    im_left_side = Image.open('buttons/leftSide.png')
    im_right_side = Image.open('buttons/rightSide.png')
    im_recs = Image.open('buttons/reks_mini.png')
    im_next = Image.open('buttons/nextTask.png')
    im_finish = Image.open('buttons/finishTest.png')

    # инициализация:
    # находим область с тестом
    rect_left_side = pag.locateOnScreen(im_left_side, grayscale=False)
    rect_right_side = pag.locateOnScreen(im_right_side, grayscale=False)
    screenshot_rect = (int(rect_left_side.left),
                       150,
                       int(rect_right_side.left + rect_right_side.width - rect_left_side.left),
                       int(pag.size()[1] - 150))
    screenshot_pos = screenshot_rect[0:2]

    while True:
        # план такой:
        # - делаем скрин
        # - ищем на нем палочки
        # - протыкиваем их
        # - если есть копка перехода - переходим
        # - если нет - скроллим и возвращаемя к шагу 1

        # делаем скрин
        screenshot = pag.screenshot(region=screenshot_rect)

        # ищем на нем палочки
        try:
            rects = pag.locateAll(im_magic, screenshot, grayscale=True, confidence=0.9)
            rects = filter_out_intersecting_rectangles(rects)
        except:
            rects = []

        # протыкиваем их
        for r in rects:
            pag.moveTo(componentwise_sum_of_tuple(screenshot_pos, pag.center(r)))
            pag.click()

            # делаем скрин и ищем "рекомендации"
            try:
                screenshot2_rect = (int(pag.position().x), int(pag.position().y), 30, 30)
                screenshot2 = pag.screenshot(region=screenshot2_rect)
                r2 = pag.locate(im_recs, screenshot2, grayscale=True, confidence=0.9)
                pag.moveTo(componentwise_sum_of_tuple(screenshot2_rect[0:2], pag.center(r2)))
            except:
                continue  # скорее всего рекомендации за нижней границей экрана

            # делаем скрин и ищем зеленый цвет
            screenshot3_rect = (int(pag.position().x) - 50, int(pag.position().y) - 20, 400, 50)
            screenshot3 = pag.screenshot(region=screenshot3_rect)
            pag.moveTo(componentwise_sum_of_tuple(screenshot3_rect[0:2], find_green(screenshot3)))
            pag.click()

        # если есть копка завершения - завершаем
        try:
            r_finish = pag.locate(im_finish, screenshot, grayscale=True, confidence=0.7)
            pag.moveTo(componentwise_sum_of_tuple(screenshot_pos, pag.center(r_finish)))
            pag.click()
            print("success!")
            return
        except:
            pass

        # если есть копка перехода - переходим
        try:
            r_next = pag.locate(im_next, screenshot, grayscale=True, confidence=0.6)
            pag.moveTo(componentwise_sum_of_tuple(screenshot_pos, pag.center(r_next)))
            pag.click()
            time.sleep(2)
            continue
        except:
            pass

        # если нет - скроллим и возвращаемя к шагу 1
        pag.scroll(-950)
        time.sleep(0.8)


if __name__ == '__main__':
    main()
