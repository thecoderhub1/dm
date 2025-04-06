import time
import random
import os
import pickle
import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Instagram credentials
USERNAME = "worlds_editzs"  # Your Instagram username
PASSWORD = "gauravsir"  # Your Instagram password

# Path to save cookies
COOKIES_FILE = "instagram_cookies.pkl"

# Default file paths
DEFAULT_CSV_PATH = r"C:\Users\GAURAV SINGH\Downloads\instagram_accounts_csv.csv"
DEFAULT_EXCEL_PATH = r"C:\Users\GAURAV SINGH\Downloads\instagram_accounts.xlsx"

# Default message - exactly as shown in the screenshot
DEFAULT_MESSAGE = """Are u looking for a video editor?

Below is my portfolio plz have a look

https://drive.google.com/drive/folders/12fAR2A31kM_bv6lNcgwfUt1vv4YsJxfm

Do  let me know if intrested"""

# Function to simulate human-like typing
def human_type(element, text):
    """Type text with random delays between keystrokes to mimic human typing"""
    for char in text:
        element.send_keys(char)
        # Random delay between keystrokes (50-200ms)
        time.sleep(random.uniform(0.05, 0.2))
    
# Function to read usernames from CSV file
def read_from_csv(file_path=DEFAULT_CSV_PATH):
    """
    Read usernames and optional messages from a CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        list: List of dictionaries with username and optional message
    """
    targets = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            
            # Check if the file has a header by reading the first row
            first_row = next(reader, None)
            if not first_row:
                return []
            
            # Determine if this is a header row or actual data
            # If the first column contains 'username' or similar, treat as header
            first_cell = first_row[0].strip().lower() if first_row and first_row[0] else ""
            is_header = first_cell in ["username", "user", "name", "instagram", "instagram username"]
            
            # Check if the CSV has a message column
            has_message_column = len(first_row) > 1 if first_row else False
            
            # Process the first row if it's not a header
            if not is_header and first_row:
                username = first_row[0].strip()
                message = first_row[1].strip() if has_message_column and len(first_row) > 1 else None
                if username:
                    targets.append({"username": username, "message": message})
            
            # Process the rest of the rows
            for row in reader:
                if not row or not row[0]:
                    continue  # Skip empty rows
                
                username = row[0].strip()
                message = row[1].strip() if has_message_column and len(row) > 1 else None
                
                targets.append({"username": username, "message": message})
        
        print(f"Loaded {len(targets)} targets from CSV file")
        return targets
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return []

# Function to read usernames from Excel file
def read_from_excel(file_path=DEFAULT_EXCEL_PATH):
    """Read usernames and messages from an Excel file"""
    if not os.path.exists(file_path):
        print(f"Excel file not found: {file_path}")
        return []
    
    try:
        df = pd.read_excel(file_path)
        
        # Check if the required columns exist
        if 'username' not in df.columns:
            print("Excel file must have a 'username' column")
            return []
        
        targets = []
        for _, row in df.iterrows():
            username = str(row['username']).strip()
            if not username or username == 'nan':
                continue  # Skip empty usernames
            
            message = str(row['message']).strip() if 'message' in df.columns and str(row['message']) != 'nan' else None
            
            targets.append({"username": username, "message": message})
        
        print(f"Loaded {len(targets)} targets from Excel file")
        return targets
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        return []

