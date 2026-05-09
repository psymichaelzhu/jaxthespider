"""
fun_fact_speaker.py
===================
Randomly speaks fun facts while performing matching robot actions.
"""

import random
import threading
from time import sleep

from robot_hat import Music, TTS
from picrawler import Picrawler
from preset_actions import actions_dict

# ── Hardware init ─────────────────────────────────────────────────────────────
music = Music()
tts = TTS(engine=TTS.ESPEAK, lang="en-us")
tts.espeak_params(amp=199, speed=140, gap=5, pitch=55)

spider = Picrawler()
sleep(1)

# ── Interval config ───────────────────────────────────────────────────────────
MIN_INTERVAL = 10
MAX_INTERVAL = 25

# ── Fun fact + action pairs ───────────────────────────────────────────────────
# Each entry: (fact_text, action_name_or_None)
# action_name must be a key in actions_dict, or None to skip motion
FACT_ACTION_PAIRS = [

    # --- excited / happy facts ---
    ("Honey never spoils. Archaeologists found 3000-year-old honey in Egyptian tombs and it was still edible!",
     "excited"),

    ("Otters hold hands while sleeping so they don't drift apart. That's called a raft.",
     "excited"),

    ("Dogs can smell your feelings. Their nose detects emotional changes through your sweat.",
     "excited"),

    ("Crows remember human faces and can hold grudges for years.",
     "excited"),

    ("A group of flamingos is called a flamboyance.",
     "excited"),

    ("Dolphins have names for each other — unique whistles they use to call specific friends.",
     "excited"),

    ("Squirrels forget where they bury about half their nuts, accidentally planting thousands of trees.",
     "excited"),

    ("Sea otters have the densest fur of any animal — up to a million hairs per square inch.",
     "excited"),

    # --- nod / agree facts ---
    ("Bananas are berries, but strawberries are not. Botanically speaking.",
     "nod"),

    ("Octopuses have three hearts, blue blood, and nine brains.",
     "nod"),

    ("The Eiffel Tower can be 15 centimeters taller in summer due to thermal expansion.",
     "nod"),

    ("There are more stars in the universe than grains of sand on all of Earth's beaches.",
     "nod"),

    ("Sharks are older than trees. They've been around for over 400 million years.",
     "nod"),

    ("A bolt of lightning is five times hotter than the surface of the sun.",
     "nod"),

    ("The inventor of the Frisbee was cremated and turned into a Frisbee after he died.",
     "nod"),

    ("Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid.",
     "nod"),

    ("Oxford University is older than the Aztec Empire.",
     "nod"),

    ("Humans share 60 percent of their DNA with bananas.",
     "nod"),

    # --- shake head / disbelief facts ---
    ("Some turtles can breathe through their butts. It's called cloacal respiration.",
     "shake_head"),

    ("Mosquitoes are the deadliest animal on Earth, killing more people per year than any other creature.",
     "shake_head"),

    ("A group of cats is called a clowder. A group of kittens is called a kindle.",
     "shake_head"),

    ("Wombat poop is cube-shaped. They use it to mark territory without it rolling away.",
     "shake_head"),

    ("Mantis shrimp can punch with the force of a bullet and see 16 types of color receptors. Humans have 3.",
     "shake_head"),

    ("Sloths can hold their breath longer than dolphins — up to 40 minutes.",
     "shake_head"),

    ("Lobsters were once considered so low-class that feeding them to prisoners was seen as cruel punishment.",
     "shake_head"),

    # --- look up / sky / space facts ---
    ("The observable universe is about 93 billion light-years in diameter.",
     "look_up"),

    ("A day on Venus is longer than a year on Venus.",
     "look_up"),

    ("If you removed all the empty space from atoms in the human body, all of humanity would fit in a sugar cube.",
     "look_up"),

    ("Light from the Sun takes about 8 minutes to reach Earth.",
     "look_up"),

    ("The Milky Way galaxy is about 100,000 light-years across.",
     "look_up"),

    # --- look down / ground / deep facts ---
    ("The deepest part of the ocean, the Mariana Trench, is deeper than Mount Everest is tall.",
     "look_down"),

    ("There are more trees on Earth than stars in the Milky Way.",
     "look_down"),

    ("The core of the Earth is as hot as the surface of the Sun.",
     "look_down"),

    # --- wave hand / social facts ---
    ("The average person will spend six months of their life waiting for red lights.",
     "wave_hand"),

    ("More people have mobile phones than toilets.",
     "wave_hand"),

    ("A group of pugs is called a grumble.",
     "wave_hand"),

    # --- look left / look right / curious facts ---
    ("Goats have rectangular pupils, giving them a nearly 360-degree field of vision.",
     "look_left"),

    ("Butterflies taste with their feet.",
     "look_right"),

    ("Cats can't taste sweetness. They lack the taste receptors for it.",
     "look_left"),

    ("Blind people dream in their non-visual senses — sound, touch, smell, and emotion.",
     "look_right"),

    # --- push up / strength facts ---
    ("A bolt of lightning contains enough energy to toast 100,000 slices of bread.",
     "push_up"),

    ("Pistol shrimp snap their claws so fast it creates a bubble hotter than the surface of the sun.",
     "push_up"),

    # --- fighting / surprise facts ---
    ("Mantis shrimp have been known to break aquarium glass with a single punch.",
     "fighting"),

    ("A single ant can carry up to 50 times its own body weight.",
     "fighting"),

    # --- play dead / dark humor facts ---
    ("Dead stars can still be seen in the night sky — their light just hasn't stopped reaching us yet.",
     "play_dead"),

    ("The average cloud weighs about 500,000 kilograms.",
     "play_dead"),

    # --- warm up / movement facts ---
    ("Hummingbirds are the only birds that can fly backwards.",
     "warm_up"),

    ("A snail can sleep for three years.",
     "warm_up"),

    # --- no action (pure speech) ---
    ("The word 'nerd' was first used by Dr. Seuss in 1950.",
     None),

    ("LEGO is the world's largest tire manufacturer by number of tires produced per year.",
     None),

    ("Nintendo was founded in 1889. It started as a playing card company.",
     None),

    ("The first computer bug was an actual bug — a moth found in a Harvard relay in 1947.",
     None),
]

