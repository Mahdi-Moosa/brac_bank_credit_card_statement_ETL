#!/usr/bin/env python
# coding: utf-8

# Import necessary libraries
import argparse  # For parsing command-line arguments
import PyPDF2    # For working with PDF files
import getpass   # For getting password input securely
import re        # For regular expressions
import pandas as pd  # For data manipulation and analysis
import json      # For working with JSON data

# Function to read the content of a PDF file and return as a string
def read_pdf_lines_as_string(pdf_path):
    all_lines = ""  # Initialize an empty string to store all lines
    with open(pdf_path, 'rb') as file:  # Open the PDF file in binary mode
        reader = PyPDF2.PdfFileReader(file)  # Create a PDF reader object
        
        # Check if the PDF file is encrypted
        if reader.isEncrypted:
            # If encrypted, prompt the user to enter the password
            password = getpass.getpass("Enter the password for the PDF file: ")
            
            # Attempt to decrypt the PDF file with the provided password
            if reader.decrypt(password) != 1:
                raise ValueError("Incorrect password or unable to decrypt PDF.")
        
        # Get the total number of pages in the PDF
        num_pages = reader.numPages
        
        # Iterate through each page of the PDF
        for page_num in range(num_pages):
            # Extract text from the current page
            page = reader.getPage(page_num)
            text = page.extractText()
            
            # Split the text into lines and iterate through each line
            lines = text.split('\n')
            for line in lines:
                # If the line is not empty, add it to the string of all lines
                if line.strip():
                    all_lines += line.strip() + "\n"
    # Return the string containing all lines from the PDF
    return all_lines

# Function to check if a string starts with the pattern 'Page [number] of'
def starts_with_page_number(text):
    pattern = r'^Page \d+ of'  # Define the regular expression pattern
    return re.match(pattern, text) is not None  # Return True if pattern matches, else False

# Function to check if a string contains only uppercase letters, numbers, and certain special characters
def is_uppercase_or_number_with_special_chars(s):
    return all(c.isupper() or c.isdigit() or c.isspace() or c in (',', '&', '(', ')', '*') for c in s)

# Function to parse expense data from a list of strings within specified separators
def parse_expense_data(lst, start_separator, end_separator=None, perform_expense_discrepancy_check=False):
    # Define a nested function to get items between start and end separators
    def get_items_between(lst, start_item, end_item=None):
        found_items = []  # Initialize an empty list to store found items
        record_items = False  # Flag to start recording items
        
        # Iterate through each item in the list
        for item in lst:
            if item == start_item:  # Check if item matches start separator
                record_items = True  # Start recording items
                if end_item is None:
                    found_items.append(item)  # Add the item to the found items list
            elif end_item is not None and item == end_item:  # Check if item matches end separator
                break  # Stop recording items
            elif record_items:  # If recording items is enabled
                found_items.append(item)  # Add the item to the found items list
        
        return found_items  # Return the list of found items
    
    # Define a nested function to filter strings based on whether they start with a date in the format DD-MM-YYYY
    def filter_date_strings(lst):
        filtered_strings = []
        date_pattern = r'\b\d{2}-\d{2}-\d{4}\b'  # Regular expression pattern for DD-MM-YYYY format date
        
        for string in lst:
            if re.match(date_pattern, string):
                filtered_strings.append(string)
                
        return filtered_strings
    
    # Define a nested function to convert transaction data string to list format
    def transaction_data_string_to_list(input_string):
        parts = input_string.split()  # Split the input string into parts
        date = parts[0]  # Extract transaction date
        
        
        try:
            float1 = float(parts[-2].replace(',', ''))  # Extract transaction amount
            float2 = float(parts[-1].replace(',', ''))  # Extract billing amount
            currency = parts[-3]  # Extract currency
            string_item = ' '.join(parts[1:-3])  # Extract transaction description
        except ValueError:
            if parts[-1].strip() == 'CR':
                float1 = float(parts[-3].replace(',', ''))  # Extract transaction amount
                float2 = float(parts[-2].replace(',', '').strip()) * -1  # Extract billing amount
                currency = parts[-4]  # Extract currency
                string_item = ' '.join(parts[1:-4])  # Extract transaction description

        # Create a list containing transaction data
        result_list = [date, string_item, currency, float1, float2]
        return result_list
    
    # Get substring between specified separators
    substring_between_separators = get_items_between(lst, start_separator, end_separator)
    
    # Filter strings based on whether they start with a date in the format DD-MM-YYYY
    basic_card_expenses = filter_date_strings(substring_between_separators)
    
    # Convert filtered strings to list format
    basic_card_expenses_list = [transaction_data_string_to_list(i) for i in basic_card_expenses]
    
    # Define column headers for the DataFrame
    column_headers = ['transaction_date', 'transaction_description', 'currency', 'transaction_amount', 'billing_amount']
    
    # Create a DataFrame from the list of transaction data
    basic_card_transaction_df = pd.DataFrame(basic_card_expenses_list, columns=column_headers)
    
    return basic_card_transaction_df  # Return the DataFrame containing parsed data

