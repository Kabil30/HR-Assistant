# import os
# import requests

# def extract_with_groq(user_message):
#     api_key = os.getenv("GROQ_API_KEY")
#     endpoint = "https://api.groq.com/openai/v1/chat/completions"

#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Content-Type": "application/json"
#     }

#     system_prompt = (
#         "You are a strict structured data assistant. Extract exactly these 6 fields from the user's message:\n"
#         "Leave: yes/no\n"
#         "Work From Home: yes/no/-\n"
#         "Work From Office: yes/no/-\n"
#         "Login Time: e.g. 9:00am or '-'\n"
#         "Logout Time: e.g. 5:00pm or '-'\n"
#         "Work Log: short summary or '-'\n\n"
#         "RULES:\n"
#         "1. If the user says they are on leave (e.g. 'I'm on leave', 'leave today', 'taking a day off'), set Leave=yes and ALL other fields = '-'\n"
#         "2. If user is NOT on leave, extract the rest as applicable. If WFH or WFO is not mentioned, return '-' for both.\n"
#         "3. Always respond using the exact format below:\n\n"
#         "Leave: ...\nWork From Home: ...\nWork From Office: ...\nLogin Time: ...\nLogout Time: ...\nWork Log: ...\n\n"

#         "Examples:\n"
#         "User: I'm on leave today\n"
#         "Output:\nLeave: yes\nWork From Home: -\nWork From Office: -\nLogin Time: -\nLogout Time: -\nWork Log: -\n\n"

#         "User: I will be working from home. Logged in at 10 and out by 5:30. Worked on chat bot.\n"
#         "Output:\nLeave: no\nWork From Home: yes\nWork From Office: no\nLogin Time: 10:00am\nLogout Time: 5:30pm\nWork Log: Worked on chat bot"
#     )



#     payload = {
#         "model": "llama3-70b-8192",
#         "messages": [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_message}
#         ]
#     }

#     response = requests.post(endpoint, headers=headers, json=payload)
#     result = response.json()

#     if 'choices' in result:
#         return result['choices'][0]['message']['content']
#     return "ERROR: Could not get response from Groq"

import os
import requests

def extract_with_groq(user_message):
    api_key = os.getenv("GROQ_API_KEY")
    endpoint = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    system_prompt = """
        You are an expert assistant that extracts 6 fields from any user's message.

        You MUST always return:
        Leave: yes/no
        Work From Home: yes/no/-
        Work From Office: yes/no/-
        Login Time: HH:MM AM/PM or '-'
        Logout Time: HH:MM AM/PM or '-'
        Work Log: short sentence or '-'

        ### INSTRUCTIONS:
        1. If user says anything like "leave today", "on leave", "off today", "day off", etc:
        → Leave = yes, all other fields = '-'

        2. Otherwise, Leave = no. Extract other values if present.

        3. WFH and WFO must be yes/no or '-', never empty.

        4. Respond with exactly the 6 lines. No extra explanation.

        ### Examples:

        Message: I'm on leave today
        Leave: yes
        Work From Home: -
        Work From Office: -
        Login Time: -
        Logout Time: -
        Work Log: -

        Message: Taking a day off
        Leave: yes
        Work From Home: -
        Work From Office: -
        Login Time: -
        Logout Time: -
        Work Log: -

        Message: Working from home, login 9am, logout 5:30, fixed bugs
        Leave: no
        Work From Home: yes
        Work From Office: no
        Login Time: 9:00 AM
        Logout Time: 5:30 PM
        Work Log: Fixed bugs

        Message: I will work from office, login 10am, logout 6pm, reviewed code
        Leave: no
        Work From Home: no
        Work From Office: yes
        Login Time: 10:00 AM
        Logout Time: 6:00 PM
        Work Log: Reviewed code
        """


    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    response = requests.post(endpoint, headers=headers, json=payload)

    try:
        result = response.json()
        if 'choices' in result:
            return result['choices'][0]['message']['content']
        return "ERROR: Could not extract response"
    except Exception as e:
        print("❌ Groq API Error:", str(e))
        return "ERROR: Groq API call failed"
