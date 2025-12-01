# juego_troll_visual.py
import pygame
import random
import sys
import math
import time

pygame.init()
WIDTH, HEIGHT = 760, 480
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Juego Troll — Sumas concatenadas + Troleos Visuales")

# Fuentes
F_BIG = pygame.font.SysFont("arial", 56)
F_MED = pygame.font.SysFont("arial", 30)
F_SM = pygame.font.SysFont("arial", 20)

# Colores
BG = (18, 18, 28)
WHITE = (245, 245, 245)
CYAN = (60, 220, 220)
GREEN = (100, 255, 140)
YELLOW = (255, 220, 100)
RED = (255, 100, 100)
GRAY = (120, 120, 130)

clock = pygame.time.Clock()

# ---------- LÓGICA REAL (con SUMA TROLL: concatenación) ----------
OPS = ["+", "-", "*", "/"]

def compute(a, b, op):
    try:
        if op == "+":
            # Regla solicitada: sumar = concatenar (ej: 2 + 3 => 23)
            return int(f"{a}{b}")
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            # division normal pero si no exacta devolvemos float con 2 decimales
            return round(a / b, 2) if b != 0 else None
    except Exception:
        return None

def generate_question():
    op = random.choice(OPS)
    a = random.randint(1, 12)
    b = random.randint(1, 12)
    # evitar division por cero: si '/' y b==0 regen
    if op == "/" and b == 0:
        b = 1
    ans = compute(a, b, op)
    return a, b, op, ans

# ---------- TROLEOS VISUALES ----------
def proximity_color(distance):
    # distance: absolute difference between user's numeric guess and correct (0 -> green)
    d = min(distance, 20) / 20
    r = int(GREEN[0] * (1 - d) + RED[0] * d)
    g = int(GREEN[1] * (1 - d) + RED[1] * d)
    b = int(GREEN[2] * (1 - d) + RED[2] * d)
    return (r, g, b)

sarcastic_fail = [
    "¿En serio? intenta con los ojos abiertos.",
    "Eso estuvo más feo que dividir por cero.",
    "A propósito? ¿o así te salió?",
    "Te faltan 2 neuronas hoy."
]
sarcastic_ok = [
    "Era fácil, ¿no?",
    "Wow… te sorprendiste a ti mismo.",
    "No era trampa... era habilidad."
]

# ---------- UI: input box & button ----------
input_text = ""
active_input = True
score = 0
a, b, op, correcta = generate_question()
message = ""
message_color = YELLOW
message_timer = 0
popup = None
popup_timer = 0

# Button rect that can move a bit
button_rect = pygame.Rect(WIDTH - 180, HEIGHT - 90, 150, 50)

# Flags
ALLOW_LIES = True  # si True, en raras ocasiones el juego "miente" en el texto mostrado
LIE_PROB = 0.05

# Parpadeo visual variables
blink = False
blink_timer = 0
blink_duration = 120  # ms

# Shake variables
shake_offset = (0, 0)
shake_timer = 0

# Puntaje oculto temporal
score_hidden = False
score_hide_timer = 0

