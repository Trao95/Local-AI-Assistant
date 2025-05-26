import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import keyboard
import requests
import time
import sys
import json
import os
import urllib.parse
from datetime import datetime

# --- Configuration ---
OLLAMA_MODEL = "llama3.1"
OLLAMA_URL = "http://localhost:11434/api/generate"
DEBUG_MODE = True
SYSTEM_PROMPT = (
    "You are an AI assistant designed to help users with a wide range of tasks. "
)

# Weather API Configuration (Tomorrow.io)
TOMORROW_API_KEY = "your_api_key_here"  # Add your Tomorrow.io API key here
TOMORROW_URL = "https://api.tomorrow.io/v4/weather/realtime"
DEFAULT_LOCATION = {"lat": 0, "lon": 0}  # Default coordinates, configure in your local setup
DEFAULT_CITY = "Your City"  # Configure your city name in your local setup

# Google Search API Configuration
GOOGLE_SEARCH_API_KEY = "your_api_key_here"  # Add your Google API key here
# The Search Engine ID must be the cx value from your Google Custom Search Engine
GOOGLE_SEARCH_ENGINE_ID = "your_search_engine_id_here"  # Add your Google Search Engine ID here
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

# Test the Google Search API on startup
def test_google_search_api():
    if DEBUG_MODE:
        print("Testing Google Search API connection...", flush=True)
    try:
        params = {
            'key': GOOGLE_SEARCH_API_KEY.strip(),
            'cx': GOOGLE_SEARCH_ENGINE_ID.strip(),
            'q': 'test query',
            'num': 1
        }
        response = requests.get(GOOGLE_SEARCH_URL, params=params)
        if DEBUG_MODE:
            print(f"API Test Status Code: {response.status_code}", flush=True)
        
        if response.status_code == 200:
            result = response.json()
            if 'items' in result:
                if DEBUG_MODE:
                    print("Google Search API test successful - results returned", flush=True)
                return True
            else:
                if DEBUG_MODE:
                    print("Google Search API test - no items in response", flush=True)
                    print(f"Response keys: {list(result.keys())}", flush=True)
                    if 'error' in result:
                        print(f"Error: {result['error']}", flush=True)
                return False
        else:
            if DEBUG_MODE:
                print(f"Google Search API test failed with status code: {response.status_code}", flush=True)
            return False
    except Exception as e:
        if DEBUG_MODE:
            print(f"Google Search API test error: {e}", flush=True)
        return False

# Assistant Modes
MODE_LLM = "llm"  # Default mode using local LLM
MODE_WEB_SEARCH = "web_search"  # Web search mode using Google API

# Memory Configuration
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conversation_memory.json")
MEMORY_MAX_CONVERSATIONS = 5   # Maximum number of conversations to store
MEMORY_MAX_MESSAGES = 20       # Maximum messages per conversation
CONTEXT_WINDOW = 10            # Number of previous messages to include in context
MIN_MESSAGE_LENGTH = 10        # Minimum length for a message to be stored in memory
MAX_MEMORY_SAVE_INTERVAL = 5   # Save memory every N messages to reduce writes

# Window Dimensions
INITIAL_HEIGHT = 500
MAX_HEIGHT = 800
MIN_HEIGHT = 200
WIDTH = 600

# Styling
# Theme colors
DARK_THEME = {
    'bg': "#1E1E1E",
    'text': "#FFFFFF",
    'accent': "#4A90E2",
    'input_bg': "#2D2D2D",
    'welcome_bg': "#2D2D2D",
    'button_bg': "#3A3A3A",
    'button_hover': "#4A4A4A"
}

LIGHT_THEME = {
    'bg': "#F5F5F5",
    'text': "#333333",
    'accent': "#1E88E5",
    'input_bg': "#FFFFFF",
    'welcome_bg': "#E0E0E0",
    'button_bg': "#E0E0E0",
    'button_hover': "#D0D0D0"
}

# Default to dark theme
CURRENT_THEME = DARK_THEME
TRANSPARENCY = 0.85

