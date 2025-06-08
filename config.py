# config.py

# -- SELENIUM CONFIGURATION --
# Command to run Chrome in debug mode:
# "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\ChromeDebug"
DEBUGGER_ADDRESS = "127.0.0.1:9222"
LINKEDIN_MESSAGES_URL = "https://www.linkedin.com/messaging/"

# -- FILE PATHS --
MESSAGES_JSON_PATH = r"messages/lnkdn copy.json"

# -- XPATH & CSS SELECTORS --
# Note: Using robust and stable selectors is crucial. These might change with LinkedIn's UI updates.
CONVERSATION_LIST_XPATH = "//ul[@aria-label='Conversation List']"
MESSAGE_EVENT_LIST_XPATH = "//li[contains(@class, 'msg-s-message-list__event clearfix')]"
MESSAGE_TEXT_SELECTOR = "p"
SENDER_NAME_XPATH = ".//span[contains(@class, 'msg-s-event-listitem--group-a11y-heading')]"
# CORRECTED: Using the more reliable selector from your original notebook.
CONNECTION_NAME_XPATH = "//a[contains(@title, '’s profile') and contains(@title, 'Open ')]"
SCROLLABLE_DIV_SELECTOR = ".msg-s-message-list.full-width.scrollable"

# -- SCRAPING PARAMETERS --
SCROLL_AMOUNT_PX = -1000  # Negative for scrolling up
SCROLL_REPETITIONS = 5
ACTION_PAUSE_DURATION_S = 0.2
SHORT_SLEEP_S = 2
MEDIUM_SLEEP_S = (4, 6) # A range for random sleep
EXPLICIT_WAIT_TIMEOUT_S = 15 # Wait up to 15 seconds for elements to appear



