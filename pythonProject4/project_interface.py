import pandas as pd
import tkinter as tk
import datetime
import re
from fuzzywuzzy import process

# ================= LOAD DATA =================
hall_info = pd.read_csv("project - hall_info.csv")
dept_info = pd.read_csv("project - department_info.csv")
routine_info = pd.read_csv("project - class_routine.csv")
faculty_info = pd.read_csv("project - faculty_info.csv")

# ================= DATE UTILITIES =================
MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12
}

def parse_date_from_text(text):
    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})\b", text)
    if m:
        d, mth, y = int(m.group(1)), MONTHS.get(m.group(2).lower()), int(m.group(3))
        if mth:
            return datetime.datetime(y, mth, d)

    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", text)
    if m:
        return datetime.datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))

    m = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text)
    if m:
        return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    return None

# ================= NLP INTENT =================
def detect_intent(text):
    t = text.lower()

    if "class" in t or "routine" in t or "lecture" in t:
        if "tomorrow" in t:
            return "class_tomorrow"
        if any(m in t for m in MONTHS.keys()) or re.search(r"\d{4}", t):
            return "class_date"
        return "class_today"

    if any(w in t for w in ["faculty", "teacher", "professor", "contact"]):
        return "faculty"

    if "hall" in t:
        return "hall"

    if "department" in t or "code" in t or "faculty number" in t:
        return "department"

    return "out"

