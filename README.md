**Scripts:**
- `parse_brac_bank_cc_statement.py` - Extract & transform BRAC Bank Credit Card Statement data.
- `run_py-scripts_on_pdfs.bat` - Batch script to process all PDF statements. _Current implementation works with only un-encrypted files._
- `load_plot.py` - Loads summary data and plots monthly vendor aggregated pie charts. You can specify the number of pie slices to be plotted for each of the monthly aggregated data.

**Features:**
* Reads PDF statement. PDF has to be unencrypted. Statements are available at the Astha app or BRAC Bank internet banking site.
* Can save basic card data, supplementary card data, refund data and fee data as excel or json file, as/if specified.
* Can save vendor aggregated summary data as a CSV file if requested via flag.
* Can print (in terminal) vendor aggregated summary data if requested via flag.

**Usage:**

```
parse_brac_bank_cc_statement.py [-h] [--save {excel,json}] [--summary_print {y,n}] [--summary_save {y,n}]
                                       pdf_path

Process a bank statement PDF file and save data to Excel, JSON, or CSV.

positional arguments:
  pdf_path              Path to the PDF file

options:
  -h, --help            show this help message and exit
  --save {excel,json}   Choose raw data save format: excel or json
  --summary_print {y,n}
                        Print vendor aggregated expense summary if y
  --summary_save {y,n}  Save vendor aggregated expense summary as CSV if y
```

**Features to implement**
* Does not work with password protected statements (that are received as emails from the bank).

**Running script on all PDF statements (using Windows batch script)**
- Put the bat file in the same folder as the python script and all pdf files.
- Modify the bat file - provide your own conda environment that can works with the script.

