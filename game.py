import tkinter as tk
from PIL import Image, ImageTk


class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.pos_x = x
        self.pos_y = y
        self.direction = [1, -1]
        self.speed = 4.5
        item = canvas.create_oval(
            x - self.radius, y - self.radius,
            x + self.radius, y + self.radius,
            fill='white'
        )
        super().__init__(canvas, item)

    def update(self):
        width = self.canvas.winfo_width()

        self.pos_x += self.direction[0] * self.speed
        self.pos_y += self.direction[1] * self.speed

        if self.pos_x - self.radius <= 0 or self.pos_x + self.radius >= width:
            self.direction[0] *= -1

        if self.pos_y - self.radius <= 0:
            self.direction[1] *= -1

        coords = self.get_position()
        dx = self.pos_x - (coords[0] + self.radius)
        dy = self.pos_y - (coords[1] + self.radius)
        self.move(dx, dy)

    def collide(self, objects):
        if not objects:
            return

        self.direction[1] *= -1

        for obj in objects:
            if isinstance(obj, Brick):
                obj.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.moving_left = False
        self.moving_right = False
        self.ball = None

        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2,
            x + self.width / 2, y + self.height / 2,
            fill='#FFB643'
        )
        super().__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def update(self):
        offset = 0
        if self.moving_left:
            offset -= 6 
        if self.moving_right:
            offset += 6

        coords = self.get_position()
        width = self.canvas.winfo_width()

        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            self.move(offset, 0)
            if self.ball:
                self.ball.pos_x += offset
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2,
            x + self.width / 2, y + self.height / 2,
            fill=Brick.COLORS[hits], tags='brick'
        )
        super().__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits <= 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.lives = 3
        self.width = 900
        self.height = 900

        self.canvas = tk.Canvas(self, width=self.width, height=self.height)
        self.canvas.pack()
        self.pack()

        # background fit
        bg = Image.open("background.png")
        ratio = min(self.width / bg.size[0], self.height / bg.size[1])
        bg = bg.resize((int(bg.size[0] * ratio), int(bg.size[1] * ratio)), Image.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(bg)

        self.canvas.create_image(
            (self.width - bg.size[0]) // 2,
            (self.height - bg.size[1]) // 2,
            image=self.bg_image,
            anchor="nw",
            tags="bg"
        )
        self.canvas.tag_lower("bg")

        self.items = {}
        self.paddle = Paddle(self.canvas, self.width / 2, 330)
        self.items[self.paddle.item] = self.paddle

        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None
        self.ball = None
        self.setup_game()

        # controls
        self.canvas.focus_set()
        self.canvas.bind("<KeyPress-Left>", lambda e: self.start_move("left"))
        self.canvas.bind("<KeyPress-Right>", lambda e: self.start_move("right"))
        self.canvas.bind("<KeyRelease-Left>", lambda e: self.stop_move("left"))
        self.canvas.bind("<KeyRelease-Right>", lambda e: self.stop_move("right"))

    def start_move(self, side):
        if side == "left":
            self.paddle.moving_left = True
        else:
            self.paddle.moving_right = True

    def stop_move(self, side):
        if side == "left":
            self.paddle.moving_left = False
        else:
            self.paddle.moving_right = False

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200, "Press SPACE to start")
        self.canvas.bind("<space>", lambda e: self.start_game())

    def add_ball(self):
        if self.ball:
            self.ball.delete()

        px = (self.paddle.get_position()[0] + self.paddle.get_position()[2]) / 2
        self.ball = Ball(self.canvas, px, 310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size=40):
        return self.canvas.create_text(x, y, text=text, font=("Forte", size))

    def update_lives_text(self):
        txt = f"Lives: {self.lives}"
        if not self.hud:
            self.hud = self.draw_text(70, 20, txt, 18)
        else:
            self.canvas.itemconfig(self.hud, text=txt)

    def start_game(self):
        self.canvas.unbind("<space>")
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        self.paddle.update()
        self.ball.update()
        self.check_collisions()

        if len(self.canvas.find_withtag("brick")) == 0:
            self.draw_text(300, 200, "YOU WIN!")
            return

        if self.ball.pos_y >= self.height:
            self.lives -= 1
            if self.lives < 0:
                self.draw_text(300, 200, "GAME OVER!")
                return
            else:
                self.after(1000, self.setup_game)
                return

        self.after(10, self.game_loop)  # 100 FPS smooth

    def check_collisions(self):
        ball_c = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_c)
        objs = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objs)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Break Those Bricks!")
    game = Game(root)
    game.mainloop()
