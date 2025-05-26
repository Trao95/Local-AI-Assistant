"""
This module contains the fixed ChatInterface class that properly handles message display
without deleting user questions when the assistant responds.
"""

import tkinter as tk
from tkinter import scrolledtext

class FixedChatInterface:
    """
    Helper class to fix the issue with user messages disappearing.
    This class provides methods to properly handle the chat display.
    """
    
    @staticmethod
    def fix_chat_interface(chat_interface):
        """
        Apply fixes to the ChatInterface instance to prevent user messages from disappearing.
        
        Args:
            chat_interface: The ChatInterface instance to fix
        """
        # Store original methods that we'll override
        original_process_web_search_query = chat_interface.process_web_search_query
        original_process_llm_query = chat_interface.process_llm_query
        
        # Override the process_web_search_query method
        def fixed_process_web_search_query(self, user_prompt):
            """Fixed version that properly handles the thinking message"""
            try:
                # First, get web search results
                api_start_time = self._time.time()
                search_results_raw = self.perform_web_search(user_prompt)
                search_time = self._time.time() - api_start_time
                
                if self._DEBUG_MODE:
                    print(f"Web search time: {search_time:.3f}s", flush=True)
                
                # Check if we got an error from the search API
                if search_results_raw.startswith("Error") or search_results_raw.startswith("No results"):
                    total_generation_time = self._time.time() - self.response_start_time
                    # Safely remove only the thinking message
                    self._safely_remove_thinking_message()
                    self.append_message(search_results_raw, "error", generation_time=total_generation_time)
                    return
                
                # Now, use the LLM to process these results and generate a comprehensive answer
                # Build context with search results
                context = [f"System: {self._SYSTEM_PROMPT}"]
                context.append("System: You have access to web search results. Use the information from these results to provide a comprehensive answer.")
                context.append(f"System: Web search results for query: '{user_prompt}'\n{search_results_raw}")
                
                # Add conversation history for context
                context += [
                    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                    for msg in self.conversation_history[-self._CONTEXT_WINDOW:]
                ]
                
                # Create a prompt for the LLM that includes the web search results
                full_prompt = "\n".join(context) + f"\nUser: {user_prompt}\nAssistant: "
                
                payload = {
                    "model": self._OLLAMA_MODEL,
                    "prompt": full_prompt,
                    "stream": False
                }
                
                if self._DEBUG_MODE:
                    print(f"Sending LLM request with web search results...", flush=True)
                
                # Get LLM response
                llm_start_time = self._time.time()
                response = self._requests.post(self._OLLAMA_URL, json=payload)
                response.raise_for_status()
                result = response.json()
                llm_time = self._time.time() - llm_start_time
                
                # Calculate total generation time
                total_generation_time = self._time.time() - self.response_start_time
                
                if self._DEBUG_MODE:
                    print(f"Web search time: {search_time:.3f}s", flush=True)
                    print(f"LLM processing time: {llm_time:.3f}s", flush=True)
                    print(f"Total generation time: {total_generation_time:.3f}s", flush=True)
                
                assistant_response = result.get('response', 'Sorry, I could not generate a response based on the search results.')
                
                # Clean up the response
                if "<think>" in assistant_response:
                    assistant_response = assistant_response.split("</think>")[-1].strip()
                if "[Focus on current question only]" in assistant_response:
                    assistant_response = assistant_response.replace("[Focus on current question only]", "").strip()
                
                # Safely remove only the thinking message
                self._safely_remove_thinking_message()
                self.append_message(assistant_response, "assistant", generation_time=total_generation_time)
                
            except self._requests.exceptions.ConnectionError as e:
                if self._DEBUG_MODE:
                    print(f"LLM API connection error: {e}", flush=True)
                total_time = self._time.time() - self.response_start_time
                # Safely remove only the thinking message
                self._safely_remove_thinking_message()
                self.append_message("Error: Could not connect to Ollama server. Is it running at http://localhost:11434?", "error")
            except Exception as e:
                if self._DEBUG_MODE:
                    print(f"Web search + LLM error: {e}", flush=True)
                total_time = self._time.time() - self.response_start_time
                # Safely remove only the thinking message
                self._safely_remove_thinking_message()
                self.append_message(f"Error processing web search results: {str(e)}", "error")
        
        # Override the process_llm_query method
        def fixed_process_llm_query(self, user_prompt):
            """Fixed version that properly handles the thinking message"""
            try:
                # Build context with more history for better memory
                context = [f"System: {self._SYSTEM_PROMPT}"]
                context += [
                    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                    for msg in self.conversation_history[-self._CONTEXT_WINDOW:]
                ]
                
                # Create a prompt that includes conversation history
                full_prompt = "\n".join(context) + f"\nUser: {user_prompt}"
                
                payload = {
                    "model": self._OLLAMA_MODEL,
                    "prompt": full_prompt,
                    "stream": False
                }
                
                if self._DEBUG_MODE:
                    print(f"Sending LLM request...", flush=True)
                
                # Get LLM response
                api_start_time = self._time.time()
                response = self._requests.post(self._OLLAMA_URL, json=payload)
                response.raise_for_status()
                result = response.json()
                
                # Calculate generation time
                total_generation_time = self._time.time() - self.response_start_time
                
                if self._DEBUG_MODE:
                    print(f"LLM response time: {total_generation_time:.3f}s", flush=True)
                
                assistant_response = result.get('response', 'Sorry, I could not generate a response.')
                
                # Clean up the response
                if "<think>" in assistant_response:
                    assistant_response = assistant_response.split("</think>")[-1].strip()
                if "[Focus on current question only]" in assistant_response:
                    assistant_response = assistant_response.replace("[Focus on current question only]", "").strip()
                
                # Safely remove only the thinking message
                self._safely_remove_thinking_message()
                self.append_message(assistant_response, "assistant", generation_time=total_generation_time)
                
            except self._requests.exceptions.ConnectionError as e:
                if self._DEBUG_MODE:
                    print(f"LLM API connection error: {e}", flush=True)
                # Safely remove only the thinking message
                self._safely_remove_thinking_message()
                self.append_message("Error: Could not connect to Ollama server. Is it running at http://localhost:11434?", "error")
            except Exception as e:
                if self._DEBUG_MODE:
                    print(f"LLM processing error: {e}", flush=True)
                # Safely remove only the thinking message
                self._safely_remove_thinking_message()
                self.append_message(f"Error processing your request: {str(e)}", "error")
        
        # Add helper method to safely remove thinking messages
        def _safely_remove_thinking_message(self):
            """Safely remove only the thinking message without affecting other messages"""
            chat_display = chat_interface.chat_display
            chat_display.configure(state=tk.NORMAL)
            
            # Find all instances of text with the "thinking" tag
            thinking_ranges = []
            start = "1.0"
            while True:
                thinking_start = chat_display.search("Assistant: Thinking...", start, stopindex=tk.END, nocase=True)
                if not thinking_start:
                    break
                
                # Find the end of this line
                thinking_end = chat_display.index(f"{thinking_start} lineend+1c")
                thinking_ranges.append((thinking_start, thinking_end))
                start = thinking_end
            
            # Delete the thinking messages in reverse order to avoid index issues
            for start, end in reversed(thinking_ranges):
                chat_display.delete(start, end)
                
            chat_display.configure(state=tk.DISABLED)
        
        # Store references to required modules and constants
        chat_interface._requests = __import__('requests')
        chat_interface._time = __import__('time')
        chat_interface._DEBUG_MODE = __import__('sys').modules['__main__'].DEBUG_MODE
        chat_interface._SYSTEM_PROMPT = __import__('sys').modules['__main__'].SYSTEM_PROMPT
        chat_interface._OLLAMA_MODEL = __import__('sys').modules['__main__'].OLLAMA_MODEL
        chat_interface._OLLAMA_URL = __import__('sys').modules['__main__'].OLLAMA_URL
        chat_interface._CONTEXT_WINDOW = __import__('sys').modules['__main__'].CONTEXT_WINDOW
        
        # Apply the fixed methods
        chat_interface._safely_remove_thinking_message = _safely_remove_thinking_message.__get__(chat_interface)
        chat_interface.process_web_search_query = fixed_process_web_search_query.__get__(chat_interface)
        chat_interface.process_llm_query = fixed_process_llm_query.__get__(chat_interface)
