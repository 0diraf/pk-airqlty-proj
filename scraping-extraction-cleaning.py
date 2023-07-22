import pandas as pd
import numpy as np
import os
import fitz
import io
from PIL import Image
import copy
import re
import requests
from lxml import html
import camelot
import tabula
from PyPDF2 import PdfReader



url = "https://environment.gov.pk/Detail/ZjU5NDM3YjItNTdiOS00NTk5LWExYzUtMjI2NzE5YjdlOGM5"

w_page = requests.get(url)


links = html.fromstring(w_page.content)

links = links.xpath('//a/@href')

extract_ext = ".pdf"




cleaned_links = []

for link in links:
    if extract_ext in link:
        if link not in cleaned_links:
            cleaned_links.append(link)


filter_string_list = ["2018", "May2019", "May23"] 

filtered_links = copy.deepcopy(cleaned_links)

for f in filter_string_list:
    for link in cleaned_links:
        if f in link:
            filtered_links.remove(link)


epa = "https://environment.gov.pk"

for l in filtered_links:
    
    file_name = re.search('([^\/]+)\.pdf$', l)
    
    file_name = file_name.group(0)
    
    file_url = epa + l
    
    
    d_file = requests.get(file_url)
    
    open('{}'.format(file_name), 'wb').write(d_file.content)


files = os.listdir()

files = [file for file in files if ".pdf" in file]


tablefiles = []
imgfiles = []

for f in files:
    
    pdf = fitz.open(f)

    page = pdf[0]

    images = page.get_images(full=True)
    
    if images == []:
        tablefiles.append(f)
    else:
        imgfiles.append(f)


output_dir = "extracted_images"
output_frmt = "png"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)


image_names = []

for i in imgfiles:    
    pdf = fitz.open(i)
    name = i.replace(".pdf","")
    image_names.append(name)

    page = pdf[0]

    images = page.get_images(full=True)

    xref = images[0][0]
    
    base_image = pdf.extract_image(xref)
    image_bytes = base_image["image"]

    image = Image.open(io.BytesIO(image_bytes))
    image.save(open(os.path.join(output_dir, "{}.png".format(name)), "wb"), format=output_frmt.upper())


from img2table.document import Image

from img2table.ocr import VisionOCR

ocr = VisionOCR(api_key="", timeout=15)             # Google Cloud Vision API key

for i in image_names:
    
    extracted_img = Image("extracted_images\\{}.png".format(i))
    # Table extraction
    extracted_img.to_xlsx(dest="{}.xlsx".format(i),
                ocr=ocr,
                implicit_rows=False,
                borderless_tables=False,
                min_confidence=50)


table_dfs_list = []

readable_files = []

incorrectly_read_files = []

somewhat_readable = []

for tf in tablefiles:
    
    year = re.search("[0-9]+", tf)
    year = year.group(0)
    
    df_list = tabula.read_pdf(tf, pages=1, pandas_options = {"header":None})
    table_df = df_list[0]
    
    if len(table_df.columns.values) < 6:
        incorrectly_read_files.append(tf)
    elif len(table_df.columns.values) > 6:
        somewhat_readable.append(tf)
    else:
        readable_files.append(tf)
        table_df['Year'] = year
        table_dfs_list.append(table_df)


col_names = ["Date", "Temperature", "Humidity", "NO2", "SO2", "PM2.5", "Year"]

cleaned_cr = []

for df in table_dfs_list:
    if pd.isnull(df[0][0]):
        cleaned_df = df.drop(0)
        if df[0][1]=="Date":
            cleaned_df = cleaned_df.drop(1)
        if "NEQS" in df[0][2]:
            cleaned_df = cleaned_df.drop(2)
        ext_month = cleaned_df.iloc[7, 0]
        month = re.search("[A-Za-z]+", ext_month)
        month = month.group(0)
        
        while 1:
            if month not in cleaned_df.iloc[-1, 0]:
                cleaned_df = cleaned_df[:-1]
            else:
                break

        cleaned_df.reset_index(drop=True, inplace=True)
        cleaned_df.columns = col_names
        cleaned_cr.append(cleaned_df)
    else:
        if df[0][0] == "Date":
            cleaned_df = df.drop(0)
            if "NEQS" in df[0][1]:
                cleaned_df = cleaned_df.drop(1)
            if "Value" in df[0][2]:
                cleaned_df = cleaned_df.drop(2)
            ext_month = cleaned_df.iloc[5, 0]
            month = re.search("[A-Za-z]+", ext_month)
            month = month.group(0)
            cleaned_df = cleaned_df[:-1]
            while 1:
                if month not in cleaned_df.iloc[-1, 0]:
                    cleaned_df = cleaned_df[:-1]
                else:
                    break
            cleaned_df.reset_index(drop=True, inplace=True)
            cleaned_df.columns = col_names
            cleaned_cr.append(cleaned_df)
        else:
            cleaned_df = df
            cleaned_df.iloc[0,2] = cleaned_df[0][0]
            cleaned_df = cleaned_df.drop([0, 1])
            ext_month = cleaned_df.iloc[5, 0]
            month = re.search("[A-Za-z]+", ext_month)
            month = month.group(0)
            cleaned_df = cleaned_df[:-1]
            while 1:
                if month not in cleaned_df.iloc[-1, 0]:
                    cleaned_df = cleaned_df[:-1]
                else:
                    break
            cleaned_df.reset_index(drop=True, inplace=True)
            cleaned_df.columns = col_names
            cleaned_cr.append(cleaned_df)
    


