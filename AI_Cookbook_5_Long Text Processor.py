# Questo script Python utilizza un'interfaccia grafica per elaborare testi lunghi utilizzando modelli di linguaggio (LLM).
# È possibile personalizzare diverse variabili per adattare lo script alle proprie esigenze.

# Chiavi API:
# - self.api_key: La chiave API per accedere ai servizi di OpenAI. Sostituisci 'YOUR_OPENAI_API_KEY' con la tua chiave API effettiva.
# - self.groq_api_key: La chiave API per accedere ai servizi di Groq. Sostituisci 'YOUR_GROQ_API_KEY' con la tua chiave API effettiva.

# Modelli:
# - self.model_name: Nome del modello OpenAI da utilizzare (ad esempio, 'gpt-4o-mini'). Puoi modificarlo in base ai modelli disponibili per il tuo account OpenAI.

# Limiti di Token:
# - self.max_total_tokens: Il limite massimo di token che il modello può gestire (ad esempio, 4000 per molti modelli OpenAI). Regola questo valore in base al modello selezionato e alle tue esigenze.

# Prompt Personalizzati:
# - Nel metodo update_prompt(), puoi personalizzare i prompt predefiniti per i diversi compiti ('correzione', 'traduzione', 'riassunto'). Assicurati di includere '{chunk}' dove desideri inserire il testo del segmento.

# Modello Groq:
# - Nel metodo call_groq_api(), il parametro 'model' specifica il modello Groq da utilizzare (ad esempio, 'llama-3.2-3b-preview'). Modificalo in base ai modelli disponibili per il tuo account Groq.

# Istruzioni per Groq:
# - La variabile 'instructions_to_use' nel metodo call_groq_api() può essere impostata con istruzioni specifiche per il modello Groq. Puoi personalizzarla o renderla configurabile se necessario.

# Selezione dell'API:
# - self.api_var: Variabile che determina quale API utilizzare per l'elaborazione ('OpenAI' o 'Groq'). È associata al menu a tendina nell'interfaccia grafica.

# Lingua per la Traduzione:
# - self.language_var: Specifica la lingua di destinazione per il compito di traduzione. Puoi modificarla tramite l'interfaccia grafica.

# Parametri Aggiuntivi:
# - encoding: Nel metodo split_text(), specifica l'encoding utilizzato per calcolare i token. Assicurati che sia compatibile con il modello selezionato.

# Note Importanti:
# - Assicurati di aver installato tutte le librerie necessarie, inclusa la libreria client di Groq.
# - Gestisci le chiavi API in modo sicuro e non includerle in codice condiviso pubblicamente.
# - Personalizza i prompt e i modelli in base alle tue esigenze specifiche.


# Configura la tua API Key in modo sicuro (ad esempio, usando variabili d'ambiente)
openai_api_key =  'la_tua_api_key'

GROQ_API_KEY='la_tua_api_key'

import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import threading
import openai
import tiktoken
import logging
import requests
import groq
from ttkthemes import ThemedTk

# Configura il logging
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='w')

class ModernTextProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Elaborazione Testo con LLM')
        
        # Configurazione base della finestra
        self.root.geometry('1280x800')
        
        # Variabili
        self.api_key = openai_api_key
        self.groq_api_key = GROQ_API_KEY
        self.groq_model = "llama-3.2-3b-preview"
        self.model_name = 'gpt-4o-mini'
        self.max_total_tokens = 40000
        
        # Stile
        self.setup_styles()
        
        # Layout principale
        self.create_main_layout()
        
        # Inizializza il prompt
        self.task_var.trace('w', self.on_task_change)
        self.language_var.trace('w', self.update_prompt)
        self.on_task_change()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('Main.TFrame', padding=10)
        style.configure('Control.TFrame', padding=5)
        style.configure('TButton', padding=5)
        style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Status.TLabel', padding=5)
        
    def create_main_layout(self):
        # Container principale con tre colonne
        main_container = ttk.Frame(self.root, style='Main.TFrame')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Colonna sinistra (300px) - Input
        left_frame = ttk.Frame(main_container, width=300)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        input_label = ttk.Label(left_frame, text='Testo Originale', style='Header.TLabel')
        input_label.pack(anchor='w', pady=(0, 5))
        
        self.input_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD)
        self.input_text.pack(fill='both', expand=True)
        
        load_button = ttk.Button(left_frame, text='Carica da File', command=self.load_text_from_file)
        load_button.pack(pady=5)
        
        # Colonna centrale (80px) - Controlli
        center_frame = ttk.Frame(main_container, width=80)
        center_frame.pack(side='left', fill='y', padx=5)
        
        # Gruppo Compito
        task_frame = ttk.LabelFrame(center_frame, text='Compito', padding=5)
        task_frame.pack(fill='x', pady=5)
        
        self.task_var = tk.StringVar(value='correzione')
        task_menu = ttk.OptionMenu(task_frame, self.task_var, 'correzione', 
                                 'correzione', 'traduzione', 'riassunto', 'personalizzato')
        task_menu.pack(fill='x')
        
        # Gruppo Lingua
        lang_frame = ttk.LabelFrame(center_frame, text='Lingua', padding=5)
        lang_frame.pack(fill='x', pady=5)
        
        self.language_var = tk.StringVar(value='english')
        self.language_entry = ttk.Entry(lang_frame, textvariable=self.language_var)
        self.language_entry.pack(fill='x')
        
        # Gruppo API
        api_frame = ttk.LabelFrame(center_frame, text='API', padding=5)
        api_frame.pack(fill='x', pady=5)
        
        self.api_var = tk.StringVar(value='OpenAI')
        api_menu = ttk.OptionMenu(api_frame, self.api_var, 'OpenAI', 'OpenAI', 'Groq')
        api_menu.pack(fill='x')
        
        # Gruppo Prompt
        prompt_frame = ttk.LabelFrame(center_frame, text='Prompt', padding=5)
        prompt_frame.pack(fill='both', expand=True, pady=5)
        
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, wrap=tk.WORD, height=10)
        self.prompt_text.pack(fill='both', expand=True)
        
        # Pulsante Elabora
        process_button = ttk.Button(center_frame, text='Inizia', command=self.start_processing)
        process_button.pack(fill='x', pady=5)
        
        # Colonna destra - Output
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        output_label = ttk.Label(right_frame, text='Testo Elaborato', style='Header.TLabel')
        output_label.pack(anchor='w', pady=(0, 5))
        
        self.output_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD)
        self.output_text.pack(fill='both', expand=True)
        
        # Barra di stato in basso
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill='x', pady=5)
        
        self.status_var = tk.StringVar(value='Pronto')
        status_label = ttk.Label(status_frame, textvariable=self.status_var, style='Status.TLabel')
        status_label.pack(side='left')
        
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        progress_bar.pack(side='right', fill='x', expand=True, padx=(10, 0))

    # Il resto dei metodi rimane invariato
    def load_text_from_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("Word Documents", "*.docx")])
        if file_path:
            if file_path.endswith('.docx'):
                from docx import Document
                doc = Document(file_path)
                full_text = []
                for para in doc.paragraphs:
                    full_text.append(para.text)
                self.input_text.delete(1.0, tk.END)
                self.input_text.insert(tk.END, '\n'.join(full_text))
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    self.input_text.delete(1.0, tk.END)
                    self.input_text.insert(tk.END, text)
            else:
                messagebox.showerror("Errore", "Formato file non supportato.")

    def update_prompt(self, *args):
        task = self.task_var.get()
        if task == 'correzione':
            default_prompt = """Agisci come trascrittore esperto di messaggi audio. Ti fornirò una trascrizione da ripulire e formattare. Segui queste istruzioni:

- **Pulisci** il testo da errori grammaticali e di punteggiatura, senza riassumere o omettere informazioni.
- **Riorganizza frasi caotiche** in espressioni complete e coerenti, mantenendo l'intenzione comunicativa originale.
- **Rendi leggibile** la trascrizione, strutturandola in paragrafi brevi. Usa un dialogo chiaro con segnaposti per chi parla (es. "Speaker 1", "Speaker 2").
- **Elimina intercalari** come "sì, sì", "insomma", "ecco" e riformula le frasi per una lettura più naturale.
- **Migliora la fluidità** del dialogo eliminando pause inutili o esitazioni, ma mantenendo il tono originale.
- Utilizza una **punteggiatura informale**, lasciando frasi lunghe ma comprensibili.
- **Correggi** errori grammaticali impliciti e segnala eventuali discrepanze di dati con (???).
- **Uniforma** il linguaggio per correggere espressioni ridondanti e migliorare la coerenza complessiva.

Ecco il testo da correggere:
{chunk}"""
        elif task == 'traduzione':
            language = self.language_var.get()
            default_prompt = f"Traduci il seguente testo in {language} sistemando punteggiatura e typo:\n\n{{chunk}}"
        elif task == 'riassunto':
            default_prompt = "Fornisci un riassunto dettagliato del seguente testo:\n\n{chunk}"
        else:
            default_prompt = ""
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(tk.END, default_prompt)

    def on_task_change(self, *args):
        task = self.task_var.get()
        if task == 'traduzione':
            self.language_entry.config(state='normal')
        else:
            self.language_entry.config(state='disabled')
        self.update_prompt()

    def split_text(self, text, max_tokens=1500):
        encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')
        user_prompt = self.prompt_text.get(1.0, tk.END)
        base_prompt_tokens = len(encoding.encode(user_prompt.replace('{chunk}', '')))
        sentences = text.split('. ')
        chunks = []
        current_chunk = ''
        for sentence in sentences:
            total_tokens = base_prompt_tokens + len(encoding.encode(current_chunk + sentence))
            if total_tokens > max_tokens:
                chunks.append(current_chunk)
                current_chunk = sentence + '. '
            else:
                current_chunk += sentence + '. '
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def process_chunk(self, chunk):
        selected_api = self.api_var.get()
        user_prompt = self.prompt_text.get(1.0, tk.END)
        prompt = user_prompt.replace('{chunk}', chunk)
        
        if selected_api == 'OpenAI':
            return self.call_openai_api(prompt, self.api_key)
        elif selected_api == 'Groq':
            return self.call_groq_api(prompt)
        return None

    def call_openai_api(self, prompt, api_key):
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': self.model_name,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
            else:
                logging.error(f"OpenAI API Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logging.error(f"Error calling OpenAI API: {str(e)}")
            return None

    def call_groq_api(self, prompt):
        try:
            client = groq.Groq(api_key=self.groq_api_key)
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": ""},
                    {"role": "user", "content": prompt}
                ],
                model=self.groq_model
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Error calling Groq API: {str(e)}")
            return None

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def start_processing(self):
        def run():
            text = self.input_text.get(1.0, tk.END)
            if not text.strip():
                messagebox.showwarning("Avviso", "Inserire il testo da elaborare")
                return

            chunks = self.split_text(text)
            total_chunks = len(chunks)
            self.output_text.delete(1.0, tk.END)
            
        
            for i, chunk in enumerate(chunks, 1):
                self.update_status(f'Elaborazione {i}/{len(chunks)}...')
                try:
                    result = self.process_chunk(chunk)
                    if result:
                        self.output_text.insert(tk.END, result + '\n\n')
                    else:
                        # Mostra un messaggio di errore specifico per questo chunk
                        error_message = f"Errore durante l'elaborazione del chunk {i}. Nessun risultato restituito."
                        print(error_message)  # Scrive in console
                        messagebox.showerror("Errore", error_message)  # Mostra il messaggio nella finestra di dialogo
                        break
                except Exception as e:
                    # Gestisce le eccezioni e stampa dettagli
                    error_message = f"Errore: {str(e)} durante l'elaborazione del chunk {i}"
                    print(error_message)  # Scrive in console
                    messagebox.showerror("Errore", error_message)  # Mostra il messaggio nella finestra di dialogo
                    break

                self.progress_var.set((i/total_chunks) * 100)
            
            self.update_status('Elaborazione completata')
            
        threading.Thread(target=run, daemon=True).start()

def main():
    root = ThemedTk(theme="arc")  # Usa un tema moderno
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    
    app = ModernTextProcessorApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()