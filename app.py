
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from groq_api import extract_with_groq
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

load_dotenv()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)

# Replace with your actual Sheet ID
SHEET_ID = "1UC83jw-ZM2YB2rVv587uAwn5qdUAEP3-m6dCcaeecdE"
sheet = client.open_by_key(SHEET_ID).sheet1

app = Flask(__name__)
app.secret_key = "your_secret_key"
CORS(app)

def smart_time_parser(time_str):
    """Parse time with smart AM/PM detection"""
    time_str = time_str.strip().lower()
    
    # If already has AM/PM, return as is
    if 'am' in time_str or 'pm' in time_str:
        return time_str.upper()
    
    # Extract hour and minute
    time_match = re.search(r'(\d{1,2}):?(\d{2})?', time_str)
    if not time_match:
        return time_str
    
    hour = int(time_match.group(1))
    minute = time_match.group(2) if time_match.group(2) else "00"
    
    # Smart AM/PM logic
    if hour >= 1 and hour <= 11:
        return f"{hour}:{minute}"
    elif hour == 12:
        return f"12:{minute}"
    elif hour >= 13 and hour <= 23:
        # Convert 24-hour to 12-hour PM
        hour_12 = hour - 12 if hour > 12 else 12
        return f"{hour_12}:{minute} PM"
    else:
        return f"{hour}:{minute}"

def determine_am_pm(time_str, is_login=True):
    """Determine AM/PM based on context"""
    if 'am' in time_str.lower() or 'pm' in time_str.lower():
        return time_str.upper()
    
    # Extract hour
    time_match = re.search(r'(\d{1,2})', time_str)
    if not time_match:
        return time_str
    
    hour = int(time_match.group(1))
    
    if is_login:
        # Login times: 6-11 likely AM, 12-5 likely PM
        if hour >= 6 and hour <= 11:
            return time_str + " AM"
        elif hour == 12 or (hour >= 1 and hour <= 5):
            return time_str + " PM"
    else:
        # Logout times: 12-11 likely PM, others context-dependent
        if hour >= 1 and hour <= 11:
            return time_str + " PM"
        elif hour == 12:
            return time_str + " PM"
    
    return time_str

def calculate_total_hours(login_time, logout_time):
    """Calculate total hours between login and logout"""
    try:
        # Clean up time strings
        login_clean = login_time.strip().upper().replace('.', '')
        logout_clean = logout_time.strip().upper().replace('.', '')
        
        # Try different formats
        formats = ["%I:%M %p", "%I %p", "%H:%M"]
        
        login_dt = None
        logout_dt = None
        
        for fmt in formats:
            try:
                login_dt = datetime.strptime(login_clean, fmt)
                break
            except ValueError:
                continue
        
        for fmt in formats:
            try:
                logout_dt = datetime.strptime(logout_clean, fmt)
                break
            except ValueError:
                continue
        
        if not login_dt or not logout_dt:
            return "-"
        
        # Handle case where logout is on next day
        if logout_dt < login_dt:
            logout_dt += timedelta(days=1)
        
        total = logout_dt - login_dt
        hours, remainder = divmod(total.total_seconds(), 3600)
        minutes = remainder // 60
        return f"{int(hours)}h {int(minutes)}m"
    except Exception as e:
        print(f"Error calculating hours: {str(e)}")
        return "-"

def find_existing_record(name, date):
    """Find existing record for a user on a specific date"""
    try:
        all_records = sheet.get_all_records()
        for i, record in enumerate(all_records):
            if record['Name'] == name and record['Date'] == date:
                return i + 2, record  # +2 because sheets are 1-indexed and header is row 1
        return None, None
    except Exception as e:
        print(f"Error finding existing record: {str(e)}")
        return None, None

def update_logout_time(name, date, new_logout_time):
    """Update only the logout time for an existing record"""
    try:
        row_index, existing_record = find_existing_record(name, date)
        
        if row_index and existing_record:
            # Parse and update logout time
            formatted_logout = determine_am_pm(new_logout_time, is_login=False)
            
            # Update logout time in the sheet
            sheet.update_cell(row_index, 8, formatted_logout)  # Column 8 is Logout Time
            
            # Recalculate total hours
            login_time = existing_record.get('Login Time', '-')
            if login_time and login_time != '-':
                total_hours = calculate_total_hours(login_time, formatted_logout)
                sheet.update_cell(row_index, 9, total_hours)  # Column 9 is Total Hours
            
            return True, f"✅ Updated logout time to {formatted_logout}"
        else:
            return False, "❌ No existing record found for today"
    except Exception as e:
        print(f"Error updating logout time: {str(e)}")
        return False, f"❌ Error updating logout time: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_chat', methods=['POST'])
