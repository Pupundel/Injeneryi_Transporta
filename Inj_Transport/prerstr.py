import cv2
from fer import FER
import tkinter as tk
from tkinter import Label, Text
from tkinter import ttk
from PIL import Image, ImageTk
import vosk
import sys
import sounddevice as sd
import queue
import json
from spellchecker import SpellChecker
from aniemore.recognizers.text import TextRecognizer
from aniemore.models import HuggingFaceModel
import threading


# Инициализация модели для анализа текста.

model2 = HuggingFaceModel.Text.Bert_Tiny2
device2 = 'cpu'
tr = TextRecognizer(model=model2, device=device2)

# Инициализация детектора эмоций
emo_detector = FER(mtcnn=True)


# Настройка интерфейса с тёмной темой
root = tk.Tk()
root.title("Распознование эмоций и речи")
root.configure(bg='#333333')

# Стиль для темной темы
style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#333333", foreground="white", font=("Arial", 12))
style.configure("TFrame", background="#333333")


# Создание элементов интерфейса (добавляем фрейм для графика)
label_frame = ttk.LabelFrame(root, text="Видео", style="TFrame")
label_frame.pack(fill="both", expand=True, padx=10, pady=5, side=tk.LEFT)  # side=tk.LEFT
label = Label(label_frame)
label.pack()

# Фрейм для графика и текстовой информации
info_frame = ttk.Frame(root, style="TFrame")
info_frame.pack(padx=10, pady=5, side=tk.RIGHT, fill=tk.Y)  # fill=tk.Y


emotion_text_label = ttk.Label(info_frame, text="Средняя эмоция из текста: неизвестно", style="TLabel")
emotion_text_label.pack(pady=5)

emotion_video_label = ttk.Label(info_frame, text="Средняя эмоция из видео: неизвестно", style="TLabel")
emotion_video_label.pack(pady=5)

text_display = Text(info_frame, height=10, width=50, bg="#333333", fg="white", font=("Arial", 10))
text_display.pack(pady=5)
text_display.insert(tk.END, "Текст речи:\n")
text_display.config(state=tk.DISABLED)

# Инициализация камеры и модели Vosk для распознавания речи
cap = cv2.VideoCapture(0)
model = vosk.Model("vosk-model-ru-0.42")
samplerate = 16000
device = 1
video_emotions = []
text_emotions = []
q = queue.Queue()

# Эмоция текст текущая tkinter
text_emotions_label = ttk.Label(info_frame, text="Эмоции из текста: ", style="TLabel")
text_emotions_label.pack()


# Инициализация модели пунктуации и spellchecker
spell = SpellChecker(language='ru')


def update_frame():
    ret, frame = cap.read()
    if not ret:
        return

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    captured_emotions = emo_detector.detect_emotions(rgb_frame)
    dominant_emotion, emotion_score = emo_detector.top_emotion(rgb_frame)

    if captured_emotions:
        for face in captured_emotions:
            bounding_box = face['box']
            cv2.rectangle(frame, (bounding_box[0], bounding_box[1]),
                          (bounding_box[0] + bounding_box[2], bounding_box[1] + bounding_box[3]),
                          (0, 255, 0), 2)
            cv2.putText(frame, f'{dominant_emotion}: {round(emotion_score * 100)}%',
                        (bounding_box[0], bounding_box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Добавляем текущую эмоцию из видео в список
        video_emotions.append(dominant_emotion)
        update_average_emotion("video")

    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)
    label.imgtk = imgtk
    label.configure(image=imgtk)
    label.after(1, update_frame)

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


def process_audio():
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=device, dtype='int16', channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(model, samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                text = json.loads(result).get('text', '')

                if text:
                    # Basic punctuation using string library
                    punctuated_text = text + "." # Basic punctuation

                    corrected_text = ' '.join([spell.correction(word) if spell.correction(word) else word for word in punctuated_text.split()])

                    # Обновление текстового окна
                    text_display.config(state=tk.NORMAL)
                    text_display.insert(tk.END, corrected_text + "\n")
                    text_display.config(state=tk.DISABLED)
                    text_display.yview(tk.END)  # Прокрутка к последнему добавленному тексту

                    try:
                        emotion = tr.recognize(corrected_text, return_single_label=True)
                        text_emotions.append(emotion)
                        update_average_emotion("text")
                        emotions_text = ", ".join(text_emotions)  # Format emotions as comma-separated string
                        text_emotions_label.config(text=f"Эмоции из текста: {emotion}")
                    except Exception as e:  # Catch potential errors during text recognition
                        print(f"Error during text recognition: {e}")



def update_average_emotion(source):
    if source == "video":
        # Подсчёт средней эмоции из видео
        emotion_counts = {emotion: video_emotions.count(emotion) for emotion in set(video_emotions)}
        avg_video_emotion = max(emotion_counts, key=emotion_counts.get)
        emotion_video_label.config(text=f"Средняя эмоция из видео: {avg_video_emotion}")
    elif source == "text":
        # Подсчёт средней эмоции из текста
        emotion_counts = {emotion: text_emotions.count(emotion) for emotion in set(text_emotions)}
        avg_text_emotion = max(emotion_counts, key=emotion_counts.get)
        emotion_text_label.config(text=f"Средняя эмоция из текста: {avg_text_emotion}")

audio_thread = threading.Thread(target=process_audio)
audio_thread.daemon = True
audio_thread.start()
update_frame()
root.mainloop()
cap.release()
