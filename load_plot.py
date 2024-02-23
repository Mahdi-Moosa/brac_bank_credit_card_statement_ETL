import argparse
import pandas as pd
import glob
import os
import re
from fuzzywuzzy import process
import warnings
import calendar
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def load_expense_files(folder_path=None):
    """
    Load expense files from a specified folder path or the current folder.
    
    Args:
        folder_path (str, optional): Path to the folder containing expense files. Defaults to None.
    
    Returns:
        pandas.DataFrame: Combined DataFrame of all loaded expense files.
    """
    if folder_path is None:
        folder_path = '.'  # Default to current folder if no folder_path provided

    # Create an empty list to store all the DataFrames
    all_data = []

    # Get a list of all files ending with _expense_summary.csv in the folder_path
    file_list = glob.glob(os.path.join(folder_path, '*_expense_summary.csv'))

    # Regular expression pattern to match month followed by an apostrophe and the year
    pattern = r'([a-zA-Z]+)\'(\d{2})'

    # List of month names
    month_names = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    # Iterate through each file
    for file_path in file_list:
        # Extract month and year information from the file name using regular expression
        match = re.search(pattern, file_path)
        if match:
            month_str = match.group(1)
            year_str = match.group(2)
            month_year_str = month_str + ' ' + year_str
            
            # Assuming years 00-49 correspond to 2000-2049 and years 50-99 correspond to 1950-1999
            year = int(year_str)
            if year < 50:
                year = 2000 + year
            else:
                year = 1900 + year
            
            # Fuzzy match the month string to get the closest match from a list of month names
            closest_match = process.extractOne(month_str, month_names)[0]
            
            # Construct the month_year datetime object
            month_number = month_names.index(closest_match) + 1
            month_year = pd.Timestamp(year, month_number, 1) + pd.offsets.MonthEnd(0)
        else:
            print(f"No valid month-year found in file name: {file_path}")
            continue

        # Read the CSV file into a DataFrame with error handling
        try:
            df = pd.read_csv(file_path)
            if len(df) == 0:
                warnings.warn(f"DataFrame from {file_path} has 0 rows.", Warning)
                continue  # Skip appending empty DataFrame
        except FileNotFoundError:
            warnings.warn(f"File {file_path} not found.", Warning)
            continue  # Skip this file
        
        # Add a new column with the month-year information as datetime object
        df['Month_Year'] = month_year
        
        # Append the DataFrame to the all_data list
        all_data.append(df)

    # Concatenate all DataFrames in the list into one DataFrame
    combined_df = pd.concat(all_data, ignore_index=True)
    
    return combined_df

def plot_top_transactions_pie(df, num_top_entries, show_plot=False):
    """
    Plot pie charts for the top transactions for each month.

    Args:
        df (pandas.DataFrame): DataFrame containing transaction data.
        num_top_entries (int): Number of top transactions to include in the pie chart.
        show_plot (bool, optional): Whether to show the plot. Defaults to False.
    """
    # Sorting DataFrame by Month_Year and transaction_amount
    combined_data_sorted = df.sort_values(by=['Month_Year', 'transaction_amount'], ascending=[True, False])

    # Grouping by Month_Year and selecting top transactions
    top_transactions = combined_data_sorted.groupby('Month_Year').head(num_top_entries)

    # Calculate total monthly amount for each month
    total_amounts = df.groupby('Month_Year')['transaction_amount'].sum()

    # Create a PDF object
    pdf_pages = PdfPages(f'pie_charts_combined_{num_top_entries}_top_entries.pdf')

    # Plotting pie charts for each Month_Year
    for month_year, group_data in top_transactions.groupby('Month_Year'):
        total_monthly_amount = total_amounts[month_year]

        # Extract month and year from the timestamp
        month_name = calendar.month_name[month_year.month]
        year = month_year.year

        plt.figure(figsize=(8, 6))  # Adjust figure size as needed
        plt.title(f"Distribution of Top {num_top_entries} Transaction Amounts for {month_name}, {year}\nTotal Monthly Amount: {total_monthly_amount} BDT", pad=20)  # Increase padding

        # Customizing the pie chart style
        explode = [0.1] * len(group_data)  # To explode the slices
        colors = sns.color_palette('pastel')  # Using Seaborn color palette
        plt.pie(group_data['transaction_amount'], labels=[f"{desc}\nBDT {amount}" for desc, amount in zip(group_data['transaction_description'], group_data['transaction_amount'])], autopct='%1.1f%%', explode=explode, colors=colors, shadow=True)

        # Save the current figure to the PDF
        pdf_pages.savefig(bbox_inches='tight')  # Adjust the bounding box to fit the content

        # Display the figure if show_plot is True
        if show_plot:
            plt.subplots_adjust(top=0.8)  # Increase the space between title and figure
            plt.show()

    # Close the PDF object
    pdf_pages.close()

def main():
    parser = argparse.ArgumentParser(description="Plot top transactions pie charts")
    parser.add_argument("-p", "--path", type=str, default='.', help="Path to the folder containing expense files")
    parser.add_argument("-n", "--num_entries", type=int, default=5, help="Number of top transactions to include in the pie chart")
    parser.add_argument("-s", "--show_plot", action="store_true", help="Flag to show the plot")
    args = parser.parse_args()

    folder_path = args.path
    num_top_entries = args.num_entries
    show_plot = args.show_plot

    combined_df = load_expense_files(folder_path)
    print(combined_df)

    plot_top_transactions_pie(combined_df, num_top_entries, show_plot)

if __name__ == "__main__":
    main()