def start_chat():
    session.clear()
    name = request.json.get('name')
    session['name'] = name
    
    welcome_msg = f"Hello {name}! Please enter your complete work log in one message (Leave, WFH/WFO, Login, Logout, Work Done)."
    
    return jsonify({"message": welcome_msg})

# Simple work location detection logic
@app.route('/message', methods=['POST'])
def message():
    user_msg = request.json.get('message')
    name = request.json.get('name')
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check for logout time update command
    logout_update_patterns = [
        r'update logout.*?(\d{1,2}:?\d{0,2})\s*(am|pm)?',
        r'change logout.*?(\d{1,2}:?\d{0,2})\s*(am|pm)?',
        r'logout.*?(\d{1,2}:?\d{0,2})\s*(am|pm)?.*update'
    ]
    
    for pattern in logout_update_patterns:
        match = re.search(pattern, user_msg.lower())
        if match:
            time_part = match.group(1)
            am_pm = match.group(2) if match.group(2) else ''
            new_logout = f"{time_part} {am_pm}".strip()
            
            success, message = update_logout_time(name, today, new_logout)
            return jsonify({"message": f"🔄 Logout Update Request\n{message}"})
    
    # Check if user is confirming or editing
    if user_msg.lower().strip() in ['yes', 'y', 'correct', 'ok', 'confirm']:
        if 'pending_data' in session:
            return save_to_sheet(session['pending_data'], name, today)
        else:
            return jsonify({"message": "No pending data to save. Please start over."})
    
    if user_msg.lower().strip() in ['no', 'n', 'incorrect', 'edit']:
        return jsonify({
            "message": "What would you like to change? Please specify the field and new value (e.g., 'Login Time: 10:00 AM' or 'Work Log: Updated task description')"
        })
    
    # Handle field edits
    if 'pending_data' in session:
        if ':' in user_msg:
            return handle_field_edit(user_msg, name, today)
        elif not any(keyword in user_msg.lower() for keyword in ['leave', 'wfh', 'wfo', 'login', 'logout', 'am', 'pm']):
            return handle_simple_work_log_edit(user_msg, name, today)
    
    # Process initial message
    leave_keywords = [
        "on leave", "leave today", "taking a day off",
        "day off", "off today", "not working", "will be on leave"
    ]
    
    if any(kw in user_msg.lower() for kw in leave_keywords):
        fields = {
            "Leave": "yes",
            "Work From Home": "-",
            "Work From Office": "-",
            "Login Time": "-",
            "Logout Time": "-",
            "Work Log": "-",
            "Total Hours": "-"
        }
    else:
        # Initialize fields first
        fields = {
            "Leave": "no",
            "Work From Home": "-",
            "Work From Office": "-",
            "Login Time": "-",
            "Logout Time": "-",
            "Work Log": "-",
            "Total Hours": "-"
        }
        
        # Try to get GROQ response with error handling
        try:
            groq_response = extract_with_groq(user_msg)
            if groq_response is None:
                groq_response = ""
        except Exception as e:
            print(f"GROQ API error: {str(e)}")
            groq_response = ""
        
        # Use work location detection (defaults to WFO if no explicit WFH)
        wfh_status, wfo_status = detect_work_location(user_msg, groq_response)
        fields["Work From Home"] = wfh_status
        fields["Work From Office"] = wfo_status
        
        # Process GROQ response if available
        if groq_response and groq_response.strip():
            for line in groq_response.strip().split("\n"):
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == "leave":
                    fields["Leave"] = value.lower()
                elif key == "login time":
                    fields["Login Time"] = determine_am_pm(value, is_login=True)
                elif key == "logout time":
                    fields["Logout Time"] = determine_am_pm(value, is_login=False)
                elif key == "work log":
                    fields["Work Log"] = value
        else:
            # Fallback: manual parsing if GROQ fails
            fields = parse_message_manually(user_msg, fields)
        
        # Handle leave case
        if fields["Leave"] == "yes":
            fields.update({
                "Work From Home": "-",
                "Work From Office": "-",
                "Login Time": "-",
                "Logout Time": "-",
                "Work Log": "-",
                "Total Hours": "-"
            })
        
        # Calculate total hours
        if fields["Login Time"] not in ["-", ""] and fields["Logout Time"] not in ["-", ""]:
            fields["Total Hours"] = calculate_total_hours(fields["Login Time"], fields["Logout Time"])
        
        # Check for missing fields
        missing = []
        if fields["Leave"] == "no":
            if fields["Login Time"] in ["-", "", "not mentioned"]:
                missing.append("Login Time")
            if fields["Logout Time"] in ["-", "", "not mentioned"]:
                missing.append("Logout Time")
            if fields["Work Log"] in ["-", "", "not mentioned"]:
                missing.append("Work Log")
        
        if missing:
            prompt = "Please provide the following missing info: " + ", ".join(missing)
            return jsonify({"message": prompt})
    
    # Store data for confirmation
    session['pending_data'] = fields
    
    # Show confirmation
    formatted = f"""
        <b>Please review your information:</b><br>
        Name: {name}<br>
        Date: {today}<br>
        Leave: {fields['Leave']}<br>
        WFH: {fields['Work From Home']}<br>
        WFO: {fields['Work From Office']}<br>
        Task: {fields['Work Log']}<br>
        Login: {fields['Login Time']}<br>
        Logout: {fields['Logout Time']}<br>
        Total Hours: {fields['Total Hours']}<br>
        <br><b>Is everything correct?</b><br>
        Type 'yes' to save or 'no' to edit.<br>
    """
    
    return jsonify({"message": formatted})

