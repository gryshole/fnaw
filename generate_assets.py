import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps, ImageChops

# --- КОНФІГУРАЦІЯ ---
WIDTH, HEIGHT = 800, 600
CAM_WIDTH, CAM_HEIGHT = 640, 480 

if not os.path.exists('assets'): os.makedirs('assets')

# --- ПАЛІТРА ---
COLORS = {
    "black": (8, 8, 10),
    "shadow_deep": (5, 5, 8),
    "wall_paint": (60, 65, 70),
    "floor_tile_1": (30, 30, 35),
    "floor_tile_2": (50, 50, 55),
    
    # Метали (оновлено для іржі)
    "metal_base": (70, 70, 75), # Трохи темніша база
    "metal_highlight": (140, 140, 150),
    "metal_dark": (30, 30, 35),
    "metal_rust": (130, 60, 30), # Більш насичена іржа
    "pipe_gray": (70, 70, 75),
    
    # Дроти
    "wire_red": (100, 30, 30),
    "wire_blue": (30, 30, 100),
    "wire_black": (20, 20, 20),
    
    # Персонажі
    "sparky_base": (100, 60, 140),
    "clanker_base": (220, 180, 40),
    "boss_base": (90, 60, 40),     
    "runner_base": (160, 40, 40),
    
    # Деталі та світло
    "teeth": (230, 230, 210),
    "eye_white": (240, 240, 240),
    "eye_glow": (255, 255, 255),
    "light_warm": (255, 220, 180),
    "light_cold": (150, 200, 255),
    
    # Декор
    "party_red": (200, 50, 50),
    "party_blue": (50, 100, 200),
    "party_yellow": (200, 200, 50),
    
    # Світлові промені
    "light_beam_open": (255, 255, 210, 50),
    "light_beam_closed": (255, 240, 190, 80)
}

# --- TEXTURE & FX ENGINE ---

