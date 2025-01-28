import requests
import psycopg2
import re
import time

DB_HOST = 'localhost' #default
DB_PORT = '5432' #default
DB_NAME = 'S363phase1'  # Replace with your own database name
DB_USER = 'postgres'  # Replace with your own username
DB_PASSWORD = 'password'  # Replace with your own password

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# Function to fetch work data
def get_work_data(work_id):
    url = f'https://openlibrary.org/works/{work_id}.json'
    response = requests.get(url)
    try:
        if response.status_code == 200:
            return response.json()  # Ensure response is parsed as JSON
        else:
            print(f"Failed to fetch work data for {work_id}, status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error parsing work data for {work_id}: {e}")
        print(f"Response content: {response.text}")
        return None

# Function to fetch author data
def fetch_author_data(author_id):
    url = f'https://openlibrary.org/authors/{author_id}.json'
    response = requests.get(url)
    if response.status_code == 200:
        try:
            return response.json()  # Parse JSON properly
        except ValueError:
            print(f"Error parsing JSON for author_id: {author_id}")
    return None

# Function to fetch ratings
def fetch_ratings(work_id):
    url = f'https://openlibrary.org/works/{work_id}/ratings.json'
    response = requests.get(url)
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print(f"Error parsing JSON for ratings of work_id: {work_id}")
    return None

# Function to fetch editions
def fetch_editions(work_id):
    url = f'https://openlibrary.org/works/{work_id}/editions.json'
    response = requests.get(url)
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print(f"Error parsing JSON for editions of work_id: {work_id}")
    return None