# ── Action lock to prevent overlapping motions ────────────────────────────────
action_lock = threading.Lock()

def do_action(action_name: str):
    """Run a robot action safely."""
    if action_name not in actions_dict:
        return
    with action_lock:
        try:
            actions_dict[action_name](spider)
        except Exception as e:
            print(f"[Action error] {e}")

# ── Main loop ─────────────────────────────────────────────────────────────────
def fun_fact_loop():
    while True:
        interval = random.uniform(MIN_INTERVAL, MAX_INTERVAL)
        sleep(interval)

        fact, action = random.choice(FACT_ACTION_PAIRS)
        print(f"\n[Fun Fact] {fact}")
        if action:
            print(f"[Action]   {action}")

        # Run action and speech concurrently
        if action:
            action_thread = threading.Thread(target=do_action, args=(action,), daemon=True)
            action_thread.start()

        try:
            tts.say(fact)
        except Exception as e:
            print(f"[TTS error] {e}")


def main():
    print("=" * 55)
    print("  Fun Fact Speaker + Spider Robot")
    print(f"  {len(FACT_ACTION_PAIRS)} fact-action pairs loaded.")
    print(f"  Interval: {MIN_INTERVAL}–{MAX_INTERVAL} seconds")
    print("  Ctrl+C to quit")
    print("=" * 55 + "\n")

    spider.do_action('sit',   speed=60)
    spider.do_action('stand', speed=60)

    t = threading.Thread(target=fun_fact_loop, daemon=True)
    t.start()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("\nQuit.")
    finally:
        try:
            music.music_stop()
        except Exception:
            pass
        spider.do_action('sit', speed=60)


if __name__ == "__main__":
    main()