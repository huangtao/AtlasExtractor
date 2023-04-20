#! /usr/bin/env python
# coding:utf-8

import os
import math
from PIL import Image as PilImage
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

'''
扫描图集的每条水平线
从左到右扫描，直到发现一个非空的颜色像素P
如果P点位于已存在的矩形区域内部，那么从此矩形右边继续扫描
否则为P点创建一个矩形区域
打包为exe:
pyinstaller -F SpriteSheetExtractor.py -w
'''

dir_path = None
sprite_path = None
prefix_name = None
out_path = None


# 计算两点之间的距离
def distance_point(point1, point2):
    result = 99999999
    if (point1 != None and point2 != None):
        a = abs(point2[0]-point1[0])
        b = abs(point2[1] - point1[1])
        result = math.sqrt(math.pow(a, 2)+math.pow(b, 2))
    return result


# 精灵类
class Sprite:
    def __init__(self) -> None:
        self.start_x = -1
        self.start_y = -1
        self.end_x = -1
        self.end_y = -1

    def __str__(self) -> str:
        result = f'({str(self.start_x)},{str(self.start_y)},{str(self.end_x)},{str(self.end_y)})'
        return result

    # 计算两个精灵的最小距离
    def distance(self, sprite):
        result = 99999999
        if (sprite == None):
            return result
        lista = []
        listb = []
        lista.append((self.start_x, self.start_y))
        lista.append((self.start_x, self.end_y))
        lista.append((self.end_x, self.start_y))
        lista.append((self.end_x, self.end_y))
        listb.append((sprite.start_x, sprite.start_y))
        listb.append((sprite.start_x, sprite.end_y))
        listb.append((sprite.end_x, sprite.start_y))
        listb.append((sprite.end_x, sprite.end_y))
        for pa in lista:
            for pb in listb:
                distance = distance_point(pa, pb)
                if (distance < result):
                    result = distance
        return result

    # 点是否在精灵内部
    def belongs(self, point):
        if (point[0] < self.start_x or point[0] > self.end_x
                or point[1] < self.start_y or point[1] > self.end_y):
            return False
        else:
            return True

    # 将点加入精灵(扩展精灵区域)
    def expand(self, point):
        if (self.start_x < 0 and self.start_y < 0 and self.end_x < 0 and self.end_y < 0):
            self.start_x = point[0]
            self.start_y = point[1]
            self.end_x = point[0]
            self.end_y = point[1]
        else:
            if (point[0] < self.start_x):
                self.start_x = point[0]
            if (point[0] > self.end_x):
                self.end_x = point[0]
            if (point[1] < self.start_y):
                self.start_y = point[1]
            if (point[1] > self.end_y):
                self.end_y = point[1]


# 找到包含pos点的精灵
def load_sprite(pos, sprites):
    result = None
    for sprite in sprites:
        if sprite.belongs(pos):
            result = sprite
            break
    return result


# 以pStart为中心向外扩散找到一个完整的精灵
def explore_bounded_box(pStart, img):
    sprite = Sprite()
    q = []
    q.append(pStart)
    sprite.expand(pStart)
    marks = [[0 for j in range(img.height+1)]for i in range(img.width+1)]
    while (len(q) > 0):
        p = q.pop(0)
        sprite.expand(p)
        neighbouring = load_neighbouring_pixels(p, img)
        try:
            for n in neighbouring:
                if (marks[n[0]][n[1]] == 1):
                    continue
                marks[n[0]][n[1]] = 1
                if (img.getpixel(n)[3] > 0):
                    q.append(n)
        except:
            print(neighbouring)
            break
    return sprite


# 得到指定点的周围有效像素(8个)
def load_neighbouring_pixels(point, img):
    result = []
    # top
    newPoint = (point[0]-1, point[1]-1)
    if (newPoint[0] >= 0 and newPoint[1] >= 0 and newPoint[0] < img.width and newPoint[1] < img.height):
        result.append(newPoint)

    newPoint = (point[0], point[1]-1)
    if (newPoint[0] >= 0 and newPoint[1] >= 0 and newPoint[0] < img.width and newPoint[1] < img.height):
        result.append(newPoint)

    newPoint = (point[0]+1, point[1]-1)
    if (newPoint[0] >= 0 and newPoint[1] >= 0 and newPoint[0] < img.width and newPoint[1] < img.height):
        result.append(newPoint)

    # middle
    newPoint = (point[0]-1, point[1])
    if (newPoint[0] >= 0 and newPoint[1] >= 0 and newPoint[0] < img.width and newPoint[1] < img.height):
        result.append(newPoint)

    newPoint = (point[0]+1, point[1])
    if (newPoint[0] >= 0 and newPoint[1] >= 0 and newPoint[0] < img.width and newPoint[1] < img.height):
        result.append(newPoint)

    # below
    newPoint = (point[0]-1, point[1]+1)
    if (newPoint[0] >= 0 and newPoint[1] >= 0 and newPoint[0] < img.width and newPoint[1] < img.height):
        result.append(newPoint)

    newPoint = (point[0], point[1]+1)
    if (newPoint[0] >= 0 and newPoint[1] >= 0 and newPoint[0] < img.width and newPoint[1] < img.height):
        result.append(newPoint)

    newPoint = (point[0]+1, point[1])
    if (newPoint[0] >= 0 and newPoint[1] >= 0 and newPoint[0] < img.width and newPoint[1] < img.height):
        result.append(newPoint)

    return result

