import random
import threading
from time import sleep
from robot_hat import Music, TTS

music = Music()
tts = TTS(engine=TTS.ESPEAK, lang="en-us")
tts.espeak_params(amp=199, speed=140, gap=5, pitch=55)

# Fun facts pool
FUN_FACTS = [
    "Honey never spoils.",
    "Bananas are berries, but strawberries aren’t.",
    "A group of flamingos is called a flamboyance.",
    "The Eiffel Tower can be 15 cm taller during hot days.",
    "There are more stars in the universe than grains of sand on Earth.",
    "Octopuses have three hearts.",
    "Some turtles can breathe through their butts.",
    "A bolt of lightning contains enough energy to toast 100,000 slices of bread.",
    "Mosquitoes are attracted to people who just ate bananas.",
    "The inventor of the Frisbee was turned into a Frisbee."
]

# Interval range (in seconds) between fun facts
MIN_INTERVAL = 10
MAX_INTERVAL = 25

def fun_fact_loop():
    while True:
        interval = random.uniform(MIN_INTERVAL, MAX_INTERVAL)
        sleep(interval)
        fact = random.choice(FUN_FACTS)
        print(f"[Fun Fact] {fact}")
        try:
            tts.say(fact)
        except Exception as e:
            print(f"(TTS error: {e})")  # Graceful fail

def main():
    print("Fun Fact Speaker is running... (Ctrl+C to quit)")

    music.music_set_volume(100)
    tts.lang("en-US")

    # Start the fun fact loop in a background thread
    t = threading.Thread(target=fun_fact_loop, daemon=True)
    t.start()

    try:
        while True:
            sleep(1)  # Keep main thread alive, can do more things if needed

    except KeyboardInterrupt:
        print("\nquit")

    finally:
        try:
            music.music_stop()
        except Exception:
            pass

if __name__ == "__main__":
    main()