# ================= GREETING =================
def detect_greeting(text):
    text = text.lower()
    if any(w in text for w in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
        return True
    return False

def respond_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        bot("Good morning ☀️ How can I help you?")
    elif hour < 18:
        bot("Good afternoon 🌤️ How can I help you?")
    else:
        bot("Good evening 🌙 How can I help you?")

# ================= DATA LOGIC =================
def show_faculty(text):
    names = faculty_info["Faculty_Name"].tolist()
    match, score = process.extractOne(text, names)

    if score < 60:
        bot("Sorry, faculty information is currently unavailable (TBA).")
        return

    r = faculty_info[faculty_info["Faculty_Name"] == match].iloc[0]
    bot(
        f"👨‍🏫 Faculty Name: {r['Faculty_Name']}\n"
        f"📌 Designation: {r['Designation']}\n"
        f"🏫 Department: {r['Department']}\n"
        f"📧 Email: {r['Email']}\n"
        f"📞 Phone: {r['Phone']}\n"
        f"🏢 Office: {r['Office Contact']}"
    )

def show_department(text):
    names = dept_info["Department_name"].tolist()
    match, score = process.extractOne(text, names)

    if score < 60:
        bot("Department information is TBA.")
        return

    r = dept_info[dept_info["Department_name"] == match].iloc[0]
    bot(
        f"🏫 Department: {r['Department_name']}\n"
        f"🔢 Code: {r['Department_code']}\n"
        f"🎓 Faculty: {r['Faculty']}\n"
        f"👥 Total Faculty Members: {r['Faculty_Number']}"
    )

def show_hall(text):
    names = hall_info["Hall_Name"].tolist()
    match, score = process.extractOne(text, names)

    if score < 60:
        bot("Hall information is TBA.")
        return

    r = hall_info[hall_info["Hall_Name"] == match].iloc[0]
    bot(
        f"🏠 Hall: {match}\n"
        f"🪑 Seat Capacity: {r['Seat_capacity']}\n"
        f"✅ Available Seat: {r['Available_Seat']}\n"
        f"🚻 Gender: {r['Male/Female']}\n"
        f"👤 Supervisor: {r['Hall_Supervisor']} ({r['Supervisor_Department']})"
    )

def ask_class_details(date_obj):
    popup = tk.Toplevel(root)
    popup.title("Class Details")
    popup.geometry("300x300")

    fields = {}
    for field in ["Department", "Year", "Series", "Semester", "Section"]:
        tk.Label(popup, text=field).pack()
        e = tk.Entry(popup)
        e.pack()
        fields[field] = e

    def submit():
        details = {
            "Department": fields["Department"].get().strip().upper(),
            "Year": fields["Year"].get().strip(),
            "Series": fields["Series"].get().strip(),
            "Semester": fields["Semester"].get().strip().capitalize(),
            "Section": fields["Section"].get().strip().upper()
        }
        popup.destroy()
        show_classes(details, date_obj)

    tk.Button(popup, text="Submit", command=submit).pack(pady=10)

def show_classes(d, date_obj):
    day = date_obj.strftime("%A")
    bot(f"📅 {date_obj.strftime('%d %B %Y')} ({day})")

    # Weekend
    if day in ["Thursday", "Friday"]:
        bot("It is weekend. No classes.")
        return

    # ---- NORMALIZE YEAR ----
    year_map = {
        "1": "1st", "1st": "1st",
        "2": "2nd", "2nd": "2nd",
        "3": "3rd", "3rd": "3rd",
        "4": "4th", "4th": "4th"
    }
    user_year = year_map.get(d["Year"].lower(), d["Year"].lower())

    # ---- FILTER WITH NORMALIZATION ----
    df = routine_info[
        (routine_info["Department"].str.upper() == d["Department"].upper()) &
        (routine_info["Year"].str.lower() == user_year) &
        (routine_info["Series"].astype(str) == str(d["Series"])) &
        (routine_info["Semester"].str.capitalize() == d["Semester"].capitalize()) &
        (routine_info["Section"].str.upper() == d["Section"].upper()) &
        (routine_info["Day"].str.capitalize() == day)
    ]

    if df.empty:
        bot("No confirmed class routine found. Status: TBA")
        return

    for _, r in df.iterrows():
        bot(
            f"📘 Course: {r['CourseCode']}\n"
            f"⏰ Time: {r['StartTime']} – {r['EndTime']}\n"
            f"🏫 Room: {r['Room']}"
        )


# ================= UI =================
def bot(msg):
    add_bot_bubble(msg)

def user(msg):
    add_user_bubble(msg)

def send():
    text = entry.get().strip()
    if not text:
        return

    user(text)
    entry.delete(0, tk.END)

    if detect_greeting(text):
        respond_greeting()
        return

    intent = detect_intent(text)

    if intent == "faculty":
        show_faculty(text)
    elif intent == "department":
        show_department(text)
    elif intent == "hall":
        show_hall(text)
    elif intent.startswith("class"):
        date = datetime.datetime.today()
        if intent == "class_tomorrow":
            date += datetime.timedelta(days=1)
        elif intent == "class_date":
            date = parse_date_from_text(text)
            if not date:
                bot("Could not understand the date.")
                return
        ask_class_details(date)
    else:
        bot("Sorry, this question is outside my university domain.")

# ================= WINDOW =================
root = tk.Tk()
root.title("RUET AI University Enquiry Chatbot")
root.geometry("720x620")
root.configure(bg="#E6F4FF")

chat_canvas = tk.Canvas(root, bg="#E6F4FF", highlightthickness=0)
chat_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

scrollbar = tk.Scrollbar(root, command=chat_canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
chat_canvas.configure(yscrollcommand=scrollbar.set)

chat_frame = tk.Frame(chat_canvas, bg="#E6F4FF")
chat_canvas.create_window((0, 0), window=chat_frame, anchor="nw")

def update_scrollregion(event=None):
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))

chat_frame.bind("<Configure>", update_scrollregion)

def add_bot_bubble(text):
    tk.Label(chat_frame, text=text, bg="white", wraplength=450,
             font=("Segoe UI", 11), padx=10, pady=6, justify="left").pack(anchor="w", pady=4)

def add_user_bubble(text):
    tk.Label(chat_frame, text=text, bg="#87CEEB", wraplength=450,
             font=("Segoe UI", 11), padx=10, pady=6, justify="left").pack(anchor="e", pady=4)

entry = tk.Entry(root, font=("Segoe UI", 11))
entry.pack(fill=tk.X, padx=10, pady=10)
entry.bind("<Return>", lambda e: send())

tk.Button(root, text="Send", bg="#87CEEB", command=send).pack(pady=(0, 10))

bot("👋 Hello! Welcome to the RUET AI University Enquiry Chatbot.\nHow can I help you today?")

root.mainloop()