# Function to send a DM to a specific username
def send_dm_to_user(driver, username, message):
    print(f"\nStarting to send message to: {username}")
    
    # Make sure we're on the inbox page
    if "direct/inbox" not in driver.current_url:
        print("Navigating to inbox first...")
        driver.get("https://www.instagram.com/direct/inbox/")
        time.sleep(5)
    
    # Click on the "Send message" button
    print("Clicking Send message button...")
    try:
        # Find by text content
        send_message_buttons = driver.find_elements(By.XPATH, "//div[contains(text(), 'Send message')]")
        if send_message_buttons and len(send_message_buttons) > 0:
            for button in send_message_buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    print("Clicked Send message button")
                    break
        else:
            # Try by role attribute
            buttons = driver.find_elements(By.XPATH, "//div[@role='button']")
            for button in buttons:
                try:
                    if "message" in button.text.lower() and button.is_displayed() and button.is_enabled():
                        button.click()
                        print("Clicked button with message text")
                        break
                except:
                    continue
    except Exception as e:
        print(f"Error clicking Send message button: {str(e)}")
        return False
    
    # Wait for search dialog
    time.sleep(5)
    print("Waiting for search dialog...")
    
    # Find search box and enter username
    try:
        # Try different methods to find the search box
        search_box = None
        
        # Method 1: Find by placeholder
        try:
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Search')]"))
            )
            print("Found search box by placeholder")
        except:
            # Method 2: Find by aria-label
            try:
                search_box = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//input[contains(@aria-label, 'Search')]"))
                )
                print("Found search box by aria-label")
            except:
                # Method 3: Just find any input in the dialog
                try:
                    search_box = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//input"))
                    )
                    print("Found search box in dialog")
                except Exception as e:
                    print(f"Could not find search box: {str(e)}")
                    return False
        
        if search_box:
            # Clear any existing text and enter username with human-like typing
            search_box.clear()
            human_type(search_box, username)
            print(f"Searching for {username}")
            time.sleep(3)
            
            # Take a screenshot of search results
            screenshot_file = f"search_results_{username}.png"
            driver.save_screenshot(screenshot_file)
            
            # Check if "No account found" is displayed
            if "No account found" in driver.page_source:
                print("No account found with that username. Trying without underscore...")
                search_box.clear()
                # Type modified username with human-like delays
                human_type(search_box, username.replace("_", ""))
                print(f"Searching for {username.replace('_', '')}")
                time.sleep(3)
                driver.save_screenshot(f"search_results_no_underscore_{username}.png")
            
    except Exception as e:
        print(f"Could not find search box: {str(e)}")
        return False
    
    # Select the first user from search results
    print("Selecting first user...")
    try:
        # Wait for search results to appear
        time.sleep(3)
        
        # Try different methods to select a user
        user_selected = False
        
        # Method 1: Look for the circular checkboxes in the search results
        try:
            checkboxes = driver.find_elements(By.XPATH, "//div[@role='dialog']//div[contains(@class, 'x1i10hfl')]//div[contains(@class, 'x9f619')]")
            
            if checkboxes and len(checkboxes) > 0:
                print(f"Found {len(checkboxes)} potential checkboxes")
                
                # Click the first checkbox
                checkboxes[0].click()
                user_selected = True
                print("Clicked on first user checkbox")
                time.sleep(2)
        except Exception as e:
            print(f"Error with checkbox method: {str(e)}")
        
        # Method 2: Try to find user rows if checkboxes aren't found
        if not user_selected:
            try:
                user_elements = driver.find_elements(By.XPATH, "//div[@role='dialog']//div[@role='button']")
                if user_elements and len(user_elements) > 0:
                    print(f"Found {len(user_elements)} user elements")
                    user_elements[0].click()
                    user_selected = True
                    print("Clicked on first user element")
                    time.sleep(2)
            except Exception as e:
                print(f"Error with user elements method: {str(e)}")
        
        # Method 3: Try to find any clickable element in the search results
        if not user_selected:
            try:
                # Use JavaScript to find and click the first result
                driver.execute_script("""
                    var dialog = document.querySelector('div[role="dialog"]');
                    if (dialog) {
                        var elements = dialog.querySelectorAll('div[role="button"]');
                        if (elements.length > 0) {
                            elements[0].click();
                            return true;
                        }
                    }
                    return false;
                """)
                user_selected = True
                print("Selected user using JavaScript")
                time.sleep(2)
            except Exception as e:
                print(f"Error with JavaScript selection: {str(e)}")
        
        if not user_selected:
            print("Could not select any user")
            return False
            
    except Exception as e:
        print(f"Error selecting user: {str(e)}")
        return False
    
    # Wait for user selection to register
    time.sleep(3)
    
    # Click the Chat button
    print("Clicking Chat button...")
    chat_clicked = False
    
    try:
        # Method 1: Find the Chat button by text
        chat_buttons = driver.find_elements(By.XPATH, "//div[text()='Chat']")
        if chat_buttons and len(chat_buttons) > 0:
            for button in chat_buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    chat_clicked = True
                    print("Clicked Chat button by text")
                    break
    except Exception as e:
        print(f"Error with Chat button text method: {str(e)}")
    
    # Method 2: Find the blue button at the bottom of the dialog
    if not chat_clicked:
        try:
            blue_buttons = driver.find_elements(By.XPATH, "//div[@role='dialog']//div[contains(@style, 'background-color')]")
            if blue_buttons and len(blue_buttons) > 0:
                for button in blue_buttons:
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        chat_clicked = True
                        print("Clicked blue button")
                        break
        except Exception as e:
            print(f"Error with blue button method: {str(e)}")
    
    # Method 3: Find any button in the dialog
    if not chat_clicked:
        try:
            buttons = driver.find_elements(By.XPATH, "//div[@role='dialog']//button")
            if buttons and len(buttons) > 0:
                buttons[-1].click()  # Click the last button (usually primary action)
                chat_clicked = True
                print("Clicked last button in dialog")
        except Exception as e:
            print(f"Error with last button method: {str(e)}")
    
    # Method 4: Use JavaScript to find and click the Chat button
    if not chat_clicked:
        try:
            chat_clicked = driver.execute_script("""
                // Try to find elements with text "Chat"
                var elements = document.querySelectorAll('*');
                for (var i = 0; i < elements.length; i++) {
                    if (elements[i].textContent === 'Chat' && elements[i].offsetParent !== null) {
                        elements[i].click();
                        return true;
                    }
                }
                
                // If no Chat text found, try to find the blue button at the bottom
                var dialog = document.querySelector('div[role="dialog"]');
                if (dialog) {
                    var buttons = dialog.querySelectorAll('div[role="button"]');
                    if (buttons.length > 0) {
                        // Click the last button (usually the primary action)
                        buttons[buttons.length - 1].click();
                        return true;
                    }
                }
                
                return false;
            """)
            
            if chat_clicked:
                print("Clicked Chat button using JavaScript")
            else:
                print("JavaScript click did not find a suitable element")
        except Exception as e:
            print(f"JavaScript click failed: {str(e)}")
    
    if not chat_clicked:
        print("Could not click Chat button")
        return False
    
    # Wait for chat window to load
    time.sleep(8)
    
    # Check if we need to send a request first
    print("Checking if we need to send a request first...")
    
    # Check for text indicating a request is needed
    request_needed = False
    try:
        request_texts = [
            "Send Message Request",
            "can't receive messages",
            "request to send",
            "accept your message request",
            "accept your request",
            "send request"
        ]
        
        page_source = driver.page_source.lower()
        for text in request_texts:
            if text.lower() in page_source:
                request_needed = True
                print(f"Found text indicating a request is needed: '{text}'")
                break
        
        # Also check for request button
        request_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Request') or contains(text(), 'request')]")
        if request_buttons and len(request_buttons) > 0:
            request_needed = True
            print("Found a request button")
    except Exception as e:
        print(f"Error checking for request indicators: {str(e)}")
    
    # If a request is needed, show warning and proceed to the next user
    if request_needed:
        print(f"⚠️ WARNING: {username} requires a request to be accepted. Moving to next user.")
        return False
    
    # Find message input and send message
    print("Looking for message input...")
    message_sent = False
    
    try:
        # Try different methods to find the message input
        message_input = None
        
        # Try using JavaScript to find the message input
        try:
            message_input = driver.execute_script("""
                // Try to find the message input
                var messageInput = document.querySelector('div[contenteditable="true"]');
                if (!messageInput) {
                    messageInput = document.querySelector('textarea');
                }
                if (!messageInput) {
                    var allElements = document.querySelectorAll('*');
                    for (var i = 0; i < allElements.length; i++) {
                        if (allElements[i].getAttribute('aria-label') === 'Message' || 
                            allElements[i].getAttribute('placeholder') === 'Message...') {
                            messageInput = allElements[i];
                            break;
                        }
                    }
                }
                
                return messageInput;
            """)
            
            if message_input:
                print("Found message input using JavaScript")
            else:
                print("JavaScript could not find message input")
        except Exception as e:
            print(f"JavaScript find input failed: {str(e)}")
        
        # If JavaScript failed, try other methods
        if not message_input:
            try:
                message_input = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
                print("Found message input as contenteditable div")
            except:
                try:
                    message_input = driver.find_element(By.XPATH, "//textarea")
                    print("Found message input as textarea")
                except:
                    try:
                        message_input = driver.find_element(By.XPATH, "//div[contains(@aria-label, 'Message')]")
                        print("Found message input by aria-label")
                    except Exception as e:
                        print(f"Could not find message input: {str(e)}")
        
        # If we found the message input, send the message
        if message_input:
            # Click the input field first to ensure it's focused
            try:
                message_input.click()
                time.sleep(1)
                print("Clicked message input field")
            except:
                print("Could not click message input, trying to send keys anyway")
            
            # Type the message with human-like delays
            try:
                # Use JavaScript to set the value directly to avoid emoji issues
                driver.execute_script("""
                    arguments[0].focus();
                """, message_input)
                
                print("Starting to type the ENTIRE message...")
                
                # Type each character with a delay
                for char in message:
                    try:
                        if char == '\n':
                            # For newlines, use Shift+Enter
                            message_input.send_keys(Keys.SHIFT, Keys.ENTER)
                        else:
                            message_input.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes
                    except:
                        print(f"Could not type character: {char}, skipping")
                
                print("COMPLETED typing the ENTIRE message")
                
                # Take a screenshot of the typed message
                driver.save_screenshot(f"message_typed_{username}.png")
                
                # Wait a moment before sending (as if reviewing)
                time.sleep(3)
                print("Reviewing message before sending...")
                
                # NOW send the message (after the entire message has been typed)
                message_input.send_keys(Keys.RETURN)
                message_sent = True
                print("Sent message AFTER typing the ENTIRE message")
            except Exception as e:
                print(f"Error typing message: {str(e)}")
                
                # Try using JavaScript as a fallback
                try:
                    print("Trying JavaScript fallback to type and send message...")
                    
                    # First set the text
                    driver.execute_script("""
                        arguments[0].focus();
                        arguments[0].innerText = arguments[1];
                    """, message_input, message)
                    
                    print("Set message text using JavaScript")
                    
                    # Take a screenshot of the typed message
                    driver.save_screenshot(f"message_typed_js_{username}.png")
                    
                    # Wait a moment before sending (as if reviewing)
                    time.sleep(3)
                    print("Reviewing message before sending...")
                    
                    # NOW send the message
                    driver.execute_script("""
                        // Create and dispatch an Enter key event
                        var enterEvent = new KeyboardEvent('keydown', {
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true
                        });
                        arguments[0].dispatchEvent(enterEvent);
                    """, message_input)
                    
                    message_sent = True
                    print("Sent message using JavaScript AFTER setting the ENTIRE message")
                except Exception as e:
                    print(f"JavaScript send failed: {str(e)}")
        else:
            # Check again for request indicators
            try:
                if any(text.lower() in driver.page_source.lower() for text in request_texts):
                    print(f"⚠️ This user requires a request to be accepted before messaging. Proceeding to next user.")
                    return False
            except:
                pass
        
        # Take a screenshot regardless of success
        driver.save_screenshot(f"message_attempt_{username}.png")
        
        # Wait a bit before returning to inbox
        time.sleep(3)
        
        return message_sent
                
    except Exception as e:
        print(f"Error handling message input: {str(e)}")
        driver.save_screenshot(f"message_error_{username}.png")
        return False

