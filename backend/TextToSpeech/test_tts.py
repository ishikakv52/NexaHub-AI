# test_tts.py
import pyttsx3
engine = pyttsx3.init()
engine.save_to_file("Testing NexaHub AI on Python 3.14", "/tmp/test.mp3")
engine.runAndWait()
engine.stop()

import os
print("File size:", os.path.getsize("/tmp/test.mp3"), "bytes")
print("✅ Working!" if os.path.getsize("/tmp/test.mp3") > 0 else "❌ Failed")