def parse_message_manually(user_msg, fields):
    """
    Manual parsing fallback when GROQ fails
    """
    user_msg_lower = user_msg.lower()
    
    # Extract work description
    if "working on" in user_msg_lower:
        work_match = re.search(r'working on (.+?) from', user_msg_lower)
        if work_match:
            fields["Work Log"] = work_match.group(1).strip()
    
    # Extract time range
    time_patterns = [
        r'from (\d{1,2}):?(\d{0,2})\s*(am|pm)?\s*to\s*(\d{1,2}):?(\d{0,2})\s*(am|pm)?',
        r'(\d{1,2}):?(\d{0,2})\s*(am|pm)?\s*to\s*(\d{1,2}):?(\d{0,2})\s*(am|pm)?',
        r'(\d{1,2})\s*to\s*(\d{1,2})'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, user_msg_lower)
        if match:
            groups = match.groups()
            if len(groups) >= 6:  # Full pattern with from/to
                start_hour = groups[0]
                start_min = groups[1] if groups[1] else "00"
                start_ampm = groups[2] if groups[2] else ""
                end_hour = groups[3]
                end_min = groups[4] if groups[4] else "00"
                end_ampm = groups[5] if groups[5] else ""
                
                start_time = f"{start_hour}:{start_min} {start_ampm}".strip()
                end_time = f"{end_hour}:{end_min} {end_ampm}".strip()
                
                fields["Login Time"] = determine_am_pm(start_time, is_login=True)
                fields["Logout Time"] = determine_am_pm(end_time, is_login=False)
            elif len(groups) >= 2:  # Simple pattern
                start_hour = groups[0]
                end_hour = groups[1]
                
                fields["Login Time"] = determine_am_pm(f"{start_hour}:00", is_login=True)
                fields["Logout Time"] = determine_am_pm(f"{end_hour}:00", is_login=False)
            break
    
    return fields

def detect_work_location(user_msg, groq_response):
    """
    Simple function to detect work location from user message
    Only detects WFH when explicitly mentioned, defaults to WFO otherwise
    """
    user_msg_lower = user_msg.lower()
    
    # WFH indicators - only explicit mentions
    wfh_keywords = [
        'from home', 'work from home', 'wfh', 'remote', 'remotely',
        'home office', 'working from home', 'at home', 'from my home',
        'home today', 'working remotely'
    ]
    
    # WFO indicators  
    wfo_keywords = [
        'from office', 'work from office', 'wfo', 'at office',
        'in office', 'office today', 'working from office',
        'at the office', 'from the office'
    ]
    
    # Check explicit mentions first
    wfh_mentioned = any(keyword in user_msg_lower for keyword in wfh_keywords)
    wfo_mentioned = any(keyword in user_msg_lower for keyword in wfo_keywords)
    
    # If explicitly mentioned, use that
    if wfh_mentioned and not wfo_mentioned:
        return "yes", "no"  # WFH: yes, WFO: no
    elif wfo_mentioned and not wfh_mentioned:
        return "no", "yes"  # WFH: no, WFO: yes
    elif wfh_mentioned and wfo_mentioned:
        # Both mentioned, need clarification - for now default to WFO
        return "no", "yes"
    
    # Check GROQ response for work location
    if groq_response:
        groq_lower = groq_response.lower()
        if 'work from home: yes' in groq_lower or 'work from home:yes' in groq_lower:
            return "yes", "no"
        elif 'work from office: yes' in groq_lower or 'work from office:yes' in groq_lower:
            return "no", "yes"
    
    # Default to WFO if no explicit WFH mention
    return "no", "yes"