# Main function
def main():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    
    print("\nStarting browser...")
    
    # Set window size
    driver.set_window_size(1200, 800)
    
    # Open Instagram
    print("Opening Instagram...")
    driver.get("https://www.instagram.com/")
    
    # Wait for the page to load
    time.sleep(3)
    
    # Try to load cookies
    try:
        print("Loading saved cookies...")
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    try:
                        driver.add_cookie(cookie)
                    except:
                        pass
            
            # Refresh the page
            driver.refresh()
            time.sleep(3)
            
            # Check if we're logged in
            if "instagram.com/accounts/login" not in driver.current_url:
                print("Successfully loaded session from cookies")
            else:
                print("Cookies expired or invalid, need to login again")
                perform_login(driver)
        else:
            print("No cookies file found, need to login")
            perform_login(driver)
    except Exception as e:
        print(f"Error loading cookies: {str(e)}")
        perform_login(driver)
    
    # If cookies didn't work, perform login
    if "instagram.com/accounts/login" in driver.current_url:
        perform_login(driver)
        
        # Save cookies for next time
        print("Saving cookies for next session...")
        with open(COOKIES_FILE, 'wb') as f:
            pickle.dump(driver.get_cookies(), f)
    
    # Go to DM page
    print("Going to DM page...")
    driver.get("https://www.instagram.com/direct/inbox/")
    time.sleep(5)
    
    # Close notifications popup if it appears
    try:
        not_now_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Not Now')]")
        not_now_button.click()
        print("Closed notifications popup")
    except:
        pass
    
    # Get targets from CSV or Excel
    targets = []
    
    # Try to read from CSV first
    targets = read_from_csv()
    
    # If CSV failed, try Excel
    if not targets:
        targets = read_from_excel()
    
    # If both failed, ask for manual input
    if not targets:
        usernames = get_usernames_manual()
        message = get_message()
        targets = [{"username": username, "message": None} for username in usernames]
    
    if not targets:
        print("No targets specified. Exiting.")
        driver.quit()
        return
    
    # Use default message if not specified
    message = DEFAULT_MESSAGE
    
    print(f"\nLoaded {len(targets)} targets from CSV file")
    
    # Show the message that will be used
    print(f"\nUsing default message:\n{message}\n")
    
    # Confirm before proceeding
    print(f"Ready to send messages to {len(targets)} targets.")
    confirmation = input("Type 'yes' to continue or anything else to exit: ")
    
    if confirmation.lower() != "yes":
        print("Operation cancelled by user.")
        driver.quit()
        return
    
    # Ask for batch size
    batch_size = 50  # Default
    try:
        batch_input = input(f"How many messages to send in this batch (max {len(targets)}, default 50): ")
        if batch_input.strip():
            batch_size = int(batch_input)
            if batch_size <= 0:
                batch_size = 50
            elif batch_size > len(targets):
                batch_size = len(targets)
    except:
        batch_size = 50
    
    # Limit the number of messages to avoid rate limiting
    if batch_size < len(targets):
        print(f"\nWARNING: You have {len(targets)} targets, but the script will only send to the first {batch_size} to avoid rate limiting.")
    
    # Get the batch of targets
    batch_targets = targets[:batch_size]
    
    # Track successful and failed attempts
    successful = []
    failed = []
    
    # Process the batch of targets
    for i, target in enumerate(batch_targets, 1):
        username = target["username"]
        custom_message = target["message"] if target["message"] else message
        
        print(f"\n[{i}/{batch_size}] Sending message to: {username}")
        
        try:
            success = send_dm_to_user(driver, username, custom_message)
            if success:
                successful.append(username)
            else:
                failed.append(username)
        except Exception as e:
            print(f"Error sending message to {username}: {str(e)}")
            failed.append(username)
        
        # Add a random delay between messages to avoid rate limiting
        if i < len(batch_targets):
            delay = random.uniform(3, 8)
            print(f"Waiting {delay:.2f} seconds before sending next message...")
            time.sleep(delay)
    
    # Retry failed attempts once
    retry_successful = []
    still_failed = []
    if failed:
        print("\n\n===== RETRYING FAILED ATTEMPTS =====")
        print(f"Retrying {len(failed)} failed attempts...")
        
        for i, username in enumerate(failed, 1):
            print(f"\n[RETRY {i}/{len(failed)}] Sending message to: {username}")
            
            try:
                success = send_dm_to_user(driver, username, message)
                if success:
                    retry_successful.append(username)
                else:
                    still_failed.append(username)
            except Exception as e:
                print(f"Error sending message to {username}: {str(e)}")
                still_failed.append(username)
            
            # Add a random delay between messages to avoid rate limiting
            if i < len(failed):
                delay = random.uniform(3, 8)
                print(f"Waiting {delay:.2f} seconds before sending next message...")
                time.sleep(delay)
    
    # Save cookies for next time
    print("Saving cookies for next session...")
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)
    
    # Print summary
    print("\nDM Summary:")
    print(f"Total DMs attempted: {batch_size}")
    print(f"Successful: {len(successful) + len(retry_successful) if 'retry_successful' in locals() else len(successful)}")
    print(f"Failed: {len(still_failed) if 'still_failed' in locals() else len(failed)}")
    
    if 'still_failed' in locals() and still_failed:
        print("\nUsernames that still failed after retry:")
        for username in still_failed:
            print(f"- {username}")
    
    print("Process completed!")
    
    # Wait for user to press Enter before closing
    input("Press Enter to close the browser...")
    
    # Close the browser
    driver.quit()

