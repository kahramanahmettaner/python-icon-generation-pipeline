import time
import os
import json
import requests
import os
import mimetypes
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class OpenArt:
    COOKIE_FILE = "openart_cookies.json"
    
    def __init__(self, headless=False):
        """Initialize the WebDriver with automatic driver management"""
        self.browser = 'chrome'
        self.headless = headless
        self.driver = None

    def is_browser_ready(self):
        try:
            self.driver.get("about:blank")
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except:
            return False

    def initialize_driver(self):
        try:
            options = Options()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            if self.headless:
                options.add_argument('--headless')
            service = ChromeService(ChromeDriverManager().install())

            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_window_size(1280, 1024)
            print(f"Initialized {self.browser} browser {'in headless mode' if self.headless else ''}")
        except Exception as e:
            print(f"Failed to initialize WebDriver: {str(e)}")
            raise RuntimeError(f"Failed to initialize WebDriver: {str(e)}")

    def navigate_to_website(self, url):
        """Navigate to the specified website URL"""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        
        print(f"Navigating to: {url}")
        self.driver.get(url)

        # Wait until the page is fully loaded
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("Page fully loaded.")
        except Exception as e:
            print(f"Timeout waiting for page to load: {str(e)}")
            raise RuntimeError(f"Timeout waiting for page to load: {str(e)}")

    def is_prompt_entered_correctly(self, expected_prompt):
        """Check if the expected prompt text is present in the prompt field"""
        try:
            prompt_area = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "textarea.MuiInputBase-input[placeholder*='e.g. A cat']"
                ))
            )
            current_value = prompt_area.get_attribute("value")
            is_match = current_value.strip() == expected_prompt.strip()
            print(f"Prompt match: {is_match} (Expected: '{expected_prompt}', Found: '{current_value}')")
            return is_match
        except Exception as e:
            print(f"Failed to verify prompt text: {str(e)}")
            return False

    def enter_prompt(self, prompt_text):
        """Enter the prompt text into the prompt field"""
        try:
            prompt_area = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "textarea.MuiInputBase-input[placeholder*='e.g. A cat']"
                ))
            )
            prompt_area.send_keys(Keys.CONTROL + "a")
            prompt_area.send_keys(Keys.DELETE)
            prompt_area.send_keys(prompt_text)
            print(f"Entered prompt: '{prompt_text}'")
            return True
        except Exception as e:
            print(f"Failed to enter prompt: {str(e)}")
            return False

    def set_number_of_images_to_generate(self, number):
        try:
            # Wait for input based on label text
            label = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'Number of Images')]"))
            )

            container = label.find_element(By.XPATH, "..")  # parent div
            input_field = container.find_element(By.XPATH, ".//input[@type='number']")

            # Scroll into view and click to focus
            self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
            input_field.click()
            input_field.send_keys(Keys.CONTROL + "a")  # select all
            input_field.send_keys(str(number))  # enter number
            input_field.send_keys(Keys.TAB)  # blur to trigger change event

            print(f"Successfully set number to {number}")
            return True

        except Exception as e:
            print(f"Failed to set number: {e}")
            return False

    def count_generated_images(self):
        try:
            # Wait for the generation history container to be present
            container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "create-generation-histories"))
            )
            print("Generation history container found.")

            # Find all <img> tags within that container
            images = container.find_elements(By.TAG_NAME, "img")
            print(f"Found {len(images)} image(s) in the generation history.")

            return images  # Optional: return the elements if needed elsewhere
        except Exception as e:
            print(f"Failed to count images: {e}")
            return []

    def wait_until_generation_complete(self, timeout=60):
        """
        Waits until image generation is complete on OpenArt.
        Assumes images are loading in `.create-generation-histories` container.
        """
        print("Waiting for image generation to complete...")

        try:
            # Wait until the container is present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "create-generation-histories"))
            )

            # Now wait until no placeholder.svg OR circular progress spinners remain
            WebDriverWait(self.driver, timeout).until(
                lambda d: not d.find_elements(By.XPATH, "//img[contains(@src, 'placeholder.svg')]")
                          and not d.find_elements(By.CLASS_NAME, "MuiCircularProgress-root")
            )

            print("Image generation completed.")
            return True

        except Exception as e:
            print(f"Timeout or error waiting for generation to finish: {e}")
            return False

    def print_content_of_generation_histories(self):
        try:
            # Wait for the generation history container to be present
            container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "create-generation-histories"))
            )
            print("Generation history container found.")

            html_content = container.get_attribute("outerHTML")
            print(html_content)

        except Exception as e:
            print(f"Failed to find container: {e}")

    def download_generated_image_as_png(self, index, image_name=None, download_folder="downloads"):
        try:
            if image_name is None:
                image_name = f'image_{index}'
            os.makedirs(download_folder, exist_ok=True)

            container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "create-generation-histories"))
            )

            images = container.find_elements(By.TAG_NAME, "img")
            if index >= len(images):
                print(f"Index {index} is out of range. Only {len(images)} image(s) found.")
                return False

            image_element = images[index]
            image_url = image_element.get_attribute("src")

            if not image_url:
                print(f"Image at index {index} has no src attribute.")
                return False

            response = requests.get(image_url)
            if response.status_code != 200:
                print(f"Failed to download image. HTTP Status Code: {response.status_code}")
                return False

            # WebP içeriğini bellekte tut
            image_bytes = BytesIO(response.content)

            # WebP'yi PIL ile aç ve PNG olarak kaydet
            with Image.open(image_bytes) as img:
                png_filename = f"{image_name}.png"
                path = os.path.join(download_folder, png_filename)
                img.save(path, format="PNG")

            print(f"Image saved as PNG: {path}")
            return True

        except Exception as e:
            print(f"Error downloading or converting image at index {index}: {e}")
            return False

    def is_generate_button_present(self):
        """Check if the 'Create' (generate) button is present and clickable"""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[.//span[text()='Create']]"
                ))
            )
            print("'Create' button is present and clickable.")
            return True
        except Exception as e:
            print(f"'Create' button not present: {str(e)}")
            return False

    def click_generate(self):
        """Click the generate button to create the image"""
        try:
            generate_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((
                    # By.CSS_SELECTOR, 
                    # "button[id*='Create'][class*='MuiButton-root']"
                    By.XPATH,
                    "//button[.//span[text()='Create']]"
                ))
            )

            # self.is_generate_button_loading()
            self.count_generated_images()
            self.print_content_of_generation_histories()
            generate_button.click()
            time.sleep(0.3)
            self.count_generated_images()
            self.print_content_of_generation_histories()
            # self.is_generate_button_loading()
            print("Clicked generate button")
            return True
        except Exception as e:
            print(f"Failed to click generate button: {str(e)}")
            return False

    def is_generate_button_loading(self):
        """Check if the generate button is in a loading state using multiple strategies"""
        try:
            generate_button = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//button[.//span[text()='Create']]"
                ))
            )

            # 1. Spinner check
            spinner_present = len(
                generate_button.find_elements(By.XPATH, ".//*[contains(@class, 'MuiCircularProgress')]")) > 0

            # 2. Disabled attribute
            is_disabled = generate_button.get_attribute("disabled") is not None

            # Result
            is_loading = spinner_present or is_disabled
            print(f"Loading state: spinner={spinner_present}, disabled={is_disabled} → {is_loading}")
            return is_loading

        except Exception as e:
            print(f"Error checking loading state: {str(e)}")
            return False

    def is_skip_all_present(self):
        """Check if the 'Skip All' button is present and clickable"""
        try:
            WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(text(), 'Skip All')]"
                ))
            )
            print("'Skip All' button is present and clickable.")
            return True
        except Exception as e:
            print(f"'Skip All' button not present: {str(e)}")
            return False

    def click_google_menu_button(self, timeout=10):
        try:
            # Wait until the ft-menu container appears
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.ft-menu"))
            )

            # Try to locate the button directly (non-shadow DOM)
            try:
                menu_button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ft-menu button.ft-styless-button"))
                )
                menu_button.click()
                print("Clicked menu button (standard DOM).")
                return
            except Exception:
                pass  # fallback to JS method below

            # Try clicking using JavaScript in case of shadow DOM or issues
            script = """
            const menu = document.querySelector("div.ft-menu");
            if (!menu) return "Menu not found";

            const button = menu.querySelector("button.ft-styless-button");
            if (!button) return "Button not found";

            button.click();
            return "Clicked";
            """
            result = self.driver.execute_script(script)
            print("JS click result:", result)

        except Exception as e:
            print("Failed to click the menu button:", str(e))

    def close_google_consent_popup(self, timeout=10):
        try:
            # Step 1: Try switching into any iframe that might contain the toolbar
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for index, iframe in enumerate(iframes):
                try:
                    self.driver.switch_to.frame(iframe)
                    result = self.driver.execute_script("""
                        return !!document.querySelector('body')
                    """)
                    if result:
                        toolbar_present = self.driver.execute_script("""
                            const deepQuery = (selector, root = document) => {
                                const result = [];
                                const walk = (node) => {
                                    if (!node) return;
                                    if (node.matches && node.matches(selector)) result.push(node);
                                    if (node.shadowRoot) walk(node.shadowRoot);
                                    if (node.children) for (const child of node.children) walk(child);
                                };
                                walk(root);
                                return result;
                            };
                            return deepQuery('#ft-floating-toolbar').length > 0;
                        """)
                        if toolbar_present:
                            print(f"Toolbar found in iframe index {index}")
                            break
                    self.driver.switch_to.default_content()
                except Exception:
                    self.driver.switch_to.default_content()

            # Step 2: Check again with possible Shadow DOM
            self.driver.switch_to.default_content()
            shadow_button = WebDriverWait(self.driver, timeout).until(lambda d: d.execute_script("""
                const deepQuery = (selector, root = document) => {
                    const result = [];
                    const walk = (node) => {
                        if (!node) return;
                        if (node.matches && node.matches(selector)) result.push(node);
                        if (node.shadowRoot) walk(node.shadowRoot);
                        if (node.children) for (const child of node.children) walk(child);
                    };
                    walk(root);
                    return result;
                };

                const toolbar = deepQuery('#ft-floating-toolbar')[0];
                if (!toolbar) return null;

                const buttons = toolbar.shadowRoot
                  ? toolbar.shadowRoot.querySelectorAll('button.ft-reg-bubble-close')
                  : toolbar.querySelectorAll('button.ft-reg-bubble-close');

                if (buttons.length) {
                    buttons[0].click();
                    return true;
                }
                return false;
            """))
            if shadow_button:
                print("✅ Consent popup closed via shadow DOM.")
            else:
                print("❌ Consent close button not found.")
        except TimeoutException:
            print("⏳ Timeout: Toolbar not found.")
        except Exception as e:
            print("❌ Failed to close toolbar:", e)

    def accept_funding_choices_consent(self, timeout=10):
        try:
            # Wait for the consent dialog to appear
            consent_button = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".fc-button.fc-cta-consent"))
            )
            consent_button.click()
            print("Funding Choices consent accepted.")
        except Exception as e:
            print("Funding Choices consent dialog not found or already handled.", str(e))

    def click_skip_all(self):
        """Click the skip all button"""
        try:
            skip_all_button = WebDriverWait(self.driver, 0).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(text(), 'Skip All')]"
                ))
            )
            skip_all_button.click()
            print("Clicked skip all button")
            return True
        except Exception as e:
            print(f"Failed to click skip all button: {str(e)}")
            return False

    def generate_image_with_prompt(self, prompt_text):
        """Complete workflow: enter prompt and generate image"""
        if not self.enter_prompt(prompt_text):
            return False
        return self.generate_image()
    
    def close(self):
        """Clean up and close the browser"""
        if self.driver:
            print("Closing browser")
            self.driver.quit()
            self.driver = None

    def load_cookies(self):
        if not self.driver:
            print("Driver not initialized, can't load cookies.")
            return

        if os.path.exists(self.COOKIE_FILE):
            with open(self.COOKIE_FILE, "r") as f:
                cookies = json.load(f)
            for cookie in cookies:
                cookie.pop('sameSite', None)  # Remove sameSite if present
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Failed to add cookie: {cookie} due to {e}")
            print("Cookies loaded.")
        else:
            print("No cookies file found.")

    def save_cookies(self):
        if not self.driver:
            print("Driver not initialized, can't save cookies.")
            return

        cookies = self.driver.get_cookies()
        with open(self.COOKIE_FILE, "w") as f:
            json.dump(cookies, f)
        print("Cookies saved.")