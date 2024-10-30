import time

import requests
from bs4 import BeautifulSoup
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By

def fetch_issuer_names(url):
    """Fetch issuer names from the given URL and filter those without numbers in their codes."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    dropdown = soup.find('select', class_='form-control')

    if not dropdown:
        print("No dropdown found!")
        return []

    # Extract and filter issuer names
    return [
        option.text.strip()
        for option in dropdown.find_all('option')
        if option.get('value') and not re.search(r'\d', option.get('value'))
    ]


def save_to_csv(issuer_names, filename='filtered_issuers.csv'):
    """Save the filtered issuer names to a CSV file."""
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Issuer Name'])  # Only the name
        writer.writerows([[name] for name in issuer_names])  # Write each name as a row
    print(f"Filtered issuer names saved to {filename}")

def listanje_na_url(sifri):
    for name in sifri:
        url="https://www.mse.mk/mk/stats/symbolhistory/"+name
        print(url)


def print_first_two_columns(url, start_date, end_date):
    driver = webdriver.Chrome()
    driver.get(url)

    from_date = driver.find_element(By.ID, "FromDate")
    from_date.clear()
    from_date.send_keys(start_date)

    to_date = driver.find_element(By.ID, "ToDate")
    to_date.clear()
    to_date.send_keys(end_date)

    search_button = driver.find_element(By.CSS_SELECTOR, ".btn.btn-primary-sm")
    search_button.click()
    time.sleep(15)


    results_table = driver.find_element(By.ID, "resultsTable")

    # Пронајди ги сите редови во табелата
    rows = results_table.find_elements(By.TAG_NAME, "tr")

    # Прочитај првите две колони од секој ред (освен насловниот ред)
    for row in rows[1:]:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) >= 2:
            col1 = cells[0].text
            col2 = cells[1].text
            print(f"Колона 1: {col1}, Колона 2: {col2}")


    driver.quit()



def main():
    url = 'https://www.mse.mk/mk/stats/symbolhistory/KMB'
    issuer_names = fetch_issuer_names(url)

    if issuer_names:
        print("Available issuers without numbers:")
        for name in issuer_names:
            print(name)
        save_to_csv(issuer_names)
        print_first_two_columns("https://www.mse.mk/mk/stats/symbolhistory/KMB","01.01.2024","30.10.2024")


if __name__ == '__main__':
    main()
