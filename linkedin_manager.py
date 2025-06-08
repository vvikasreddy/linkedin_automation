# 

# scraper.py

import json
import os
import random
import time
from datetime import datetime, timedelta
from collections import defaultdict
import re

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
 
# "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\ChromeDebug" --no-first-run --no-default-browser-check


import config

class LinkedInScraper:
    """
    A class to automate scraping messages from LinkedIn.
    This version includes the corrected logic to only check the most recent
    message in a conversation before deciding to scrape it.
    """
    def __init__(self, debugger_address: str, messages_url: str, json_path: str):
        self.json_path = json_path
        self.driver = self._setup_driver(debugger_address)
        self.driver.get(messages_url)
        self.messages_data, self.unique_messages_set = self._load_messages()
        self.message_ids_by_name, self.last_convid_by_name, self.next_message_id = self._process_loaded_messages()
        self.most_recent_scraped_datetime = self._find_most_recent_datetime()

        print(f"Scraper initialized. Loaded {len(self.messages_data)} messages.")
        print(f"Next new message ID will be messg_{self.next_message_id}.")
        if self.most_recent_scraped_datetime:
            print(f"Scraping will stop upon reaching conversations from on or before: {self.most_recent_scraped_datetime}.")

    def _setup_driver(self, debugger_address: str) -> webdriver.Chrome:
        print("Setting up Selenium WebDriver...")
        options = Options()
        options.add_experimental_option("debuggerAddress", debugger_address)
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print(f"Successfully connected to Chrome on {debugger_address}")

        return driver

    def _load_messages(self) -> (list, set):
        if not os.path.exists(self.json_path):
            return [], set()
        with open(self.json_path, "r", encoding="utf-8") as f:
            try:
                messages = json.load(f)
            except json.JSONDecodeError:
                return [], set()

        unique_messages = {
            (m.get('message_date'), m.get('conversation_id'), m.get('connection_name'), m.get('message_text')): m
            for m in messages
        }
        cleaned_messages = list(unique_messages.values())
        print(f"Removed {len(messages) - len(cleaned_messages)} duplicate messages from loaded data.")
        unique_set = set((m['message_date'], m['conversation_id'], m['connection_name']) for m in cleaned_messages)
        return cleaned_messages, unique_set

    def _process_loaded_messages(self) -> (defaultdict, defaultdict, int):
        message_ids, last_conv_ids, max_id = defaultdict(str), defaultdict(str), -1
        for msg in self.messages_data:
            name, msg_id_str = msg['connection_name'], msg['message_id']
            if name not in message_ids:
                message_ids[name] = msg_id_str
            last_conv_ids[name] = msg['conversation_id']
            try:
                numeric_id = int(msg_id_str.split('_')[1])
                if numeric_id > max_id:
                    max_id = numeric_id
            except (IndexError, ValueError):
                continue
        return message_ids, last_conv_ids, max_id + 1

    def _find_most_recent_datetime(self) -> datetime | None:
        if not self.unique_messages_set:
            return None
        recent = None
        for date_str, _, _ in self.unique_messages_set:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                if recent is None or dt > recent:
                    recent = dt
            except ValueError:
                continue
        return recent

    def _is_valid_datetime_format(self, date_string: str) -> bool:
        try:
            datetime.strptime(date_string.strip(), "%b %d, %Y %I:%M %p")
            return True
        except ValueError:
            return False

    def _time_formatter(self, raw: str) -> datetime:
        return datetime.strptime(raw.strip(), "%b %d, %Y %I:%M %p")

    def _get_preview_timestamp(self, conversation_item: WebElement) -> datetime | None:
        """
        Parses the timestamp from a conversation list item (left pane).
        This version is robustly handles multiple time formats.
        """
        try:
            time_el = conversation_item.find_element(By.TAG_NAME, "time")
            print("current time::: ", time_el.text)
            time_str = time_el.text.strip()
            now = datetime.now()

            # Case 1: Starts with a weekday (e.g., "Thursday 11:09 PM")
            parts = time_str.split()
            weekdays = {
                "MON": 0, "MONDAY": 0, "TUE": 1, "TUESDAY": 1, "WED": 2, "WEDNESDAY": 2,
                "THU": 3, "THURSDAY": 3, "FRI": 4, "FRIDAY": 4, "SAT": 5, "SATURDAY": 5,
                "SUN": 6, "SUNDAY": 6
            }
            if parts[0].upper() in weekdays:
                day_index = weekdays[parts[0].upper()]
                days_ago = (now.weekday() - day_index) % 7
                target_date = (now - timedelta(days=days_ago)).date()

                # Check if there is a time part included
                time_part_str = " ".join(parts[1:])
                if re.fullmatch(r'\d{1,2}:\d{2}\s[AP]M', time_part_str, re.IGNORECASE):
                    time_part = datetime.strptime(time_part_str, '%I:%M %p').time()
                    return datetime.combine(target_date, time_part)
                else: # Just the weekday, default to midnight
                    return datetime.combine(target_date, datetime.min.time())

            # Case 2: Time only (e.g., "11:09 PM") -> Assumes today
            if re.fullmatch(r'\d{1,2}:\d{2}\s[AP]M', time_str, re.IGNORECASE):
                return datetime.combine(now.date(), datetime.strptime(time_str, '%I:%M %p').time())

            # Case 3: Other date formats
            for fmt in ['%b %d', '%b %d, %Y', '%m/%d/%Y']:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    # If year was not in format, it defaults to 1900. Correct it.
                    if dt.year == 1900:
                        return dt.replace(year=now.year)
                    return dt
                except ValueError:
                    continue

            print(f"Warning: Could not parse preview timestamp '{time_str}'")
            return None
        except NoSuchElementException:
            return None

    def _get_time_from_event(self, event: WebElement, prev: str) -> (str, str):
        time_elems = event.find_elements(By.TAG_NAME, "time")
        time_value = ""
        time_count = 0
        for i in time_elems:
            try:
                if datetime.strptime(i.text, "%b %d"):
                    time_value = i.text + f", {datetime.now().year}"
            except:
                time_value += f" {i.text}"
            time_count += 1
        time_value = time_value.strip()

        if time_value and time_value.split()[0].upper() in ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY", "TODAY"]:
            day_of_week_or_today = time_value.split()[0].upper()
            time_part = " ".join(time_value.split()[1:])
            today = datetime.now()
            if day_of_week_or_today == "TODAY":
                recent_date = today
            else:
                days_of_week = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
                days_ago = (today.weekday() - days_of_week.index(day_of_week_or_today)) % 7
                recent_date = today - timedelta(days=days_ago)
            time_value = recent_date.strftime("%b %d, %Y") + " " + time_part

        if time_count <= 1 and prev:
            try:
                date_part = " ".join(prev.strip().split()[:3])
                time_value = f"{date_part} {time_value}"
            except IndexError:
                pass
        return time_value, time_value

    def _scroll_in_conversation(self, repeats: int = config.SCROLL_REPETITIONS):
        try:
            scroll_el = self.driver.find_element(By.CSS_SELECTOR, config.SCROLLABLE_DIV_SELECTOR)
            origin = ScrollOrigin.from_element(scroll_el)
            actions = ActionChains(self.driver)
            for _ in range(repeats):
                actions.scroll_from_origin(origin, 0, config.SCROLL_AMOUNT_PX)
                actions.pause(config.ACTION_PAUSE_DURATION_S)
            actions.perform()
            time.sleep(config.SHORT_SLEEP_S)
        except NoSuchElementException:
            print("Could not find the scrollable message list.")

    def _get_active_connection_name(self) -> str:
        try:
            wait = WebDriverWait(self.driver, 5)
            a_tag = wait.until(EC.presence_of_element_located((By.XPATH, config.CONNECTION_NAME_XPATH)))
            name = a_tag.get_attribute("title").replace("’s profile", "").replace("Open ", "")
            return name.strip()
        except TimeoutException:
            print("Could not find connection name in time.")
            return "Unknown Connection"

    def _scrape_active_conversation(self, base_message_id: int):
        # <<< MODIFIED/NEW: This function now returns a tuple (connection_name, was_skipped_as_old)
        self._scroll_in_conversation()
        connection_name = self._get_active_connection_name()
        print(f"\n--- Checking conversation with: {connection_name} ---")

        event_elements = self.driver.find_elements(By.XPATH, config.MESSAGE_EVENT_LIST_XPATH)
        if not event_elements:
            print("No message events found. Skipping.")
            return connection_name, False

        # <<< NEW: Check the last message's timestamp before committing to a full scrape.
        if self.most_recent_scraped_datetime:
            # First, build a full list of timestamps for the conversation.
            all_timestamps = []
            prev_timestamp_str = ""
            for event in event_elements:
                time_value, prev_timestamp_str = self._get_time_from_event(event, prev_timestamp_str)
                all_timestamps.append(time_value)

            # Find the last fully valid timestamp from the end of the list.
            last_full_timestamp_str = ""
            for ts in reversed(all_timestamps):
                if self._is_valid_datetime_format(ts):
                    last_full_timestamp_str = ts
                    break

            if last_full_timestamp_str:
                last_message_dt = self._time_formatter(last_full_timestamp_str)
                # If the last message is not newer than our latest scrape, skip.
                if last_message_dt <= self.most_recent_scraped_datetime:
                    print(f"No new messages. Most recent is from {last_message_dt}. Skipping.")
                    return connection_name, True # <<< MODIFIED: Return True for 'was_skipped'

        print(f"Scraping new messages from: {connection_name}...")
        message_id = base_message_id
        # last_conversation_id = 0
        if connection_name in self.message_ids_by_name:
            try:
                message_id = int(self.message_ids_by_name[connection_name].split('_')[1])
                # last_conversation_id = int(self.last_conversation_id_by_name[connection_name].split('_')[1]) + 1
            except (ValueError, IndexError):
                pass

        new_messages_count = 0
        prev_timestamp_str, last_valid_timestamp_str = "", ""
        
        
        for i, event in enumerate(event_elements):
            try:
                message_text = event.find_element(By.TAG_NAME, config.MESSAGE_TEXT_SELECTOR).text
            except NoSuchElementException:
                message_text = ""

            ######
            try:
                message_sender = event.find_element(By.XPATH, ".//img").get_attribute("title")
            except NoSuchElementException:
                pass

            try:
                div_with_title = self.driver.find_element(By.XPATH, ".//div[@title]")
                connection_title = div_with_title.get_attribute("title")
                # print("_________________________________")
                # print("connection_title: ", connection_title)
            except NoSuchElementException:
                connection_title = "N/A"

            time_value, prev_timestamp_str = self._get_time_from_event(event, prev_timestamp_str)

            if self._is_valid_datetime_format(time_value):
                final_time_str = time_value
                last_valid_timestamp_str = time_value
            else:
                final_time_str = last_valid_timestamp_str

            if not final_time_str:
                continue

            temp_time = self._time_formatter(final_time_str)

            message = {
                "message_id": f"messg_{message_id}",
                "conversation_id": f"conv_{i}",
                "platform": "LinkedIn",
                "connection_name": connection_name,
                "message_sender": message_sender,
                "message_date": temp_time.strftime("%Y-%m-%d %H:%M:%S"),
                "message_text": message_text.strip(),
                "connection_title": connection_title
            }
            unique_key = (message['message_date'], message['conversation_id'], message['connection_name'])
            if unique_key not in self.unique_messages_set:
                self.messages_data.append(message)
                self.unique_messages_set.add(unique_key)
                new_messages_count += 1

        print(f"Added {new_messages_count} new messages for {connection_name}.")
        return connection_name, False # <<< MODIFIED: Return False for 'was_skipped'

    def run_scraper(self):
        try:
            print("Waiting for conversation list to load...")
            wait = WebDriverWait(self.driver, config.EXPLICIT_WAIT_TIMEOUT_S)
            conversation_list_ul = wait.until(EC.presence_of_element_located((By.XPATH, config.CONVERSATION_LIST_XPATH)))

            processed_conversations = set()
            processed_count = 0
            stop_scraping = False

            while not stop_scraping:
                all_conversations_in_view = conversation_list_ul.find_elements(By.TAG_NAME, "li")

                new_conversations_found_in_pass = False
                for item in all_conversations_in_view:
                    try:
                        if item.id in processed_conversations:
                            continue

                        new_conversations_found_in_pass = True
                        processed_conversations.add(item.id)
                        processed_count += 1

                        # <<< MODIFIED: Removed the inaccurate preview timestamp check.
                        # The check is now inside _scrape_active_conversation.
                        print(f"\nProcessing conversation #{processed_count}...")

                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                        time.sleep(0.5)
                        item.click()

                        # <<< MODIFIED: Capture the new return values.
                        connection_name, was_skipped_as_old = self._scrape_active_conversation(self.next_message_id)

                        # <<< NEW: If a conversation was skipped because it's old,
                        # stop the entire scraping process.
                        if was_skipped_as_old:
                            print("Stopping scraper as we have reached previously scraped conversations.")
                            stop_scraping = True
                            break

                        if connection_name not in self.message_ids_by_name and connection_name != "Unknown Connection":
                            self.next_message_id += 1

                        time.sleep(random.randint(*config.MEDIUM_SLEEP_S))

                    except StaleElementReferenceException:
                        print("Conversation item became stale, re-finding and continuing...")
                        break
                    except Exception as e:
                        print(f"An error occurred while processing a conversation: {e}")
                        continue

                if stop_scraping or not new_conversations_found_in_pass:
                    if not new_conversations_found_in_pass:
                         print("Scrolled to the end of the conversation list. No new conversations were loaded.")
                    break

                print("\nScrolling conversation list to load more...")
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", conversation_list_ul)
                time.sleep(config.SHORT_SLEEP_S)

        except TimeoutException:
            print("Timed out waiting for the conversation list to appear.")
            print("Please ensure you are logged in and on the main messaging page.")
        finally:
            self.save_messages()
            self.driver.quit()
            print("Scraping complete and WebDriver closed.")

    def save_messages(self):
        print(f"\nSaving {len(self.messages_data)} messages to {self.json_path}...")
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        with open(self.json_path, 'w', encoding="utf-8") as f:
            json.dump(self.messages_data, f, indent=4, default=str)
        print("Save complete.")

def main():
    """
    Main function to initialize and run the LinkedIn scraper.
    """
    try:
        scraper = LinkedInScraper(
            debugger_address=config.DEBUGGER_ADDRESS,
            messages_url=config.LINKEDIN_MESSAGES_URL,
            json_path=config.MESSAGES_JSON_PATH
        )
        scraper.run_scraper()
    except Exception as e:
        print(f"A critical error occurred: {e}")
        # Optionally, save any partially scraped data here if the scraper object exists
        if 'scraper' in locals() and scraper:
            scraper.save_messages()

if __name__ == "__main__":
    main()
