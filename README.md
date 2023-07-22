### Islamabad, Pakistan Air Quality Dataset

In this project, I wanted to analyze the Air Quality trends in Pakistan. There is a relative unavailability of complete historical data on air quality in different cities of Pakistan. The Pakistan Environment Protection Agency publishes the air quality data on its official website. However, I realized that it is not readily available for analytical purposes due to poor data reporting. 

The data is published on the EPA website in .pdf format. Some of these pdf files contain the data in table format, while some contain just images of this table format. This led me to devote a significant chunk of this analytical project to scraping, extracting, reading, and cleaning this data. I have also made the data files I extracted available on Kaggle so that there is an easier access to this dataset.

The pdf files of data from June, 2019 to March, 2023 for the city of Islamabad are first downloaded from the EPA website. I chose to extract this range as it represented the most complete date range. The air quality data for May, 2023 is not available and the data before June, 2019 is incomplete as well. The pdf files are then separated based on whether they contain actual tables or just the images of the tables. Fir the pdf files with images, the images are first extracted out of the pdf files and then passed to Google Cloud Vision API which performs OCR. They are then saved as .csv files. The files with tables of data are read with libraries such as tabula-py, cleaned and then saved.

After scraping, extracting, and cleaning the time-series data, it is analyzed as well as utilized to forecast AQI values for the month of April, 2023.