def fetch_bio_from_wikipedia(author_name):
    try:
        headers = {
            'User-Agent': 'S363phase1project/1.0 (N_puert@live.concordia.ca)'
        }

        # Search for the author on Wikipedia
        search_url = 'https://en.wikipedia.org/w/api.php'
        search_params = {
            'action': 'query',
            'list': 'search',
            'srsearch': author_name,
            'format': 'json'
        }
        search_response = requests.get(search_url, params=search_params, headers=headers)
        search_response.raise_for_status()
        search_results = search_response.json()

        if search_results.get('query', {}).get('search'):
            page_title = search_results['query']['search'][0]['title']

            time.sleep(0.5)

            # Fetch the introduction section
            extract_url = 'https://en.wikipedia.org/w/api.php'
            extract_params = {
                'action': 'query',
                'prop': 'extracts',
                'exintro': True,
                'explaintext': True,
                'titles': page_title,
                'format': 'json'
            }
            extract_response = requests.get(extract_url, params=extract_params, headers=headers)
            extract_response.raise_for_status()
            extract_data = extract_response.json()

            pages = extract_data.get('query', {}).get('pages', {})
            page = next(iter(pages.values()))
            bio_text = page.get('extract', None)

            if bio_text:
                return bio_text.strip()
            else:
                print(f"No bio extract found for page '{page_title}'.")
        else:
            print(f"No search results found for author '{author_name}'.")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while fetching bio for '{author_name}': {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred while fetching bio for '{author_name}': {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred while fetching bio for '{author_name}': {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request exception occurred while fetching bio for '{author_name}': {req_err}")
    except Exception as e:
        print(f"An error occurred while fetching bio for '{author_name}': {e}")
    return None

# Function to insert work data into the database
def insert_work_into_db(work_data, connection):
    with connection.cursor() as cursor:
        try:
            work_id = work_data.get("key", "").split("/")[-1]
            title = work_data.get("title", None)
            first_publish_date = work_data.get("first_publish_date", None)

        # Insert work
            cursor.execute(
                """
                INSERT INTO work (wid, title, first_publish_date)
                VALUES (%s, %s, %s)
                ON CONFLICT (wid) DO NOTHING;
                """,
                (work_id, title, first_publish_date)
            )
        except psycopg2.Error as db_error:
            print(f"Database error while inserting work ID {work_id}: {db_error}")
        except Exception as general_error:
            print(f"Error processing work ID {work_id}: {general_error}")

        # Insert authors and bios
        for author in work_data.get("authors", []):
            author_id = author["author"]["key"].split("/")[-1]
            author_data = fetch_author_data(author_id)
            if author_data:
                author_name = author_data.get("name", None)

                # Initialize variables
                openlib_bio = None
                wiki_bio = None

                # Attempt to fetch bio from Open Library
                author_bio_field = author_data.get("bio", None)
                if isinstance(author_bio_field, dict):
                    openlib_bio = author_bio_field.get("value", None)
                elif isinstance(author_bio_field, str):
                    openlib_bio = author_bio_field

                # Attempt to fetch bio from Wikipedia
                if author_name:
                    wiki_bio = fetch_bio_from_wikipedia(author_name)
                    if wiki_bio:
                        print(f"Fetched bio from Wikipedia for author: {author_name}")

                # Insert author
                cursor.execute(
                    """
                    INSERT INTO authors (aid, name)
                    VALUES (%s, %s)
                    ON CONFLICT (aid) DO NOTHING;
                    """,
                    (author_id, author_name)
                )

                # Insert Open Library bio
                if openlib_bio:
                    bio_source = 'OpenLib'
                    try:
                        cursor.execute(
                            """
                            INSERT INTO bio (aid, b_text, source)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (aid, source) DO NOTHING;
                            """,
                            (author_id, openlib_bio, bio_source)
                        )
                    except psycopg2.Error as db_error:
                        print(f"Database error while inserting Open Library bio for author ID {author_id}: {db_error}")

                # Insert Wikipedia bio
                if wiki_bio:
                    bio_source = 'Wikipedia'
                    try:
                        cursor.execute(
                            """
                            INSERT INTO bio (aid, b_text, source)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (aid, source) DO NOTHING;
                            """,
                            (author_id, wiki_bio, bio_source)
                        )
                    except psycopg2.Error as db_error:
                        print(f"Database error while inserting Wikipedia bio for author ID {author_id}: {db_error}")

                # Insert work-author relationship
                cursor.execute(
                    """
                    INSERT INTO work_authors (wid, aid)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                    """,
                    (work_id, author_id)
                )

        # Fetch and insert ratings
        ratings = fetch_ratings(work_id)
        if ratings:
            avg_rating = ratings['summary'].get('average', None)
            count = ratings['summary'].get('count', 0)
            cursor.execute(
                """
                INSERT INTO rating (wid, cnt, avg_rating)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING;
                """,
                (work_id, count, avg_rating)
            )

        # Fetch and insert editions
        editions = fetch_editions(work_id)
        if editions:
            for edition in editions.get("entries", []):
                isbn10_list = edition.get("isbn_10", [])
                publish_date = edition.get("publish_date", None)
                physical_format = edition.get("physical_format", None)

                for isbn10_candidate in isbn10_list:
                    isbn10 = isbn10_candidate
                    if isbn10 and re.match(r'^\d{9}[0-9Xx]$', isbn10):
                        isbn10_cleaned = isbn10.upper()
                        try:
                            # Insert into edition table
                            cursor.execute(
                                """
                                INSERT INTO edition (isbn10, wid, publish_date)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (isbn10) DO NOTHING;
                                """,
                                (isbn10_cleaned, work_id, publish_date)
                            )
                
                        # If physical_format is specified, insert into digital or physical table
                            if physical_format:
                                # Check if physical_format indicates a digital edition
                                digital_keywords = ['audio', 'digital', 'ebook', 'electronic']
                                is_digital = any(keyword.lower() in physical_format.lower() for keyword in digital_keywords)

                                if is_digital:
                                    # Insert into digital table
                                    cursor.execute(
                                        """
                                        INSERT INTO digital (isbn10, form)
                                        VALUES (%s, %s)
                                        ON CONFLICT (isbn10) DO NOTHING;
                                        """,
                                        (isbn10_cleaned, physical_format)
                                    )
                                else:
                                    # Insert into physical table
                                    cursor.execute(
                                        """
                                        INSERT INTO physical (isbn10, type)
                                        VALUES (%s, %s)
                                        ON CONFLICT (isbn10) DO NOTHING;
                                        """,
                                        (isbn10_cleaned, physical_format)
                                    )
                        except psycopg2.Error as db_error:
                            print(f"Database error while inserting edition ISBN {isbn10_cleaned} for work ID {work_id}: {db_error}")
                    else:
                        print(f"Invalid ISBN-10 format for edition of work {work_id}: {isbn10}")
    connection.commit()

# Main function
def main():
    wids = ['OL76837W', 'OL76833W', 'OL14873315W', 'OL81634W', 'OL1914022W', 'OL81613W', 'OL81628W', 'OL76835W', 'OL81631W', 'OL81630W', 'OL76836W', 'OL81618W', 'OL77001W', 'OL46876W', 'OL81609W', 'OL81612W', 'OL81625W', 'OL81615W', 'OL77014W', 'OL23480W', 'OL3454854W', 'OL36626W', 'OL3899224W', 'OL81624W', 'OL81586W', 'OL2794726W', 'OL510879W', 'OL81594W', 'OL553754W', 'OL14917748W', 'OL46913W', 'OL16239762W', 'OL167179W', 'OL11913975W', 'OL22914W', 'OL41256W', 'OL167155W', 'OL15168588W', 'OL46904W', 'OL167160W', 'OL15008W', 'OL167161W', 'OL41249W', 'OL181821W', 'OL134880W', 'OL134885W', 'OL167162W', 'OL15165640W', 'OL167150W', 'OL167174W', 'OL167152W', 'OL9302808W', 'OL14920152W', 'OL5842017W', 'OL5842018W', 'OL3297218W', 'OL16806568W', 'OL86274W', 'OL448959W', 'OL20126932W', 'OL5337429W', 'OL106064W', 'OL167333W', 'OL59431W', 'OL17116913W', 'OL167177W', 'OL19356257W', 'OL17079190W', 'OL17725006W', 'OL16708051W', 'OL19356256W', 'OL3917426W', 'OL17868937W', 'OL1822016W', 'OL15191187W', 'OL18081210W', 'OL874049W', 'OL106059W', 'OL19356870W', 'OL18147682W', 'OL16809825W', 'OL15679291W', 'OL278110W', 'OL17929924W', 'OL5718957W', 'OL17930362W', 'OL17062554W', 'OL17426934W', 'OL27641W', 'OL17606520W', 'OL15284W', 'OL261852W', 'OL17306744W', 'OL17356815W', 'OL17283721W', 'OL17358795W', 'OL19865381W', 'OL491818W', 'OL17359906W', 'OL20036181W']  # Sample work IDs
    connection = get_db_connection()

    try:
        for wid in wids:
            work_data = get_work_data(wid)
            if work_data:
                print(f"Processing Work ID: {wid}")
                try:
                    insert_work_into_db(work_data, connection)
                except Exception as e:
                    print(f"Error processing Work ID {wid}: {e}")
            else:
                print(f"No data found for Work ID {wid}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    main()
