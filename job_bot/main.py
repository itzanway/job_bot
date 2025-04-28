from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException, ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import time
import re
import json

class EasyApplyLinkedin:

    def __init__(self, data):
        """Parameter initialization"""
        self.email = data['email']
        self.password = data['password']
        self.keywords = data['keywords']
        self.location = data['location']

        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--enable-unsafe-swiftshader")
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        service = Service(executable_path=data['driver_path'])
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute CDP commands to prevent detection
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

        self.wait = WebDriverWait(self.driver, 15)

        print("Starting the bot...")

    def login_linkedin(self):
        """This function logs into your personal LinkedIn profile"""
        self.driver.get("https://www.linkedin.com/login")

        login_email = self.wait.until(EC.presence_of_element_located((By.NAME, 'session_key')))
        login_email.clear()
        login_email.send_keys(self.email)

        login_pass = self.driver.find_element(By.NAME, 'session_password')
        login_pass.clear()
        login_pass.send_keys(self.password)
        login_pass.send_keys(Keys.RETURN)

        print("Login successful!")

    def job_search(self):
        """This function searches based on keywords and location."""
        try:
            # Navigate directly to LinkedIn jobs page with search parameters in URL
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={self.keywords}&location={self.location}"
            self.driver.get(search_url)
            print(f"Navigating directly to search URL: {search_url}")
            time.sleep(5)  # Allow page to fully load
            
            # Check if we're on the correct page
            if "/jobs/search" not in self.driver.current_url:
                # If direct URL didn't work, try the standard jobs page
                print("Direct search URL didn't work. Trying standard jobs page...")
                self.driver.get("https://www.linkedin.com/jobs/")
                time.sleep(5)  # Allow page to fully load
                
                # Try to find and use the search fields
                self._try_standard_search()
            else:
                print("Successfully navigated to search results using direct URL")
                
        except Exception as e:
            print(f"Error during job search: {e}")
            self.driver.save_screenshot("error_jobs_page.png")
            self.close_session()
            return
            
    def _try_standard_search(self):
        """Helper method to attempt standard search using input fields"""
        # Try multiple approaches to find and interact with search fields
        for attempt in range(3):
            try:
                print(f"Search attempt {attempt + 1}...")
                
                # Try a different selector strategy each time
                if attempt == 0:
                    self._try_regular_search_fields()
                elif attempt == 1:
                    self._try_search_with_javascript()
                else:
                    self._try_alternative_search_approach()
                    
                # If we get here without exception, search was successful
                print("Search successful!")
                time.sleep(5)  # Wait for results to load
                return True
                
            except Exception as e:
                print(f"Search attempt {attempt + 1} failed: {e}")
                time.sleep(3)
                self.driver.refresh()
                time.sleep(3)
                
        # If we get here, all attempts failed
        print("All search attempts failed")
        with open("error_page_source.html", "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)
        self.driver.save_screenshot("error_filling_search.png")
        return False
        
    def _try_regular_search_fields(self):
        """Try to use standard search input fields"""
        # Find the keyword field
        keyword_selectors = [
            "input.jobs-search-box__text-input[aria-label*='title']",
            "input.jobs-search-box__text-input[name='keywords']",
            "input[aria-label*='title']",
            "input[data-tracking-control-name*='search']"
        ]
        
        keyword_field = None
        for selector in keyword_selectors:
            try:
                keyword_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                if keyword_field.is_displayed() and keyword_field.is_enabled():
                    break
            except:
                continue
                
        if not keyword_field:
            raise Exception("Could not find keyword search field")
            
        # Clear and fill keyword field
        self.driver.execute_script("arguments[0].value = '';", keyword_field)
        keyword_field.send_keys(self.keywords)
        
        # Find the location field
        location_selectors = [
            "input.jobs-search-box__text-input[aria-label*='location']",
            "input.jobs-search-box__text-input[name='location']",
            "input[aria-label*='location']"
        ]
        
        location_field = None
        for selector in location_selectors:
            try:
                location_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                if location_field.is_displayed() and location_field.is_enabled():
                    break
            except:
                continue
                
        if not location_field:
            raise Exception("Could not find location search field")
            
        # Clear and fill location field
        self.driver.execute_script("arguments[0].value = '';", location_field)
        location_field.send_keys(self.location)
        
        # Try to find and click search button
        search_button_selectors = [
            "button[data-control-name*='search']",
            "button[aria-label*='search']",
            "button.jobs-search-box__submit-button"
        ]
        
        for selector in search_button_selectors:
            try:
                search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if search_button.is_displayed() and search_button.is_enabled():
                    search_button.click()
                    return
            except:
                continue
                
        # If no button found, try Enter key
        location_field.send_keys(Keys.RETURN)
        
    def _try_search_with_javascript(self):
        """Try to search using direct JavaScript execution"""
        js_script = f"""
        // Find all input elements
        var inputs = document.querySelectorAll('input');
        var keywordInput = null;
        var locationInput = null;
        
        // Look for keyword and location inputs
        for (var i = 0; i < inputs.length; i++) {{
            var input = inputs[i];
            var ariaLabel = input.getAttribute('aria-label') || '';
            var placeholder = input.getAttribute('placeholder') || '';
            var name = input.getAttribute('name') || '';
            
            if (ariaLabel.includes('title') || placeholder.includes('title') || 
                name === 'keywords' || ariaLabel.includes('keyword') || 
                placeholder.includes('Search job titles')) {{
                keywordInput = input;
            }}
            
            if (ariaLabel.includes('location') || placeholder.includes('location') || 
                name === 'location') {{
                locationInput = input;
            }}
        }}
        
        // Fill in values if found
        if (keywordInput) {{
            keywordInput.value = '{self.keywords}';
            var event = new Event('input', {{ bubbles: true }});
            keywordInput.dispatchEvent(event);
        }}
        
        if (locationInput) {{
            locationInput.value = '{self.location}';
            var event = new Event('input', {{ bubbles: true }});
            locationInput.dispatchEvent(event);
        }}
        
        // Try to find and click a search button
        var buttons = document.querySelectorAll('button');
        var searchButton = null;
        
        for (var i = 0; i < buttons.length; i++) {{
            var button = buttons[i];
            var text = button.innerText || '';
            var ariaLabel = button.getAttribute('aria-label') || '';
            
            if (text.includes('Search') || ariaLabel.includes('search') || 
                button.classList.contains('jobs-search-box__submit')) {{
                searchButton = button;
                break;
            }}
        }}
        
        // Click search button if found
        if (searchButton) {{
            searchButton.click();
            return true;
        }}
        
        // If fields were found but no button, trigger enter key on location
        if (locationInput) {{
            var enterEvent = new KeyboardEvent('keydown', {{
                key: 'Enter',
                code: 'Enter',
                keyCode: 13,
                which: 13,
                bubbles: true
            }});
            locationInput.dispatchEvent(enterEvent);
            return true;
        }}
        
        return false;
        """
        
        result = self.driver.execute_script(js_script)
        if not result:
            raise Exception("JavaScript search approach failed")
            
    def _try_alternative_search_approach(self):
        """Use a completely different approach as last resort"""
        # Try clicking into global search first
        try:
            global_search = self.driver.find_element(By.CSS_SELECTOR, "input.search-global-typeahead__input")
            global_search.click()
            time.sleep(1)
            global_search.send_keys(f"{self.keywords} {self.location}")
            global_search.send_keys(Keys.RETURN)
            time.sleep(3)
            
            # Try to find and click on "Jobs" tab or filter
            jobs_tabs = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Jobs')]")
            if jobs_tabs:
                jobs_tabs[0].click()
                return
                
        except:
            pass
            
        # Direct URL navigation with parameters as last resort
        encoded_keywords = self.keywords.replace(' ', '%20')
        encoded_location = self.location.replace(' ', '%20')
        self.driver.get(f"https://www.linkedin.com/jobs/search/?keywords={encoded_keywords}&location={encoded_location}")
        time.sleep(5)
        
        # If we reached this point without errors, consider it successful

    def filter(self):
        """This function filters all the job results by 'Easy Apply'"""
        try:
            all_filters_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='All filters']")))
            all_filters_button.click()

            easy_apply_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//label[@for='f_AL']")))
            easy_apply_button.click()

            apply_filter_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Apply current filters to show results']")))
            apply_filter_button.click()

            print("Filtering results...")
        except TimeoutException:
            print("Filter step skipped due to timeout.")

    def find_offers(self):
        """This function finds all the offers"""
        print("Finding offers...")

        try:
            total_results = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "display-flex.t-12.t-black--light.t-normal")))
            total_results_int = int(total_results.text.split(' ', 1)[0].replace(",", ""))
            print(f"Total jobs found: {total_results_int}")
        except Exception:
            print("Couldn't find total results text, assuming few jobs...")
            total_results_int = 0

        current_page = self.driver.current_url
        results = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "job-card-container--clickable")))

        for result in results:
            try:
                hover = ActionChains(self.driver).move_to_element(result)
                hover.perform()
                title = result.find_element(By.CLASS_NAME, 'job-card-list__title')
                self.submit_apply(title)
            except Exception as e:
                print("Error while processing a job card:", e)
                continue

        if total_results_int > 24:
            try:
                find_pages = self.driver.find_elements(By.CLASS_NAME, "artdeco-pagination__indicator--number")
                total_pages = find_pages[-1].text
                total_pages_int = int(re.sub(r"[^\d.]", "", total_pages))

                for page_number in range(25, total_pages_int * 25 + 1, 25):
                    self.driver.get(current_page + f"&start={page_number}")
                    results_ext = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "job-card-container--clickable")))

                    for result_ext in results_ext:
                        try:
                            hover_ext = ActionChains(self.driver).move_to_element(result_ext)
                            hover_ext.perform()
                            title_ext = result_ext.find_element(By.CLASS_NAME, 'job-card-list__title')
                            self.submit_apply(title_ext)
                        except Exception as e:
                            print("Error while processing a job card on another page:", e)
                            continue
            except Exception as e:
                print("Pagination error:", e)

    def submit_apply(self, job_add):
        """This function submits the application"""
        print('You are applying to the position of:', job_add.text)
        job_add.click()

        try:
            in_apply = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'jobs-apply-button')]")))
            in_apply.click()
        except (NoSuchElementException, TimeoutException):
            print('No Easy Apply button, skipping...')
            return

        try:
            submit = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Submit application']")))
            submit.click()
            print('Application submitted.')
        except (NoSuchElementException, TimeoutException):
            print('Complex application, skipping...')
            try:
                discard = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Dismiss']")))
                discard.click()

                discard_confirm = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-test-dialog-primary-btn]")))
                discard_confirm.click()

                print("Application discarded.")
            except (NoSuchElementException, TimeoutException):
                print('Could not discard properly.')

    def close_session(self):
        """Close the browser"""
        print('End of the session, see you later!')
        self.driver.quit()

    def apply(self):
        """Main function to apply"""
        print("Applying for jobs...")
        self.login_linkedin()
        self.job_search()
        self.filter()
        self.find_offers()
        self.close_session()

if __name__ == '__main__':
    with open('config.json') as config_file:
        data = json.load(config_file)

    bot = EasyApplyLinkedin(data)
    bot.apply()

