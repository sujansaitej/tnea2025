import gspread

gc         = gspread.service_account("credentials.json")  # <- no scopes needed
spreadsheet = gc.open_by_key("1x37iFC4Qg1l-voMcrxT5v71TxT9EXEoYIGIRy7RFU_k")
worksheet   = spreadsheet.worksheet("2025_data")
worksheet.append_row(["Test", "1234567890", "CSE", "OC", 199.0])
print("✅  Row written!")