def extract_with_groq(message):
    """
    GROQ extraction with simple work location detection
    """
    # Your existing GROQ implementation should include simple prompting
    # Example prompt enhancement:
    prompt = f"""
    Extract the following information from this work log message: "{message}"
    
    Return ONLY in this exact format:
    Leave: [yes/no]
    Work From Home: [yes/no] 
    Work From Office: [yes/no]
    Login Time: [time or not mentioned]
    Logout Time: [time or not mentioned]  
    Work Log: [work description or not mentioned]
    
    Rules:
    - Only set Work From Home: yes if message explicitly mentions "from home", "WFH", "remote", "remotely", "working from home", "at home"
    - Only set Work From Office: yes if message explicitly mentions "from office", "WFO", "at office", "in office", "working from office"
    - If no location is explicitly mentioned, default to Work From Office: yes, Work From Home: no
    - Only one of Work From Home or Work From Office should be "yes"
    - Do NOT use task type (like UI, coding, meeting) to determine work location
    """
    
    # Call your GROQ API with the enhanced prompt
    # return groq_api_call(prompt)
    pass  # Replace with your actual GROQ implementation
def handle_simple_work_log_edit(user_msg, name, today):
    """Handle simple work log edits without field specification"""
    if 'pending_data' not in session:
        return jsonify({"message": "No pending data to edit. Please start over."})
    
    fields = session['pending_data']
    fields['Work Log'] = user_msg
    session['pending_data'] = fields
    
    return show_confirmation(fields, name, today)

def handle_field_edit(user_msg, name, today):
    """Handle editing of specific fields"""
    if 'pending_data' not in session:
        return jsonify({"message": "No pending data to edit. Please start over."})
    
    fields = session['pending_data']
    updated_fields = []
    
    field_updates = [update.strip() for update in user_msg.split(',')]
    
    for update in field_updates:
        if ':' in update:
            try:
                field_name, new_value = update.split(':', 1)
                field_name = field_name.strip().lower()
                new_value = new_value.strip()
                
                field_mapping = {
                    'leave': 'Leave',
                    'work from home': 'Work From Home',
                    'wfh': 'Work From Home',
                    'work from office': 'Work From Office',
                    'wfo': 'Work From Office',
                    'login time': 'Login Time',
                    'login': 'Login Time',
                    'logout time': 'Logout Time',
                    'logout': 'Logout Time',
                    'work log': 'Work Log',
                    'task': 'Work Log',
                    'work': 'Work Log'
                }
                
                if field_name in field_mapping:
                    actual_field = field_mapping[field_name]
                    
                    # Apply smart time parsing for time fields
                    if actual_field == 'Login Time':
                        new_value = determine_am_pm(new_value, is_login=True)
                    elif actual_field == 'Logout Time':
                        new_value = determine_am_pm(new_value, is_login=False)
                    
                    fields[actual_field] = new_value
                    updated_fields.append(actual_field)
            except ValueError:
                continue
    
    # Recalculate total hours if time fields changed
    if any(field in updated_fields for field in ['Login Time', 'Logout Time']):
        if fields["Login Time"] not in ["-", ""] and fields["Logout Time"] not in ["-", ""]:
            fields["Total Hours"] = calculate_total_hours(fields["Login Time"], fields["Logout Time"])
    
    session['pending_data'] = fields
    
    if updated_fields:
        return show_confirmation(fields, name, today, f"Updated: {', '.join(updated_fields)}")
    else:
        return jsonify({"message": "I couldn't understand what you want to change. Please use format 'Field: New Value'"})
# ADD THESE ROUTES TO YOUR FLASK APP