cleaned_sr = []

for s in somewhat_readable:
    year = re.search("[0-9]+", s)
    year = year.group(0)
    
    reader = PdfReader(s)
    page = reader.pages[0]
    string_t = page.extract_text()

    string_bytes = io.StringIO(string_t)

    df = pd.read_csv(string_bytes, sep = "\n")
    df = df[df.columns.values[0]].str.split(" ", expand=True)
    df = df.iloc[:, :6]
    
    df["Year"] = year
    
    ext_month = df.iloc[0, 0]
    month = re.search("[A-Za-z]", ext_month)
    month = month.group(0)
    
    while month not in df.iloc[-1, 0]:
        df = df[:-1]
    df.columns = col_names
    cleaned_sr.append(df)
    



all_clean_list = cleaned_cr + cleaned_sr


cleaned_ir = []

for i in incorrectly_read_files:
    year = re.search("[0-9]+", i)
    year = year.group(0)

    reader = PdfReader(i)
    page = reader.pages[0]
    string_t = page.extract_text()

    string_bytes = io.StringIO(string_t)

    df = pd.read_csv(string_bytes, sep = "\n")
    df = df.drop(0)
    df.reset_index(drop=True, inplace=True)
    df = df[:-1]
    
    ext_month = df.iloc[7, 0]
    month = re.search("[A-Za-z]", ext_month)
    month = month.group(0)
    
    
    while 1:
        if month not in df.iloc[0, 0]:
            df = df.drop(0)
            df.reset_index(drop=True, inplace=True)
        else:
            break
    df.columns = ["Date Temperature Humidity NO2 SO2 PM2.5"]
    df = df[df.columns.values[0]].str.split(" ", expand=True)
    if len(df.columns.values) == 7:
        df = df.drop(6, axis=1)
    if len(df.columns.values) > 7:
        df["hum"] = df[2] + df[3]
        df = df.drop(2, axis=1)
        df = df.drop(3, axis=1)
        df["no2"] = df[4] + df[5]
        df = df.drop(4, axis=1)
        df = df.drop(5, axis=1)
        df["so2"] = df[6] + df[7]
        df = df.drop(6, axis=1)
        df = df.drop(7, axis=1)
        df["pm"] = df[8] + df[9]
        df = df.drop(8, axis=1)
        df = df.drop(9, axis=1)
        df.replace("", float("NaN"), inplace=True)
        df.dropna(how='all', axis=1, inplace=True)

    df["Year"] = year
    df.reset_index(drop=True, inplace=True)
    df.columns = col_names
    cleaned_ir.append(df)




all_clean_list = all_clean_list + cleaned_ir




xlsx_files = os.listdir()
xlsx_files = [f for f in xlsx_files if ".xlsx" in f]



cleaned_xlf = []

for j in xlsx_files:
    t = pd.read_excel(j, header=1)
    year = re.search("\d{4}\.\w+", j)
    year = year.group(0)
    year = year.replace(".xlsx", "")
    t = t.drop(0)
    t.reset_index(drop=True, inplace=True)
    while 1:
        if "NEQS" in t.loc[0][0]:
            t = t.drop(0)
            t.reset_index(drop=True, inplace=True)
        elif "Value" in t.loc[0][0]:
            t = t.drop(0)
            t.reset_index(drop=True, inplace=True)
        else:
            break
    t = t[:-1]
    t = t.dropna(axis='columns', how='all')
    t["Year"] = year
    t.columns = col_names
    t.reset_index(drop=True, inplace=True)
    cleaned_xlf.append(t)



all_clean_list = all_clean_list + cleaned_xlf


extracted_dir = "extracted_data"

if not os.path.exists(extracted_dir):
    os.makedirs(extracted_dir)



for c in range(len(readable_files)):
    name = readable_files[c].replace(".pdf", "")
    df = cleaned_cr[c].drop("Year", axis=1)
    df.to_csv(os.path.join(extracted_dir, "{}.csv".format(name)), index=False)

for c in range(len(somewhat_readable)):
    name = somewhat_readable[c].replace(".pdf", "")
    df = cleaned_sr[c].drop("Year", axis=1)
    df.to_csv(os.path.join(extracted_dir, "{}.csv".format(name)), index=False)

for c in range(len(incorrectly_read_files)):
    name = incorrectly_read_files[c].replace(".pdf", "")
    df = cleaned_ir[c].drop("Year", axis=1)
    df.to_csv(os.path.join(extracted_dir, "{}.csv".format(name)), index=False)
    
for x in range(len(xlsx_files)):
    name = xlsx_files[x].replace(".xlsx", "")
    df = cleaned_xlf[x].drop("Year", axis=1)
    df.to_csv(os.path.join(extracted_dir, "{}.csv".format(name)), index=False)


data_files = os.listdir("extracted_data")


final_df = pd.concat(all_clean_list)


final_df["Date"] = final_df["Date"].str.replace('\s+', '', regex=True)
final_df["Date"] = final_df["Date"].str.replace('-', ' ', regex=True)
final_df["Date"] = final_df["Date"].str.replace('\d{4}', '', regex=True)
final_df["Date"] = final_df["Date"].str.replace('^0+(?!$)', '', regex=True)
final_df["Date"] = final_df["Date"].str.replace('\d{2}$', '', regex=True)
final_df["Date"] = final_df["Date"].str.rstrip()


final_df.to_csv("final_data.csv", index=False)

