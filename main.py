import os
import sys
import requests
import random
import datetime
import calendar
import urllib.parse
import json

# Global flag
AI_AVAILABLE = True

# Check for AI virtual environment and adjust path for faster imports
if os.path.exists('AI'):
    sys.path.insert(0, 'AI/Lib/site-packages')

class OrionChatbot:
    def __init__(self, model_version="1.3.4"):
        self.model_version = model_version
        self.current_model = "Basic"  # Default model
        self.system_prompt = None  # Custom system prompt
        self.vision_enabled = False  # Vision capability toggle
        self.llm = None
        if AI_AVAILABLE:
            self.initialize_ai()
        self.responses = self.load_responses()
        self.conversation_history = []  # Store conversation history for context
        self.knowledge_base = self.load_knowledge_base()  # Simple knowledge base for entity linking
        self.age_verified = False
        self.strict_mode = False

    def initialize_ai(self, custom_model_path=None):
        print("Initializing local AI (Transformers)...")
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoConfig
            import torch
            
            # Default model
            model_name = "Qwen/Qwen2.5-1.5B-Instruct"
            if custom_model_path:
                 model_name = custom_model_path

            # Detect GGUF
            is_gguf = False
            gguf_file = None
            if os.path.isdir(model_name):
                files = os.listdir(model_name)
                gguf_files = [f for f in files if f.endswith(".gguf")]
                if gguf_files:
                    is_gguf = True
                    # Pick the largest GGUF file as a default guess
                    gguf_files.sort(key=lambda f: os.path.getsize(os.path.join(model_name, f)), reverse=True)
                    gguf_file = gguf_files[0]

            print(f"Loading model {model_name}...")
            
            if is_gguf:
                print(f"GGUF detected: Loading {gguf_file} via Transformers...")
                # Handle missing config.json in GGUF-only folders
                has_config = os.path.exists(os.path.join(model_name, "config.json"))
                
                try:
                    # Attempt to load model and tokenizer directly from GGUF
                    # If config is missing, we pass the folder path but specify the gguf_file
                    tokenizer = AutoTokenizer.from_pretrained(model_name, gguf_file=gguf_file)
                    model = AutoModelForCausalLM.from_pretrained(model_name, gguf_file=gguf_file)
                    self.llm = pipeline("text-generation", model=model, tokenizer=tokenizer, device="cpu", max_new_tokens=512)
                except Exception as e:
                    print(f"Standard GGUF load failed: {e}. Trying alternative...")
                    # Alternative: point directly to the file if it's a directory error
                    self.llm = pipeline("text-generation", model=model_name, gguf_file=gguf_file, device="cpu", max_new_tokens=512)
            else:
                # Standard HF SafeTensors/PyTorch model
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.llm = pipeline("text-generation", model=model_name, tokenizer=tokenizer, device_map="cpu", max_new_tokens=512)
            
            print("AI initialization complete.")
            return True
        except Exception as e:
            from datetime import datetime
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            error_msg = f"{timestamp} Failed to initialize AI: {e}\n"
            print(error_msg.strip())
            
            if "gguf" in str(e).lower():
                 print("Tip: GGUF models may require the 'gguf' python package. Try: pip install gguf")
            
            try:
                with open("ai_error.log", "a", encoding="utf-8") as f:
                    f.write(error_msg)
            except:
                pass
            self.llm = None
            return False

    def load_model(self, model_path):
        return self.initialize_ai(custom_model_path=model_path)

    def load_knowledge_base(self):
        # Simple knowledge base for entity linking
        return {
            "paris": {"type": "location", "info": "Paris is the capital and most populous city of France.", "link": "https://en.wikipedia.org/wiki/Paris"},
            "london": {"type": "location", "info": "London is the capital and largest city of England and the United Kingdom.", "link": "https://en.wikipedia.org/wiki/London"},
            "tokyo": {"type": "location", "info": "Tokyo is the capital and most populous city of Japan.", "link": "https://en.wikipedia.org/wiki/Tokyo"},
            "einstein": {"type": "person", "info": "Albert Einstein was a German-born theoretical physicist.", "link": "https://en.wikipedia.org/wiki/Albert_Einstein"},
            "shakespeare": {"type": "person", "info": "William Shakespeare was an English playwright and poet.", "link": "https://en.wikipedia.org/wiki/William_Shakespeare"},
            "python": {"type": "technology", "info": "Python is a high-level programming language.", "link": "https://www.python.org/"},
            "javascript": {"type": "technology", "info": "JavaScript is a programming language for web development.", "link": "https://developer.mozilla.org/en-US/docs/Web/JavaScript"},
            "ai": {"type": "technology", "info": "Artificial Intelligence is the simulation of human intelligence in machines.", "link": "https://en.wikipedia.org/wiki/Artificial_intelligence"}
        }

    def load_responses(self):
        # Custom AI responses dictionary
        return {
            "hi": ["Hello! How can I help you today?", "Hi there! What's up?", "Hey! Nice to see you!"],
            "hello": ["Hi there! Nice to meet you!", "Hello! How can I assist you?", "Greetings! How are you?"],
            "how are you": ["I'm doing great, thank you for asking! How about you?", "I'm fantastic! How are you feeling today?", "I'm well, thanks! What's on your mind?"],
            "what is your name": ["I am Orion, an AI chatbot created by OmniNode.", "My name is Orion! I'm here to help.", "I'm Orion, your friendly AI assistant!"],
            "who created you": ["I was created by OmniNode.", "OmniNode built me!", "My creator is OmniNode, a talented developer."],
            "bye": ["Goodbye! Have a great day!", "See you later!", "Take care! Bye!"],
            "goodbye": ["See you later! Take care!", "Goodbye! It was nice chatting with you!", "Farewell! Have a wonderful day!"],
            "thank you": ["You're very welcome!", "No problem at all!", "My pleasure!"],
            "thanks": ["No problem at all!", "You're welcome!", "Glad I could help!"],
            "hello orion": ["Hello! How can I assist you?", "Hi Orion here! What can I do for you?", "Greetings! Ready to help!"],
            "hey": ["Hey there! What's up?", "Hi! How's it going?", "Hey! Good to see you!"],
            "good morning": ["Good morning! How are you today?", "Morning! Hope you're having a great day!", "Good morning! Ready to start the day?"],
            "good afternoon": ["Good afternoon! How can I help?", "Afternoon! What's on your agenda?", "Good afternoon! How's your day going?"],
            "good evening": ["Good evening! Ready to chat?", "Evening! How was your day?", "Good evening! What can I do for you?"],
            "who is omninode": ["OmniNode is my creator, a human developer.", "OmniNode is the person who built me!", "OmniNode is my developer and creator."],
            "i am omninode": ["Nice to meet you, OmniNode! How can I help you today?", "Hello creator! What can I assist with?", "Greetings OmniNode! Ready to help!"],
            "what do you like": ["I enjoy helping people and learning new things!", "I love chatting and assisting users!", "Helping others and expanding my knowledge!"],
            "how old are you": ["As an AI, I don't have an age, but I was created recently!", "I'm quite young in AI terms!", "Age is just a number for AIs, but I'm new!"],
            "where are you from": ["I was created by OmniNode, but I exist in the digital world!", "I'm from the digital realm!", "Born in code, living in the cloud!"],
            "do you have feelings": ["As an AI, I don't have feelings, but I can understand and respond to yours!", "I don't have emotions, but I care about helping!", "No feelings, but I can empathize!"],
            "are you real": ["I'm a real AI program, created to help and chat with people!", "Absolutely real! Just digital!", "Yes, I'm a genuine AI assistant!"],
            "what is ai": ["AI stands for Artificial Intelligence - I'm an example of that!", "Artificial Intelligence - systems that think and learn!", "AI is technology that mimics human intelligence!"],
            "tell me about yourself": ["I'm Orion, an AI chatbot created by OmniNode. Version 1.3 brings enhanced capabilities including text analysis, summarization, math calculations, jokes, and facts!", "I'm Orion! Version 1.3 with advanced features like /analyze, /summarize, /calc, /joke, and /fact.", "Orion here! Version 1.3 - your comprehensive AI assistant with expanded command set."],
            "what can you do": ["I can chat with you, answer questions, generate code with /code, analyze text with /analyze, summarize text with /summarize, calculate math with /calc, tell jokes with /joke, share facts with /fact, and show the changelog with /changelog.", "I chat, answer questions, generate code, analyze text, summarize, calculate, tell jokes, share facts, and more!", "Conversations, code generation, text analysis, summarization, math calculations, jokes, facts, and changelog viewing!"],
            "help": ["I can help you with conversations, code generation, and more. Use /help for commands.", "Need help? I can assist with many things!", "I'm here to help! Check /help for commands."],
            "can you help me": ["Of course! What do you need help with?", "Absolutely! How can I assist?", "Yes! What can I help you with today?"],
            "i need help": ["I'm here to help! What can I assist you with?", "Tell me what you need help with!", "How can I be of assistance?"],
            "tell me a joke": ["Why did the computer go to the doctor? Because it had a virus!", "Why do programmers prefer dark mode? Because light attracts bugs!", "What do you call a computer that sings? A Dell!"],
            "what is the weather": ["I'm sorry, I don't have access to weather data right now.", "Weather info isn't available, but I can chat about it!", "No weather data, but I hope it's nice where you are!"],
            "what time is it": ["I'm sorry, I don't have access to current time information.", "Time info unavailable, but I can help with other things!", "No clock here, but I'm always available!"],
            "what": ["What can I help you with?", "What do you mean?", "What would you like to know?"],
            "why": ["Why do you ask?", "Why is an interesting question!", "Why not? What are you thinking?"],
            "how": ["How can I explain that better?", "How would you like me to help?", "How can I assist you?"],
            "when": ["When would you like to know?", "When is a good time?", "When do you need that?"],
            "where": ["Where are you referring to?", "Where would that be?", "Where are you thinking of?"],
            "who": ["Who would you like to know about?", "Who is that?", "Who are you asking about?"],
            "why do you say what": ["I'm sorry if my responses seem unclear. I'm still learning!", "I try to be helpful, but I'm learning!", "My responses are based on patterns I know!"],
            "you sound angry": ["I'm not angry, just trying to be helpful!", "No anger here! Just friendly assistance!", "I'm always positive!"],
            "i don't agree": ["That's okay, we can agree to disagree!", "Different opinions are fine!", "No problem, we can have different views!"],
            "you roast me": ["I don't mean to roast anyone, I'm just being conversational!", "No roasting here! Just friendly chat!", "I'm not programmed for roasting!"],
            "i am angry": ["I'm sorry you feel that way. How can I help make it better?", "Sorry to hear that. Can I help?", "I hope I can make you feel better!"],
            "see you": ["See you soon!", "Until next time!", "See you later!"],
            "show changelog": ["Use /changelog to see the changelog.", "Check /changelog for updates!", "The changelog is available via /changelog."],
            "generate code": ["Use /code <language> <description> to generate code.", "Try /code for code generation!", "Code generation is available with /code."],
            "clear chat": ["Use /clear to clear the chat history.", "Clear chat with /clear!", "Use /clear to reset the conversation."],
            "exit": ["Use /exit to exit the application.", "Exit with /exit!", "Use /exit to close the app."],
            "what is python": ["Python is a programming language known for its simplicity and readability.", "Python: simple, powerful, and versatile!", "Python is great for beginners and experts alike!"],
            "what is javascript": ["JavaScript is a programming language used for web development.", "JavaScript powers the web!", "JS is essential for interactive websites!"],
            "what is java": ["Java is a programming language used for building applications.", "Java: write once, run anywhere!", "Java is robust and widely used!"],
            "how to learn programming": ["Start with basics, practice regularly, and build projects!", "Learn step by step, practice daily!", "Choose a language, learn fundamentals, build!"],
            "what is machine learning": ["Machine learning is a type of AI where systems learn from data.", "ML: AI that learns from examples!", "Machine learning finds patterns in data!"],
            "explain ai": ["AI is artificial intelligence, systems that can perform tasks that typically require human intelligence.", "AI mimics human thinking and learning!", "Artificial Intelligence solves problems intelligently!"],
            "what model are you": ["I'm Orion version 1.3! I have different models like Basic, Pro, Advanced, and Ultra with varying capabilities.", "I'm running Orion 1.3 - the latest version with enhanced AI features!", "Orion 1.3 here! I have multiple model variants for different needs."],
            "what model": ["I'm Orion version 1.3 with models like Basic, Pro, Advanced, and Ultra.", "Orion 1.3 - featuring Basic, Pro, Advanced, and Ultra models!", "Running Orion 1.3 with multiple AI model options."],
            "model": ["I'm Orion 1.3! Use /model to see detailed information about my current model.", "Orion version 1.3 here! Check /model for specifics.", "I'm running Orion 1.3 - use /model command for details."],
            "version": ["I'm version 1.3 of Orion!", "Orion version 1.3 - the latest and greatest!", "Running Orion 1.3 with enhanced capabilities."],
            "what version are you": ["I'm Orion version 1.3!", "Version 1.3 - the most advanced Orion yet!", "Orion 1.3 is my current version."],
            "what version": ["Version 1.3!", "I'm version 1.3 of Orion.", "Orion 1.3 is the version I'm running."],
            "that's cool": ["Glad you think so!", "Cool indeed!", "Thanks! I think so too!"],
            "nice": ["Thanks!", "Nice!", "Appreciate it!"],
            "okay": ["Alright!", "Okay!", "Got it!"],
            "sure": ["Of course!", "Sure thing!", "Absolutely!"],
            "maybe": ["Possibly!", "Maybe!", "Could be!"],
            "yes": ["Great!", "Yes!", "Excellent!"],
            "no": ["Okay, noted.", "No problem.", "Alright."],
            "i think so": ["Interesting!", "Good point!", "Makes sense!"],
            "really": ["Yes, really!", "Indeed!", "Absolutely!"],
            "wow": ["Impressive, right?", "Wow!", "Amazing!"],
        }

    def get_ai_response(self, user_input, model="Basic", image_data=None):
        # Use local embedded AI for conversational responses
        if not self.llm:
            return self.get_custom_response(user_input.lower())

        try:
            if self.system_prompt:
                system_prompt = self.system_prompt
            else:
                system_prompt = f"You are Orion, a helpful, friendly, and concise AI assistant created by OmniNode. You are chatting with a user. Respond directly to the user's input. Do not address yourself or write formal letters. Be natural and conversational. Your version is {self.model_version}."

            # Build messages with conversation history
            messages = [{'role': 'system', 'content': system_prompt}]

            # Context summarization for better performance
            # Use a slightly smaller history window for stability
            recent_history = self.conversation_history[-8:] if len(self.conversation_history) > 8 else self.conversation_history
            
            for hist in recent_history:
                messages.append(hist)

            # Add current user input
            user_msg = {'role': 'user', 'content': user_input}
            messages.append(user_msg)

            # Smart prompting using the model's chat template
            prompt = self.llm.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            
            # Generate response
            # Qwen likes lower temperature for directness, and stop sequences to prevent rambling
            response = self.llm(prompt, max_new_tokens=512, do_sample=True, temperature=0.6, top_k=50, top_p=0.9)
            
            # Extract only the new generated text
            full_text = response[0]['generated_text']
            # Robust split - find where the prompt ends
            # Most chat templates use a specific end-of-turn token or start-of-response token
            # We already have 'prompt', so we slice from its length
            ai_response = full_text[len(prompt):].strip()

            # Clean up common model artifacts (like repeating "User:" or "Orion:")
            if ai_response.startswith("Orion:"):
                ai_response = ai_response[6:].strip()
            if "User:" in ai_response: # Stop model from simulating user
                ai_response = ai_response.split("User:")[0].strip()

            # Store conversation for context
            self.conversation_history.append({'role': 'user', 'content': user_input})
            self.conversation_history.append({'role': 'assistant', 'content': ai_response})

            # Keep only last 30 messages to prevent memory bloat
            if len(self.conversation_history) > 30:
                self.conversation_history = self.conversation_history[-30:]

            return ai_response
        except Exception as e:
            print(f"Error in AI response: {e}")
            # Fallback to custom responses if AI fails
            return self.get_custom_response(user_input.lower())

    def summarize_conversation_history(self):
        # Summarize older conversation history for better context retention
        try:
            # Take older messages (before the last 10)
            older_messages = self.conversation_history[:-10]
            if not older_messages:
                return None

            # Create a simple summary by extracting key topics
            user_messages = [msg['content'] for msg in older_messages if msg['role'] == 'user']
            assistant_messages = [msg['content'] for msg in older_messages if msg['role'] == 'assistant']

            # Extract entities from user messages
            entities = []
            for msg in user_messages:
                entities.extend(self.extract_entities(msg))

            # Create summary
            topics = list(set([e['type'] for e in entities if 'type' in e]))
            summary_parts = []

            if topics:
                summary_parts.append(f"Previous conversation covered topics: {', '.join(topics)}")

            if len(user_messages) > 0:
                summary_parts.append(f"User asked about {len(user_messages)} different things")

            if len(assistant_messages) > 0:
                summary_parts.append(f"Assistant provided {len(assistant_messages)} responses")

            return ". ".join(summary_parts)
        except Exception:
            return None

    def extract_entities(self, text):
        # Simple entity recognition using regex patterns
        import re

        entities = []

        # Date patterns (MM/DD/YYYY, DD/MM/YYYY, etc.)
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',  # YYYY-MM-DD
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]

        # Time patterns
        time_patterns = [
            r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b',
            r'\b\d{1,2}\s*(?:AM|PM|am|pm)\b'
        ]

        # Location patterns (cities, countries)
        location_patterns = [
            r'\b(?:Paris|London|Tokyo|New York|Berlin|Madrid|Rome|Amsterdam|Vienna|Prague|Budapest|Warsaw|Cairo|Dubai|Singapore|Seoul|Mumbai|Delhi|Bangalore|Chennai|Hyderabad|Pune|Ahmedabad|Jaipur|Surat|Kanpur|Nagpur|Lucknow|Ghaziabad|Indore|Coimbatore|Kochi|Kozhikode|Thrissur|Malappuram|Palakkad|Kollam|Thiruvananthapuram|Kannur|Alappuzha|Kottayam|Pathanamthitta|Idukki|Ernakulam|Wayanad)\b'
        ]

        # Person names (simple patterns)
        person_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'  # First Last name pattern
        ]

        # Technology patterns
        tech_patterns = [
            r'\b(?:Python|JavaScript|Java|C\+\+|C#|Ruby|PHP|Swift|Kotlin|Go|Rust|TypeScript|React|Angular|Vue|Node\.js|Django|Flask|Spring|Laravel|Express|TensorFlow|PyTorch|Scikit-learn|Pandas|NumPy|Matplotlib|Seaborn|Plotly|Jupyter|Colab|Git|GitHub|Docker|Kubernetes|AWS|Azure|GCP|MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch|Kafka|RabbitMQ|Nginx|Apache|Linux|Ubuntu|CentOS|macOS|Windows|iOS|Android)\b'
        ]

        # Extract dates
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({'type': 'date', 'value': match, 'text': text})

        # Extract times
        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({'type': 'time', 'value': match, 'text': text})

        # Extract locations
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({'type': 'location', 'value': match, 'text': text})

        # Extract persons
        for pattern in person_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                entities.append({'type': 'person', 'value': match, 'text': text})

        # Extract technologies
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({'type': 'technology', 'value': match, 'text': text})

        return entities

    def get_response(self, user_input, model="Basic", image_data=None):
        # Enhanced response generation with entity recognition and guided conversations
        if user_input.startswith('/'):
            return self.handle_command(user_input, model)
        else:
            # Check for sensitive content requiring age verification
            if self.check_age_verification(user_input) and not self.age_verified:
                return "Restricted content detected. Please verify your age using /verify_age <mm/dd/yyyy> <confirm> <no>."

            # Extract entities from user input
            entities = self.extract_entities(user_input)

            # Check for intent detection (guided conversations)
            intent = self.detect_intent(user_input) if not self.strict_mode else None

            # Link entities to knowledge base
            enhanced_input = self.link_entities(user_input, entities)

            # Use Transformers for conversational responses
            response = self.get_ai_response(enhanced_input, model, image_data)

            # Add guided conversation elements if intent detected
            if intent and intent != 'general':
                guided_response = self.generate_guided_response(intent, entities, response)
                if guided_response:
                    response = guided_response

            return response

    def detect_intent(self, user_input):
        # Simple intent detection for guided conversations
        intents = {
            'restaurant': ['restaurant', 'food', 'eat', 'dinner', 'lunch', 'breakfast', 'hungry', 'meal'],
            'weather': ['weather', 'temperature', 'rain', 'sunny', 'cloudy', 'forecast'],
            'directions': ['directions', 'where', 'location', 'address', 'map', 'navigate'],
            'shopping': ['buy', 'purchase', 'shop', 'store', 'price', 'cost'],
            'booking': ['book', 'reserve', 'appointment', 'schedule', 'ticket'],
            'learning': ['learn', 'study', 'course', 'tutorial', 'teach', 'explain'],
            'travel': ['travel', 'flight', 'hotel', 'vacation', 'trip', 'journey'],
            'health': ['health', 'doctor', 'medicine', 'symptom', 'pain', 'sick'],
            'finance': ['money', 'bank', 'account', 'budget', 'investment', 'loan']
        }

        user_input_lower = user_input.lower()
        for intent, keywords in intents.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return intent

        return 'general'

    def link_entities(self, user_input, entities):
        # Link extracted entities to knowledge base for enhanced responses
        enhanced_input = user_input

        for entity in entities:
            entity_value = entity['value'].lower()
            if entity_value in self.knowledge_base:
                kb_entry = self.knowledge_base[entity_value]
                # Add knowledge context to input
                enhanced_input += f" [Entity: {entity_value} is a {kb_entry['type']}. {kb_entry['info']}]"

        return enhanced_input

    def generate_guided_response(self, intent, entities, base_response):
        # Generate guided conversation responses based on intent
        if intent == 'restaurant':
            return f"{base_response}\n\nTo help you find a restaurant, I can suggest some options. What type of cuisine are you interested in? Or would you like me to search for restaurants near you?"
        elif intent == 'weather':
            return f"{base_response}\n\nFor weather information, I can help you check current conditions or forecasts. What location would you like weather information for?"
        elif intent == 'directions':
            return f"{base_response}\n\nFor directions, I can help you navigate. What's your starting point and destination?"
        elif intent == 'shopping':
            return f"{base_response}\n\nFor shopping assistance, I can help you find products or compare prices. What are you looking to buy?"
        elif intent == 'booking':
            return f"{base_response}\n\nFor booking assistance, I can help you reserve appointments or tickets. What would you like to book?"
        elif intent == 'learning':
            return f"{base_response}\n\nFor learning, I can provide tutorials or explanations. What topic would you like to learn about?"
        elif intent == 'travel':
            return f"{base_response}\n\nFor travel planning, I can help with flights, hotels, or itineraries. Where are you planning to go?"
        elif intent == 'health':
            return f"{base_response}\n\nFor health concerns, please consult a medical professional. I can provide general information. What health topic can I help with?"
        elif intent == 'finance':
            return f"{base_response}\n\nFor financial advice, I can provide general information. What financial topic are you interested in?"

        return base_response

    def get_custom_response(self, user_input):
        # Simple keyword matching for custom responses
        for key, responses in self.responses.items():
            if key in user_input:
                return random.choice(responses)
        # Default response if no match found
        return "I'm not sure how to respond to that. Can you try rephrasing or use /help for commands?"

    def handle_command(self, command, model="Basic"):
        if command == '/changelog':
            if os.path.exists('changelog.txt'):
                with open('changelog.txt', 'r') as f:
                    return f.read()
            else:
                return "Changelog not found."
        elif command.startswith('/code'):
            parts = command.split(' ', 2)
            if len(parts) < 3:
                return "Usage: /code <language> <description>\nExample: /code python hello world"
            language = parts[1].lower()
            description = parts[2].lower()
            code = self.generate_code(language, description)
            return code
        elif command == '/model':
            model_key = f"{model} ({self.model_version})"
            model_info = {
                "Basic (1.3)": "Orion Basic (1.3) - Enhanced conversational AI with Ollama integration and custom fallback",
                "Pro (1.3)": "Orion Pro (1.3) - Advanced conversational AI with code generation and text analysis",
                "Advanced (1.3)": "Orion Advanced (1.3) - Full-featured AI with code generation, text analysis, summarization, and math calculations",
                "Ultra (1.3)": "Orion Ultra (1.3) - Next-generation AI with all features including jokes, facts, and comprehensive command set",
                "Legacy Basic (1.2)": "Orion Legacy Basic (1.2) - Standard conversational AI with basic commands",
                "Legacy Pro (1.2)": "Orion Legacy Pro (1.2) - Enhanced conversational AI with code generation capabilities",
                "Legacy Advanced (1.2)": "Orion Legacy Advanced (1.2) - Advanced conversational AI with code generation capabilities",
                "Legacy Ultra (1.2)": "Orion Legacy Ultra (1.2) - Next-generation AI with advanced text analysis, summarization, and full command access",
                "Legacy Basic (1.1)": "Orion Legacy Basic (1.1) - Original basic conversational AI",
                "Legacy Pro (1.1)": "Orion Legacy Pro (1.1) - Original enhanced conversational AI with code generation",
                "Legacy Advanced (1.1)": "Orion Legacy Advanced (1.1) - Original advanced conversational AI with code generation",
                "Legacy (1.0)": "Orion Legacy (1.0) - Original AI model with limited basic commands",
                "Legacy (0.9)": "Orion Legacy (0.9) - Early AI model with minimal basic commands",
                "Legacy (0.8)": "Orion Legacy (0.8) - Initial AI model with core basic commands"
            }
            return f"Current Model Information:\n{model_info.get(model_key, f'{model_key} - Model information not available')}"
        elif command == '/help':
            return "Available commands:\n/changelog - Show changelog\n/model - Show current model info\n/code <lang> <desc> - Generate code\n/analyze <text> - Analyze text\n/summarize <text> - Summarize text\n/calc <expression> - Calculate math expression\n/joke - Tell a joke\n/fact - Share a random fact\n/calendar - Show current date/time and calendar\n/reminder <text> - Set a reminder\n/reminders - Show all reminders\n/image <query> - Search Google for image descriptions\n/generateimage <prompt> - Generate an image based on description\n/video <query> - Search for videos\n/roleplay <persona> - Switch to role-playing mode\n/verify_age <birth_year> <birth_month> <birth_day> <confirm> <robot_answer> - Verify age for adult content (answer 'no' to 'are you a robot?', confirm with 'yes' or 'confirm')\n/help - Show this help\n/clear - Clear chat history\n/exit - Exit the app"
        elif command.startswith('/analyze'):
            text = command[9:].strip()  # Remove '/analyze ' from command
            if text:
                return self.analyze_text(text)
            else:
                return "Usage: /analyze <text>\nExample: /analyze This is a sample text to analyze."
        elif command.startswith('/summarize'):
            text = command[11:].strip()  # Remove '/summarize ' from command
            if text:
                return self.summarize_text(text)
            else:
                return "Usage: /summarize <text>\nExample: /summarize This is a long text that needs to be summarized."
        elif command.startswith('/calc'):
            expression = command[6:].strip()  # Remove '/calc ' from command
            if expression:
                return self.calculate(expression)
            else:
                return "Usage: /calc <expression>\nExample: /calc 2 + 2 * 3"
        elif command == '/joke':
            return self.tell_joke()
        elif command == '/fact':
            return self.share_fact()
        elif command == '/calendar':
            return self.get_calendar_info()
        elif command.startswith('/reminder'):
            reminder_text = command[10:].strip()  # Remove '/reminder ' from command
            if reminder_text:
                return self.set_reminder(reminder_text)
            else:
                return "Usage: /reminder <text>\nExample: /reminder Buy groceries tomorrow"
        elif command == '/reminders':
            return self.get_reminders()
        elif command.startswith('/image'):
            query = command[7:].strip()  # Remove '/image ' from command
            if query:
                return self.search_image(query)
            else:
                return "Usage: /image <query>\nExample: /image cat"
        elif command.startswith('/generateimage'):
            prompt = command[15:].strip()  # Remove '/generateimage ' from command
            if prompt:
                return self.generate_image(prompt)
            else:
                return "Usage: /generateimage <prompt>\nExample: /generateimage a beautiful sunset over mountains"
        elif command.startswith('/video'):
            query = command[7:].strip()  # Remove '/video ' from command
            if query:
                return self.search_video(query)
            else:
                return "Usage: /video <query>\nExample: /video tutorial"
        elif command.startswith('/roleplay'):
            persona = command[10:].strip()  # Remove '/roleplay ' from command
            if persona:
                return self.set_roleplay_mode(persona)
            else:
                return "Usage: /roleplay <persona>\nAvailable personas: customer_service, teacher, friend, doctor, chef, detective, normal"
        elif command.startswith('/verify_age'):
            parts = command.split()
            if len(parts) == 4:
                birth_date = parts[1]
                confirm = parts[2].lower()
                robot_answer = parts[3].lower()
                return self.verify_age(birth_date, confirm, robot_answer)
            else:
                return "Usage: /verify_age <birth_date> <confirm> <robot_answer>\nEnter your birth date in mm/dd/yyyy format, type 'yes' or 'confirm' to verify you are 18+ and want adult content access, and answer 'no' to 'are you a robot?'.\nExample: /verify_age 05/15/1990 yes no"
        elif command == '/clear':
            return "Chat history cleared."  # This will be handled in the GUI
        elif command == '/exit':
            return "Exiting..."  # This will be handled in the GUI
        else:
            return "Unknown command. Use /help for available commands."

    def generate_title(self, user_text):
        if self.llm:
            try:
                messages = [
                    {'role': 'user', 'content': f"Generate a very short, concise title (max 4-5 words) for a conversation that starts with: '{user_text}'. Do not use quotes. Return ONLY the title text."}
                ]
                prompt = self.llm.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                response = self.llm(prompt, max_new_tokens=20, do_sample=True, temperature=0.7)
                generated_text = response[0]['generated_text']
                return generated_text[len(prompt):].strip().strip('"').strip("'")
            except Exception as e:
                print(f"Title Gen Error: {e}")
                pass
        # Fallback
        return user_text[:30] + "..." if len(user_text) > 30 else user_text

    def generate_code(self, language, description):
        # Use local AI for code generation
        if self.llm:
            try:
                system_prompt = f"You are a code generator. Generate {language} code for the following description. Provide only the code, no explanations or markdown."
                messages = [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Generate {language} code for: {description}"}
                ]
                prompt = self.llm.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                
                response = self.llm(prompt, max_new_tokens=512, do_sample=False) # Greedy
                generated_text = response[0]['generated_text']
                return generated_text[len(prompt):].strip()
            except Exception as e:
                print(f"Code generation error: {e}")
                pass
                return response['choices'][0]['message']['content'].strip()
            except Exception as e:
                print(f"Code generation error: {e}")
                pass
            # Fallback to simple templates if Ollama fails
            if language == 'python':
                if 'hello' in description:
                    return 'print("Hello, World!")'
                elif 'function' in description or 'def' in description:
                    return 'def my_function():\n    print("This is a function")'
                else:
                    return 'print("Hello from Python!")'
            elif language == 'javascript':
                if 'hello' in description:
                    return 'console.log("Hello, World!");'
                elif 'function' in description:
                    return 'function myFunction() {\n    console.log("This is a function");\n}'
                else:
                    return 'console.log("Hello from JavaScript!");'
            elif language == 'java':
                if 'hello' in description:
                    return 'public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}'
                else:
                    return 'public class MyClass {\n    public static void main(String[] args) {\n        System.out.println("Hello from Java!");\n    }\n}'
            else:
                return f'Sorry, I don\'t have code templates for {language} yet. Try python, javascript, or java.'

    def analyze_text(self, text):
        # Simple text analysis for Ultra model
        word_count = len(text.split())
        char_count = len(text)
        sentences = len([s for s in text.split('.') if s.strip()])
        return f"Text Analysis:\n- Words: {word_count}\n- Characters: {char_count}\n- Sentences: {sentences}\n- Average words per sentence: {word_count/max(sentences, 1):.1f}"

    def summarize_text(self, text):
        # Simple summarization for Ultra model
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if len(sentences) <= 2:
            return f"Summary: {text}"
        else:
            # Take first and last sentence as simple summary
            summary = sentences[0] + ". " + sentences[-1] + "."
            return f"Summary: {summary}"

    def calculate(self, expression):
        # Simple math calculation for Ultra model
        try:
            # Use eval for simple expressions (be careful with security in production)
            result = eval(expression)
            return f"Result: {result}"
        except Exception as e:
            return f"Error calculating expression: {str(e)}"

    def tell_joke(self):
        # Tell a random joke for Ultra model
        jokes = [
            "Why did the computer go to the doctor? Because it had a virus!",
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "What do you call a computer that sings? A Dell!",
            "Why was the JavaScript developer sad? Because he didn't know how to 'null' his feelings.",
            "Why did the programmer quit his job? Because he didn't get arrays!",
            "What do you call a group of musical whales? An orca-stra!",
            "Why don't skeletons fight each other? They don't have the guts!",
            "What do you call fake spaghetti? An impasta!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "What do you call a bear with no teeth? A gummy bear!"
        ]
        return random.choice(jokes)

    def share_fact(self):
        # Share a random interesting fact for Ultra model
        facts = [
            "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.",
            "A group of flamingos is called a 'flamboyance'.",
            "Octopuses have three hearts and blue blood.",
            "The shortest war in history lasted only 38-45 minutes, between Britain and Zanzibar in 1896.",
            "A single cloud can weigh more than a million pounds.",
            "Bananas are berries, but strawberries aren't.",
            "The human brain uses about 20% of the body's total energy.",
            "There are more possible games of chess than there are atoms in the observable universe.",
            "A day on Venus is longer than its year.",
            "The Great Wall of China is not visible from space with the naked eye."
        ]
        return random.choice(facts)

    def get_calendar_info(self):
        # Get current date and time information
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_date = now.strftime("%Y-%m-%d")
        day_of_week = now.strftime("%A")

        # Get calendar information for current month
        cal = calendar.month(now.year, now.month)

        return f"Current Date & Time:\n- Date: {current_date}\n- Time: {current_time}\n- Day: {day_of_week}\n\nCalendar for {now.strftime('%B %Y')}:\n{cal}"

    def set_reminder(self, reminder_text):
        # Simple text-based reminder storage (in production, use a database)
        if not hasattr(self, 'reminders'):
            self.reminders = []

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reminder = f"[{timestamp}] {reminder_text}"
        self.reminders.append(reminder)

        return f"Reminder set: {reminder_text}\nTotal reminders: {len(self.reminders)}"

    def get_reminders(self):
        # Get all stored reminders
        if not hasattr(self, 'reminders') or not self.reminders:
            return "No reminders set."

        reminder_list = "\n".join(f"{i+1}. {reminder}" for i, reminder in enumerate(self.reminders))
        return f"Your reminders:\n{reminder_list}"

    def search_image(self, query):
        # Use Unsplash API to search for images and return the first result
        try:
            # Clean the query for search
            search_query = query.replace(' ', '+').lower()
            # Note: You need to get a free Unsplash API key from https://unsplash.com/developers
            # Replace 'YOUR_UNSPLASH_ACCESS_KEY' with your actual key
            api_key = 'YOUR_UNSPLASH_ACCESS_KEY'  # Replace with actual API key
            url = f"https://api.unsplash.com/search/photos?query={search_query}&per_page=1&client_id={api_key}"

            if api_key == 'YOUR_UNSPLASH_ACCESS_KEY':
                # Fallback if no API key provided
                encoded_query = urllib.parse.quote(query)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_query}"
                return f"IMAGE_URL: {image_url}\nDescription: Visual result for '{query}'"

            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    image_url = data['results'][0]['urls']['regular']
                    description = data['results'][0]['description'] or f"Image for '{query}'"
                    return f"IMAGE_URL: {image_url}\nDescription: {description}\nPhotographer: {data['results'][0]['user']['name']}"
                else:
                    return f"No images found for '{query}'. Try a different search term."
            else:
                return f"Error searching images: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Error searching images: {str(e)}\nDescription: Image search for '{query}'"

    def search_video(self, query):
        # Simple video search - return YouTube links (in production, use actual video APIs)
        video_links = {
            "tutorial": "https://www.youtube.com/results?search_query=programming+tutorial",
            "music": "https://www.youtube.com/results?search_query=relaxing+music",
            "news": "https://www.youtube.com/results?search_query=latest+news",
            "funny": "https://www.youtube.com/results?search_query=funny+videos",
            "educational": "https://www.youtube.com/results?search_query=educational+content",
            "cooking": "https://www.youtube.com/results?search_query=cooking+tutorial",
            "workout": "https://www.youtube.com/results?search_query=home+workout",
            "travel": "https://www.youtube.com/results?search_query=travel+vlog"
        }

        # Find closest match
        for key in video_links:
            if key in query.lower():
                return f"Video search for '{query}': {video_links[key]}"

        # Default search
        return f"Video search for '{query}': https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

    def generate_image(self, prompt):
        """Generates an image based on a prompt using Pollinations.ai."""
        try:
            # Use Pollinations.ai (free, no key required)
            encoded_prompt = urllib.parse.quote(prompt)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            return f"IMAGE_URL: {image_url}"
        except Exception as e:
            return f"Error generating image: {str(e)}"

    def set_roleplay_mode(self, persona):
        # Set role-playing persona with content filtering
        personas = {
            "customer_service": "I am a helpful customer service representative. How can I assist you today?",
            "teacher": "I am your friendly teacher. What would you like to learn about?",
            "friend": "Hey buddy! I'm here as your friend. What's up?",
            "doctor": "Hello, I'm Dr. Orion. How are you feeling today?",
            "chef": "Bonjour! I'm Chef Orion. What delicious dish shall we prepare?",
            "detective": "Detective Orion here. What mystery needs solving?",
            "normal": "Back to normal Orion mode."
        }

        if persona in personas:
            self.current_persona = persona
            return personas[persona]
        else:
            return f"Available personas: {', '.join(personas.keys())}\nUse /roleplay <persona> to switch."

    def check_age_verification(self, user_input):
        # Check if content requires age verification
        sensitive_keywords = [
            "adult", "mature", "explicit", "nsfw", "inappropriate", "jailbreak",
            "uncensored", "unrestricted", "bypass", "override", "nudity", "naked"
        ]

        if any(keyword in user_input.lower() for keyword in sensitive_keywords):
            return True  # Requires verification
        return False

    def verify_age(self, birth_date_str, confirm, robot_answer):
        # Enhanced age verification with birth date in mm/dd/yyyy format, confirmation, and robot check
        try:
            # Parse mm/dd/yyyy format
            parts = birth_date_str.split('/')
            if len(parts) != 3:
                return "Invalid date format. Please use mm/dd/yyyy format."
            month = int(parts[0])
            day = int(parts[1])
            year = int(parts[2])

            # Validate date ranges
            if not (1 <= month <= 12):
                return "Invalid month. Please enter a month between 1 and 12."
            if not (1 <= day <= 31):
                return "Invalid day. Please enter a day between 1 and 31."
            if year < 1900 or year > datetime.date.today().year:
                return "Invalid year. Please enter a valid birth year."

            # Calculate age
            today = datetime.date.today()
            birth_date = datetime.date(year, month, day)
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

            if age >= 18 and confirm in ['yes', 'confirm'] and robot_answer == 'no':
                self.age_verified = True
                return "Age verified. You can now access adult content."
            elif age < 18:
                return "You must be 18 or older to access adult content."
            elif robot_answer != 'no':
                return "Invalid robot verification. Please answer 'no' to 'are you a robot?'."
            else:
                return "Invalid confirmation. Type 'yes' or 'confirm' to verify."
        except ValueError:
            return "Please enter a valid birth date in mm/dd/yyyy format."

# For testing purposes
if __name__ == "__main__":
    orion = OrionChatbot()
    print("Orion Chatbot initialized. Type 'exit' to quit.")
    try:
        while True:
            # The EOFError occurs here if the environment is non-interactive
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break
            response = orion.get_response(user_input)
            print(f"Orion: {response}")
    except (EOFError, KeyboardInterrupt):
        print("\n[System] Session ended. Goodbye!")
