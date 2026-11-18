import math

from PIL import Image, ImageDraw

from anim.engine import (Scene, get_font, lerp, lerp_color, ease_in_out,
                         ease_out_back, ease_out, segment, clamp01)

SKY_TOP = (92, 148, 235)
SKY_BOT = (186, 220, 255)
RED = (226, 74, 74)
DARK = (40, 44, 52)
WHITE = (255, 255, 255)

FONT_L = get_font(64)
FONT_S = get_font(36)


class DemoScene(Scene):
    def setup(self):
        self.width = 1280
        self.height = 720
        self.fps = 30
        self.duration = 8.0
        self.ground = self.height - 120
        self.hop_decay = [1.0, 0.72, 0.52, 0.38, 0.27, 0.19, 0.13, 0.09]
        self.cycle = 0.0
        self.gravity = 1800.0
        self.v0 = math.sqrt(2 * self.gravity * (self.ground - 220))
        v = 0.0
        segments = []
        for k in self.hop_decay:
            kv = self.v0 if v == 0.0 else v
            dur = 2 * kv / self.gravity
            segments.append((kv, dur))
            v = kv * math.sqrt(k)
            self.cycle += dur
        self.segments = segments

    def draw(self, t, img, dr):
        self.draw_sky(t, dr)
        self.draw_clouds(t, dr)
        self.draw_sun(t, dr)
        self.draw_ground(t, dr)
        self.draw_ball(t, dr)
        self.draw_title(t, img, dr)

    def draw_sky(self, t, dr):
        for y in range(0, self.height, 4):
            f = y / self.height
            dr.line([(0, y), (self.width, y)], fill=lerp_color(SKY_TOP, SKY_BOT, f))

    def draw_clouds(self, t, dr):
        for i, (y, s, speed, x0) in enumerate([(110, 1.0, 22, 200), (210, 0.7, 35, 700), (70, 0.85, 28, 1050)]):
            x = (x0 + (t * speed)) % (self.width + 400) - 400
            self._cloud(dr, x, y, s)

    def _cloud(self, dr, x, y, s):
        puff = [(0, 0, 60), (55, 12, 45), (-55, 12, 42), (20, -28, 42), (-25, -22, 36)]
        for dx, dy, r in puff:
            cx, cy, rr = x + dx * s, y + dy * s, r * s
            dr.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(250, 252, 255))

    def draw_sun(self, t, dr):
        p = ease_in_out(segment(t, 0.2, 3.5))
        x = lerp(140, 1140, p)
        y = 250 - 160 * math.sin(math.pi * clamp01(p))
        r = 46
        for gr, gl in [(r + 26, (255, 236, 170)), (r + 12, (255, 226, 130))]:
            dr.ellipse([x - gr, y - gr, x + gr, y + gr], fill=gl)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(255, 214, 96))

    def draw_ground(self, t, dr):
        g = self.ground
        dr.rectangle([0, g, self.width, self.height], fill=(106, 168, 79))
        dr.rectangle([0, g, self.width, g + 14], fill=(84, 140, 64))
        for x in range(20, self.width, 90):
            ph = 6.0 * math.sin(t * 3 + x * 0.05)
            dr.polygon([(x, g), (x + 12, g - 26 + ph), (x + 24, g)], fill=(94, 152, 70))

    def draw_ball(self, t, dr):
        arc = self.ground - 40
        tt = t - 0.6
        if tt <= 0:
            self._ball_at(dr, self.width / 2, arc, 1, 1, shadow=arc - 40)
            return
        local = tt % self.cycle
        acc = 0.0
        for kv, dur in self.segments:
            if local < acc + dur:
                vt = local - acc
                dy = kv * vt - 0.5 * self.gravity * vt * vt
                sq = max(0.0, 1 - dy / 200) if dy < 30 else 0.0
                stretch = 0.35 * min(1, max(0, (dy - 150) / 300))
                self._ball_at(dr, self.width / 2 + 260 * math.sin(tt * 0.9),
                              arc + dy, 1 + 0.28 * sq, 1 - 0.30 * sq,
                              shadow=self.ground, stretch=stretch)
                return
            acc += dur

    def _ball_at(self, dr, x, y, sx, sy, shadow, stretch=0.0):
        r = 42
        sw = max(0.25, 1 - abs(y - self.ground) / 500)
        sw_r = r * (0.9 + 0.5 * sw) * (1 - 0.3 * stretch)
        dr.ellipse([x - sw_r, self.ground + 18, x + sw_r, self.ground + 30],
                   fill=(60, 90, 50))
        rx, ry = r * sx * (1 + stretch), r * sy / (1 + stretch)
        dr.ellipse([x - rx, y - ry, x + rx, y + ry], fill=RED)
        hl = r * 0.28
        dr.ellipse([x - r * 0.35 - hl, y - r * 0.45 - hl,
                    x - r * 0.35 + hl, y - r * 0.45 + hl], fill=(255, 170, 160))

    def draw_title(self, t, img, dr):
        p1 = ease_out_back(segment(t, 0.4, 1.0))
        if p1 <= 0:
            return
        text = "Hello, 2D Animation!"
        tw = dr.textlength(text, font=FONT_L)
        x = (self.width - tw) / 2
        y = 60 + 30 * (1 - p1)
        alpha = int(255 * min(1, p1 * 1.4))
        col = (DARK[0], DARK[1], DARK[2], alpha)
        tmp = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d2 = ImageDraw.Draw(tmp)
        d2.text((x + 4, y + 4), text, font=FONT_L, fill=(0, 0, 0, 90))
        d2.text((x, y), text, font=FONT_L, fill=col)
        img.paste(tmp.convert("RGB"), mask=tmp.split()[3])
        p2 = ease_out(segment(t, 3.6, 1.2))
        if p2 > 0:
            sub = "Python + Pillow + ffmpeg"
            sw2 = dr.textlength(sub, font=FONT_S)
            tmp2 = Image.new("RGBA", img.size, (0, 0, 0, 0))
            d3 = ImageDraw.Draw(tmp2)
            d3.text(((self.width - sw2) / 2, 150), sub, font=FONT_S,
                    fill=(255, 255, 255, int(230 * p2)))
            img.paste(tmp2.convert("RGB"), mask=tmp2.split()[3])


if __name__ == "__main__":
    scene = DemoScene()
    scene.setup()
    scene.render("out/demo.mp4")
