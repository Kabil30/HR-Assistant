# # import spacy
# # import re

# # nlp = spacy.load("en_core_web_sm")

# # def extract_structured_info(name, message):
# #     doc = nlp(message.lower())

# #     leave = "no" if "no leave" in message.lower() or "leave: no" in message.lower() else "yes" if "leave" in message.lower() else "not mentioned"
# #     wfh = "yes" if "work from home" in message.lower() or "wfh: yes" in message.lower() else "no" if "wfh: no" in message.lower() else "not mentioned"

# #     login_match = re.search(r'login[:\- ]?(\d{1,2}[:.]?\d{0,2})', message, re.IGNORECASE)
# #     logout_match = re.search(r'logout[:\- ]?(\d{1,2}[:.]?\d{0,2})', message, re.IGNORECASE)
# #     login = login_match.group(1).replace('.', ':') if login_match else "not found"
# #     logout = logout_match.group(1).replace('.', ':') if logout_match else "not found"

# #     work_match = re.search(r'work[:\- ]?(.*)', message, re.IGNORECASE)
# #     work_log = work_match.group(1).strip() if work_match else "not mentioned"

# #     return f"""
# #     **Here is the extracted info:**  
# #     - **Name:** {name}  
# #     - **Leave:** {leave}  
# #     - **Work From Home:** {wfh}  
# #     - **Login Time:** {login}  
# #     - **Logout Time:** {logout}  
# #     - **Work Log:** {work_log}
# #     """
# import re

# def extract_structured_info(user_input: str):
#     info = {
#         "Leave": "no",
#         "Work From Home": "no",
#         "Login Time": "-",
#         "Logout Time": "-",
#         "Work Log": "-"
#     }

#     # Leave check
#     if re.search(r"\bleave\b", user_input, re.IGNORECASE):
#         if "no leave" in user_input.lower() or "not on leave" in user_input.lower():
#             info["Leave"] = "no"
#         else:
#             info["Leave"] = "yes"

#     # WFH check
#     if "work from home" in user_input.lower():
#         if "not working from home" in user_input.lower() or "no work from home" in user_input.lower():
#             info["Work From Home"] = "no"
#         else:
#             info["Work From Home"] = "yes"

#     # Login/logout extraction
#     login_match = re.search(r"log(?:ged)? in at\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", user_input, re.IGNORECASE)
#     logout_match = re.search(r"log(?:ged)? out at\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", user_input, re.IGNORECASE)

#     if login_match:
#         info["Login Time"] = login_match.group(1)
#     if logout_match:
#         info["Logout Time"] = logout_match.group(1)

#     # Work Log - remove time/wfh/leave statements
#     work_log = re.sub(r"(?i)log(?:ged)? (in|out) at.*?(?:\.|$)", "", user_input)
#     work_log = re.sub(r"(?i)(no )?leave( today)?", "", work_log)
#     work_log = re.sub(r"(?i)(not )?working from home", "", work_log)

#     info["Work Log"] = work_log.strip().strip('.')

#     return info
import re

def extract_structured_info(user_input: str):
    info = {
        "Leave": "not mentioned",
        "Work From Home": "not mentioned",
        "Login Time": "-",
        "Logout Time": "-",
        "Work Log": "-"
    }

    user_input = user_input.lower()

    # Leave
    if "no leave" in user_input or "not on leave" in user_input:
        info["Leave"] = "no"
    elif "leave" in user_input:
        info["Leave"] = "yes"

    # WFH
    if "not working from home" in user_input or "no work from home" in user_input:
        info["Work From Home"] = "no"
    elif "work from home" in user_input or "wfh" in user_input:
        info["Work From Home"] = "yes"

    # Login Time
    login_match = re.search(r"log(?:ged)? in at\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", user_input)
    if login_match:
        info["Login Time"] = login_match.group(1)

    # Logout Time
    logout_match = re.search(r"log(?:ged)? out at\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", user_input)
    if logout_match:
        info["Logout Time"] = logout_match.group(1)

    # Work Log
    work_log = re.sub(r"log(?:ged)? (in|out) at.*?(?:\.|$)", "", user_input)
    work_log = re.sub(r"(no )?leave( today)?", "", work_log)
    work_log = re.sub(r"(not )?working from home", "", work_log)
    info["Work Log"] = work_log.strip().strip('.')

    return info
