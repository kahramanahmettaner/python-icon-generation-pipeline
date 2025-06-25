import time
import tkinter as tk
from glob import glob
import pandas as pd
from tkinter import filedialog, ttk
from openart import OpenArt
import threading
import functools
import os


def catch_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"An error occurred in {func.__name__}: {str(e)}")
    return wrapper


def run_in_thread(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()
    return wrapper


def threaded_catch_exceptions(func):
    @run_in_thread
    @catch_exceptions
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@threaded_catch_exceptions
def generate_click(openart_pipeline_ui):

    # create object
    openart = OpenArt()

    # Open Browser
    openart_pipeline_ui.set_status('Opening Browser...')
    openart.initialize_driver()

    # Navigate to openart (Waits until the page is fully loaded.)
    openart_pipeline_ui.set_status('Navigating to Open Art...')
    openart.navigate_to_website("https://openart.ai/create")

    # Load Cookies
    openart.load_cookies()

    # Navigate to openart (Waits until the page is fully loaded.)
    openart.navigate_to_website("https://openart.ai/create")

    openart_pipeline_ui.set_status('Closing overlays that could prevent the interaction with the actual page...')
    # Close google overlays
    openart.accept_funding_choices_consent()

    # Check if skip all is present and click if so
    while openart.is_skip_all_present() is True:
        openart.click_skip_all()
        time.sleep(0.2)

    # Close google overlays
    openart.close_google_consent_popup()

    # Set the number for images to generate for each prompt
    openart_pipeline_ui.set_status('Setting parameters...')
    openart.set_number_of_images_to_generate(openart_pipeline_ui.number_of_images_for_each_prompt.get())

    openart_pipeline_ui.set_status('Starting with image generation process...')
    # Find all Excel files (*.xlsx, *.xls) in the folder
    excel_paths = glob(os.path.join(openart_pipeline_ui.folder_path.get(), "*.xls*"))

    for index, excel_path in enumerate(excel_paths):

        try:
            # Read the Excel file
            df = pd.read_excel(excel_path)

            # Get the first column (image prompts)
            if not df.empty:
                first_column_name = df.columns[0]
                prompts = df[first_column_name].dropna().tolist()

                # Create a folder named after the Excel file (without extension)
                excel_name = os.path.splitext(os.path.basename(excel_path))[0]
                output_folder = os.path.join(openart_pipeline_ui.download_folder_path.get(), excel_name)
                os.makedirs(output_folder, exist_ok=True)

                # Call your processing function here
                generate_image_set(openart, prompts, openart_pipeline_ui, index, output_folder)

        except Exception as e:
            print(f"Failed to process {excel_path}: {e}")

        current_total_progress = ((index+1) / len(excel_paths)) * 100
        openart_pipeline_ui.set_total_progress(current_total_progress)


def generate_image_set(openart, image_prompts, openart_pipeline_ui, image_set_index, output_folder):

    # For each image prompt:
    for index, image_prompt in enumerate(image_prompts):

        openart_pipeline_ui.set_status(f'Starting with image {index+1} from image set {image_set_index+1}...')

        # Check if prompt area is present ???
        # Clean the prompt area ???

        # Enter the prompt
        openart.enter_prompt(image_prompt)

        # Check if the prompt is entered
        is_correct = openart.is_prompt_entered_correctly(image_prompt)
        if is_correct is False:
            pass

        # Check if the 'create' button is present
        openart.is_generate_button_present()

        openart_pipeline_ui.set_status(f'Generating image {index+1} from image set {image_set_index+1}...')
        # Click the 'create' button
        openart.click_generate()

        # Wait until loading state is finished
        # is_loading = True
        # while is_loading:
        #     time.sleep(1)
        #     is_loading = openart.is_generate_button_loading()

        completed = openart.wait_until_generation_complete()
        if completed is False:
            openart_pipeline_ui.set_status(f'Generation is failed image {index+1} from image set {image_set_index + 1}...')
            continue

        time.sleep(2)
        completed = openart.wait_until_generation_complete()
        if completed is False:
            openart_pipeline_ui.set_status(f'Generation is failed image {index+1} from image set {image_set_index + 1}...')
            continue

        time.sleep(2)
        completed = openart.wait_until_generation_complete()
        if completed is False:
            openart_pipeline_ui.set_status(f'Generation is failed image {index+1} from image set {image_set_index + 1}...')
            continue

        # Download the generated images
        openart_pipeline_ui.set_status(f'Downloading image {index} from image set {image_set_index+1}...')
        for image_index in range(0, int(openart_pipeline_ui.number_of_images_for_each_prompt.get())):
            openart.download_generated_image_as_png(image_index, image_prompt, output_folder)

        current_progress = ((index+1) / len(image_prompts)) * 100
        openart_pipeline_ui.set_current_progress(current_progress)


class OpenArtPipelineUI:
    def __init__(self, root):

        self.cookies_openart = OpenArt()

        self.root = root
        self.root.title("OpenArt Pipeline")

        # === START LAYOUT ===
        self.start = tk.Frame(root)

        # Login Button
        tk.Button(self.start, text="Login and Save Cookies", command=self.login_click).pack(pady=5)

        # Title
        title_label = tk.Label(self.start, text="OpenArt Pipeline", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        # Excel Folder Input
        file_frame = tk.Frame(self.start)
        file_frame.pack(pady=5)
        self.folder_path = tk.StringVar()
        tk.Label(file_frame, text="Excel Folder:").pack(side=tk.LEFT, padx=(0, 5))
        tk.Entry(file_frame, textvariable=self.folder_path, width=40).pack(side=tk.LEFT)
        tk.Button(file_frame, text="Browse", command=self.browse_folder).pack(side=tk.LEFT, padx=5)

        # Download Folder Input
        download_folder_frame = tk.Frame(self.start)
        download_folder_frame.pack(pady=5)
        tk.Label(download_folder_frame, text="Output Folder:").pack(side=tk.LEFT, padx=(0, 5))
        self.download_folder_path = tk.StringVar()
        tk.Entry(download_folder_frame, textvariable=self.download_folder_path, width=40).pack(side=tk.LEFT)
        tk.Button(download_folder_frame, text="Browse", command=self.browse_download_folder).pack(side=tk.LEFT, padx=5)

        # Parameters Section
        parameters_frame = tk.LabelFrame(self.start, text="Parameters", padx=10, pady=10)
        parameters_frame.pack(padx=10, pady=10, fill="x")

        # Dropdown for number of images
        dropdown_frame = tk.Frame(parameters_frame)
        dropdown_frame.pack(pady=5)
        tk.Label(dropdown_frame, text="Number of images to generate per prompt:").pack(side=tk.LEFT, padx=(0, 5))
        self.number_of_images_for_each_prompt = tk.StringVar(value="1")
        tk.OptionMenu(dropdown_frame, self.number_of_images_for_each_prompt, "1", "2", "3", "4").pack(side=tk.LEFT)

        # Start Button
        start_button = tk.Button(self.start, text="Start Image Generation", bg="green", fg="white",
                                 font=("Helvetica", 12, "bold"), command=self.start_generation)
        start_button.pack(pady=20)

        # === GENERATING LAYOUT ===
        self.generating_layout = tk.Frame(root)
        tk.Label(self.generating_layout, text="Generating Images", font=("Helvetica", 16, "bold")).pack(pady=10)

        self.status_label = tk.Label(self.generating_layout, text="Preparing...", font=("Helvetica", 12))
        self.status_label.pack(pady=10)

        self.progress_current_label = tk.Label(self.generating_layout, text="Current Image Set:", font=("Helvetica", 8))
        self.progress_current_label.pack(pady=10)
        self.progress_current = ttk.Progressbar(self.generating_layout, orient="horizontal", length=400,
                                                mode="determinate")
        self.progress_current.pack(pady=5)

        self.progress_total_label = tk.Label(self.generating_layout, text="All Image Sets:", font=("Helvetica", 8))
        self.progress_total_label.pack(pady=10)
        self.progress_total = ttk.Progressbar(self.generating_layout, orient="horizontal", length=400,
                                              mode="determinate")
        self.progress_total.pack(pady=5)

        # === GENERATED LAYOUT ===
        self.generated_layout = tk.Frame(root)
        tk.Label(self.generated_layout, text="Generation Process Finished", font=("Helvetica", 16, "bold")).pack(pady=20)

        restart_button = tk.Button(self.generated_layout, text="Start Over", command=lambda: self.update_layout("START"))
        restart_button.pack(pady=10)

        # === LOGIN LAYOUT ===
        self.login_layout = tk.Frame(root)
        tk.Label(self.login_layout, text="Login and Save Cookies", font=("Helvetica", 16, "bold")).pack(pady=20)

        back_to_start_button = tk.Button(self.login_layout, text="Back To Start", command=lambda: self.update_layout("START"))
        back_to_start_button.pack(pady=10)
        open_browser_button = tk.Button(self.login_layout, text="Open Browser", command=lambda: self.open_chrome)
        open_browser_button.pack(pady=10)
        save_cookies_button = tk.Button(self.login_layout, text="Save Cookies and Close Browser", command=lambda: self.save_cookies_and_close_chrome)
        save_cookies_button.pack(pady=10)

        self.update_layout('START')

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path.set(folder_path)

    def browse_download_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.download_folder_path.set(folder_path)

    def start_generation(self):
        # Update to generating layout
        self.update_layout("GENERATING")

        generate_click(self)

    def login_click(self):
        self.update_layout("LOGIN")

    def open_chrome(self):
        self.cookies_openart.initialize_driver()
        self.cookies_openart.navigate_to_website('https://openart.ai/create')

    def save_cookies_and_close_browser(self):
        self.cookies_openart.save_cookies()
        self.cookies_openart.close()

    def update_layout(self, state):
        self.start.pack_forget()
        self.generating_layout.pack_forget()
        self.generated_layout.pack_forget()
        self.login_layout.pack_forget()

        if state == 'START':
            self.start.pack()

        elif state == 'GENERATING':
            self.generating_layout.pack()

        elif state == 'GENERATED':
            self.generated_layout.pack()

        elif state == 'LOGIN':
            self.login_layout.pack()

    def set_status(self, message):
        """Updates the status label in the generating layout."""
        self.status_label.config(text=message)
        self.status_label.update_idletasks()

    def set_current_progress(self, value):
        """Sets progress value for the current image set (0-100)."""
        self.progress_current['value'] = value
        self.progress_current.update_idletasks()

    def set_total_progress(self, value):
        """Sets progress value for overall image sets (0-100)."""
        self.progress_total['value'] = value
        self.progress_total.update_idletasks()
