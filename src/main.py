import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import requests
from apify import Actor

# URL from which the request is to be sent
url = 'https://monroecountypl.librarycalendar.com/events/upcoming?branches%5B72%5D=72'

# Headers based on the information you provided
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-US,en;q=0.9,fr;q=0.8',
    'cache-control': 'max-age=0',
    'if-modified-since': 'Fri, 21 Feb 2025 18:25:55 GMT',
    'if-none-match': 'W/"1740162355"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
}

async def main():
    async with Actor:
        # Send the GET request
        response = requests.get(url, headers=headers)

        # Print the status code and response text
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            html_content = str(soup)

            event_datas = soup.find_all("div", class_="lc-event__month-details")

            results = []

            for event_data in event_datas:
                name = None
                age_group = None
                program_type = None
                description = None

                date_str = f"{event_data.find('span', class_='lc-date-icon__item lc-date-icon__item--month').get_text(strip=True)} {event_data.find('span', class_='lc-date-icon__item lc-date-icon__item--day').get_text(strip=True)} {event_data.find('span', class_='lc-date-icon__item lc-date-icon__item--year').get_text(strip=True)}"
                date_obj = datetime.strptime(date_str, "%b %d %Y")
                date = date_obj.strftime("%Y-%m-%d")

                time = event_data.find("div", class_="lc-event-info-item lc-event-info-item--time").get_text(strip=True)
                start_time = time.split(" - ")[0]

                time_obj = datetime.strptime(start_time, "%I:%M%p")
                start_time = time_obj.strftime("%H:%M:%S")
                
                end_time = time.split(" - ")[1]
                time_obj = datetime.strptime(end_time, "%I:%M%p")
                end_time = time_obj.strftime("%H:%M:%S")

                if event_data.find("h3", class_="lc-event__title--details"):
                    name = event_data.find("h3", class_="lc-event__title--details").get_text(strip=True)
                if event_data.find("div", class_="lc-event__age-groups"):
                    age_group = event_data.find("div", class_="lc-event__age-groups").find("span").get_text(strip=True)
                if event_data.find("div", class_="lc-event__program-types"):
                    program_type = event_data.find("div", class_="lc-event__program-types").find("span").get_text(strip=True)

                branch_div = soup.find('div', class_='lc-event__branch')
                library_branch = branch_div.find('strong').next_sibling.strip()

                if event_data.find("div", class_="field field-container field--name-body field--type-text-with-summary field--label-hidden field-item"):
                    for em_tag in event_data.find("div", class_="field field-container field--name-body field--type-text-with-summary field--label-hidden field-item").find_all('em'):
                        em_tag.replace_with(f"*{em_tag.get_text()}*")
                if event_data.find('div', class_='field field-container field--name-body field--type-text-with-summary field--label-hidden field-item'):
                    div_content = event_data.find('div', class_='field field-container field--name-body field--type-text-with-summary field--label-hidden field-item')
                    description = div_content.get_text(strip=True)

                results.append({
                    'date': date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'name': name,
                    'description': description,
                    'library_branch': library_branch,
                    'age_group': age_group,
                    'program_type': program_type,
                })

            for row in results:
                await Actor.push_data(
                    {
                        "date": row.get('date'),
                        "start_time": row.get('start_time'),
                        "end_time": row.get('end_time'),
                        'name': name,
                        "description": row.get('description'),
                        "library_branch": row.get('library_branch'),
                        "age_group": row.get('age_group'),
                        "program_type": row.get('program_type'),
                    }
                )
        
        else:
            print("Failed to retrieve the page. Status code:", response.status_code)