def draw():
    WIN.fill(BG)
    # apply shake offset
    ox, oy = shake_offset

    # Pregunta (posible parpadeo)
    if blink and blink_timer > 0:
        # show a misleading temporary fake question
        fa = random.randint(1, 12)
        fb = random.randint(1, 12)
        fop = random.choice(OPS)
        q_surf = F_BIG.render(f"{fa} {fop} {fb} = ?", True, CYAN)
    else:
        q_surf = F_BIG.render(f"{a} {op} {b} = ?", True, CYAN)
    WIN.blit(q_surf, ((WIDTH - q_surf.get_width())//2 + ox, 30 + oy))

    # Input box
    input_box = pygame.Rect((WIDTH//2 - 160 + ox, 140 + oy, 320, 50))
    pygame.draw.rect(WIN, (40,40,50), input_box, border_radius=8)
    txt = input_text if input_text != "" else ""
    t_surf = F_MED.render(txt, True, WHITE)
    WIN.blit(t_surf, (input_box.x + 8, input_box.y + 8))

    # Button (puede moverse)
    pygame.draw.rect(WIN, (60,60,80), button_rect.move(ox, oy), border_radius=8)
    btxt = F_MED.render("Responder", True, WHITE)
    WIN.blit(btxt, (button_rect.x + 12 + ox, button_rect.y + 8 + oy))

    # Message (color depends on proximity if numeric)
    if message:
        WIN.blit(F_MED.render(message, True, message_color), ((WIDTH - 400)//2 + ox, 210 + oy))

    # Score (a veces oculto)
    if score_hidden:
        score_s = "Puntuación: ???"
        sc_col = GRAY
    else:
        score_s = f"Puntuación: {score}"
        sc_col = GREEN if score >= 0 else RED
    WIN.blit(F_SM.render(score_s, True, sc_col), (16 + ox, HEIGHT - 36 + oy))

    # Popup
    global popup
    if popup:
        pop_w, pop_h = 420, 110
        pr = pygame.Rect((WIDTH - pop_w)//2, (HEIGHT - pop_h)//2, pop_w, pop_h)
        pygame.draw.rect(WIN, (35,35,48), pr, border_radius=10)
        pygame.draw.rect(WIN, (90,50,150), (pr.x, pr.y, pr.w, 6), border_radius=3)
        WIN.blit(F_MED.render(popup, True, WHITE), (pr.x + 16, pr.y + 30))

    # hint text bottom
    hint = "Escribe tu respuesta y presiona ENTER o haz click en 'Responder'. (Sumas = concatenar)"
    WIN.blit(F_SM.render(hint, True, GRAY), ((WIDTH - 680)//2, HEIGHT - 20))

def apply_shake(duration=400, magnitude=6):
    global shake_timer
    shake_timer = duration

def trigger_popup(text, duration_ms=1500):
    global popup, popup_timer
    popup = text
    popup_timer = duration_ms

# Main loop
running = True
last_time = pygame.time.get_ticks()
while running:
    dt = clock.tick(60)
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Submit answer
                if input_text.strip() == "":
                    message = "Escribe algo primero, genio."
                    message_color = YELLOW
                    message_timer = 1200
                else:
                    # parse number (allow floats)
                    try:
                        # If user typed a decimal, accept float; but concatenation yields int normally.
                        user_val = float(input_text) if "." in input_text else int(input_text)
                    except:
                        message = "Eso no parece un número."
                        message_color = YELLOW
                        message_timer = 1200
                        input_text = ""
                        continue

                    # evaluate correct (real math, except '+' is concatenation)
                    correct = correcta
                    # If division and correct is float, allow tolerance
                    is_correct = False
                    if correct is None:
                        is_correct = False
                    else:
                        if isinstance(correct, float):
                            is_correct = abs(user_val - correct) < 0.02
                        else:
                            # correct is int: compare exactly (if user gave float like 23.0, treat as equal)
                            if isinstance(user_val, float) and user_val.is_integer():
                                is_correct = int(user_val) == correct
                            else:
                                is_correct = user_val == correct

                    # Proximity color
                    try:
                        dist = abs(float(user_val) - float(correct)) if correct is not None else 999
                    except:
                        dist = 999
                    message_color = proximity_color(dist if isinstance(dist, (int, float)) else 999)

                    # Occasional lie (only in text, scoring follows truth)
                    lied = False
                    if ALLOW_LIES and random.random() < LIE_PROB:
                        lied = True

                    if is_correct:
                        # scoring real
                        score += 1
                        message = random.choice(sarcastic_ok) if not lied else "Incorrecto... o no."
                        if lied:
                            message_color = RED
                        else:
                            message_color = GREEN
                        if random.random() < 0.12:
                            apply_shake(250, 5)
                    else:
                        # wrong
                        score -= 1
                        message = random.choice(sarcastic_fail) if not lied else "CORRECTO! (aleatorio)"
                        if lied:
                            message_color = GREEN
                        else:
                            message_color = RED
                        apply_shake(360, 8)

                    # occasional popup
                    if random.random() < 0.09:
                        trigger_popup(random.choice([
                            "¿Seguro? (no realmente)",
                            "Ventana emergente inútil: presiona X para nada",
                            "¿Quieres ayuda? Ja.",
                            "Sugerencia: respira."
                        ]), duration_ms=1200)

                    # sometimes hide score briefly as troll
                    if random.random() < 0.08:
                        score_hidden = True
                        score_hide_timer = 1200

                    # reset input
                    input_text = ""
                    # new question (but we keep operations real and visible)
                    a, b, op, correcta = generate_question()

            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                # accept digits and decimal and minus only at start
                ch = event.unicode
                if ch.isdigit() or (ch == "." and "." not in input_text) or (ch == "-" and input_text == ""):
                    input_text += ch

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if button_rect.collidepoint(mx, my):
                # simulate ENTER press (click submit)
                # slightly move button as troll sometimes
                if random.random() < 0.12:
                    # move button to new random nearby position
                    button_rect.x = random.randint(WIDTH - 300, WIDTH - 120)
                    button_rect.y = random.randint(HEIGHT - 140, HEIGHT - 70)

                # create a fake KEYDOWN enter by injecting logic (duplicate of enter handling)
                if input_text.strip() == "":
                    message = "Escribe algo primero, campeón."
                    message_color = YELLOW
                    message_timer = 1200
                else:
                    try:
                        user_val = float(input_text) if "." in input_text else int(input_text)
                    except:
                        message = "Eso no parece un número."
                        message_color = YELLOW
                        input_text = ""
                        continue

                    correct = correcta
                    is_correct = False
                    if correct is None:
                        is_correct = False
                    else:
                        if isinstance(correct, float):
                            is_correct = abs(user_val - correct) < 0.02
                        else:
                            if isinstance(user_val, float) and user_val.is_integer():
                                is_correct = int(user_val) == correct
                            else:
                                is_correct = user_val == correct

                    try:
                        dist = abs(float(user_val) - float(correct)) if correct is not None else 999
                    except:
                        dist = 999
                    message_color = proximity_color(dist if isinstance(dist, (int, float)) else 999)

                    lied = False
                    if ALLOW_LIES and random.random() < LIE_PROB:
                        lied = True

                    if is_correct:
                        score += 1
                        message = random.choice(sarcastic_ok) if not lied else "Incorrecto... o no."
                        if lied:
                            message_color = RED
                        else:
                            message_color = GREEN
                        if random.random() < 0.12:
                            apply_shake(250, 5)
                    else:
                        score -= 1
                        message = random.choice(sarcastic_fail) if not lied else "CORRECTO! (aleatorio)"
                        if lied:
                            message_color = GREEN
                        else:
                            message_color = RED
                        apply_shake(360, 8)

                    if random.random() < 0.09:
                        trigger_popup(random.choice([
                            "¿Seguro? (no realmente)",
                            "Ventana emergente inútil: presiona X para nada",
                            "¿Quieres ayuda? Ja.",
                            "Sugerencia: respira."
                        ]), duration_ms=1200)

                    if random.random() < 0.08:
                        score_hidden = True
                        score_hide_timer = 1200

                    input_text = ""
                    a, b, op, correcta = generate_question()

    # Update timers
    # blink chance: occasionally show a fake blink (parpadeo) for a short time
    if blink_timer > 0:
        blink_timer -= dt
        blink = True
    else:
        # occasionally trigger a blink
        if random.random() < 0.005:
            blink_timer = blink_duration
            blink = True
        else:
            blink = False

    if popup_timer > 0:
        popup_timer -= dt
        if popup_timer <= 0:
            popup = None

    if shake_timer > 0:
        shake_timer -= dt
        # compute small random offset
        shake_offset = (random.randint(-6,6), random.randint(-6,6))
        if shake_timer <= 0:
            shake_offset = (0,0)
    else:
        shake_offset = (0,0)

    if score_hidden:
        score_hide_timer -= dt
        if score_hide_timer <= 0:
            score_hidden = False

    # small chance the button teleports a bit to troll
    if random.random() < 0.002:
        button_rect.x = random.randint(WIDTH - 300, WIDTH - 120)
        button_rect.y = random.randint(HEIGHT - 140, HEIGHT - 70)

    # draw everything
    draw()
    pygame.display.update()

pygame.quit()
sys.exit()