# 返回第一个无效的精灵(无大小)


def first_non_sprite(sprites):
    result = None
    for sprite in sprites:
        if (sprite.end_x <= sprite.start_x or sprite.end_y <= sprite.start_y):
            result = sprite
            break
    return result


# 合并两个精灵
def merge_sprite(sprite1, sprite2):
    sprite = None
    if (sprite1 != None and sprite2 != None):
        sprite = Sprite()
        sprite.start_x = min(sprite1.start_x, sprite2.start_x)
        sprite.start_y = min(sprite1.start_y, sprite2.start_y)
        sprite.end_x = max(sprite1.end_x, sprite2.end_x)
        sprite.end_y = max(sprite1.end_y, sprite2.end_y)
    return sprite


def find_next_sprite(pivot, sprites):
    result = None
    distance = 99999999
    for sprite in sprites:
        if sprite != pivot:
            itemDistrance = pivot.distance(sprite)
            if (itemDistrance < distance):
                distance = itemDistrance
                result = sprite
    return result


def fix_merge_sprites(sprites):
    result = []
    pivot_non_sprite = first_non_sprite(sprites)
    while(pivot_non_sprite != None):
        next_sprite = find_next_sprite(pivot_non_sprite, sprites)
        if next_sprite == None:
            break
        new_sprite = merge_sprite(pivot_non_sprite, next_sprite)
        sprites.remove(next_sprite)
        sprites.remove(pivot_non_sprite)
        sprites.append(new_sprite)
        pivot_non_sprite = first_non_sprite(sprites)
    result = sprites
    return result


def extract_sheet():
    total = 0
    im = PilImage.open(sprite_path)
    print(im.format, im.size, im.mode)
    print(f'width={im.width},height={im.height}')

    sprites = []
    for y in range(im.height):
        for x in range(im.width):
            pixel = im.getpixel((x, y))
            # 如果alpha通道为0则表示没有颜色像素(空白区域)
            haycolor = True if pixel[3] > 0 else False
            if (haycolor):
                pos = (x, y)
                # print(f'({x},{y})->{pixel}')
                sprite = load_sprite(pos, sprites)
                if (sprite != None):
                    x = sprite.end_x
                else:
                    sprite = explore_bounded_box(pos, im)
                    sprites.append(sprite)
                    print('sprite', len(sprites),
                          'processed->'+str(sprite))

    #sprites = fix_merge_sprites(sprites)
    idx = 1
    for sprite in sprites:
        imSprite = im.crop((sprite.start_x, sprite.start_y,
                           sprite.end_x+1, sprite.end_y+1))
        png_file = os.path.join(out_path, str(idx) + '.png')
        imSprite.save(png_file)
        idx += 1
        total += 1

    print(f'total child {len(sprites)} image saved!')
    return total

def submit_validate():
    global prefix_name, out_path
    info_label['foreground'] = 'black'
    info_label['text'] = ''
    if dir_path == None:
        info_label['foreground'] = 'red'
        info_label['text'] = '错误:你必须选择一个图集'
    else:
        info_label['text'] = '处理中...'
        selectButton['state'] = 'disabled'
        submitButton['state'] = 'disabled'
        root.update_idletasks()

        # 建立输出目录
        out_path = os.path.join(dir_path, prefix_name)
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        print('Createing Directory:', out_path)
        # 解出子图
        n = extract_sheet()

        info_label['foreground'] = 'green'
        info_label['text'] = f'处理完成,共解出{n}个子图!'
        selectButton['state'] = 'active'
        submitButton['state'] = 'active'
        root.update_idletasks()


def select_file():
    global sprite_path, dir_path, prefix_name
    info_label['text'] = ''
    sprite_path = filedialog.askopenfilename(initialdir='/', title='选择图集',
                                             filetypes=(('png files', '*.png'), ('all files', '*.*')))
    sheet_label['text'] = '图集:' + sprite_path
    dir_path = os.path.dirname(sprite_path)
    basename = os.path.basename(sprite_path)
    prefix_name = os.path.splitext(basename)[0]


# 创建窗口
root = Tk()
root.title('图集解包工具')
root.geometry('350x180')
root.resizable(width=0, height=0)

# 控件
selectButton = Button(text='选择图集', command=select_file)
selectButton.place(width=100, height=50, x=50, y=20)
submitButton = Button(text='解出', command=submit_validate)
submitButton.place(width=100, height=50, x=200, y=20)

sheet_label = Label(text='图集:未选择')
sheet_label.place(x=50, y=80)

info_label = Label(text='')
info_label.place(x=50, y=110)

Label(text='作者:黄涛 huangtao117@yeah.net').place(x=145, y=155)

root.mainloop()
