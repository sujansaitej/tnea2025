import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key("1x37iFC4Qg1l-voMcrxT5v71TxT9EXEoYIGIRy7RFU_k")
worksheet = spreadsheet.worksheet("2025_data")

worksheet.append_row(["Test", "1234567890", "CSE", "OC", 199.0])

print("✅ Successfully wrote to the sheet.")