def create_metal_texture(size, orientation='v'):
    noise = Image.effect_noise(size, 40).convert('L')
    if orientation == 'v':
        noise = noise.resize((size[0], size[1]//10)).resize(size, Image.BICUBIC)
    else:
        noise = noise.resize((size[0]//10, size[1])).resize(size, Image.BICUBIC)
    dirt = Image.effect_noise(size, 20).convert('L').filter(ImageFilter.GaussianBlur(3))
    base = Image.new('L', size, 128)
    base = Image.blend(base, noise, 0.3)
    base = Image.blend(base, dirt, 0.4)
    return base.convert('RGB')

def apply_texture(img, texture_type="noise", intensity=0.1):
    if texture_type == "noise":
        noise = Image.effect_noise(img.size, 30).convert('RGB')
        return Image.blend(img, noise, intensity)
    elif texture_type == "rust":
        # Посилена іржа для загального тону
        rust = Image.effect_noise(img.size, 60).convert('RGB').filter(ImageFilter.GaussianBlur(3))
        rust = ImageOps.colorize(rust.convert('L'), COLORS['metal_dark'], COLORS['metal_rust'])
        return Image.blend(img, rust, intensity * 1.5)
    elif texture_type == "dirt":
        dirt = Image.effect_noise(img.size, 100).convert('RGB').filter(ImageFilter.GaussianBlur(10))
        dirt = ImageOps.colorize(dirt.convert('L'), (30,30,30), (80,70,60))
        return Image.blend(img, dirt, intensity * 2.5)
    return img

def add_vignette(img, darkness=0.6, blur_radius=100):
    width, height = img.size
    mask = Image.new('L', (width, height), 0)
    d = ImageDraw.Draw(mask)
    x_margin, y_margin = width * 0.02, height * 0.02
    d.ellipse((x_margin, y_margin, width - x_margin, height - y_margin), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    black_layer = Image.new('RGB', (width, height), COLORS['shadow_deep'])
    return Image.composite(img, black_layer, mask)

def apply_cctv_master(img, text_main="", text_sub="", is_camera=True):
    # Хроматична аберація
    r, g, b = img.split()
    r = ImageChops.offset(r, 4, 0); b = ImageChops.offset(b, -4, 0)
    img = Image.merge('RGB', (r, g, b))
    
    # Шум і сканлайн
    noise = Image.effect_noise(img.size, 50).convert('RGB')
    img = Image.blend(img, noise, 0.15)
    
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    for y in range(0, img.height, 3): d.line([(0, y), (img.width, y)], fill=(0, 0, 0, 50), width=1)
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    # Віньєтка
    img = add_vignette(img, 0.7)
    
    # UI
    draw = ImageDraw.Draw(img)
    if text_main:
        draw.text((22, 22), text_main, fill=(0,0,0)); draw.text((20, 20), text_main, fill=(200, 255, 200))
    if text_sub:
        draw.text((22, 45), text_sub, fill=(0,0,0)); draw.text((20, 43), text_sub, fill=(200, 255, 200))
    if is_camera and (text_main or text_sub == "REC"):
        draw.ellipse((img.width-45, 25, img.width-15, 55), fill=(220, 0, 0))
        
    img = ImageEnhance.Color(img).enhance(0.5)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = ImageEnhance.Brightness(img).enhance(0.9)
    return img

# --- GEOMETRY HELPERS ---
def draw_screw(draw, x, y, size=4):
    # Темніші гвинти
    draw.ellipse((x-size, y-size, x+size, y+size), fill=(100,100,100), outline=(30,30,30))
    draw.line((x-size+1, y, x+size-1, y), fill=(30,30,30))

def draw_teeth(draw, x, y, width, height, num_teeth=5, top=True):
    step = width / num_teeth
    for i in range(num_teeth):
        tx = x + i * step
        if top: draw.polygon([(tx, y), (tx + step/2, y + height), (tx + step, y)], fill=COLORS['teeth'])
        else: draw.polygon([(tx, y), (tx + step/2, y - height), (tx + step, y)], fill=COLORS['teeth'])

def draw_eye(draw, x, y, size, glowing=False):
    draw.ellipse((x-size, y-size, x+size, y+size), fill=(10,10,10))
    if glowing:
        draw.ellipse((x-size*0.5, y-size*0.5, x+size*0.5, y+size*0.5), fill=COLORS['eye_glow'])
        draw.ellipse((x-size*0.2, y-size*0.2, x+size*0.2, y+size*0.2), fill=(255,255,255))
    else:
        draw.ellipse((x-size*0.7, y-size*0.7, x+size*0.7, y+size*0.7), fill=(255,255,255))
        draw.ellipse((x-size*0.3, y-size*0.3, x+size*0.3, y+size*0.3), fill=(0,0,0))

def draw_hanging_wires(draw, x_start, y_start, width, drop, num_wires=5):
    for _ in range(num_wires):
        x1 = x_start + random.randint(0, width)
        y1 = y_start
        x2 = x1 + random.randint(-20, 20)
        y2 = y1 + drop + random.randint(-20, 20)
        cp1x, cp1y = x1, y1 + drop * 0.6
        cp2x, cp2y = x2, y2 - drop * 0.2
        col = random.choice([COLORS['wire_red'], COLORS['wire_blue'], COLORS['wire_black']])
        w = random.randint(1, 3)
        points = []
        for t in [i/20 for i in range(21)]:
            px = (1-t)**3*x1 + 3*(1-t)**2*t*cp1x + 3*(1-t)*t**2*cp2x + t**3*x2
            py = (1-t)**3*y1 + 3*(1-t)**2*t*cp1y + 3*(1-t)*t**2*cp2y + t**3*y2
            points.append((px, py))
        draw.line(points, fill=col, width=w)

def draw_debris_and_scratches(draw, x, y, w, h):
    # Додає подряпини та бруд на панель
    for _ in range(random.randint(5, 15)):
        # Подряпини
        sx1 = random.randint(x, x+w)
        sy1 = random.randint(y, y+h)
        length = random.randint(10, 40)
        angle = math.radians(random.randint(0, 360))
        sx2 = sx1 + length * math.cos(angle)
        sy2 = sy1 + length * math.sin(angle)
        # Світла лінія (свіжий метал) з темною окантовкою (тінь)
        draw.line((sx1, sy1+1, sx2, sy2+1), fill=(30,30,30), width=2)
        draw.line((sx1, sy1, sx2, sy2), fill=(150,150,160), width=1)
        
    for _ in range(random.randint(10, 30)):
        # Дрібний бруд/сколи
        bx = random.randint(x, x+w)
        by = random.randint(y, y+h)
        draw.ellipse((bx, by, bx+random.randint(1,3), by+random.randint(1,3)), fill=(20,20,25))

# --- DETAILED ANIMATRONICS ---

def draw_detailed_animatronic(draw, x, y, type_name, scale=1.0, silhouette=False):
    s = scale
    
    if silhouette:
        base_col = (5, 5, 5); highlight_col = (5, 5, 5); eye_glow = False
    else:
        base_col = COLORS.get(f'{type_name}_base', (100,100,100))
        highlight_col = (min(255, base_col[0]+40), min(255, base_col[1]+40), min(255, base_col[2]+40))
        eye_glow = True

    # --- SPARKY (Rabbit) ---
    if type_name == 'sparky':
        for offset in [-1, 1]:
            draw.polygon([(x+15*s*offset, y-40*s), (x+25*s*offset, y-80*s), (x+5*s*offset, y-80*s)], fill=base_col, outline=COLORS['black'])
            draw.polygon([(x+25*s*offset, y-80*s), (x+5*s*offset, y-80*s), (x+15*s*offset, y-120*s)], fill=base_col, outline=COLORS['black'])
            if not silhouette: draw.polygon([(x+20*s*offset, y-85*s), (x+10*s*offset, y-85*s), (x+15*s*offset, y-110*s)], fill=(180, 150, 180))
        draw.ellipse((x-40*s, y-50*s, x+40*s, y+40*s), fill=base_col) 
        draw.ellipse((x-45*s, y, x-15*s, y+30*s), fill=highlight_col)
        draw.ellipse((x+15*s, y, x+45*s, y+30*s), fill=highlight_col)
        draw.ellipse((x-20*s, y+10*s, x+20*s, y+40*s), fill=(200, 180, 220) if not silhouette else base_col)
        if not silhouette: draw.polygon([(x-8*s, y+15*s), (x+8*s, y+15*s), (x, y+25*s)], fill=(30, 30, 30))
        if eye_glow:
            draw.ellipse((x-20*s, y-10*s, x-5*s, y+5*s), fill=(0,0,0))
            draw.ellipse((x+5*s, y-10*s, x+20*s, y+5*s), fill=(0,0,0))
            draw.ellipse((x-16*s, y-6*s, x-9*s, y+1*s), fill=COLORS['eye_glow'])
            draw.ellipse((x+9*s, y-6*s, x+16*s, y+1*s), fill=COLORS['eye_glow'])
        if not silhouette: draw_teeth(draw, x-15*s, y+35*s, 30*s, 10*s, 2, top=True)

    # --- CLANKER (Chicken) ---
    elif type_name == 'clanker':
        draw.polygon([(x, y-70*s), (x-15*s, y-40*s), (x+15*s, y-40*s)], fill=base_col)
        draw.ellipse((x-38*s, y-45*s, x+38*s, y+45*s), fill=base_col)
        if not silhouette:
            draw.polygon([(x-20*s, y+5*s), (x+20*s, y+5*s), (x, y+25*s)], fill=(255, 140, 0))
            draw.polygon([(x-15*s, y+25*s), (x+15*s, y+25*s), (x, y+40*s)], fill=(200, 80, 0))
            draw_teeth(draw, x-10*s, y+22*s, 20*s, 6*s, 4, top=True)
        if eye_glow:
            draw_eye(draw, x-20*s, y-15*s, 12*s, glowing=False)
            draw_eye(draw, x+20*s, y-15*s, 12*s, glowing=False)
        if not silhouette:
            draw.arc((x-35*s, y-35*s, x-5*s, y-15*s), 180, 0, fill=(0,0,0), width=int(4*s))
            draw.arc((x+5*s, y-35*s, x+35*s, y-15*s), 180, 0, fill=(0,0,0), width=int(4*s))

    # --- BOSS (Bear) ---
    elif type_name == 'boss':
        draw.ellipse((x-55*s, y-55*s, x-20*s, y-20*s), fill=base_col)
        draw.ellipse((x+20*s, y-55*s, x+55*s, y-20*s), fill=base_col)
        draw.rectangle((x-45*s, y-35*s, x+45*s, y+40*s), fill=base_col)
        draw.ellipse((x-45*s, y-50*s, x+45*s, y-20*s), fill=base_col)
        draw.ellipse((x-45*s, y+20*s, x+45*s, y+50*s), fill=base_col)
        draw.ellipse((x-30*s, y+10*s, x+30*s, y+50*s), fill=(140, 100, 80) if not silhouette else base_col)
        if not silhouette: 
            draw.ellipse((x-12*s, y+15*s, x+12*s, y+30*s), fill=(0,0,0))
            draw.rectangle((x-25*s, y-75*s, x+25*s, y-45*s), fill=(10,10,15))
            draw.rectangle((x-40*s, y-45*s, x+40*s, y-40*s), fill=(10,10,15))
            draw.line((x-25*s, y-55*s, x+25*s, y-55*s), fill=(100,20,20), width=int(3*s))
        if eye_glow:
            draw.ellipse((x-25*s, y-10*s, x-5*s, y+10*s), fill=(0,0,0))
            draw.ellipse((x+5*s, y-10*s, x+25*s, y+10*s), fill=(0,0,0))
            draw.ellipse((x-17*s, y-2*s, x-13*s, y+2*s), fill=(255,255,255))
            draw.ellipse((x+13*s, y-2*s, x+17*s, y+2*s), fill=(255,255,255))
        if not silhouette:
            draw_teeth(draw, x-25*s, y+40*s, 50*s, 8*s, 6, top=False)

    # --- RUNNER (Fox) ---
    elif type_name == 'runner':
        draw.polygon([(x-40*s, y-40*s), (x-65*s, y-100*s), (x-15*s, y-40*s)], fill=base_col)
        draw.polygon([(x+40*s, y-40*s), (x+65*s, y-100*s), (x+15*s, y-40*s)], fill=base_col)
        draw.polygon([(x-45*s, y-40*s), (x+45*s, y-40*s), (x+30*s, y+30*s), (x-30*s, y+30*s)], fill=base_col)
        draw.polygon([(x-45*s, y-20*s), (x-70*s, y+10*s), (x-35*s, y+20*s)], fill=base_col) 
        draw.polygon([(x+45*s, y-20*s), (x+70*s, y+10*s), (x+35*s, y+20*s)], fill=base_col)
        if eye_glow:
            draw.ellipse((x-25*s, y-20*s, x-5*s, y), fill=(255, 200, 0)) 
            draw.ellipse((x-18*s, y-12*s, x-12*s, y-6*s), fill=(0,0,0)) 
            draw.ellipse((x+5*s, y-20*s, x+25*s, y), fill=(15,15,15), outline=(0,0,0))
            draw.line((x+15*s, y-20*s, x+50*s, y-60*s), fill=(20,20,20), width=int(3*s))
        if not silhouette:
            draw.polygon([(x-30*s, y+30*s), (x+30*s, y+30*s), (x, y+70*s)], fill=(10,10,10)) 
            draw_teeth(draw, x-20*s, y+30*s, 40*s, 10*s, 4, top=True)
            try:
                f = ImageFont.load_default()
                draw.text((x-20*s, y+60*s), "IT'S ME", fill=(200, 0, 0), font=f)
            except: pass

# --- ROOM BUILDERS ---

def create_office_view():
    img = Image.new('RGB', (WIDTH, HEIGHT), COLORS['black'])
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, WIDTH, HEIGHT), fill=COLORS['wall_paint'])
    wall_tex = create_metal_texture((WIDTH, HEIGHT), 'v')
    img = Image.blend(img, wall_tex, 0.15)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 600), (100, 480), (700, 480), (800, 600)], fill=COLORS['floor_tile_2'])
    d.polygon([(0, 0), (100, 100), (100, 480), (0, 600)], fill=(40,40,45))
    d.polygon([(800, 0), (700, 100), (700, 480), (800, 600)], fill=(40,40,45))
    d.rectangle((0, 150, 90, 480), fill=(5,5,8))
    d.rectangle((710, 150, 800, 480), fill=(5,5,8))
    poster_x, poster_y = 350, 150
    d.rectangle((poster_x, poster_y, poster_x+100, poster_y+130), fill=(20,20,20), outline=(100,100,100))
    d.ellipse((poster_x+20, poster_y+20, poster_x+80, poster_y+80), fill=COLORS['boss_base'])
    d.text((poster_x+25, poster_y+90), "PARTY!", fill=(255, 50, 50))
    d.polygon([(50, 600), (150, 480), (650, 480), (750, 600)], fill=(60, 60, 65))
    for _ in range(5):
        px = random.randint(200, 600); py = random.randint(500, 580)
        d.rectangle((px, py, px+40, py+50), fill=(220,220,220), outline=(150,150,150))
    return add_vignette(img, 0.4)

