@echo off

rem Activate the desired Conda environment
call conda activate table_extract

rem Get the current directory and set it as the folder path
set "folder_path=%cd%"

rem Initialize counter for total number of files processed
set "total_files_processed=0"

rem Initialize variable to store names of processed files
set "processed_files="

rem Iterate over PDF files in the folder that match the specified pattern
for %%I in ("%folder_path%\BRAC*.pdf") do (
    echo Processing file: %%~nxI
    python parse_brac_bank_cc_statement.py "%%I" --summary_save y --summary_print y --save json

    rem Increment total number of files processed
    set /a total_files_processed+=1
)

rem Print total number of files processed
echo Total number of files processed: %total_files_processed%

rem Deactivate the Conda environment after script execution (optional)
call conda deactivate


