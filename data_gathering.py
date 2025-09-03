import serial
import time
import csv
import os

PORT = 'COM3'  # Change to your Arduino's port if needed
BAUD = 9600

# Data type selection
options = [
    "Baseline Readings",
    "Soy Sauce",
    "Fish Sauce",
    "Oyster Sauce",
    "Worcestershire Sauce"
]
print("Select data type:")
for i, opt in enumerate(options, 1):
    print(f"{i}. {opt}")
choice = input("Enter number (1-5): ").strip()

try:
    choice = int(choice)
    assert 1 <= choice <= 5
except:
    print("Invalid selection. Exiting.")
    exit(1)

selected = options[choice-1]

# File and label setup
if selected == "Baseline Readings":
    filename = "baseline.csv"
    mode = "w"  # Overwrite
    trial = None
else:
    filename = selected.lower().replace(" ", "_") + ".csv"
    mode = "r+" if os.path.exists(filename) else "w+"
    trial = input("Enter trial number: ").strip()
    try:
        trial = int(trial)
        assert trial > 0
    except:
        print("Invalid trial number. Exiting.")
        exit(1)

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset
except Exception as e:
    print(f"Error opening serial port {PORT}: {e}")
    exit(1)

header = ["Trial", "MQ136", "MQ2", "MQ3", "MQ135", "MQ138", "MQ137", "Label"]
if selected == "Baseline Readings":
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header[1:])
        print(f"Recording baseline readings to {filename} for 10 minutes. Press Ctrl+C to stop early.")
        start_time = time.time()
        try:
            while time.time() - start_time < 600:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    values = line.split(",")
                    if len(values) == 6:
                        writer.writerow(values + ["Baseline"])
                        print(values, "Baseline")
                    else:
                        print(f"Unexpected data format: {line}")
        except KeyboardInterrupt:
            print("Stopped by user.")
else:
    # Read all rows, update or append trial
    with open(filename, mode, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
        # If file is empty, add header
        if not rows:
            rows.append(header)
        # Remove all rows for this trial
        rows = [row for row in rows if not (row and row[0] == f"Trial {trial}")]
        print(f"Recording trial {trial} for {selected} to {filename} for 10 minutes. Press Ctrl+C to stop early.")
        new_trial_rows = []
        start_time = time.time()
        try:
            while time.time() - start_time < 600:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    values = line.split(",")
                    if len(values) == 6:
                        new_row = [f"Trial {trial}"] + values + [selected]
                        new_trial_rows.append(new_row)
                        print(f"Trial {trial}", values, selected)
                    else:
                        print(f"Unexpected data format: {line}")
        except KeyboardInterrupt:
            print("Stopped by user.")
        # Write all rows back to file, with new trial data
        f.seek(0)
        f.truncate()
        writer = csv.writer(f)
        writer.writerows(rows + new_trial_rows)

ser.close()
print("Serial port closed.")