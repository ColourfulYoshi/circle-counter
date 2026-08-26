from random import random
from math import cos, sin, floor, sqrt, pi, ceil
import numpy as np
import cv2
import tkinter as tk

# алгоритм работает по принципу дискретного семплирования Пуассона (poisson disk sampling)

# менять желательно только переменные снизу
# размер макета (возможно придётся немного поменять, он не идеально 120 на 120)
prop_width = 120
prop_height = 120
# диаметр кругов (не обязательно должен совпадать с настоящим, это чисто для визуала)
diam = 4
# минимальное расстояние между кругами
min_dist = 12
# количество кандитатов на выбор положения. если слишком маленькое, то тогда круги будут неравномерные
candidates = 150
# коэффициент для увеличения изображения. чисто визуально
resizer = 5

window = tk.Tk()
window.wm_geometry("300x300")
window.title("六十七")

def euclidean_distance(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return sqrt(dx * dx + dy * dy)


def poisson_disc_samples(width, height, r, k=5, distance=euclidean_distance, random=random):
    tau = 2 * pi
    cellsize = r / sqrt(2)

    grid_width = int(ceil(width / cellsize))
    grid_height = int(ceil(height / cellsize))
    grid = [None] * (grid_width * grid_height)

    def grid_coords(p):
        return int(floor(p[0] / cellsize)), int(floor(p[1] / cellsize))

    def fits(p, gx, gy):
        yrange = list(range(max(gy - 2, 0), min(gy + 3, grid_height)))
        for x in range(max(gx - 2, 0), min(gx + 3, grid_width)):
            for y in yrange:
                g = grid[x + y * grid_width]
                if g is None:
                    continue
                if distance(p, g) <= r:
                    return False
        return True

    p = width * random(), height * random()
    queue = [p]
    grid_x, grid_y = grid_coords(p)
    grid[grid_x + grid_y * grid_width] = p

    while queue:
        qi = int(random() * len(queue))
        qx, qy = queue[qi]
        queue[qi] = queue[-1]
        queue.pop()
        for _ in range(k):
            alpha = tau * random()
            d = r * sqrt(3 * random() + 1)
            px = qx + d * cos(alpha)
            py = qy + d * sin(alpha)
            if not (0 <= px < width and 0 <= py < height):
                continue
            p = (px, py)
            grid_x, grid_y = grid_coords(p)
            if not fits(p, grid_x, grid_y):
                continue
            queue.append(p)
            grid[grid_x + grid_y * grid_width] = p
    return [p for p in grid if p is not None]

img = np.zeros([1, 1, 3])
def gen():
    global img

    img = np.zeros([prop_width * resizer, prop_height * resizer, 3], dtype=np.uint8)
    img.fill(255)

    points = poisson_disc_samples(prop_width, prop_height, min_dist, candidates)
    true_count = 0
    for p in points:
        if not (((diam / 2) + 1) < p[0] < (prop_width - ((diam / 2) + 1))):
            continue
        if not (((diam / 2) + 1) < p[1] < (prop_height - ((diam / 2) + 1))):
            continue
        true_count += 1
        pos = [round(p[0]), round(p[1])]
        cv2.circle(img, (pos[0] * resizer, pos[1] * resizer), int((int(diam / 2) * resizer) / 3), (0, 125, 255), 3)
        cv2.circle(img, (pos[0] * resizer, pos[1] * resizer), int(diam / 2) * resizer, (0, 255, 0), 2)
        cv2.putText(img, f"{pos[0]}", ((pos[0] * resizer) - 13, (pos[1] * resizer) - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 2)
        cv2.putText(img, f"{pos[1]}", ((pos[0] * resizer) - 13, (pos[1] * resizer) + 11), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 100),2)

    count_label.config(text=f"count: {true_count}")

    cv2.imshow("img", img)

count_label = tk.Label(font=("Arial", 16))
count_label.place(relwidth=1, relheight=0.4)

gen_btn = tk.Button(font=("Arial", 14), text="generate")
gen_btn.config(command=gen)
gen_btn.place(relheight=0.15, relwidth=0.4, relx=0.5, rely=0.7, anchor="c")

def save():
    global img
    cv2.imwrite("saved.png", img)

save_btn = tk.Button(font=("Arial", 14), text="save")
save_btn.config(command=save)
save_btn.place(relheight=0.15, relwidth=0.4, relx=0.5, rely=0.875, anchor="c")

tk.mainloop()
