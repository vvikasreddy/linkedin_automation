 
## Linkedin Referral automation.

### Prerequisites
To run this project, you’ll need the following:
- **Google Chrome Browser**: Ensure Chrome is installed on your system.
- **Login Credentials**: Log in to the target website using your username and password in Chrome before proceeding.

### Setup Instructions
1. **Install Selenium**:
   - Ensure Python is installed, then install the Selenium package via pip:
     ```
     pip install selenium
     ```

2. **Launch Chrome with Remote Debugging**:
   - Open the Command Prompt (CMD) on your system.
   - Run the following command to start Chrome with remote debugging enabled:
     ```
     "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
     ```
   - This allows the Selenium script to interact with your logged-in Chrome session.

3. **Run the Demo**:
   - Open the `demo.ipynb` file in Jupyter Notebook.
   - Execute the cells in the notebook sequentially to run the script.

---

Now the Selenium installation comes first, followed by launching Chrome, and then running the demo. Let me know if you need further tweaks!