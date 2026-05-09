"""
voice_control.py
================
Voice keyword -> robot action + sound effect control program

Usage:
    python voice_control.py             # voice mode (default)
    python voice_control.py --keyboard  # keyboard mode (for debugging)

Supported language: English
"""

import os
import sys
import time
import threading
import readline  # optimizes keyboard input, import only

import speech_recognition as sr
from picrawler import Picrawler
from robot_hat import Music, Pin

from preset_actions import actions_dict
from utils import gray_print, redirect_error_2_null, cancel_redirect_error

# ── Startup arguments ─────────────────────────────────────────────────────────
args = sys.argv[1:]
INPUT_MODE = 'keyboard' if '--keyboard' in args else 'voice'

# ── Hardware initialization ───────────────────────────────────────────────────
os.popen("pinctrl set 20 op dh")  # enable robot_hat speaker switch
current_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_path)

try:
    spider = Picrawler()
    time.sleep(1)
except Exception as e:
    raise RuntimeError(f"Picrawler init failed: {e}")

music = Music()
led   = Pin('LED')

# ── Keyword → action mapping ──────────────────────────────────────────────────
# Any keyword in the tuple triggers the corresponding action.
# All matching is case-insensitive.
KEYWORD_ACTION_MAP = {
    # keyword tuple                              → action name (key in actions_dict)
    ("sit", "sit down"):                          "sit",
    ("stand", "stand up", "get up"):              "stand",
    ("wave", "wave hand", "goodbye", "bye"):      "wave_hand",
    ("shake", "shake hand", "handshake"):         "shake_hand",
    ("fight", "fighting", "attack"):              "fighting",
    ("excited", "hooray", "yay", "happy"):        "excited",
    ("play dead", "dead", "lie down"):            "play_dead",
    ("nod", "yes", "agree"):                      "nod",
    ("shake head", "no", "disagree"):             "shake_head",
    ("look left", "left"):                        "look_left",
    ("look right", "right"):                      "look_right",
    ("look up", "up"):                            "look_up",
    ("look down", "down"):                        "look_down",
    ("warm up", "warm", "stretch"):               "warm_up",
    ("push up", "push", "pushup"):                "push_up",
}

# Flatten the nested keys into a single {keyword: action} dict for fast lookup
FLAT_MAP: dict[str, str] = {}
for keywords, action in KEYWORD_ACTION_MAP.items():
    for kw in keywords:
        FLAT_MAP[kw.lower()] = action

# ── Sound effect mapping (add entries as needed) ──────────────────────────────
# SOUND_MAP = {
#     "talk": lambda: music.sound_play('./sounds/talk1.wav'),
# }

# ── LED control thread ────────────────────────────────────────────────────────
robot_state = "standby"   # "standby" | "listen" | "action"
state_lock  = threading.Lock()

LED_STANDBY_INTERVAL = 0.8   # double-blink interval (seconds)
LED_LISTEN_INTERVAL  = 0.1   # fast-blink interval (seconds)

def led_handler():
    last_state   = None
    last_time    = 0

    while True:
        with state_lock:
            state = robot_state

        if state != last_state:
            last_time  = 0
            last_state = state

        now = time.time()

        if state == "standby":
            if now - last_time > LED_STANDBY_INTERVAL:
                # double blink
                led.on();  time.sleep(0.1)
                led.off(); time.sleep(0.1)
                led.on();  time.sleep(0.1)
                led.off()
                last_time = time.time()

        elif state == "listen":
            if now - last_time > LED_LISTEN_INTERVAL:
                led.off(); time.sleep(LED_LISTEN_INTERVAL)
                led.on();  time.sleep(LED_LISTEN_INTERVAL)
                last_time = time.time()

        elif state == "action":
            led.on()

        time.sleep(0.01)

led_thread = threading.Thread(target=led_handler, daemon=True)
led_thread.start()

# ── Core: text → action matching ──────────────────────────────────────────────
def match_action(text: str) -> str | None:
    """
    Search the recognized text for all keywords.
    Returns the first matched action name, or None if no match.
    """
    text_lower = text.lower()
    for kw, action in FLAT_MAP.items():
        if kw in text_lower:
            return action
    return None

def do_action(action_name: str):
    """Execute an action and update the LED state."""
    func = actions_dict.get(action_name)
    if func is None:
        print(f"[Warning] Unknown action: {action_name}")
        return

    gray_print(f">> Running action: {action_name}")
    with state_lock:
        global robot_state
        robot_state = "action"

    try:
        func(spider)
    except Exception as e:
        print(f"[Action error] {e}")
    finally:
        with state_lock:
            robot_state = "standby"

# ── Speech recognition setup ──────────────────────────────────────────────────
recognizer = sr.Recognizer()
recognizer.dynamic_energy_adjustment_damping = 0.16
recognizer.dynamic_energy_ratio = 1.6
recognizer.pause_threshold = 0.8  # seconds of silence to end a phrase

def listen_once() -> str | None:
    """Record one utterance and return the recognized text, or None on failure."""
    _stderr_back = redirect_error_2_null()
    try:
        with sr.Microphone(chunk_size=8192) as source:
            cancel_redirect_error(_stderr_back)
            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            with state_lock:
                global robot_state
                robot_state = "listen"

            gray_print("Listening...")
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=6)
    except sr.WaitTimeoutError:
        cancel_redirect_error(_stderr_back)
        gray_print("(Timeout, waiting again)")
        return None
    except Exception as e:
        cancel_redirect_error(_stderr_back)
        print(f"[Mic error] {e}")
        return None

    # STT via Google (swap for sphinx / vosk for offline use)
    try:
        text = recognizer.recognize_google(audio, language="en-US")
    except sr.UnknownValueError:
        gray_print("(Could not understand, please try again)")
        return None
    except sr.RequestError as e:
        print(f"[STT network error] {e}")
        return None

    return text

# ── Help message ──────────────────────────────────────────────────────────────
def print_help():
    print("\n" + "=" * 55)
    print("  Spider Robot - Voice Keyword Control")
    print("=" * 55)
    print("  Supported keywords (say any one to trigger):\n")
    for keywords, action in KEYWORD_ACTION_MAP.items():
        kw_str = " / ".join(keywords)
        print(f"  [{action:12s}]  {kw_str}")
    print('\n  Say "quit" or "exit" to stop the program.')
    print("=" * 55 + "\n")

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    global robot_state

    spider.do_action('sit',   speed=60)
    spider.do_action('stand', speed=60)

    print_help()

    while True:
        # ── Get input ──
        if INPUT_MODE == 'voice':
            text = listen_once()
            if not text:
                with state_lock:
                    robot_state = "standby"
                continue
            print(f"[Recognized] {text}")

        else:  # keyboard
            with state_lock:
                robot_state = "standby"
            text = input("\033[1;30minput> \033[0m").strip()
            if not text:
                continue

        # ── Check for quit command ──
        if any(q in text.lower() for q in ("quit", "exit", "bye bye")):
            print("Goodbye!")
            break

        # ── Match and execute action ──
        action = match_action(text)
        if action:
            do_action(action)
        else:
            gray_print("(No command recognized, please try again)")
            with state_lock:
                robot_state = "standby"

        print()  # blank line separator


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Interrupted by user]")
    except Exception as e:
        print(f"\033[31m[ERROR] {e}\033[m")
    finally:
        led.off()
        spider.do_action('sit', speed=60)
        print("Reset complete. Program exited.")