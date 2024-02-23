#!/usr/bin/env python
# coding: utf-8

import argparse
import PyPDF2
import getpass
import re
import pandas as pd
import json

def read_pdf_lines_as_string(pdf_path):
    all_lines = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfFileReader(file)
        
        if reader.isEncrypted:
            password = getpass.getpass("Enter the password for the PDF file: ")
            
            if reader.decrypt(password) != 1:
                raise ValueError("Incorrect password or unable to decrypt PDF.")
        
        num_pages = reader.numPages
        for page_num in range(num_pages):
            page = reader.getPage(page_num)
            text = page.extractText()
            lines = text.split('\n')
            for line in lines:
                if line.strip():
                    all_lines += line.strip() + "\n"
    return all_lines

def starts_with_page_number(text):
    pattern = r'^Page \d+ of'
    return re.match(pattern, text) is not None

def is_uppercase_or_number_with_special_chars(s):
    return all(c.isupper() or c.isdigit() or c.isspace() or c in (',', '&', '(', ')', '*') for c in s)

def parse_expense_data(lst, start_separator, end_separator=None, perform_expense_discrepancy_check=False):
    def get_items_between(lst, start_item, end_item=None):
        found_items = []
        record_items = False
        
        for item in lst:
            if item == start_item:
                record_items = True
                if end_item is None:
                    found_items.append(item)
            elif end_item is not None and item == end_item:
                break
            elif record_items:
                found_items.append(item)
                
        return found_items
    
    def filter_strings(lst, accepted_start_chars):
        filtered_strings = [string for string in lst if string.startswith(tuple(accepted_start_chars))]
        return filtered_strings
    
    def transaction_data_string_to_list(input_string):
        parts = input_string.split()
        date = parts[0]
        string_item = ' '.join(parts[1:-3])
        currency = parts[-3]
        try:
            float1 = float(parts[-2].replace(',', ''))
            float2 = float(parts[-1].replace(',', ''))
        except ValueError:
            if parts[-1].strip() == 'CR':
                float1 = float(parts[-3].replace(',', ''))
                float2 = float(parts[-2].replace(',', '').strip()) * -1

        result_list = [date, string_item, currency, float1, float2]
        return result_list
    
    substring_between_separators = get_items_between(lst, start_separator, end_separator)
    
    accepted_start_chars = ['0', '1', '2', '3']
    
    basic_card_expenses = filter_strings(substring_between_separators, accepted_start_chars)
    
    basic_card_expenses_list = [transaction_data_string_to_list(i) for i in basic_card_expenses]
    
    column_headers = ['transaction_date', 'transaction_description', 'currency', 'transaction_amount', 'billing_amount']
    
    basic_card_transaction_df = pd.DataFrame(basic_card_expenses_list, columns=column_headers)
    
    return basic_card_transaction_df

def main():
    parser = argparse.ArgumentParser(description='Process a bank statement PDF file and save data to Excel, JSON, or CSV.')
    parser.add_argument('pdf_path', type=str, help='Path to the PDF file')
    parser.add_argument('--save', type=str, default='excel', choices=['excel', 'json'], help='Choose raw data save format: excel or json')
    parser.add_argument('--summary_print', type=str, default='n', choices=['y', 'n'], help='Print vendor aggregated expense summary if y')
    parser.add_argument('--summary_save', type=str, default='n', choices=['y', 'n'], help='Save vendor aggregated expense summary as CSV if y')
    args = parser.parse_args()
    
    pdf_path = args.pdf_path
    save_format = args.save
    summary_print = args.summary_print
    summary_save = args.summary_save
    
    lines_string = read_pdf_lines_as_string(pdf_path)
    line_list = lines_string.split('\n')

    excluded_starts = ['-', '*', 
                       'Cash Limit is subject to availability of total Credit Limit.',
                      'originated in Bangladesh etc. with foreign currencies or through your international card, as these type of transactions are strictly prohibited and punishable offences by the directives of Bangladesh Bank and Bangladesh',
                       'Government.'                  
                      ]

    filtered_lines = [line for line in line_list if not any(line.startswith(start) for start in excluded_starts)]
    filtered_lines = [i for i in filtered_lines if not starts_with_page_number(i)]

    separator_strings = [i for i in filtered_lines if is_uppercase_or_number_with_special_chars(i)]
    
    fixed_items = ['PAYMENTS', 'INTERESTS, FEES & VAT', 'REFUND, REVERSAL & CREDITS']
    variable_item_start = ['BASIC CARD', 'SUPPLEMENTARY CARD']

    ideal_separators = [item for item in separator_strings if any(item.startswith(start) for start in variable_item_start) or item in fixed_items]

    fees_df = parse_expense_data(filtered_lines, ideal_separators[1], ideal_separators[2], perform_expense_discrepancy_check=False)
    refund_df = parse_expense_data(filtered_lines, ideal_separators[2], ideal_separators[3], perform_expense_discrepancy_check=False)
    basic_card_expenses = parse_expense_data(filtered_lines, ideal_separators[3], ideal_separators[4], perform_expense_discrepancy_check=True)
    supplementary_card_expenses = parse_expense_data(filtered_lines, ideal_separators[4],  perform_expense_discrepancy_check=True)
    
    basic_card_expenses['transaction_origin'] = 'basic'
    supplementary_card_expenses['transaction_origin'] = 'supplementary'
    
    if summary_print == 'y':
        expense_df = pd.concat([basic_card_expenses, supplementary_card_expenses], ignore_index=True)
        summary = expense_df.groupby(by='transaction_description')['transaction_amount'].sum().sort_values(ascending=False)
        print(summary)
    
    if summary_save == 'y':
        summary_filename = pdf_path.replace('.pdf', '_expense_summary.csv')
        summary_df = pd.concat([basic_card_expenses, supplementary_card_expenses], ignore_index=True)
        summary_df.groupby(by='transaction_description')['transaction_amount'].sum().sort_values(ascending=False).to_csv(summary_filename, sep=',', index=True)
    
    if save_format == 'excel':
        excel_filename = pdf_path.replace('.pdf', '.xlsx')
        with pd.ExcelWriter(excel_filename) as writer:
            basic_card_expenses.to_excel(writer, sheet_name='Basic Card Expenses', index=False)
            supplementary_card_expenses.to_excel(writer, sheet_name='Supplementary Card Expenses', index=False)
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

if __name__ == "__main__":
    main()