@app.route('/admin/spreadsheet', methods=['GET'])
def get_spreadsheet_data():
    """Get all spreadsheet records for admin view"""
    try:
        # Get all records from the sheet
        records = sheet.get_all_records()
        
        # Sort by date (newest first)
        records.sort(key=lambda x: x.get('Date', ''), reverse=True)
        
        return jsonify({
            "success": True,
            "records": records
        })
    except Exception as e:
        print(f"Error fetching spreadsheet data: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/admin/stats', methods=['GET'])
def get_admin_stats():
    """Get statistics for admin dashboard"""
    try:
        records = sheet.get_all_records()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Calculate stats
        total_entries = len(records)
        today_entries = len([r for r in records if r.get('Date') == today])
        active_users = len(set(r.get('Name', '') for r in records if r.get('Name')))
        
        # Calculate average hours
        total_hours = 0
        valid_entries = 0
        
        for record in records:
            total_hours_str = record.get('Total Hours', '')
            if total_hours_str and total_hours_str != '-':
                try:
                    # Parse hours from "8h 30m" format
                    hours = 0
                    if 'h' in total_hours_str:
                        hours_part = total_hours_str.split('h')[0]
                        hours += int(hours_part)
                    if 'm' in total_hours_str:
                        minutes_part = total_hours_str.split('h')[-1].split('m')[0]
                        if minutes_part.strip():
                            hours += int(minutes_part.strip()) / 60
                    
                    total_hours += hours
                    valid_entries += 1
                except:
                    continue
        
        avg_hours = f"{total_hours/valid_entries:.1f}h" if valid_entries > 0 else "0h"
        
        return jsonify({
            "success": True,
            "totalEntries": total_entries,
            "todayEntries": today_entries,
            "activeUsers": active_users,
            "avgHours": avg_hours
        })
    except Exception as e:
        print(f"Error calculating stats: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Optional: Add admin authentication route for enhanced security
@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Handle admin login with backend validation"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        # You can store these in environment variables or database
        ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
        ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return jsonify({
                "success": True,
                "message": "Admin login successful"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Invalid credentials"
            }), 401
            
    except Exception as e:
        print(f"Admin login error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Login failed"
        }), 500

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Handle admin logout"""
    session.pop('admin_logged_in', None)
    return jsonify({
        "success": True,
        "message": "Admin logout successful"
    })

# Middleware to check admin authentication (optional)
def admin_required(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({
                "success": False,
                "message": "Admin authentication required"
            }), 403
        return f(*args, **kwargs)
    return decorated_function

# You can apply this decorator to admin routes like:
# @admin_required
# def get_spreadsheet_data():
@app.route('/admin/sheet', methods=['GET'])
@admin_required
def admin_sheet():
    """Return all records from the admin_review Google Sheet for admin modal display"""
    try:
        # If you want a specific sheet, change this to open_by_key(...).worksheet('admin_review')
        records = sheet.get_all_records()
        return jsonify({
            "success": True,
            "records": records
        })
    except Exception as e:
        print(f"Error fetching admin sheet: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

def show_confirmation(fields, name, today, extra_msg=""):
    """Show confirmation message"""
    formatted = f"""
        <b>Updated information:</b><br>
        Name: {name}<br>
        Date: {today}<br>
        Leave: {fields['Leave']}<br>
        WFH: {fields['Work From Home']}<br>
        WFO: {fields['Work From Office']}<br>
        Task: {fields['Work Log']}<br>
        Login: {fields['Login Time']}<br>
        Logout: {fields['Logout Time']}<br>
        Total Hours: {fields['Total Hours']}<br>
        {f"<br><i>{extra_msg}</i>" if extra_msg else ""}
        <br><b>Is everything correct now?</b><br>
        Type 'yes' to save or continue editing.
    """
    return jsonify({"message": formatted})

def save_to_sheet(fields, name, today):
    """Save confirmed data to Google Sheets"""
    try:
        row = [
            name,
            today,
            fields["Leave"],
            fields["Work From Home"],
            fields["Work From Office"],
            fields["Work Log"],
            fields["Login Time"],
            fields["Logout Time"],
            fields["Total Hours"]
        ]
        sheet.append_row(row)
        sheet_status = "✅ Data saved to Google Sheets successfully!"
        
        # Clear pending data
        session.pop('pending_data', None)
        
    except Exception as e:
        sheet_status = "❌ Failed to save to Google Sheets"
        print(f"Sheet error: {str(e)}")
    
    formatted = f"""
        <b>Final Saved Data:</b><br>
        Name: {name}<br>
        Date: {today}<br>
        Leave: {fields['Leave']}<br>
        WFH: {fields['Work From Home']}<br>
        WFO: {fields['Work From Office']}<br>
        Task: {fields['Work Log']}<br>
        Login: {fields['Login Time']}<br>
        Logout: {fields['Logout Time']}<br>
        Total Hours: {fields['Total Hours']}<br>
        <br><b>{sheet_status}</b><br>
        <br>Thank you! You can submit a new entry anytime.<br>
    """
    return jsonify({"message": formatted})

@app.route('/admin/dashboard')
def admin_dashboard():
    # Shows only the Google Sheet iframe
    return render_template('admin_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)