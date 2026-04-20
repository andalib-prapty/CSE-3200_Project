import pandas as pd


# ---------------- LOAD DATA ----------------
hall_info = pd.read_csv("project - hall_info.csv")
dept_info = pd.read_csv("project - department_info.csv")
routine_info = pd.read_csv("project - class_routine.csv")
faculty_info = pd.read_csv("project - faculty_info.csv")

# ---------------- HELPER FUNCTIONS ----------------
import re
import datetime

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9,
    "sept": 9, "oct": 10, "nov": 11, "dec": 12
}

def parse_date_from_text(text):
    text = text.strip()

    # 1) “7 January 2026” / “7 Jan 2026”
    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})\b", text)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        month = MONTHS.get(month_name)
        if month:
            try:
                return datetime.datetime(year, month, day)
            except ValueError:
                pass  # invalid calendar date (e.g., 31 Feb)

    # 2) Numeric “07-01-2026” / “07/01/2026” (DD-MM-YYYY or DD/MM/YYYY)
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", text)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        # Assume BD style DD-MM-YYYY
        try:
            return datetime.datetime(y, mth, d)
        except ValueError:
            pass

    # 3) ISO “2026-01-07”
    m = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text)
    if m:
        y, mth, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime.datetime(y, mth, d)
        except ValueError:
            pass

    # 4) Fallback: try a few explicit formats
    for fmt in ["%d %B %Y", "%d %b %Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"]:
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None


def get_day_name(date_obj):
    return date_obj.strftime("%A")
def get_today():
    return datetime.datetime.today().strftime("%A")

def get_tomorrow():
    today = datetime.datetime.today()
    tomorrow = today + datetime.timedelta(days=1)
    return tomorrow.strftime("%A")


