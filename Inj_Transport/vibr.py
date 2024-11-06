import tkinter as tk
import serial
import time

# визуал
root = tk.Tk()
root.title("Вибрация")

integrated_label = tk.Label(root, text="вибрация:")
integrated_label.pack()

integrated_value = tk.Label(root, text="---")
integrated_value.pack()

counter_label = tk.Label(root, text="Счётчик: 0")
counter_label.pack()

# всё под счётчик
counter = 0
data_array = []
start_time = time.time()
data_collection_started = False
last_counter_increment_time = 0
counter_increments_in_interval = 0
interval_start_time = time.time()
# состояние
anxiety_label = tk.Label(root, text="")
anxiety_label.pack()

ser = None

try:
    ser = serial.Serial('COM3', 9600)
    print("Соединение установлено.")
except serial.SerialException as e:
    print(f"Ошибка при подключении: {e}")
    error_label = tk.Label(root, text=f"Ошибка: {e}", fg="red")
    error_label.pack()
    root.mainloop()
    exit()
def read_data():
    
    global counter
    global data_array
    global data_collection_started
    global start_time
    global last_counter_increment_time
    global counter_increments_in_interval
    global interval_start_time


    elapsed_time = time.time() - start_time

    if ser and (data_collection_started or elapsed_time >= 2):
        if not data_collection_started:
            print("Data collection started")
            data_collection_started = True

        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            try:
                integrated = int(line.strip())
                integrated_value.config(text=integrated)

                data_array.append(integrated)
                if len(data_array) > 100:
                    data_array.pop(0)

                if len(data_array) == 100:
                    min_val = min(data_array)
                    max_val = max(data_array)
                    med_val = sum(data_array) / len(data_array)

                    if max_val - med_val >= 5 or med_val - min_val >=5:
                            current_time = time.time()
                            time_difference = current_time - last_counter_increment_time

                            if time_difference >= 1.25:
                                counter += 1
                                counter_label.config(text=f"Счётчик: {counter}")
                                print(f"Счётчик увеличен, макс: {max_val}, мин: {min_val}, ср: {med_val}")
                                data_array.clear()
                                last_counter_increment_time = current_time
                                counter_increments_in_interval += 1


            except ValueError as e:
                print(f"Ошибка парсинга: {e}")


    if time.time() - interval_start_time >= 5:
        frequency = counter_increments_in_interval

        if frequency < 1:
            anxiety_label.config(text="Спокойствие", fg="green")
        elif 1 <= frequency <= 2:
            anxiety_label.config(text="Частичная тревожность", fg="orange")
        else:
            anxiety_label.config(text="Тревожность", fg="red")

        counter_increments_in_interval = 0
        interval_start_time = time.time()

    root.after(1, read_data)


read_data()
root.mainloop()