class WelcomeScreen(tk.Frame):
    def __init__(self, parent, on_start):
        super().__init__(parent, bg=CURRENT_THEME['welcome_bg'])
        self.on_start = on_start
        
        self.title_label = tk.Label(
            self,
            text="Personal AI Assistant",
            font=("Segoe UI", 24, "bold"),
            fg=CURRENT_THEME['text'],
            bg=CURRENT_THEME['welcome_bg']
        )
        self.title_label.pack(pady=(50, 20))
        
        self.desc_label = tk.Label(
            self,
            text="Your personal AI with web search and weather updates.",
            font=("Segoe UI", 12),
            fg=CURRENT_THEME['text'],
            bg=CURRENT_THEME['welcome_bg']
        )
        self.desc_label.pack(pady=(0, 30))
        
        self.start_button = tk.Button(
            self,
            text="Start Chat",
            command=self.on_start,
            font=("Segoe UI", 12, "bold"),
            bg=CURRENT_THEME['accent'],
            fg=CURRENT_THEME['text'], 
            activebackground=CURRENT_THEME['accent'],
            activeforeground=CURRENT_THEME['text'],
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.start_button.pack(pady=20)
        
        self.instructions_label = tk.Label(
            self,
            text="Press Ctrl+/ to toggle visibility\nType your message and press Enter to chat\nCtrl+R to reset chat\nClick 'LLM/Web' button to switch modes",
            font=("Segoe UI", 10),
            fg=CURRENT_THEME['text'],
            bg=CURRENT_THEME['welcome_bg'],
            justify=tk.LEFT
        )
        self.instructions_label.pack(pady=10)

    def apply_theme(self):
        """Applies the current theme to all widgets."""
        self.config(bg=CURRENT_THEME['welcome_bg'])
        self.title_label.config(fg=CURRENT_THEME['text'], bg=CURRENT_THEME['welcome_bg'])
        self.desc_label.config(fg=CURRENT_THEME['text'], bg=CURRENT_THEME['welcome_bg'])
        self.start_button.config(
            bg=CURRENT_THEME['accent'], 
            fg=CURRENT_THEME['text'], 
            activebackground=CURRENT_THEME['accent'], 
            activeforeground=CURRENT_THEME['text']
        )
        self.instructions_label.config(fg=CURRENT_THEME['text'], bg=CURRENT_THEME['welcome_bg'])

class ChatInterface(tk.Frame):
    def __init__(self, parent, toggle_theme_callback): # Added toggle_theme_callback
        self.toggle_theme_callback = toggle_theme_callback # Store the callback
        super().__init__(parent, bg=CURRENT_THEME['bg'])
        self.conversation_history = []
        self.conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.message_count_since_save = 0
        self.important_conversation = False  # Flag to mark important conversations
        self.response_start_time = 0  # Track when response generation starts
        self.current_mode = MODE_LLM  # Default to LLM mode
        self.thinking_position = None  # Track position of thinking message
        self.load_memory()
        self.chat_display = scrolledtext.ScrolledText(
            self,
            bg=CURRENT_THEME['bg'],
            fg=CURRENT_THEME['text'],
            font=("Segoe UI", 11),
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=10,
            pady=10,
            height=20
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
        self.chat_display.tag_configure("user", foreground=CURRENT_THEME['accent'], font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_configure("assistant", foreground=CURRENT_THEME['text'])
        self.chat_display.tag_configure("thinking", foreground="#888888", font=("Segoe UI", 10, "italic"))
        self.chat_display.tag_configure("error", foreground="#FF4444", font=("Segoe UI", 11, "bold"))
        self.chat_display.tag_configure("system", foreground="#888888", font=("Segoe UI", 10, "italic"))
        self.chat_display.tag_configure("web_search", foreground="#4CAF50", font=("Segoe UI", 10, "italic"))
        self.chat_display.tag_configure("time", foreground="#888888", font=("Segoe UI", 8, "italic"))
        
        self.input_frame = tk.Frame(self, bg=CURRENT_THEME['bg']) # Made instance var and use theme
        self.input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.user_input = tk.Entry(
            self.input_frame, # Use self.input_frame
            bg=CURRENT_THEME['input_bg'],
            fg=CURRENT_THEME['text'],
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            insertbackground=CURRENT_THEME['text']
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 5))
        self.user_input.bind("<Return>", self.on_enter_pressed)
        self.user_input.focus_set()
        
        # Theme toggle button
        self.theme_button_text = tk.StringVar()
        self.theme_button_text.set("🌙" if CURRENT_THEME == DARK_THEME else "☀️")
        self.theme_button = tk.Button(
            self.input_frame, # Use self.input_frame
            textvariable=self.theme_button_text,
            command=self.toggle_theme_callback, # Use the passed callback
            bg=CURRENT_THEME['button_bg'],
            fg=CURRENT_THEME['text'],
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            bd=0,
            padx=10,
            cursor="hand2"
        )
        self.theme_button.pack(side=tk.RIGHT, padx=(0, 5)) # Pack it before mode_button
        
        # Mode toggle button
        self.mode_button = tk.Button(
            self.input_frame, # Use self.input_frame
            text="LLM",
            command=self.toggle_mode,
            bg=CURRENT_THEME['accent'],
            fg=CURRENT_THEME['text'],
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=5,
            pady=2,
            cursor="hand2",
            activebackground=CURRENT_THEME['accent'],
            activeforeground=CURRENT_THEME['text']
        )
        self.mode_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.send_button = tk.Button( # Made instance var
            self.input_frame, # Use self.input_frame
            text="Send",
            command=lambda: self.on_enter_pressed(None),
            font=("Segoe UI", 11, "bold"),
            bg=CURRENT_THEME['accent'],
            fg=CURRENT_THEME['text'],
            activebackground=CURRENT_THEME['accent'],
            activeforeground=CURRENT_THEME['text'],
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        self.send_button.pack(side=tk.RIGHT)
        self.append_message("Hello! I'm your AI assistant. How can I help you today?", "assistant")

    def apply_theme(self):
        """Applies the current theme to all chat interface widgets."""
        self.config(bg=CURRENT_THEME['bg'])
        self.chat_display.config(bg=CURRENT_THEME['bg'], fg=CURRENT_THEME['text'])
        self.chat_display.tag_configure("user", foreground=CURRENT_THEME['accent'])
        self.chat_display.tag_configure("assistant", foreground=CURRENT_THEME['text'])
        # Assuming other tags like 'thinking', 'error' should also adapt or have specific theme entries
        self.chat_display.tag_configure("thinking", foreground="#888888" if CURRENT_THEME == LIGHT_THEME else "#AAAAAA") # Example adjustment
        self.chat_display.tag_configure("error", foreground="#FF4444" if CURRENT_THEME == LIGHT_THEME else "#FF6666") # Example adjustment

        self.input_frame.config(bg=CURRENT_THEME['bg'])
        self.user_input.config(bg=CURRENT_THEME['input_bg'], fg=CURRENT_THEME['text'], insertbackground=CURRENT_THEME['text'])
        
        self.theme_button_text.set("🌙" if CURRENT_THEME == DARK_THEME else "☀️")
        self.theme_button.config(
            bg=CURRENT_THEME['button_bg'], 
            fg=CURRENT_THEME['text'],
            activebackground=CURRENT_THEME['button_hover'],
            activeforeground=CURRENT_THEME['text']
        )
        self.mode_button.config(
            bg=CURRENT_THEME['accent'], 
            fg=CURRENT_THEME['text'],
            activebackground=CURRENT_THEME['accent'], # Or button_hover
            activeforeground=CURRENT_THEME['text']
        )
        self.send_button.config(
            bg=CURRENT_THEME['accent'], 
            fg=CURRENT_THEME['text'],
            activebackground=CURRENT_THEME['accent'], # Or button_hover
            activeforeground=CURRENT_THEME['text']
        )
        
    def get_weather_condition(self, cloud_cover):
        """Convert cloud cover percentage to weather condition description"""
        if cloud_cover < 10:
            return "Clear sky"
        elif cloud_cover < 30:
            return "Mostly clear"
        elif cloud_cover < 70:
            return "Partly cloudy"
        elif cloud_cover < 90:
            return "Mostly cloudy"
        else:
            return "Overcast"

    def remove_thinking_message(self):
        """Helper method to remove the thinking message without affecting other messages"""
        self.chat_display.configure(state=tk.NORMAL)
        
        # Find all instances of text with the "thinking" tag
        start = "1.0"
        while True:
            # Search for "Assistant: Thinking..." text
            thinking_start = self.chat_display.search("Assistant: Thinking...", start, stopindex=tk.END, nocase=True)
            if not thinking_start:
                break
            
            # Find the end of this line
            thinking_end = self.chat_display.index(f"{thinking_start} lineend+1c")
            # Delete just the thinking message
            self.chat_display.delete(thinking_start, thinking_end)
            # No need to update start since we've deleted the current match
        
        self.chat_display.configure(state=tk.DISABLED)
            
    def append_message(self, text, sender="assistant", generation_time=None):
        self.chat_display.configure(state=tk.NORMAL)
        if sender == "user":
            self.chat_display.insert(tk.END, f"You: {text}\n", "user")
            self.conversation_history.append({"role": "user", "content": text})
            # Start timing the response generation
            self.response_start_time = time.time()
            
            # Check if this might be an important message
            if len(text) > MIN_MESSAGE_LENGTH:
                self.message_count_since_save += 1
                
                # Mark conversation as important if it contains certain keywords
                important_keywords = ["remember", "important", "don't forget", "note", "save"]
                if any(keyword in text.lower() for keyword in important_keywords):
                    self.important_conversation = True
                    
                # Save memory periodically or for important conversations
                if self.important_conversation or self.message_count_since_save >= MAX_MEMORY_SAVE_INTERVAL:
                    self.save_memory()
                    self.message_count_since_save = 0
                    
        elif sender == "assistant":
            # Add the main message
            self.chat_display.insert(tk.END, f"Assistant: {text}", "assistant")
            
            # Add generation time if provided
            if generation_time is not None:
                time_text = f" [{generation_time:.2f}s]"
                self.chat_display.insert(tk.END, time_text, "time")
            
            # Add newline
            self.chat_display.insert(tk.END, "\n")
            
            self.conversation_history.append({"role": "assistant", "content": text})
            
            # Save memory after important responses
            if self.important_conversation and len(text) > MIN_MESSAGE_LENGTH:
                self.save_memory()
                
        elif sender == "thinking":
            # Store the current position before inserting the thinking message
            self.thinking_position = self.chat_display.index(tk.END)
            self.chat_display.insert(tk.END, f"Assistant: {text}\n", "thinking")
        elif sender == "error":
            self.chat_display.insert(tk.END, f"Error: {text}\n", "error")
        elif sender == "system":
            self.chat_display.insert(tk.END, f"System: {text}\n", "system")
        elif sender == "web_search":
            self.chat_display.insert(tk.END, f"Web Search Results:\n{text}\n", "web_search")
        # Removed extra newline that was causing the large gap between messages
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def on_enter_pressed(self, event):
        user_text = self.user_input.get().strip()
        if not user_text:
            return
            
        # Check for weather command
        if user_text.lower().startswith("!weather"):
            self.handle_weather_command(user_text)
            self.user_input.delete(0, tk.END)
            return
            
        # Check for memory control commands
        if user_text.lower() == "!remember this":
            self.important_conversation = True
            self.append_message("I'll remember this conversation.", "system")
            self.user_input.delete(0, tk.END)
            return
        elif user_text.lower() == "!forget this":
            self.important_conversation = False
            self.append_message("This conversation won't be saved to memory.", "system")
            self.user_input.delete(0, tk.END)
            return
        elif user_text.lower() == "!wipe memory":
            self.reset_chat(wipe_all_memory=True)
            self.user_input.delete(0, tk.END)
            return
            
        self.append_message(user_text, "user")
        self.user_input.delete(0, tk.END)
        threading.Thread(target=self.process_query, args=(user_text,), daemon=True).start()

    def toggle_mode(self):
        """Toggle between LLM and Web Search modes"""
        self.current_mode = MODE_WEB_SEARCH if self.current_mode == MODE_LLM else MODE_LLM
        self.mode_button.config(text="Web" if self.current_mode == MODE_WEB_SEARCH else "LLM")
        self.append_message("system", f"Switched to {self.current_mode.upper()} mode")
    def perform_web_search(self, query):
        """Perform a Google search using the Google Custom Search JSON API"""
        if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
            return "Error: Google Search API key or Search Engine ID is not configured. Please add your API credentials to the configuration."
        
        try:
            # Prepare the search parameters
            params = {
                'key': GOOGLE_SEARCH_API_KEY.strip(),
                'cx': GOOGLE_SEARCH_ENGINE_ID.strip(),
                'q': query,
                'num': 5  # Number of search results to return
            }
            
            search_url = GOOGLE_SEARCH_URL
            
            if DEBUG_MODE:
                print(f"Making Google search request to: {search_url}", flush=True)
                print(f"Search parameters: key={params['key'][:5]}..., cx={params['cx']}, query={params['q']}", flush=True)
            
            # Make the API request
            response = requests.get(search_url, params=params)
            
            if DEBUG_MODE:
                print(f"Search response status code: {response.status_code}", flush=True)
            
            response.raise_for_status()
            search_results = response.json()
            
            if DEBUG_MODE:
                print(f"Search response keys: {list(search_results.keys())}", flush=True)
                if 'error' in search_results:
                    print(f"API Error: {search_results['error']}", flush=True)
            
            if 'items' not in search_results:
                error_msg = "No results found for your query."
                if 'error' in search_results:
                    error_msg += f" Error: {search_results['error'].get('message', '')}"
                elif 'searchInformation' in search_results:
                    total_results = search_results['searchInformation'].get('totalResults', '0')
                    error_msg += f" Total results: {total_results}"
                return error_msg
            
            # Format the search results
            formatted_results = ""
            for i, item in enumerate(search_results['items'], 1):
                formatted_results += f"{i}. {item['title']}\n"
                formatted_results += f"   {item['link']}\n"
                if 'snippet' in item:
                    formatted_results += f"   {item['snippet']}\n"
                formatted_results += "\n"
            
            return formatted_results
        
        except Exception as e:
            if DEBUG_MODE:
                print(f"Google Search API error: {e}", flush=True)
                import traceback
                traceback.print_exc()
            return f"Error performing web search: {str(e)}"

    def process_query(self, user_prompt):
        self.append_message("Thinking...", "thinking")
        
        try:
            # Choose processing method based on current mode
            if self.current_mode == MODE_WEB_SEARCH:
                return self.process_web_search_query(user_prompt)
            else:
                return self.process_llm_query(user_prompt)
        except Exception as e:
            if DEBUG_MODE:
                print(f"Query processing unexpected error: {e}", flush=True)
            total_time = time.time() - self.response_start_time
            self.chat_display.configure(state=tk.NORMAL)

    def process_web_search_query(self, user_prompt):
        """Process a query using web search and then use the LLM to formulate an answer"""
        try:
            # First, get web search results
            api_start_time = time.time()
            search_results_raw = self.perform_web_search(user_prompt)
            search_time = time.time() - api_start_time
            
            if DEBUG_MODE:
                print(f"Web search time: {search_time:.3f}s", flush=True)
            
            # Check if we got an error from the search API
            if search_results_raw.startswith("Error") or search_results_raw.startswith("No results"):
                total_generation_time = time.time() - self.response_start_time
                # Remove only the thinking message
                self.remove_thinking_message()
                self.append_message(search_results_raw, "error", generation_time=total_generation_time)
                return
            
            # Now, use the LLM to process these results and generate a comprehensive answer
            # Build context with search results
            context = [f"System: {SYSTEM_PROMPT}"]
            context.append("System: You have access to web search results. Use the information from these results to provide a comprehensive answer.")
            context.append(f"System: Web search results for query: '{user_prompt}'\n{search_results_raw}")
            
            # Add conversation history for context
            context += [
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in self.conversation_history[-CONTEXT_WINDOW:]
            ]
            
            # Create a prompt for the LLM that includes the web search results
            full_prompt = "\n".join(context) + f"\nUser: {user_prompt}\nAssistant: "
            
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False
            }
            
            if DEBUG_MODE:
                print(f"Sending LLM request with web search results...", flush=True)
            
            # Get LLM response
            llm_start_time = time.time()
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            llm_time = time.time() - llm_start_time
            
            # Calculate total generation time
            total_generation_time = time.time() - self.response_start_time
            
            if DEBUG_MODE:
                print(f"Web search time: {search_time:.3f}s", flush=True)
                print(f"LLM processing time: {llm_time:.3f}s", flush=True)
                print(f"Total generation time: {total_generation_time:.3f}s", flush=True)
            
            assistant_response = result.get('response', 'Sorry, I could not generate a response based on the search results.')
            
            # Clean up the response
            if "<think>" in assistant_response:
                assistant_response = assistant_response.split("</think>")[-1].strip()
            if "[Focus on current question only]" in assistant_response:
                assistant_response = assistant_response.replace("[Focus on current question only]", "").strip()
            
            # Update the display - delete only the thinking message
            self.remove_thinking_message()
            self.append_message(assistant_response, "assistant", generation_time=total_generation_time)
            
        except requests.exceptions.ConnectionError as e:
            if DEBUG_MODE:
                print(f"LLM API connection error: {e}", flush=True)
            total_time = time.time() - self.response_start_time
            # Use the improved remove_thinking_message method instead of line-based deletion
            self.remove_thinking_message()
            self.append_message("Error: Could not connect to Ollama server. Is it running at http://localhost:11434?", "error")
        except Exception as e:
            if DEBUG_MODE:
                print(f"Web search + LLM error: {e}", flush=True)
            total_time = time.time() - self.response_start_time
            # Use the improved remove_thinking_message method instead of line-based deletion
            self.remove_thinking_message()
            self.append_message(f"Error processing web search results: {str(e)}", "error")

    def process_llm_query(self, user_prompt):
        """Process a query using the local LLM"""
        try:
            # Build context with more history for better memory
            context = [f"System: {SYSTEM_PROMPT}"]
            context += [
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in self.conversation_history[-CONTEXT_WINDOW:]
            ]
            
            # Create a prompt that includes conversation history
            full_prompt = "\n".join(context) + f"\nUser: {user_prompt}"
            
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False
            }
            
            if DEBUG_MODE:
                print(f"Sending query request: {payload['prompt'][:50]}...", flush=True)
            
            # Get API response time
            api_start_time = time.time()
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            api_time = time.time() - api_start_time
            
            # Calculate total generation time (from user input to response)
            total_generation_time = time.time() - self.response_start_time
            
            if DEBUG_MODE:
                print(f"API call time: {api_time:.3f}s", flush=True)
                print(f"Total generation time: {total_generation_time:.3f}s", flush=True)
                print(f"Query API response: {result}", flush=True)
                
            assistant_response = result.get('response', 'Sorry, I could not generate a response.')
            
            if "<think>" in assistant_response:
                assistant_response = assistant_response.split("</think>")[-1].strip()
            if "[Focus on current question only]" in assistant_response:
                assistant_response = assistant_response.replace("[Focus on current question only]", "").strip()
                
            # Use the improved remove_thinking_message method instead of line-based deletion
            self.remove_thinking_message()
            self.append_message(assistant_response, "assistant", generation_time=total_generation_time)
        except requests.exceptions.ConnectionError as e:
            if DEBUG_MODE:
                print(f"Query API connection error: {e}", flush=True)
            total_time = time.time() - self.response_start_time
            # Use the improved remove_thinking_message method instead of line-based deletion
            self.remove_thinking_message()
            self.append_message("Error: Could not connect to Ollama server. Is it running at http://localhost:11434?", "error")
        except requests.exceptions.HTTPError as e:
            if DEBUG_MODE:
                print(f"Query API HTTP error: {e}", flush=True)
            total_time = time.time() - self.response_start_time
            # Use the improved remove_thinking_message method instead of line-based deletion
            self.remove_thinking_message()
            self.append_message(f"Error: HTTP error from Ollama server: {str(e)}", "error")
        except Exception as e:
            if DEBUG_MODE:
                print(f"Query API unexpected error: {e}", flush=True)
            total_time = time.time() - self.response_start_time
            # Use the improved remove_thinking_message method instead of line-based deletion
            self.remove_thinking_message()
            self.append_message(f"Error: {str(e)}", "error")

    def save_memory(self):
        """Save conversation history to a file, filtering out trivial messages"""
        try:
            # Skip saving if conversation is too short and not important
            if len(self.conversation_history) < 3 and not self.important_conversation:
                if DEBUG_MODE:
                    print("Skipping memory save - conversation too short", flush=True)
                return
                
            # Filter out short/trivial messages
            filtered_history = []
            for msg in self.conversation_history:
                # Always keep system messages
                if msg.get("role") == "system":
                    filtered_history.append(msg)
                # Filter user and assistant messages by length and content
                elif len(msg.get("content", "")) > MIN_MESSAGE_LENGTH:
                    filtered_history.append(msg)
            
            # Skip saving if filtered conversation is empty
            if not filtered_history:
                if DEBUG_MODE:
                    print("Skipping memory save - no significant messages", flush=True)
                return
                
            # Load existing memory file if it exists
            memory_data = {}
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, 'r') as f:
                    memory_data = json.load(f)
            
            # Add or update current conversation
            memory_data[self.conversation_id] = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'important': self.important_conversation,
                'messages': filtered_history[-MEMORY_MAX_MESSAGES:] if filtered_history else []
            }
            
            # Keep important conversations and most recent ones
            if len(memory_data) > MEMORY_MAX_CONVERSATIONS:
                # First prioritize important conversations
                important_convs = {k: v for k, v in memory_data.items() if v.get('important', False)}
                regular_convs = {k: v for k, v in memory_data.items() if not v.get('important', False)}
                
                # If we have too many important conversations, keep the most recent ones
                if len(important_convs) > MEMORY_MAX_CONVERSATIONS:
                    sorted_important = sorted(important_convs.items(), key=lambda x: x[1]['timestamp'])
                    important_convs = dict(sorted_important[-MEMORY_MAX_CONVERSATIONS:])
                    memory_data = important_convs
                else:
                    # Fill remaining slots with most recent regular conversations
                    slots_left = MEMORY_MAX_CONVERSATIONS - len(important_convs)
                    if slots_left > 0 and regular_convs:
                        sorted_regular = sorted(regular_convs.items(), key=lambda x: x[1]['timestamp'])
                        regular_convs = dict(sorted_regular[-slots_left:])
                        memory_data = {**important_convs, **regular_convs}
                    else:
                        memory_data = important_convs
            
            # Save to file
            with open(MEMORY_FILE, 'w') as f:
                json.dump(memory_data, f, indent=2)
                
            if DEBUG_MODE:
                print(f"Saved conversation to memory file with {len(filtered_history)} messages", flush=True)
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error saving memory: {e}", flush=True)
    
    def load_memory(self):
        """Load conversation history from file"""
        try:
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, 'r') as f:
                    memory_data = json.load(f)
                    
                # Count messages in memory for debugging
                total_messages = sum(len(conv.get('messages', [])) for conv in memory_data.values())
                important_convs = sum(1 for conv in memory_data.values() if conv.get('important', False))
                    
                if DEBUG_MODE:
                    print(f"Loaded {len(memory_data)} conversations from memory", flush=True)
                    print(f"  - {total_messages} total messages", flush=True)
                    print(f"  - {important_convs} important conversations", flush=True)
            else:
                if DEBUG_MODE:
                    print("No memory file found, starting fresh", flush=True)
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error loading memory: {e}", flush=True)
    
    def reset_chat(self, wipe_all_memory=True):
        # Wipe all stored conversations if requested
        if wipe_all_memory:
            try:
                if os.path.exists(MEMORY_FILE):
                    os.remove(MEMORY_FILE)
                    if DEBUG_MODE:
                        print("Wiped all stored conversations from memory file", flush=True)
            except Exception as e:
                if DEBUG_MODE:
                    print(f"Error wiping memory file: {e}", flush=True)
        # Otherwise save current conversation if it's important or substantial
        elif self.conversation_history and (self.important_conversation or len(self.conversation_history) > 3):
            self.save_memory()
            
        # Create a new conversation ID
        self.conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.conversation_history = []
        self.important_conversation = False
        self.message_count_since_save = 0
        
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.configure(state=tk.DISABLED)
        self.append_message("Chat has been reset and all memory has been wiped. How can I help you?", "system")
        self.user_input.focus_set()

    def handle_weather_command(self, command):
        """Handle the weather command and return current weather conditions"""
        try:
            # Use default location coordinates
            location = DEFAULT_LOCATION
            location_name = DEFAULT_CITY
            
            # TODO: Add geocoding support for custom locations
            if len(command.split()) > 1:
                location_name = " ".join(command.split()[1:])
            
            # Make API request
            params = {
                'apikey': TOMORROW_API_KEY,
                'location': f"{location['lat']},{location['lon']}",
                'units': 'metric'
            }
            
            if DEBUG_MODE:
                print(f"Fetching weather for {location_name}...", flush=True)
                
            response = requests.get(TOMORROW_URL, params=params)
            response.raise_for_status()
            weather_data = response.json()
            
            # Format weather information
            data = weather_data['data']['values']
            temp = data['temperature']
            feels_like = data['temperatureApparent']
            humidity = data['humidity']
            cloud_cover = data['cloudCover']
            wind_speed = data['windSpeed']
            conditions = self.get_weather_condition(cloud_cover)
            
            weather_message = (
                f"📍 Weather in {location_name}\n"
                f"🌡️ Temperature: {temp}°C\n"
                f"🤔 Feels like: {feels_like}°C\n"
                f"💧 Humidity: {humidity}%\n"
                f"🌤️ Conditions: {conditions}\n"
                f"💨 Wind Speed: {wind_speed} m/s"
            )
            
            self.append_message(weather_message, "system")
            
        except requests.exceptions.RequestException as e:
            self.append_message(f"Error fetching weather data: {str(e)}", "error")
        except KeyError as e:
            self.append_message(f"Error parsing weather data: {str(e)}", "error")
        except Exception as e:
            self.append_message(f"Unexpected error: {str(e)}", "error")

class AssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Personal Assistant")
        style = ttk.Style()
        style.configure("Accent.TButton", 
                       background=CURRENT_THEME['accent'],
                       foreground=CURRENT_THEME['text'],
                       borderwidth=0,
                       focusthickness=0,
                       focuscolor=CURRENT_THEME['accent'])
        style.map("Accent.TButton",
                 background=[('active', CURRENT_THEME['accent']), ('pressed', CURRENT_THEME['accent'])],
                 foreground=[('active', CURRENT_THEME['text']), ('pressed', CURRENT_THEME['text'])])
        self.root.geometry("1x1+0+0")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-alpha", 1.0)
        self.win = tk.Toplevel(root)
        self.win.title("Personal AI Assistant")
        self.win.geometry(f"{WIDTH}x{INITIAL_HEIGHT}+400+200")
        self.win.attributes("-topmost", False)
        self.win.attributes("-alpha", 1.0)
        self.win.overrideredirect(True)
        self.win.configure(bg=CURRENT_THEME['bg'])
        self.welcome_screen = WelcomeScreen(self.win, self.show_chat)
        self.welcome_screen.pack(fill=tk.BOTH, expand=True)
        self.chat_interface = ChatInterface(self.win, self.toggle_theme) # Pass toggle_theme callback
        
        # Set up window close handler to save memory
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.win.protocol("WM_DELETE_WINDOW", self.on_close)
        
        threading.Thread(target=self.hotkey_listener, daemon=True).start()
        self.hide_window()

    def move_window(self, dx, dy):
        x = self.win.winfo_x() + dx
        y = self.win.winfo_y() + dy
        self.win.geometry(f"+{x}+{y}")

    def show_chat(self):
        self.welcome_screen.pack_forget()
        self.chat_interface.pack(fill=tk.BOTH, expand=True)

    def hide_window(self):
        self.win.withdraw()

    def show_window(self):
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()

    def toggle_theme(self):
        """Toggles the theme between light and dark mode."""
        global CURRENT_THEME
        if CURRENT_THEME == DARK_THEME:
            CURRENT_THEME = LIGHT_THEME
        else:
            CURRENT_THEME = DARK_THEME
        
        self.win.configure(bg=CURRENT_THEME['bg'])
        if self.welcome_screen.winfo_ismapped(): # Apply to welcome screen if visible
            self.welcome_screen.apply_theme()
        if self.chat_interface.winfo_ismapped(): # Apply to chat interface if visible
            self.chat_interface.apply_theme()
        # If one is packed, the other might need an update too for when it's shown next
        # Or, ensure apply_theme is called in show_chat / when welcome screen is shown
        self.welcome_screen.apply_theme() # Apply theme regardless of visibility
        self.chat_interface.apply_theme() # Apply theme regardless of visibility

    def toggle_window(self):
        if self.win.winfo_ismapped():
            self.hide_window()
        else:
            self.show_window()

    def reset_chat(self):
        if hasattr(self, 'chat_interface'):
            self.chat_interface.reset_chat(wipe_all_memory=True)

    def hotkey_listener(self):
        try:
            keyboard.remove_hotkey("ctrl+/")
            keyboard.remove_hotkey("ctrl+up")
            keyboard.remove_hotkey("ctrl+down")
            keyboard.remove_hotkey("ctrl+left")
            keyboard.remove_hotkey("ctrl+right")
            keyboard.remove_hotkey("ctrl+r")
        except:
            pass
        
        keyboard.add_hotkey("ctrl+/", self.toggle_window, suppress=True)
        keyboard.add_hotkey("ctrl+up", lambda: self.move_window(0, -10), suppress=True)
        keyboard.add_hotkey("ctrl+down", lambda: self.move_window(0, 10), suppress=True)
        keyboard.add_hotkey("ctrl+left", lambda: self.move_window(-10, 0), suppress=True)
        keyboard.add_hotkey("ctrl+right", lambda: self.move_window(10, 0), suppress=True)
        keyboard.add_hotkey("ctrl+r", self.reset_chat, suppress=True)
        
        keyboard_thread = threading.Thread(target=keyboard.wait, daemon=True)
        keyboard_thread.start()

    def on_close(self):
        """Handle window closing - save memory before exit"""
        if hasattr(self, 'chat_interface'):
            self.chat_interface.save_memory()
        self.root.destroy()

if __name__ == "__main__":
    if DEBUG_MODE:
        print(f"Starting Lyro AI with memory...", flush=True)
        print(f"Memory file: {MEMORY_FILE}", flush=True)
    
    # Test Google Search API connection
    google_api_working = test_google_search_api()
    if not google_api_working and DEBUG_MODE:
        print("Warning: Google Search API test failed. Web search mode may not work correctly.", flush=True)
        print("Please check your API key and Search Engine ID.", flush=True)
    
    root = tk.Tk()
    app = AssistantApp(root)
    root.mainloop()