# Function to perform login
def perform_login(driver):
    print("Performing login...")
    try:
        username_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = driver.find_element(By.NAME, "password")
        
        # Enter credentials with human-like typing
        human_type(username_field, USERNAME)
        time.sleep(random.uniform(0.5, 1.5))
        human_type(password_field, PASSWORD)
        time.sleep(random.uniform(0.5, 1.5))
        
        # Click login button
        password_field.send_keys(Keys.RETURN)
        
        print("Waiting for login to complete...")
        time.sleep(10)
        
        return True
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False

# Function to get usernames manually
def get_usernames_manual():
    print("\nEnter usernames to send messages to (one per line, enter a blank line when done):")
    usernames = []
    
    while True:
        username = input("> ")
        if not username:
            break
        usernames.append(username.strip())
    
    if not usernames:
        # Default username if none provided
        usernames = ["_sky_snapper"]
        print(f"No usernames entered, using default: {usernames[0]}")
    
    return usernames

# Function to get message from user input
def get_message():
    print("\nEnter the message you want to send:")
    message = input("> ")
    
    if not message:
        # Default message if none provided
        message = DEFAULT_MESSAGE
        print(f"No message entered, using default message")
    
    return message

# Create example CSV file if it doesn't exist
def create_example_csv():
    if not os.path.exists(DEFAULT_CSV_PATH):
        try:
            with open(DEFAULT_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["username", "message"])
                writer.writerow(["_sky_snapper", "Hey, this is a test message from CSV!"])
                writer.writerow(["instagram", "Hello Instagram, this is another test message!"])
            print(f"Created example CSV file: {DEFAULT_CSV_PATH}")
        except Exception as e:
            print(f"Error creating example CSV file: {str(e)}")

# Create example Excel file if it doesn't exist
def create_example_excel():
    if not os.path.exists(DEFAULT_EXCEL_PATH):
        try:
            df = pd.DataFrame({
                "username": ["_sky_snapper", "instagram"],
                "message": ["Hey, this is a test message from Excel!", "Hello Instagram, this is another test message!"]
            })
            df.to_excel(DEFAULT_EXCEL_PATH, index=False)
            print(f"Created example Excel file: {DEFAULT_EXCEL_PATH}")
        except Exception as e:
            print(f"Error creating example Excel file: {str(e)}")

# Run the main function if script is executed directly
if __name__ == "__main__":
    # Create example files if they don't exist
    create_example_csv()
    create_example_excel()
    main() 