import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
from pydub import AudioSegment
import requests
import json
import threading
import pyperclip

import tempfile
import datetime

from pydub.exceptions import CouldntDecodeError
import logging

# Configurazione della chiave API di OpenAI
API_KEY = 'Qui_la_Tua_Chiave_Open_AI'

class PodcastGeneratorGUI:
    def __init__(self, master):
        self.master = master
        master.title("Podcast Generator")
        master.geometry("800x800")
        
        style = ttk.Style("united")

        # Load configuration
        self.config = self.load_configuration()

        self.create_widgets()

        # Set initial values from config
        self.prompt_text.delete("1.0", END)  # Clear any existing text
        self.prompt_text.insert(END, self.config['prompt'])  # Insert the loaded prompt
        self.text_file_path.set(self.config['last_text_file'])
        self.music_file_path.set(self.config['last_music_file'])

    def load_configuration(self):
        config_file = 'config.json'
        default_config = {
            "prompt": """Crea un dialogo in italiano tra due personaggi, Alessia (voce femminile) e Marco (voce maschile), che discutono in un avvincente podcast di "AI, MAX" del seguente testo scritto da Massimiliano Turazzini. I personaggi sono esperti di intelligenza artificiale e conoscono bene Max Turazzini e si riferiscono a lui come Max. Il dialogo deve essere coinvolgente, informativo e riassumere i punti chiave del testo. 
            ...
            Marca i nomi come **Alessia** e **Marco** nel dialogo per identificare chi parla."""
        }

        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Ensure the prompt is set correctly
                if 'prompt' in config:
                    return config
        return default_config

    def save_configuration(self):
        config_file = 'config.json'
        config_data = {
            "prompt": self.prompt_text.get("1.0", END).strip(),
            "characters": {
                "Alessia": "alloy",
                "Marco": "onyx"
            },
            "last_text_file": self.text_file_path.get(),
            "last_music_file": self.music_file_path.get(),
            "openai_model": "gpt-4o-mini"
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=4)

    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding="20 20 20 20")
        main_frame.pack(fill=BOTH, expand=YES)

        # Title
        title_label = ttk.Label(main_frame, text="AI Podcast Generator", font=("TkDefaultFont", 24, "bold"))
        title_label.pack(pady=20)

        # Text file selection
        text_frame = ttk.LabelFrame(main_frame, text="Select Text File", padding="10 5 10 10")
        text_frame.pack(fill=X, expand=YES, pady=10)

        self.text_file_path = tk.StringVar()
        text_entry = ttk.Entry(text_frame, textvariable=self.text_file_path)
        text_entry.pack(side=LEFT, expand=YES, fill=X, padx=(0, 10))

        text_button = ttk.Button(text_frame, text="Choose File", command=self.select_text_file)
        text_button.pack(side=RIGHT)

        # Music file selection
        music_frame = ttk.LabelFrame(main_frame, text="Select Music File (Optional)", padding="10 5 10 10")
        music_frame.pack(fill=X, expand=YES, pady=10)

        self.music_file_path = tk.StringVar()
        music_entry = ttk.Entry(music_frame, textvariable=self.music_file_path)
        music_entry.pack(side=LEFT, expand=YES, fill=X, padx=(0, 10))

        music_button = ttk.Button(music_frame, text="Choose File", command=self.select_music_file)
        music_button.pack(side=RIGHT)

        # Prompt customization
        prompt_frame = ttk.LabelFrame(main_frame, text="Customize Prompt", padding="10 5 10 10")
        prompt_frame.pack(fill=BOTH, expand=YES, pady=10)

        self.prompt_text = ttk.Text(prompt_frame, height=6, wrap=WORD)
        self.prompt_text.pack(fill=BOTH, expand=YES)
        self.prompt_text.insert(END, """Crea un dialogo in italiano tra due personaggi, Alessia (voce femminile) e Marco (voce maschile), che discutono in un avvincente podcast del seguente testo scritto da Massimiliano Turazzini. I personaggi sono esperti di intelligenza artificiale e conoscono bene Max Turazzini e si riferiscono a lui come Max. Il dialogo deve essere coinvolgente, informativo e riassumere i punti chiave del testo. Marca i nomi come **Alessia** e **Marco**.""")

        # Frame for buttons and checkbox
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        # Toggle for saving configuration
        self.save_config_var = tk.BooleanVar(value=False)  # Default is disabled
        save_config_switch = ttk.Checkbutton(button_frame, text="Save Configuration", variable=self.save_config_var)
        save_config_switch.pack(side=LEFT, padx=(0, 10))

        # Generate Script button
        generate_script_button = ttk.Button(button_frame, text="Generate Script", command=self.generate_script, style="success.TButton")
        generate_script_button.pack(side=LEFT, padx=(0, 10))

        # Generate Podcast button
        generate_podcast_button = ttk.Button(button_frame, text="Generate Podcast", command=self.generate_podcast, style="success.TButton")
        generate_podcast_button.pack(side=LEFT)

        # Progress bar
        self.progress_var = ttk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100, style="success.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=X, expand=YES, pady=10)

        # Status label
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, wraplength=750)
        self.status_label.pack(pady=10)

        # Generated Script Display
        script_frame = ttk.LabelFrame(main_frame, text="Generated Script", padding="10 5 10 10")
        script_frame.pack(fill=BOTH, expand=YES, pady=10)

        self.script_text = ttk.Text(script_frame, height=10, wrap=WORD)
        self.script_text.pack(fill=BOTH, expand=YES)

        # Copy Script Button
        self.copy_button = ttk.Button(main_frame, text="Copy Script", command=self.copy_script, state=DISABLED)
        self.copy_button.pack(pady=10)

    def select_text_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        self.text_file_path.set(file_path)

    def select_music_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("MP3 Files", "*.mp3")])
        self.music_file_path.set(file_path)

    def generate_script(self):
        text_file = self.text_file_path.get()
        custom_prompt = self.prompt_text.get("1.0", END).strip()

        if not text_file:
            messagebox.showerror("Error", "Please select a text file.")
            return

        # Clear previous script
        self.script_text.delete("1.0", END)
        self.copy_button.config(state=DISABLED)

        # Start script generation in a separate thread
        threading.Thread(target=self.generate_script_thread, args=(text_file, custom_prompt)).start()

    def generate_script_thread(self, text_file, custom_prompt):
        try:
            self.update_status("Reading text file...", 10)
            with open(text_file, 'r', encoding='utf-8') as file:
                content = file.read()

            self.update_status("Generating dialogue...", 20)
            dialogue = self.generate_dialogue(content, custom_prompt)

            if dialogue is None:
                self.update_status("Error in dialogue generation.")
                return

            # Display the generated script
            self.master.after(0, self.display_script, dialogue)

            # Save configuration if the toggle is enabled
            if self.save_config_var.get():
                self.save_configuration()

        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))

    def generate_podcast(self):
        music_file = self.music_file_path.get()
        custom_prompt = self.prompt_text.get("1.0", END).strip()

        # Get the script from the text area
        script = self.script_text.get("1.0", END).strip()
        if not script:
            messagebox.showerror("Error", "Please generate a script first.")
            return

        # Start podcast generation in a separate thread
        threading.Thread(target=self.generate_podcast_thread, args=(script, music_file)).start()

    def generate_podcast_thread(self, script, music_file):
        try:
            self.update_status("Splitting dialogue...", 30)
            combined_lines = self.split_dialogue(script)  # Get a single list of tuples

            # Define the voice map
            voice_map = {
                "Alessia": "alloy",  # Replace with the actual voice identifier for Alessia
                "Marco": "onyx"      # Replace with the actual voice identifier for Marco
            }

            # Generate audio for combined lines
            self.update_status("Generating audio...", 40)
            audio_files = self.generate_audio(combined_lines, voice_map)  # Pass the combined lines

            # Combine audio files
            self.update_status("Combining audio files...", 80)
            output_file = self.combine_audio(audio_files, music_file)  # Combine all audio files

            self.update_status("Cleaning up temporary files...", 90)
            self.cleanup_files(audio_files)  # Clean up the generated audio files

            # Notify success
            self.update_status("Podcast generated successfully as '{}'".format(output_file))

        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))

    def update_status(self, message, progress=None):
        self.status_var.set(message)
        if progress is not None:
            self.progress_var.set(progress)
        else:
            self.progress_bar.pack_forget()  # Hide the progress bar when done

    def display_script(self, script):
        self.script_text.delete("1.0", END)
        self.script_text.insert(END, script)
        self.copy_button.config(state=NORMAL)

        # Enable editing of the script
        self.script_text.config(state=tk.NORMAL)  # Allow editing

    def copy_script(self):
        script = self.script_text.get("1.0", END).strip()
        pyperclip.copy(script)
        messagebox.showinfo("Copied", "Script copied to clipboard!")

    def call_openai_api(self, prompt, api_key):
        url = 'https://api.openai.com/v1/chat/completions'
        data = {
            'model': 'gpt-4o-mini',
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.update_status('Sending request to GPT model...')
        response = requests.post(url, headers=headers, json=data)
        self.update_status('Response received from GPT model.')
        if response.status_code == 200:
            response_data = response.json()
            result = response_data['choices'][0]['message']['content'].strip()
            logging.info(f"Received response from OpenAI API: {result}")  # Log the response
            return result
        else:
            self.update_status(f"API Error: {response.status_code} - {response.text}")
            logging.error(f"API Error: {response.status_code} - {response.text}")  # Log the error
            return None

    def generate_dialogue(self, content, custom_prompt):
        prompt = f"{custom_prompt}\n\nTesto:\n\"\"\"\n{content}\n\"\"\""
        return self.call_openai_api(prompt, API_KEY)

    def split_dialogue(self, dialogue):
        logging.info(f"Raw dialogue received for splitting: {dialogue}")  # Log the raw dialogue
        lines = dialogue.split('\n')
        combined_lines = []
        
        for line in lines:
            if "Alessia" in line[:20]:  # Check the first 20 characters
                combined_lines.append(("Alessia", line.strip()))
            elif "Marco" in line[:20]:  # Check the first 20 characters
                combined_lines.append(("Marco", line.strip()))
        
        logging.info(f"Total lines processed: {len(combined_lines)}")  # Log the number of lines
        return combined_lines

    def text_to_speech(self, text, voice, filename):
        self.update_status(f"Generating audio for: \"{text[:50]}...\"")
        url = 'https://api.openai.com/v1/audio/speech'
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': 'tts-1',
            'input': text,
            'voice': voice,
            'response_format': 'mp3'
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
        else:
            self.update_status(f"TTS Error: {response.status_code} - {response.text}")

    def verifica_mp3(self, file_path):
        try:
            audio = AudioSegment.from_mp3(file_path)
            if len(audio) == 0:
                raise ValueError(f"Audio file is empty: {file_path}")
            logging.info(f"Successfully verified MP3 file: {file_path}")
            return True
        except CouldntDecodeError:
            logging.error(f"Failed to decode MP3 file: {file_path}")
            return False
        except Exception as e:
            logging.error(f"Error verifying MP3 file {file_path}: {str(e)}")
            return False

    def generate_audio(self, combined_lines, voice_map):
        audio_files = []
        temp_dir = tempfile.mkdtemp()
        logging.info(f"Using temporary directory: {temp_dir}")

        for idx, item in enumerate(combined_lines):
            # Log the item to see its structure
            logging.info(f"Processing item {idx}: {item}")
            
            # Ensure that the item is a tuple with exactly two elements
            if len(item) != 2:
                logging.error(f"Unexpected item format: {item}")
                continue  # Skip this item if it doesn't have the expected format

            character, line = item  # Unpack the tuple
            filename = os.path.join(temp_dir, f"{character.lower()}_{idx}.mp3")
            try:
                self.update_status(f"Generating audio for {character} line {idx + 1} of {len(combined_lines)}...")
                voice = voice_map.get(character)  # Get the voice based on the character
                self.text_to_speech(line, voice, filename)
                
                # Verify the generated MP3 file
                if self.verifica_mp3(filename):
                    audio_files.append(filename)
                else:
                    raise ValueError(f"Generated file is not a valid MP3: {filename}")
                
                self.progress_var.set((idx + 1) / len(combined_lines) * 100)
            except Exception as e:
                logging.error(f"Error generating audio for {character} line {idx + 1}: {str(e)}")
                self.update_status(f"Error generating audio for {character} line {idx + 1}: {str(e)}")
                self.cleanup_files(audio_files)
                raise

        logging.info(f"Successfully generated {len(audio_files)} audio files.")
        self.update_status(f"Successfully generated {len(audio_files)} audio files.")
        return audio_files

    def combine_audio(self, audio_files, background_music_file):
        self.update_status("Combining audio files...")
        logging.info("Starting audio combination process")
        combined = AudioSegment.empty()
        
        try:
            for file in audio_files:
                if not self.verifica_mp3(file):  # Check validity
                    raise ValueError(f"Invalid MP3 file: {file}")
                audio = AudioSegment.from_mp3(file)
                combined += audio
                logging.info(f"Added audio file to combination: {file}")

            if background_music_file and os.path.exists(background_music_file):
                if not self.verifica_mp3(background_music_file):
                    raise ValueError(f"Invalid background music file: {background_music_file}")
                background_music = AudioSegment.from_mp3(background_music_file)
                
                # Lower the volume of the background music by 20%
                background_music = background_music - 20  # Reduce volume by 20 dB

                if len(background_music) < len(combined):
                    background_music = background_music * (len(combined) // len(background_music) + 1)
                background_music = background_music[:len(combined)]  # Match length
                combined = combined.overlay(background_music)
                logging.info("Added background music with reduced volume")

            # Get current date and time for the filename
            timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
            output_file = f"podcast_{timestamp}.mp3"  # Construct the filename with timestamp
            combined.export(output_file, format="mp3", bitrate="192k")
            logging.info(f"Successfully exported combined audio to {output_file}")
            self.update_status("Podcast generated successfully.")
            
            # Verify the final file
            if not self.verifica_mp3(output_file):
                raise ValueError("Final podcast file is invalid")

        except Exception as e:
            logging.error(f"Error in combine_audio: {str(e)}")
            self.update_status(f"Error combining audio: {str(e)}")
            raise

        return output_file
    
    def cleanup_files(self, file_list):
        for file in file_list:
            if os.path.exists(file):
                os.remove(file)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.DEBUG, filename='podcast_generator.log', filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s')

    root = ttk.Window()
    app = PodcastGeneratorGUI(root)
    root.mainloop()
