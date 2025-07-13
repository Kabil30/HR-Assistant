Conversational AI Work Logger using Flask, Google Sheets, and NLP
This is an AI-powered, single-page web application designed to simplify daily work logging and streamline admin review. It features a natural language interface that lets employees report their work conversationally, with structured data automatically extracted using AI. Built with Flask and integrated with Google Sheets, the system provides a smart, secure, and efficient solution for logging and managing employee activity.

What Makes It AI-Powered
Instead of traditional forms, users describe their daily work in natural language. The backend uses AI models (e.g., LLMs like Groq or OpenAI-compatible models) to intelligently extract:

Employee Name

Date

Leave / WFH / WFO Status

Work Log

Login and Logout Time

Total Hours Worked

This allows fast and intuitive work reporting with minimal user effort.

Features
Conversational Work Logging
Employees log their tasks, hours, and status via a chat-style interface that accepts natural language input.

AI-Powered Data Extraction
User messages are processed by an AI model to extract structured fields automatically, reducing the need for manual input.

Google Sheets Integration
All logs are stored in a Google Sheet, making the data easily accessible for analysis, backup, or export.

Secure Admin Panel
Admins can log in through a secure modal dialog to view submitted logs and access the live Google Sheet directly.

Single-Page App
All functionality—chat, admin login, and sheet view—runs seamlessly without page reloads, improving user experience.

Session-Based Authentication
Flask sessions protect admin routes and ensure secure access to sensitive data.

Tech Stack
Frontend: HTML, CSS, JavaScript

Backend: Python (Flask)

AI/NLP: LLMs via Groq or OpenAI-compatible API

Data Storage: Google Sheets API

Authentication: Flask Sessions

Use Cases
Remote or hybrid team work tracking

AI-driven internal HR reporting

Conversational timesheet automation

Daily check-ins for employees

Work-from-home attendance logging

Getting Started (Optional Section)
If you'd like to include setup instructions later, here’s a placeholder:

Clone the repo

Set up your Flask environment

Configure Google Sheets API

Add your AI model API key

Run the server and open in browser

