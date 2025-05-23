import pandas as pd

# Path to your CSV file
file_path = r'G:\College-Predictor-Tool-PickMyCareer-main\College-Predictor-Tool-PickMyCareer-main\input_2024_cutoff.csv'

# Read the CSV file
df = pd.read_csv(file_path)

# Replace all null values with 0
df.fillna(0, inplace=True)

# Save the updated DataFrame back to the same CSV file
df.to_csv(file_path, index=False)

print("Null values replaced with 0 and file saved successfully.")
