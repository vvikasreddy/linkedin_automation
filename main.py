from selenium import webdriver
# from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

class LinkedInConnector:
    def __init__(self, email, password):
        options = Options()
        options.debugger_address = "127.0.0.1:55672"  # Matches the port from CMD
        self.driver = webdriver.Chrome(options=options)  # Update path
        self.email = email
        self.password = password
        self.driver.get('https://www.linkedin.com/login')

    def login(self):
       
        time.sleep(random.uniform(1, 3))

        email_field = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'username'))
        )
        password_field = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'password'))
        )
        
        for char in self.email:
            email_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        time.sleep(random.uniform(0.5, 1))
        
        for char in self.password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        time.sleep(random.uniform(0.5, 1))
        
        password_field.send_keys(Keys.RETURN)
        time.sleep(random.uniform(2, 4))

    def search_company(self, company_name):
        print("Navigating to search")
        self.driver.execute_script("window.scrollBy(0, 200);")
        time.sleep(random.uniform(0.5, 1.5))
        
        search_field = WebDriverWait(self.driver, random.uniform(10, 15)).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@role='combobox' and @aria-label='Search']"))
        )
        print("Search field located")
        
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", search_field)
        time.sleep(random.uniform(0.5, 1))
        
        if not search_field.is_displayed() or not search_field.is_enabled():
            print("Search field not immediately interactable, focusing")
            self.driver.execute_script("arguments[0].focus();", search_field)
            time.sleep(random.uniform(0.3, 0.7))
        
        try:
            search_field.click()
            print("Search field clicked successfully")
        except Exception as e:
            print(f"Normal click failed: {e}, attempting JavaScript workaround")
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('click', {bubbles: true}));", search_field)
            time.sleep(random.uniform(0.3, 0.7))
        
        for char in company_name:
            search_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.1))
        time.sleep(random.uniform(0.5, 1))
        
        search_field.send_keys(Keys.RETURN)
        print("Search submitted")
        time.sleep(random.uniform(1.5, 3))

    def search_school(self, company_name):
        print("Navigating to search")
        self.driver.execute_script("window.scrollBy(0, 200);")
        time.sleep(random.uniform(0.5, 1.5))
        
        search_field = WebDriverWait(self.driver, random.uniform(10, 15)).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@role='combobox' and @aria-label='Search']"))
        )
        print("Search field located")
        
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", search_field)
        time.sleep(random.uniform(0.5, 1))
        
        if not search_field.is_displayed() or not search_field.is_enabled():
            print("Search field not immediately interactable, focusing")
            self.driver.execute_script("arguments[0].focus();", search_field)
            time.sleep(random.uniform(0.3, 0.7))
        
        try:
            search_field.click()
            print("Search field clicked successfully")
        except Exception as e:
            print(f"Normal click failed: {e}, attempting JavaScript workaround")
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('click', {bubbles: true}));", search_field)
            time.sleep(random.uniform(0.3, 0.7))
        
        for char in company_name:
            search_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.1))
        time.sleep(random.uniform(0.5, 1))
        
        search_field.send_keys(Keys.RETURN)
        print("Search submitted")
        time.sleep(random.uniform(1.5, 3))



    def apply_filters(self, university=None, role=None):
        
        print("Applying filters")
        # Step 1: Open the "All filters" modal
        all_filters_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'search-reusables__all-filters-pill-button') and text()='All filters']"))
        )
        all_filters_button.click()
        time.sleep(random.uniform(0.5, 1.5))  # Wait for modal to load
        # step 1: Find the scrollable container
        container = self.driver.find_element(By.CLASS_NAME, "artdeco-modal__content")

        # stepp 2: Scroll the container down by 500 pixels
        self.driver.execute_script("arguments[0].scrollTop += 1000;", container)

        time.sleep(random.uniform(0.5, 1.5))  # Wait for content to load

        try: 
            # Step 3: Click the "Add a school" button
            add_school_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'reusable-search-filters-advanced-filters__add-filter-button') and .//span[text()='Add a school']]"))
            )
            add_school_button.click()
        except:
            print("Add school might have already clicked")

            
        time.sleep(random.uniform(0.5, 1.5))  # Wait for input to appear

        # step 4: Find the school input field
        school_input = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Add a school']"))
        )
        print("School input located")
        school_input.send_keys("University of Maryland Baltimore County")

        # step 5: Select the first suggestion
        time.sleep(random.uniform(0.5, 1.5))  # Wait for suggestions to load
        school_input.send_keys(Keys.DOWN)    # Press Down Arrow to select first suggestion
        time.sleep(random.uniform(0.5, 1.5))  # Brief pause for selection
        school_input.send_keys(Keys.ENTER)   # Press Enter to confirm
        print("School selected")

        #setp 6: Click the show results button
        show_results_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Show results']]"))
        )
        print("Show results button located")
        show_results_button.click()

def main():
    connector = LinkedInConnector('vikasreddy270@gmail.com', 'VIKASreddy2002!')
    
    try:
        # connector.login()  # Uncomment if not logged in
        connector.search_company('Microsoft')
        
        connector.apply_filters(
            university='Stanford University', 
            role='Software Engineer'
        )
        # connector.connect_and_message(
        #     "Hi there! I'm interested in connecting to learn more about your professional journey.",
        #     max_connections=2
        # )
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        connector.close()

if __name__ == '__main__':
    main()