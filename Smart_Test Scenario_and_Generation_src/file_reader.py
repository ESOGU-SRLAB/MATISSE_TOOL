""" This module contains functions to read different types of files. """

import io
import docx
import pandas as pd

# Function to read a text file
def read_txt(file):
    """Read the text file."""
    file_content = file.read().decode('utf-8')
    return file_content

# Function to read a docx file
def read_docx(file):
    """Using python-docx to read the docx file."""
    doc = docx.Document(io.BytesIO(file.read()))
    doc_content = "\n".join([para.text for para in doc.paragraphs])
    return doc_content

# Function to read an xlsx file
def read_xlsx(file):
    """Using pandas to read the excel file."""
    df = pd.read_excel(io.BytesIO(file.read()))
    return df

# Function to read a csv file
def read_python(file):
    """Read the Python (.py) file."""
    file_content = file.read().decode('utf-8')
    return file_content
