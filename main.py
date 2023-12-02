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

def filter_out_under_bookmark(rects, bookmark_rect):
    result = []
    for r in rects:
        if r.top + r.height < bookmark_rect.top:
            continue
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


def get_bookmark(screenshot):  # возвращает нижнюю часть главного скриншота (без панели задач)
    color = (231, 243, 245)
    y_to = None
    x = int(screenshot.size[0] / 2)
    for y in range(screenshot.size[1] - 1, 0, -1):
        if screenshot.getpixel((x, y)) == color:
            y_to = y - 5
            break
    y_from = y_to - 50
    return screenshot.crop((0, y_from, int(screenshot.size[0] / 2), y_to))


def main():
    im_magic = Image.open('buttons/magic.png')
    im_left_side = Image.open('buttons/leftSide.png')
    im_right_side = Image.open('buttons/rightSide.png')
    im_recs = Image.open('buttons/reks_mini.png')
    im_next = Image.open('buttons/nextTask2.png')
    im_finish = Image.open('buttons/finishTest2.png')

    # инициализация:
    # находим область с тестом
    rect_left_side = pag.locateOnScreen(im_left_side, grayscale=False)
    rect_right_side = pag.locateOnScreen(im_right_side, grayscale=False)
    screenshot_rect = (int(rect_left_side.left),
                       150,
                       int(rect_right_side.left + rect_right_side.width - rect_left_side.left),
                       int(pag.size()[1] - 150))
    screenshot_pos = screenshot_rect[0:2]

    bookmark = None
    bookmark_rect = None

    while True:
        # план такой:
        # - делаем скрин
        # - ищем на нем палочки
        # - протыкиваем их
        # - если есть копка перехода - переходим
        # - если нет - скроллим и возвращаемя к шагу 1

        # делаем скрин
        screenshot = pag.screenshot(region=screenshot_rect)

        # если есть закладка - то обрезаем скрин до нее
        if bookmark is not None:
            bookmark_rect = pag.locate(bookmark, screenshot, grayscale=True, confidence=0.9)

            # bookmark_rect = pag.locate(bookmark, screenshot, grayscale=True, confidence=0.9)
            # screenshot = screenshot.crop((0, bookmark_rect.top, *screenshot.size))
            # screenshot_rect = (screenshot_rect[0],
            #                    screenshot_rect[1] + int(bookmark_rect.top),
            #                    screenshot_rect[2],
            #                    screenshot_rect[3] - int(bookmark_rect.top))
            # screenshot_pos = screenshot_rect[0:2]
        # ищем на нем палочки
        try:
            rects = pag.locateAll(im_magic, screenshot, grayscale=True, confidence=0.9)
            rects = filter_out_intersecting_rectangles(rects)
            if bookmark_rect is not None:
                rects = filter_out_under_bookmark(rects, bookmark_rect)
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
            r_finish = pag.locate(im_finish, screenshot, grayscale=True, confidence=0.8)
            pag.moveTo(componentwise_sum_of_tuple(screenshot_pos, pag.center(r_finish)))
            pag.click()
            print("success!")
            return
        except:
            pass

        # если есть копка перехода - переходим
        try:
            r_next = pag.locate(im_next, screenshot, grayscale=True, confidence=0.8)
            pag.moveTo(componentwise_sum_of_tuple(screenshot_pos, pag.center(r_next)))
            pag.click()
            time.sleep(2)

            bookmark = None
            bookmark_rect = None
            continue
        except:
            pass

        # если нет - скроллим, сохраняем, до куда дорешали и возвращаемя к шагу 1
        bookmark = get_bookmark(screenshot)
        pag.scroll(-950)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