# Main function to handle command-line arguments and execute the script
def main():
    parser = argparse.ArgumentParser(
        description='Process a bank statement PDF file and save data to Excel, JSON, or CSV.')
    parser.add_argument('pdf_path', type=str,
                        help='Path to the PDF file')
    parser.add_argument('--save', type=str, default='excel',
                        choices=['no', 'excel', 'json', 'yes'], help='Choose raw data save format: excel, json, or specify "no" to not save data. If "yes" is provided, default to saving in Excel format.')
    parser.add_argument('--summary_print', type=str, default='n',
                        choices=['y', 'n'], help='Print vendor aggregated expense summary if y')
    parser.add_argument('--summary_save', type=str, default='n',
                        choices=['y', 'n'], help='Save vendor aggregated expense summary as CSV if y')

    args = parser.parse_args()

    pdf_path = args.pdf_path
    save_format = args.save
    summary_print = args.summary_print
    summary_save = args.summary_save

    if save_format == 'yes':
        # Default to Excel format if --save is set to 'yes'
        save_format = 'excel'

    lines_string = read_pdf_lines_as_string(pdf_path)
    line_list = lines_string.split('\n')

    excluded_starts = ['-', '*', 'Cash Limit is subject to availability of total Credit Limit.',
                      'originated in Bangladesh etc. with foreign currencies or through your international card, as these type of transactions are strictly prohibited and punishable offences by the directives of Bangladesh Bank and Bangladesh',
                      'Government.']
    filtered_lines = [line for line in line_list if not any(
        line.startswith(start) for start in excluded_starts)]
    filtered_lines = [i for i in filtered_lines if not starts_with_page_number(
        i)]

    separator_strings = [i for i in filtered_lines if is_uppercase_or_number_with_special_chars(
        i)]

    fixed_items = ['PAYMENTS', 'INTERESTS, FEES & VAT',
                   'REFUND, REVERSAL & CREDITS']
    variable_item_start = ['BASIC CARD', 'SUPPLEMENTARY CARD']
    ideal_separators = [item for item in separator_strings if any(
        item.startswith(start) for start in variable_item_start) or item in fixed_items]

    fees_df = parse_expense_data(
        filtered_lines, ideal_separators[1], ideal_separators[2], perform_expense_discrepancy_check=False)
    refund_df = parse_expense_data(
        filtered_lines, ideal_separators[2], ideal_separators[3], perform_expense_discrepancy_check=False)
    basic_card_expenses = parse_expense_data(
        filtered_lines, ideal_separators[3], ideal_separators[4], perform_expense_discrepancy_check=True)
    supplementary_card_expenses = parse_expense_data(
        filtered_lines, ideal_separators[4], perform_expense_discrepancy_check=True)

    basic_card_expenses['transaction_origin'] = 'basic'
    supplementary_card_expenses['transaction_origin'] = 'supplementary'

    if summary_print == 'y':
        expense_df = pd.concat(
            [basic_card_expenses, supplementary_card_expenses], ignore_index=True)
        summary = expense_df.groupby(
            by='transaction_description')['transaction_amount'].sum().sort_values(ascending=False)
        print(summary)

    if summary_save == 'y':
        summary_filename = pdf_path.replace(
            '.pdf', '_expense_summary.csv')
        summary_df = pd.concat(
            [basic_card_expenses, supplementary_card_expenses], ignore_index=True)
        summary_df.groupby(by='transaction_description')[
            'transaction_amount'].sum().sort_values(ascending=False).to_csv(summary_filename, sep=',', index=True)

    if save_format == 'no':
        print("No output will be provided. Data will not be saved.")
        return

    if save_format == 'excel':
        excel_filename = pdf_path.replace('.pdf', '.xlsx')
        with pd.ExcelWriter(excel_filename) as writer:
            basic_card_expenses.to_excel(
                writer, sheet_name='Basic Card Expenses', index=False)
            supplementary_card_expenses.to_excel(
                writer, sheet_name='Supplementary Card Expenses', index=False)
            refund_df.to_excel(writer, sheet_name='Refund Data', index=False)
            fees_df.to_excel(writer, sheet_name='Fees Data', index=False)
    elif save_format == 'json':
        json_filename = pdf_path.replace('.pdf', '.json')
        data_dict = {
            'Basic Card Expenses': basic_card_expenses.to_dict(orient='records'),
            'Supplementary Card Expenses': supplementary_card_expenses.to_dict(orient='records'),
            'Refund Data': refund_df.to_dict(orient='records'),
            'Fees Data': fees_df.to_dict(orient='records')
        }
        with open(json_filename, 'w') as json_file:
            json.dump(data_dict, json_file, indent=4)

# Execute main function if the script is run as the main program
if __name__ == "__main__":
    main()