def generate_office_animation():
    base = create_office_view()
    frames = []
    fx, fy = 400, 450
    for i in range(4):
        frame = base.copy()
        d = ImageDraw.Draw(frame)
        d.rectangle((fx-10, fy, fx+10, fy+60), fill=(20,20,20))
        d.ellipse((fx-50, fy-50, fx+50, fy+50), outline=(50,50,50), width=3)
        angle = i * 45; rad = math.radians(angle)
        for offset in [0, 120, 240]:
            a = math.radians(offset) + rad; x1 = fx + math.cos(a) * 45; y1 = fy + math.sin(a) * 45
            d.line((fx, fy, x1, y1), fill=(40,40,40), width=8)
        d.ellipse((fx-8, fy-8, fx+8, fy+8), fill=(10,10,10))
        frames.append(frame)
    frames[0].save('assets/office_main.gif', save_all=True, append_images=frames[1:], duration=80, loop=0)
    frames[0].save('assets/office_main.png')
    print("Generated: Office Animation")

def generate_doors_and_lights():
    # --- ВАРІАНТ 1: СИЛЬНА ІРЖА ТА ПОДРЯПИНИ ---
    door_w, door_h = 90, 360
    door_img = Image.new('RGBA', (door_w, door_h), (0,0,0,0))
    d = ImageDraw.Draw(door_img)
    
    # Базова рама (темніша)
    d.rectangle((0, 0, door_w, door_h), fill=COLORS['metal_base'], outline=(10,10,10))
    # Внутрішні панелі (трохи світліші, але брудні)
    d.rectangle((10, 10, door_w-10, door_h-10), fill=(80,80,85), outline=COLORS['metal_dark'], width=2)
    
    # Поперечні балки (темні)
    d.rectangle((0, door_h//3, door_w, door_h//3 + 20), fill=COLORS['metal_dark'])
    d.rectangle((0, door_h*2//3, door_w, door_h*2//3 + 20), fill=COLORS['metal_dark'])
    
    # Попереджувальні смуги (брудні та потерті)
    stripe_y = door_h-40
    d.rectangle((0, stripe_y, door_w, door_h), fill=(30,30,30)) # Темна основа під смуги
    for i in range(-20, door_w, 20):
        d.polygon([(i, stripe_y), (i+10, stripe_y), (i-10, door_h), (i-20, door_h)], fill=(180, 160, 0))
    
    # Гвинти
    for y in range(20, door_h, 40): draw_screw(d, 5, y); draw_screw(d, door_w-5, y)

    # --- НОВЕ: Шар важкої іржі та бруду ---
    # Створюємо маску шуму для плям іржі
    rust_mask = Image.effect_noise((door_w, door_h), 50).convert('L').filter(ImageFilter.GaussianBlur(2))
    # Робимо маску контрастнішою, щоб були чіткі плями
    rust_mask = rust_mask.point(lambda p: 255 if p > 130 else 0)
    
    rust_layer = Image.new('RGBA', (door_w, door_h), COLORS['metal_rust'])
    # Накладаємо іржу тільки там, де маска біла
    door_img.paste(rust_layer, (0,0), rust_mask)

    # --- НОВЕ: Додаємо подряпини поверх іржі ---
    draw_debris_and_scratches(d, 10, 10, door_w-20, door_h//3 - 10)
    draw_debris_and_scratches(d, 10, door_h//3 + 20, door_w-20, door_h*2//3 - 10)
    draw_debris_and_scratches(d, 10, door_h*2//3 + 20, door_w-20, door_h - stripe_y - 10)

    # Фінальне текстурування (гранж)
    door_img = apply_texture(door_img.convert('RGB'), "dirt", 0.3)
    door_img = apply_texture(door_img, "noise", 0.2).convert('RGBA')
    
    door_img.save('assets/door_left_closed.png')
    door_img.transpose(Image.FLIP_LEFT_RIGHT).save('assets/door_right_closed.png')
    
    base_size = (WIDTH, HEIGHT)
    
    # --- ЛІВЕ СВІТЛО ---
    beam_l = Image.new('RGBA', base_size, (0,0,0,0))
    bd = ImageDraw.Draw(beam_l)
    
    # Верх (0, 150) -> (90, 150)
    # Низ (-20, 600) -> (140, 600)
    bd.polygon([(0, 150), (90, 150), (140, 600), (-20, 600)], fill=COLORS['light_beam_open'])
    
    sparky_vis = beam_l.copy()
    sd = ImageDraw.Draw(sparky_vis)
    draw_detailed_animatronic(sd, 45, 280, 'sparky', 1.15, silhouette=False)
    
    sparky_shad = door_img.copy()
    ssd = ImageDraw.Draw(sparky_shad)
    draw_detailed_animatronic(ssd, 45, 180, 'sparky', 1.15, silhouette=True)
    highlight = Image.new('RGBA', (door_w, door_h), COLORS['light_beam_closed']) 
    sparky_shad = Image.alpha_composite(sparky_shad, highlight)

    beam_l.crop((0, 150, 140, 600)).save('assets/light_left_on.png')
    sparky_vis.crop((0, 150, 140, 600)).save('assets/light_left_sparky.png')
    sparky_shad.save('assets/light_left_closed_sparky.png')

    # --- ПРАВЕ СВІТЛО ---
    beam_r = Image.new('RGBA', base_size, (0,0,0,0))
    bd = ImageDraw.Draw(beam_r)
    
    # Верх (710, 150) -> (800, 150)
    # Низ (660, 600) -> (820, 600)
    bd.polygon([(710, 150), (800, 150), (820, 600), (660, 600)], fill=COLORS['light_beam_open'])
    
    clanker_vis = beam_r.copy(); cd = ImageDraw.Draw(clanker_vis)
    draw_detailed_animatronic(cd, 755, 280, 'clanker', 1.15, silhouette=False)
    
    boss_vis = beam_r.copy(); bod = ImageDraw.Draw(boss_vis)
    draw_detailed_animatronic(bod, 755, 280, 'boss', 1.15, silhouette=False)

    clanker_shad = door_img.transpose(Image.FLIP_LEFT_RIGHT).copy()
    csd = ImageDraw.Draw(clanker_shad)
    draw_detailed_animatronic(csd, 45, 180, 'clanker', 1.15, silhouette=True)
    clanker_shad = Image.alpha_composite(clanker_shad, highlight)
    
    boss_shad = door_img.transpose(Image.FLIP_LEFT_RIGHT).copy()
    bsd = ImageDraw.Draw(boss_shad)
    draw_detailed_animatronic(bsd, 45, 180, 'boss', 1.15, silhouette=True)
    boss_shad = Image.alpha_composite(boss_shad, highlight)

    beam_r.crop((660, 150, 800, 600)).save('assets/light_right_on.png')
    clanker_vis.crop((660, 150, 800, 600)).save('assets/light_right_clanker.png')
    boss_vis.crop((660, 150, 800, 600)).save('assets/light_right_boss.png')
    
    clanker_shad.save('assets/light_right_closed_clanker.png')
    boss_shad.save('assets/light_right_closed_boss.png')
    print("Generated: Doors & Lights (Heavy Rust Variant)")

def generate_cams():
    def get_room_bg(type_name):
        img = Image.new('RGB', (CAM_WIDTH, CAM_HEIGHT), COLORS['black'])
        d = ImageDraw.Draw(img)
        
        if type_name == 'stage':
            d.rectangle((0,0,CAM_WIDTH, CAM_HEIGHT), fill=(30,20,20))
            d.polygon([(0,0), (100,0), (50,480), (0,480)], fill=(60,10,10))
            d.polygon([(640,0), (540,0), (590,480), (640,480)], fill=(60,10,10))
            d.rectangle((50, 350, 590, 480), fill=(80, 50, 30))
            for x in range(50, 590, 30): d.line((x, 350, x, 480), fill=(50, 30, 20), width=2)
            d.ellipse((150, 20, 250, 60), fill=COLORS['light_warm']); d.ellipse((390, 20, 490, 60), fill=COLORS['light_warm'])

        elif type_name == 'dining': 
            d.rectangle((0,0,CAM_WIDTH, 300), fill=COLORS['wall_paint'])
            d.rectangle((0,300,CAM_WIDTH, CAM_HEIGHT), fill=COLORS['floor_tile_1'])
            d.line((50, 100, 590, 120), fill=COLORS['wire_black'], width=2)
            for i, x in enumerate(range(70, 570, 50)):
                col = [COLORS['party_red'], COLORS['party_blue'], COLORS['party_yellow']][i%3]
                d.polygon([(x, 110), (x+20, 110), (x+10, 140)], fill=col)
            for y in [320, 420]:
                d.rectangle((50, y, 590, y+40), fill=(200,200,200), outline=(150,150,150))
                for x in range(70, 570, 80):
                    d.ellipse((x, y-15, x+30, y+5), fill=(80,80,80))
                    d.ellipse((x+5, y+5, x+25, y+20), fill=(255,255,255), outline=(200,200,200))
            for _ in range(100):
                cx = random.randint(0, CAM_WIDTH)
                cy = random.randint(300, CAM_HEIGHT)
                ccol = random.choice([COLORS['party_red'], COLORS['party_blue'], COLORS['party_yellow']])
                d.rectangle((cx, cy, cx+3, cy+3), fill=ccol)

        elif type_name == 'hall_l':
            d.polygon([(150, 100), (490, 100), (490, 400), (150, 400)], fill=(10,10,15))
            d.polygon([(0,0), (150,100), (150,400), (0,480)], fill=(50,50,55))
            d.polygon([(640,0), (490,100), (490,400), (640,480)], fill=(50,50,55))
            d.polygon([(0,480), (150,400), (490,400), (640,480)], fill=(30,30,35))
            d.rectangle((0, 20, 640, 60), fill=COLORS['pipe_gray'])
            for x in range(0, 640, 100): d.rectangle((x, 10, x+20, 70), fill=COLORS['metal_dark'])
            draw_hanging_wires(d, 50, 60, 500, 80, 7)
            d.rectangle((50, 200, 100, 300), fill=COLORS['metal_dark'], outline=(100,100,100))
            d.ellipse((60, 210, 70, 220), fill=(255, 0, 0))

        elif type_name == 'hall_r':
            d.polygon([(150, 100), (490, 100), (490, 400), (150, 400)], fill=(10,10,15))
            d.polygon([(0,0), (150,100), (150,400), (0,480)], fill=(70,60,70))
            d.polygon([(640,0), (490,100), (490,400), (640,480)], fill=(70,60,70))
            floor_poly = [(0,480), (150,400), (490,400), (640,480)]
            d.polygon(floor_poly, fill=(20,20,20))
            for i in range(5):
                y = 480 - i*20
                x_l = 150 * (y-400)/80; x_r = 640 - (150 * (y-400)/80)
                d.line((x_l, y, x_r, y), fill=(50,50,50))
            d.rectangle((530, 140, 600, 240), fill=(100,80,40), outline=(150,130,90), width=3)
            d.rectangle((540, 150, 590, 230), fill=COLORS['clanker_base'])
            d.rectangle((540, 260, 610, 360), fill=(100,80,40), outline=(150,130,90), width=3)
            d.rectangle((550, 270, 600, 350), fill=COLORS['sparky_base'])
            d.rectangle((20, 180, 100, 380), fill=(40, 30, 50), outline=(80,60,100))
            d.rectangle((30, 200, 90, 300), fill=(20,20,30))

        elif type_name == 'cove':
            d.rectangle((0,0,640,480), fill=(20, 15, 30))
            d.polygon([(50, 50), (250, 50), (150, 400), (50, 480)], fill=(90, 30, 100))
            d.polygon([(590, 50), (390, 50), (490, 400), (590, 480)], fill=(90, 30, 100))
            for _ in range(20):
                sx = random.randint(50, 590)
                sy = random.randint(50, 400)
                d.ellipse((sx, sy, sx+5, sy+5), fill=(255,255,50))
            d.text((280, 50), "PIRATE COVE", fill=(200, 150, 200), font=ImageFont.load_default())

        if type_name in ['hall_l', 'hall_r', 'dining']: img = apply_texture(img, "dirt", 0.1)
        return apply_texture(img, "noise", 0.08)

    scenes = [
        ('cam_1A.png', 'stage', ['sparky', 'clanker', 'boss']),
        ('cam_1A_sparky.png', 'stage', ['clanker', 'boss']),
        ('cam_1A_clanker.png', 'stage', ['sparky', 'boss']),
        ('cam_1A_boss.png', 'stage', ['boss']),
        ('cam_1A_empty.png', 'stage', []),
        ('cam_1B.png', 'dining', []), 
        ('cam_1B_sparky.png', 'dining', ['sparky']),
        ('cam_1B_clanker.png', 'dining', ['clanker']),
        ('cam_1B_boss.png', 'dining', ['boss']),
        ('cam_2A.png', 'hall_l', []),
        ('cam_2A_sparky.png', 'hall_l', ['sparky']),
        # --- НОВИЙ КАДР БІГУНА ---
        ('cam_2A_runner.png', 'hall_l', ['runner_running']),
        # -------------------------
        ('cam_4A.png', 'hall_r', []),
        ('cam_4A_clanker.png', 'hall_r', ['clanker']),
        ('cam_4A_boss.png', 'hall_r', ['boss']),
        ('cam_4A_boss_clanker.png', 'hall_r', ['boss', 'clanker']),
        ('cam_1C_stage0.png', 'cove', []),
        ('cam_1C_stage1.png', 'cove', ['eyes']),
        ('cam_1C_stage2.png', 'cove', ['eyes']),
        ('cam_1C_stage3.png', 'cove', ['runner_gone'])
    ]

    for filename, room_type, occupants in scenes:
        img = get_room_bg(room_type)
        d = ImageDraw.Draw(img)
        
        if room_type == 'stage':
            if 'boss' in occupants: draw_detailed_animatronic(d, 320, 250, 'boss', 1.3)
            if 'sparky' in occupants: draw_detailed_animatronic(d, 150, 270, 'sparky', 1.2)
            if 'clanker' in occupants: draw_detailed_animatronic(d, 490, 270, 'clanker', 1.2)
        elif room_type == 'dining':
            if 'sparky' in occupants: draw_detailed_animatronic(d, 200, 350, 'sparky', 1.6)
            if 'clanker' in occupants: draw_detailed_animatronic(d, 450, 350, 'clanker', 1.6)
            if 'boss' in occupants: draw_detailed_animatronic(d, 320, 280, 'boss', 1.1, silhouette=True)
        elif room_type == 'hall_l':
            # --- ЛОГІКА ДЛЯ БІГУНА ---
            if 'runner_running' in occupants:
                # 1. Ефект розмиття (Motion Blur)
                # Малюємо напівпрозорий силует трохи позаду
                ghost = Image.new('RGBA', img.size, (0,0,0,0))
                gd = ImageDraw.Draw(ghost)
                draw_detailed_animatronic(gd, 280, 320, 'runner', 2.8, silhouette=True)
                ghost.putalpha(100) # Напівпрозорий
                img.paste(ghost, (0,0), ghost)
                
                # 2. Основна фігура (нахилена вперед, але тут просто зміщена для динаміки)
                # Ближче до центру коридору і трохи збільшений масштаб
                draw_detailed_animatronic(d, 350, 350, 'runner', 3.0)
            elif 'sparky' in occupants: 
                draw_detailed_animatronic(d, 320, 280, 'sparky', 2.2)
            # -------------------------
        elif room_type == 'hall_r':
            if 'clanker' in occupants and 'boss' in occupants:
                draw_detailed_animatronic(d, 260, 250, 'boss', 1.8)
                draw_detailed_animatronic(d, 400, 300, 'clanker', 2.2)
            else:
                if 'clanker' in occupants: draw_detailed_animatronic(d, 320, 280, 'clanker', 2.2)
                if 'boss' in occupants: draw_detailed_animatronic(d, 320, 250, 'boss', 1.8)
        elif room_type == 'cove':
            if 'eyes' in occupants: draw_eye(d, 280, 220, 8, True); draw_eye(d, 320, 220, 8, True)
            if 'runner_gone' in occupants:
                d.rectangle((260, 200, 380, 250), fill=(20,20,20), outline=(50,50,50))
                d.text((270, 220), "OUT OF ORDER", fill=(200,200,200), font=ImageFont.load_default())

        raw_name = filename.replace("cam_", "")
        cam_id = raw_name.split("_")[0].split(".")[0]
        display_text = f"CAM {cam_id}"

        img = apply_cctv_master(img, display_text, "REC")
        img.save(f'assets/{filename}')
    print("Generated: Detailed Cameras")

def generate_jumpscares():
    chars = ['sparky', 'clanker', 'boss', 'runner']
    for char in chars:
        img = Image.new('RGB', (800, 600), (0,0,0))
        d = ImageDraw.Draw(img)
        draw_detailed_animatronic(d, 400, 400, char, 6.5)
        red = Image.new('RGB', (800, 600), (150, 0, 0))
        img = Image.blend(img, red, 0.3)
        img = apply_cctv_master(img, "", "", is_camera=False)
        img.save(f'assets/jumpscare_{char}.png')
    print("Generated: Jumpscares")

def generate_menu_head():
    img = Image.new('RGB', (400, 600), (0,0,0))
    d = ImageDraw.Draw(img)
    draw_detailed_animatronic(d, 200, 350, 'boss', 4.5)
    mask = Image.new('L', (400, 600), 255)
    for x in range(400):
        for y in range(600):
            alpha = int(255 * (x / 400)) 
            mask.putpixel((x, y), alpha)
    black = Image.new('RGB', (400, 600), (0,0,0))
    img = Image.composite(img, black, mask)
    img = apply_cctv_master(img, "", "", is_camera=False)
    img.save('assets/menu_head_boss.png')
    print("Generated: Menu Head")

def generate_extras():
    img = Image.new('RGB', (CAM_WIDTH, CAM_HEIGHT), (0,0,0))
    img = apply_cctv_master(img, "CAM 6", "AUDIO ONLY")
    img.save('assets/cam_6.png')
    noise = Image.effect_noise((800, 600), 80).convert('RGB')
    noise.save('assets/cam_static.png')
    m = Image.new('RGBA', (300, 200), (0,0,0,200))
    md = ImageDraw.Draw(m)
    md.rectangle((0,0,299,199), outline=(0,255,0), width=2)
    rooms = [(100,20,200,70), (80,80,220,140), (30,90,70,130), (40,150,100,190), (200,150,260,190), (230,100,270,140)]
    for r in rooms: md.rectangle(r, outline=(0,200,0), fill=(0,50,0))
    md.rectangle((130, 160, 170, 190), fill=(200,200,200)) 
    m.save('assets/map.png')
    print("Generated: Extras")

print("--- STARTING GENERATION (RUSTED DOORS) ---")
generate_office_animation()
generate_doors_and_lights()
generate_cams()
generate_jumpscares()
generate_menu_head()
generate_extras()
print("--- DONE ---")