def detect_intent(text):

    tl = text.lower()

    if any(w in tl for w in ["class", "routine", "lecture", "today", "schedule"]):
        if "tomorrow" in tl:
            return "class_tomorrow"
        # If any month name or a numeric date pattern is present → class_date
        has_month = any(m in tl for m in [
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december",
                "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec"
            ])
        has_numeric_date = bool(re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", tl)) or bool(
            re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", tl))
        if has_month or has_numeric_date:
            return "class_date"
        return "class_today"

    if any(w in tl for w in ["teacher", "faculty", "professor", "contact"]):
        return "faculty_query"

    if any(w in tl for w in ["hall", "seat", "accommodation"]):
         return "hall_query"

    if any(w in tl for w in ["department", "code", "faculty number", "faculty count"]):
        return "department_query"

    return "out_of_domain"


def ask_class_details():
    year = input("🤖 Which year? (e.g., 3rd): ").strip()
    series = input("🤖 Which series? (e.g., 21): ").strip()
    semester = input("🤖 Semester (Odd / Even): ").strip().capitalize()
    section = input("🤖 Section (A/B/C): ").strip().upper()
    department = input("🤖 Department (CSE/EEE/...): ").strip().upper()

    return year, series, semester, section, department

def show_classes(details, query_type="today", date_obj=None):
    year, series, semester, section, department = details

    # Decide the day
    if query_type == "today":
        date_obj = datetime.datetime.today()
        day = date_obj.strftime("%A")
        print(f"\n📅 Today is {day}")

    elif query_type == "tomorrow":
        date_obj = datetime.datetime.today() + datetime.timedelta(days=1)
        day = date_obj.strftime("%A")
        print(f"\n📅 Tomorrow is {day}")

    elif query_type == "date":
        if not date_obj:
            print("🤖 I couldn’t parse that date. Try formats like '7 January 2026', '07/01/2026', or '2026-01-07'.")
            return
        day = date_obj.strftime("%A")
        print(f"\n📅 {date_obj.strftime('%d %B %Y')} is a {day}")

    else:
        print("🤖 Unknown query type.")
        return

    # Weekend policy (Thursday/Friday)
    if day in ["Thursday", "Friday"]:
        if query_type == "today":
            print("🤖 Today is your weekend. No class today.")
        elif query_type == "tomorrow":
            print("🤖 Tomorrow is your weekend. No class tomorrow.")
        else:
            print(f"🤖 {date_obj.strftime('%d %B %Y')} is your weekend. No class on that day.")
        return

    # Query routine
    df = routine_info[
        (routine_info["Department"] == department) &
        (routine_info["Year"] == year) &
        (routine_info["Series"].astype(str) == series) &
        (routine_info["Semester"] == semester) &
        (routine_info["Section"] == section) &
        (routine_info["Day"] == day)
    ]

    if df.empty:
        print("🤖 No confirmed class info yet. Status: **TBA**")
        return

    print("\n📚 Your classes:\n")
    for _, row in df.iterrows():
        print(
            f"🕒 {row['StartTime']}–{row['EndTime']} | "
            f"{row['CourseCode'] or 'TBA'} | "
            f"Room: {row['Room'] or 'TBA'} | "
            f"Teacher: {row.get('Teacher', 'TBA')}"
        )

from fuzzywuzzy import process

def show_faculty_info(user_text):
    # Extract the best match from faculty names
    faculty_names = faculty_info["Faculty_Name"].tolist()
    best_match, score = process.extractOne(user_text, faculty_names)

    if score < 70:  # threshold to avoid wrong matches
        print("🤖 Sorry, faculty information is currently unavailable (TBA).")
        return

    row = faculty_info[faculty_info["Faculty_Name"] == best_match].iloc[0]

    print("\n👨‍🏫 Faculty Information")
    print(f"Name       : {row['Faculty_Name']}")
    print(f"Designation: {row['Designation']}")
    print(f"Department : {row['Department']}")
    print(f"Email      : {row['Email']}")
    print(f"Phone      : {row['Phone']}")
    print(f"Office     : {row['Office Contact']}")



from fuzzywuzzy import process

def show_hall_info(user_text=None):
    if not user_text:
        user_text = input("🏢 Enter hall query: ").strip()

    text = user_text.lower()

    # --- Step 1: Detect intent ---
    if "available seat" in text or "vacant" in text or "empty" in text:
        intent = "available"
    elif "capacity" in text or "total seat" in text:
        intent = "capacity"
    elif "supervisor" in text or "warden" in text:
        intent = "supervisor"
    elif "gender" in text or "male" in text or "female" in text:
        intent = "gender"
    else:
        intent = "full_info"

    # --- Step 2: Extract hall name ---
    # Remove intent words so fuzzy match only sees the hall name
    hall_query = user_text
    for word in ["available seat", "vacant", "empty", "capacity", "total seat",
                 "supervisor", "warden", "male", "female", "gender",
                 "how many", "tell me", "info", "information", "about"]:
        hall_query = hall_query.replace(word, "")
    hall_query = hall_query.strip()

    hall_names = hall_info["Hall_Name"].tolist()
    best_match, score = process.extractOne(hall_query, hall_names)

    if not best_match or score < 70:
        print("🤖 Hall information is currently TBA.")
        return

    row = hall_info[hall_info["Hall_Name"] == best_match].iloc[0]

    # --- Step 3: Respond based on intent ---
    if intent == "available":
        print(f"🤖 The available seat number in {best_match} is {row['Available_Seat']}.")
    elif intent == "capacity":
        print(f"🤖 The total seat capacity of {best_match} is {row['Seat_capacity']}.")
    elif intent == "supervisor":
        print(f"🤖 The hall supervisor of {best_match} is {row['Hall_Supervisor']} "
              f"from {row['Supervisor_Department']} department.")
    elif intent == "gender":
        print(f"🤖 {best_match} is for {row['Male/Female']} students.")
    else:
        print("\n🏢 Hall Information")
        print(row.to_string())

from fuzzywuzzy import process

def show_department_info(user_text=None):
    if not user_text:
        user_text = input("🏫 Enter department query: ").strip()

    text = user_text.lower()

    # --- Step 1: Detect intent ---
    if "faculty" in text and "number" in text:
        intent = "faculty_number"
    elif "faculty" in text or "school" in text:
        intent = "faculty"
    elif "code" in text:
        intent = "code"
    else:
        intent = "full_info"

    # --- Step 2: Try matching by department code first ---
    dept_codes = dept_info["Department_code"].tolist()
    best_code, score_code = process.extractOne(user_text.upper(), dept_codes)

    if score_code and score_code >= 90:  # strong match on code
        row = dept_info[dept_info["Department_code"] == best_code].iloc[0]
    else:
        # --- Step 3: Fuzzy match on department name ---
        dept_names = dept_info["Department_name"].tolist()
        best_match, score = process.extractOne(user_text, dept_names)
        if not best_match or score < 70:
            print("🤖 Department information is currently TBA.")
            return
        row = dept_info[dept_info["Department_name"] == best_match].iloc[0]

    # --- Step 4: Respond based on intent ---
    if intent == "faculty":
        print(f"🤖 {row['Department_name']} belongs to the {row['Faculty']} faculty.")
    elif intent == "code":
        print(f"🤖 The department code for {row['Department_name']} is {row['Department_code']}.")
    elif intent == "faculty_number":
        print(f"🤖 The {row['Department_name']} has {row['Faculty_Number']} faculty members.")
    else:
        print("\n🏫 Department Information")
        print(row.to_string())


# ---------------- CHAT LOOP ----------------
def chatbot():
    print("🎓 RUET AI University Enquiry Chatbot")
    print("🤖 Ask me about classes, faculty contacts, halls.")
    print("🤖 Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("🤖 Goodbye! Best wishes 🌟")
            break

        intent = detect_intent(user_input)

        if intent in ["class_today", "class_tomorrow", "class_date"]:
            print("🤖 Let me check your classes.")
            details = ask_class_details()

            if intent == "class_today":
                show_classes(details, query_type="today")

            elif intent == "class_tomorrow":
                show_classes(details, query_type="tomorrow")

            elif intent == "class_date":
                date_obj = parse_date_from_text(user_input)
                show_classes(details, query_type="date", date_obj=date_obj)

        elif intent == "faculty_query":
            print("🤖 Searching faculty contact details...")
            show_faculty_info(user_input)

        elif intent == "hall_query":
            show_hall_info(user_input)

        elif intent == "department_query":
            show_department_info(user_input)


        else:
            print("🤖 Sorry, that question is outside my university domain.")

# ---------------- RUN ----------------
if __name__ == "__main__":
    chatbot()

