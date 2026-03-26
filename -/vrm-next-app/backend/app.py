from flask import Flask, request, jsonify
from flask_cors import CORS
from pinecone import Pinecone
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import os
import sys
import re
from difflib import get_close_matches

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Let's grab our environment variables first
load_dotenv()

# -------------------------
# CONFIGURATION SETTINGS
# -------------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Setting up our API clients for Pinecone and Groq
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("nutrition-myths")
client = Groq(api_key=GROQ_API_KEY)

# Loading our embedding model (needs to be 1024 dimensions to work with our Pinecone setup)
embedding_model = SentenceTransformer("BAAI/bge-large-en-v1.5")

# -------------------------
# FLASK APP SETUP
# -------------------------
app = Flask(__name__)
CORS(app)

# -------------------------
# SPELL CHECKER VOCABULARY
# -------------------------
# Here's our dictionary of common nutrition words to help catch typos
NUTRITION_VOCABULARY = [
    'protein', 'carbs', 'carbohydrates', 'fat', 'fats', 'calories', 'diet', 
    'weight', 'muscle', 'loss', 'gain', 'healthy', 'nutrition', 'food',
    'vegan', 'vegetarian', 'keto', 'ketogenic', 'diabetes', 'diabetic',
    'pregnant', 'pregnancy', 'vitamins', 'minerals', 'fiber', 'sugar',
    'sodium', 'cholesterol', 'gluten', 'dairy', 'lactose', 'organic',
    'processed', 'whole', 'grain', 'fruit', 'vegetable', 'meat', 'chicken',
    'fish', 'eggs', 'milk', 'cheese', 'bread', 'rice', 'pasta', 'beans',
    'nuts', 'seeds', 'oil', 'butter', 'water', 'juice', 'coffee', 'tea',
    'breakfast', 'lunch', 'dinner', 'snack', 'meal', 'eating', 'drink',
    'good', 'bad', 'better', 'worse', 'best', 'worst', 'should', 'could',
    'myth', 'fact', 'true', 'false', 'really', 'actually', 'always', 'never'
]

def correct_spelling(text):
    """
    Helps fix typos in what users type using smart fuzzy matching
    """
    words = text.split()
    corrected_words = []
    corrections_made = []
    
    for word in words:
        # Don't bother correcting really short words
        if len(word) <= 3:
            corrected_words.append(word)
            continue
        
        # Clean up the word by removing any punctuation
        clean_word = re.sub(r'[^\w\s]', '', word.lower())
        
        # Let's see if we can find a similar word in our vocabulary
        matches = get_close_matches(clean_word, NUTRITION_VOCABULARY, n=1, cutoff=0.7)
        
        if matches and matches[0] != clean_word:
            # Great! We found a better match
            corrected_words.append(matches[0])
            corrections_made.append(f"{word} → {matches[0]}")
        else:
            # This word looks fine or we couldn't find a match
            corrected_words.append(word)
    
    corrected_text = ' '.join(corrected_words)
    return corrected_text, corrections_made

# -------------------------
# TEXT EMBEDDING FUNCTION
# -------------------------
def embed(text):
    emb = embedding_model.encode(text)
    return emb.tolist()

# -------------------------
# UNDERSTANDING WHAT USERS NEED
# -------------------------
def extract_user_context(message):
    """
    Figures out what the user's goals are, what diet they follow, and any health stuff
    This helps us give them personalized advice that actually matters to them
    """
    message_lower = message.lower()
    context_parts = []
    
    # What's their fitness goal?
    if any(word in message_lower for word in ['lose weight', 'weight loss', 'fat loss', 'slim down', 'cut']):
        context_parts.append("User wants to lose weight")
    elif any(word in message_lower for word in ['gain muscle', 'build muscle', 'bulk', 'get stronger', 'bodybuilding']):
        context_parts.append("User wants to gain muscle")
    elif any(word in message_lower for word in ['maintain', 'stay healthy', 'general health']):
        context_parts.append("User focused on general health")
    
    # What's their eating style?
    if any(word in message_lower for word in ['vegan', "i'm vegan", "i am vegan"]):
        context_parts.append("User is vegan")
    elif any(word in message_lower for word in ['vegetarian', "i'm vegetarian", "i am vegetarian"]):
        context_parts.append("User is vegetarian")
    
    if any(word in message_lower for word in ['keto', 'ketogenic', 'low carb']):
        context_parts.append("User follows keto/low-carb diet")
    
    # Any health conditions we should know about?
    if any(word in message_lower for word in ['diabetic', 'diabetes', 'blood sugar']):
        context_parts.append("User has diabetes concerns")
    elif any(word in message_lower for word in ['pregnant', 'pregnancy', "i'm pregnant"]):
        context_parts.append("User is pregnant")
    
    if context_parts:
        return ". ".join(context_parts) + "."
    return ""

def is_general_question(query):
    """
    Checks if someone's asking something super vague that needs more details
    Returns True if we should ask them to be more specific about their goals
    """
    query_lower = query.lower()
    
    # These are the vague nutrition words people use when they need more specific advice
    general_terms = [
        'protein', 'carbs', 'carbohydrates', 'fat', 'fats', 
        'calories', 'diet', 'food', 'eat', 'nutrition',
        'healthy', 'good', 'bad', 'should i', 'can i'
    ]
    
    # Is it a broad question without enough detail to give a useful answer?
    has_general_term = any(term in query_lower for term in general_terms)
    has_no_context = not extract_user_context(query)
    
    # Really vague questions like "is protein good?" or "should I eat carbs?"
    is_vague = any(pattern in query_lower for pattern in [
        'is protein good', 'are carbs good', 'are fats good',
        'should i eat protein', 'should i eat carbs', 'should i eat fats',
        'is diet good', 'how much protein', 'how much carbs',
        'protein intake', 'carb intake', 'fat intake'
    ])
    
    return (has_general_term and has_no_context) or is_vague

def get_context_specific_buttons(query):
    """
    Gives users relevant options based on what they're asking about
    Makes the conversation more personalized and helpful
    """
    query_lower = query.lower()
    
    # If they're asking about protein...
    if any(word in query_lower for word in ['protein', 'meat', 'chicken', 'fish', 'eggs', 'tofu']):
        return [
            {"label": "💪 Build Muscle", "value": "I want to gain muscle"},
            {"label": "🏃‍♀️ Lose Weight", "value": "I want to lose weight"},
            {"label": "🌱 I'm Vegan", "value": "I'm vegan"},
            {"label": "🏋️ Athletic Performance", "value": "I'm an athlete"},
            {"label": "👶 Pregnancy", "value": "I'm pregnant"},
            {"label": "🥗 General Health", "value": "I want to maintain general health"}
        ]
    
    # If they're asking about carbs...
    elif any(word in query_lower for word in ['carbs', 'carbohydrate', 'rice', 'bread', 'pasta', 'sugar', 'glucose']):
        return [
            {"label": "🏃‍♀️ Lose Weight", "value": "I want to lose weight"},
            {"label": "💪 Build Muscle", "value": "I want to gain muscle"},
            {"label": "🥑 Low-Carb/Keto", "value": "I follow a keto diet"},
            {"label": "🩺 Diabetic", "value": "I have diabetes"},
            {"label": "🏋️ Athletic Training", "value": "I'm an athlete"},
            {"label": "🧠 Mental Focus", "value": "I want better energy and focus"}
        ]
    
    # If they're asking about fats...
    elif any(word in query_lower for word in ['fat', 'fats', 'oil', 'butter', 'cheese', 'avocado', 'omega']):
        return [
            {"label": "❤️ Heart Health", "value": "I'm concerned about heart health"},
            {"label": "🏃‍♀️ Lose Weight", "value": "I want to lose weight"},
            {"label": "🥑 Low-Carb/Keto", "value": "I follow a keto diet"},
            {"label": "🧠 Brain Health", "value": "I want to improve cognitive function"},
            {"label": "💪 Build Muscle", "value": "I want to gain muscle"},
            {"label": "🩺 High Cholesterol", "value": "I have high cholesterol"}
        ]
    
    # If they're asking about dairy...
    elif any(word in query_lower for word in ['milk', 'dairy', 'lactose', 'yogurt', 'cheese']):
        return [
            {"label": "🦴 Bone Health", "value": "I'm concerned about bone health"},
            {"label": "🌱 Dairy-Free", "value": "I'm lactose intolerant or vegan"},
            {"label": "🏃‍♀️ Lose Weight", "value": "I want to lose weight"},
            {"label": "💪 Build Muscle", "value": "I want to gain muscle"},
            {"label": "🥗 General Health", "value": "I want to maintain general health"}
        ]
    
    # If they're asking about sugar...
    elif any(word in query_lower for word in ['sugar', 'sweet', 'dessert', 'candy', 'artificial sweetener']):
        return [
            {"label": "🩺 Diabetic", "value": "I have diabetes"},
            {"label": "🏃‍♀️ Lose Weight", "value": "I want to lose weight"},
            {"label": "🦷 Dental Health", "value": "I'm concerned about teeth health"},
            {"label": "🧠 Energy Levels", "value": "I want stable energy throughout the day"},
            {"label": "🥑 Low-Carb", "value": "I follow a keto or low-carb diet"}
        ]
    
    # If they're asking about diets in general...
    elif any(word in query_lower for word in ['diet', 'dieting', 'eating plan', 'meal plan']):
        return [
            {"label": "🏃‍♀️ Lose Weight", "value": "I want to lose weight"},
            {"label": "💪 Build Muscle", "value": "I want to gain muscle"},
            {"label": "🌱 Plant-Based", "value": "I'm vegan or vegetarian"},
            {"label": "🥑 Low-Carb/Keto", "value": "I follow a keto diet"},
            {"label": "🩺 Medical Diet", "value": "I have specific health conditions"},
            {"label": "⚖️ Balanced Approach", "value": "I want sustainable healthy eating"}
        ]
    
    # If they're asking about calories or weight...
    elif any(word in query_lower for word in ['calorie', 'calories', 'weight', 'lose', 'gain', 'metabolism']):
        return [
            {"label": "🏃‍♀️ Lose Weight", "value": "I want to lose weight"},
            {"label": "💪 Gain Muscle", "value": "I want to gain muscle"},
            {"label": "⚖️ Maintain Weight", "value": "I want to maintain my weight"},
            {"label": "🏋️ Athletic Goals", "value": "I'm training for sports"},
            {"label": "🩺 Medical Reasons", "value": "I need to manage weight for health"},
            {"label": "🥗 General Health", "value": "I want to eat healthier overall"}
        ]
    
    # If they're asking about fruits and vegetables...
    elif any(word in query_lower for word in ['fruit', 'vegetable', 'veggie', 'salad', 'greens', 'produce']):
        return [
            {"label": "🥗 General Health", "value": "I want to maintain general health"},
            {"label": "🏃‍♀️ Lose Weight", "value": "I want to lose weight"},
            {"label": "🌱 Vegan", "value": "I'm vegan or vegetarian"},
            {"label": "🩺 Disease Prevention", "value": "I want to prevent chronic diseases"},
            {"label": "💪 Athletic Nutrition", "value": "I'm an athlete"},
            {"label": "🧒 Family Nutrition", "value": "I'm planning meals for my family"}
        ]
    
    # If they're asking about vitamins or supplements...
    elif any(word in query_lower for word in ['vitamin', 'supplement', 'mineral', 'nutrient', 'deficiency']):
        return [
            {"label": "🥗 General Health", "value": "I want to optimize my nutrition"},
            {"label": "🌱 Vegan/Vegetarian", "value": "I follow a plant-based diet"},
            {"label": "👶 Pregnancy", "value": "I'm pregnant or planning to be"},
            {"label": "👴 Aging Health", "value": "I'm concerned about aging"},
            {"label": "🏋️ Athletic Performance", "value": "I'm an athlete"},
            {"label": "🩺 Health Condition", "value": "I have specific health concerns"}
        ]
    
    # If they're asking about when to eat...
    elif any(word in query_lower for word in ['breakfast', 'lunch', 'dinner', 'snack', 'fasting', 'meal timing', 'when to eat']):
        return [
            {"label": "🏃‍♀️ Lose Weight", "value": "I want to lose weight"},
            {"label": "💪 Build Muscle", "value": "I want to gain muscle"},
            {"label": "🏋️ Athletic Performance", "value": "I'm training for sports"},
            {"label": "🧠 Energy & Focus", "value": "I want better energy throughout the day"},
            {"label": "⏰ Intermittent Fasting", "value": "I practice intermittent fasting"},
            {"label": "🥗 General Health", "value": "I want healthy eating habits"}
        ]
    
    # If they're asking about water or drinks...
    elif any(word in query_lower for word in ['water', 'hydration', 'drink', 'fluid', 'juice', 'beverage']):
        return [
            {"label": "🏋️ Athletic Performance", "value": "I'm an athlete"},
            {"label": "🏃‍♀️ Lose Weight", "value": "I want to lose weight"},
            {"label": "🧠 Better Focus", "value": "I want improved mental clarity"},
            {"label": "🦴 Kidney Health", "value": "I'm concerned about kidney health"},
            {"label": "🩺 Health Condition", "value": "I have specific medical needs"},
            {"label": "🥗 General Health", "value": "I want to stay healthy"}
        ]
    
    # For everything else, give them the most common options
    else:
        return [
            {"label": "🏃‍♀️ Lose Weight", "value": "I want to lose weight"},
            {"label": "💪 Build Muscle", "value": "I want to gain muscle"},
            {"label": "🥗 Stay Healthy", "value": "I want to maintain general health"},
            {"label": "🌱 I'm Vegan", "value": "I'm vegan"},
            {"label": "🥑 Low-Carb/Keto", "value": "I follow a keto diet"},
            {"label": "🩺 Health Condition", "value": "I have specific health concerns"}
        ]

# -------------------------
# SEARCHING OUR NUTRITION DATABASE
# -------------------------
def pinecone_search(query):
    query_vec = embed(query)

    result = index.query(
        vector=query_vec,
        top_k=5,
        include_metadata=True,
        namespace="default"  # This is where we stored our nutrition data
    )

    chunks = []
    for m in result.matches:
        # Pull out the myth, fact, and explanation from what we stored
        myth = m.metadata.get("myth", "")
        fact = m.metadata.get("fact", "")
        explanation = m.metadata.get("explanation", "")
        source_title = m.metadata.get("source_title", "")
        source_url = m.metadata.get("source_url", "")
        source_type = m.metadata.get("source_type", "")
        
        # Put it together in a nice readable format
        if myth and fact:
            text = f"**Myth**: {myth}\n\n**Fact**: {fact}"
            if explanation:
                text += f"\n\n**Explanation**: {explanation}"
        else:
            # If the data structure is different, try other fields
            text = (m.metadata.get("text", "") or 
                   m.metadata.get("chunk_text", "") or 
                   m.metadata.get("raw_text", ""))
        
        if text and len(text) > 10:
            chunks.append({
                "id": m.id,
                "score": m.score,
                "text": text,
                "source_title": source_title,
                "source_url": source_url,
                "source_type": source_type
            })

    return chunks

# -------------------------
# FIGURING OUT IF IT'S A MYTH OR FACT
# -------------------------
def classify_myth_or_fact(query):
    prompt = f"Classify the following nutrition question as either a MYTH or a FACT.\nQuestion: '{query}'\nReply with EXACTLY ONE WORD: either 'myth' or 'fact'."
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.choices[0].message.content.strip().lower()
    if "myth" in result:
        return "myth"
    return "fact"
# -------------------------
# PUTTING TOGETHER THE FINAL ANSWER
# -------------------------
def build_answer(result_type, chunks):
    if result_type == "myth":
        prefix = "❌ This looks like a myth based on my nutrition notes:\n\n"
    else:
        prefix = "✅ This is generally true based on nutrition evidence:\n\n"

    body = ""
    for c in chunks:
        body += f"- {c['text']}\n\n"

    return prefix + body.strip()

# -------------------------
# MAIN CHAT API ENDPOINT
# -------------------------
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get("message", "").strip()
    user_selection = data.get("userSelection", None)
    user_preferences = data.get("userPreferences", [])

    if not user_msg:
        return jsonify({"error": "Message is required"}), 400

    try:
        print(f"📩 Received message: {user_msg}")
        print(f"👆 User selection: {user_selection}")
        print(f"💾 Stored preferences: {user_preferences}")
        
        # Let's fix any typos first
        corrected_msg, corrections = correct_spelling(user_msg)
        if corrections:
            print(f"✏️ Spell corrections: {', '.join(corrections)}")
            correction_note = f"*(I understood: {corrected_msg})*\n\n"
        else:
            correction_note = ""
        
        # Work with the corrected version from here on
        processed_msg = corrected_msg
        
        # Remember what they told us before about their goals and preferences
        preference_context = ""
        if user_preferences:
            preference_context = " ".join(user_preferences) + ". "
        
        # Is this question too vague? Should we ask them for more details?
        # Only show buttons on their first question (before they've told us their preferences)
        if not user_selection and not user_preferences and is_general_question(processed_msg):
            print("❓ Detected general question - returning context-specific options")
            dynamic_buttons = get_context_specific_buttons(processed_msg)
            return jsonify({
                "answer": f"{correction_note}🤔 Great question! To give you the most helpful answer, what's your situation?",
                "buttons": dynamic_buttons,
                "originalQuery": processed_msg
            })
        
        # If they selected something, add it to their original question for better context
        if user_selection:
            combined_query = f"{preference_context}{user_selection}. {processed_msg}"
            print(f"🔄 Combined query: {combined_query}")
        else:
            # Just use what they've told us before
            combined_query = f"{preference_context}{processed_msg}"
            print(f"🔄 Query with preferences: {combined_query}")
        
        # What do we know about this user from their message?
        user_context = extract_user_context(combined_query)
        if user_context:
            print(f"🎯 Detected context: {user_context}")
        
        # Let's search our database for relevant nutrition info
        chunks = pinecone_search(combined_query)
        print(f"🔍 Found {len(chunks)} chunks from Pinecone")
        
        if chunks and len(chunks) > 0:
            # Build context with actual source citations from the dataset
            context_parts = []
            for i, c in enumerate(chunks[:3]):
                source_text = c['text']
                source_title = c.get('source_title', '')
                source_url = c.get('source_url', '')
                
                # Create a natural source reference
                if source_title:
                    source_ref = f"**From: {source_title}**"
                    if source_url:
                        source_ref += f"\n({source_url})"
                    context_parts.append(f"{source_ref}\n{source_text}")
                else:
                    context_parts.append(source_text)
            
            context = "\n\n---\n\n".join(context_parts)
            
            # If we know something about the user's goals/diet/health, tell Groq to personalize
            context_note = ""
            if user_context:
                context_note = f"\n\n⚠️ IMPORTANT PERSONALIZATION: {user_context}\nTailor your advice specifically for this user's situation. Make recommendations that align with their goals/diet/conditions."
            
            prompt = f"""You are a friendly, helpful nutrition expert. Based on the verified nutrition information below, answer the user's question in a warm, conversational way.

Retrieved Information:
{context}{context_note}

User Question: {user_msg}

Instructions:
1. Start directly with the myth/fact assessment - NO greetings like "Hey there, friend!" or "Hello!"
2. If it's debunking a myth or something is unhealthy/untrue, start with "❌ Myth Alert!" followed by what's wrong
3. If it's confirming something is healthy/true/good, start with "✅ That's Right!" or "✅ Yes!" followed by affirmation
4. ALWAYS reference the actual sources from the Retrieved Information - mention the source titles naturally (e.g., "According to Mayo Clinic..." or "Harvard Health explains...")
5. Use clear sections with headers like:
   - **The Truth:** (directly quote or paraphrase from the sources)
   - **The Science:** (explain using the evidence)
   - **Bottom Line:** (practical takeaway)
6. When citing, use the actual source names provided in the "From:" sections - integrate them naturally into your answer
7. Add relevant food emojis where appropriate (🍚 for rice, 🍗 for chicken, 🥦 for vegetables, etc.)
8. Keep it friendly and encouraging - use "you" to make it personal
9. Keep response under 250 words but make it engaging
10. If personalization context is provided, prioritize advice relevant to their specific needs
11. NEVER start with greetings - jump straight into the answer
12. Base your answer on the Retrieved Information and cite the actual source titles naturally

Make it feel like evidence-based advice from a knowledgeable friend, not a textbook!"""

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a friendly, supportive nutrition expert who makes healthy eating feel approachable and fun. Use emojis naturally and structure your responses clearly with markdown formatting. NEVER use greetings like 'Hey there, friend!' or 'Hello!' - start directly with the answer. Always base your answers strictly on the provided Retrieved Information from the nutrition database - cite specific myths, facts, and explanations from the sources."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            answer = completion.choices[0].message.content
            print(f"✅ Generated answer from Groq", flush=True)
            print(f"📝 Full answer start: {answer[:300]}", flush=True)
            
            # Is this debunking a myth or confirming a fact? Let's figure that out
            answer_lower = answer.lower()
            answer_first_200 = answer_lower[:200]
            
            # Check for myth indicators
            is_myth = (
                '❌' in answer or 
                'myth alert' in answer_first_200 or 
                'this is a myth' in answer_first_200 or 
                "that's not quite right" in answer_first_200 or 
                'not true' in answer_first_200 or 
                'false' in answer_first_200 or
                'actually not' in answer_first_200 or
                "isn't true" in answer_first_200 or
                'misconception' in answer_first_200
            )
            
            print(f"🔴 is_myth check: {is_myth}", flush=True)
            
            # Check for fact indicators - expanded to catch positive responses
            is_fact = (
                '✅' in answer or 
                "that's right" in answer_first_200 or 
                "this is true" in answer_first_200 or 
                "this is correct" in answer_first_200 or
                ('yes' in answer_first_200[:50] and '!' in answer_first_200[:50]) or
                'absolutely' in answer_first_200 or
                'indeed' in answer_first_200 or
                ('can be' in answer_first_200 and 'healthy' in answer_first_200) or
                ('part of a healthy' in answer_first_200) or
                ('is a' in answer_first_200 and 'healthy' in answer_first_200) or
                ('good' in answer_first_200 and ('option' in answer_first_200 or 'choice' in answer_first_200 or 'source' in answer_first_200)) or
                ('beneficial' in answer_first_200) or
                ('nutritious' in answer_first_200) or
                ('essential' in answer_first_200 and 'for' in answer_first_200) or
                ('important' in answer_first_200 and 'for' in answer_first_200) or
                ('helps' in answer_first_200 and ('build' in answer_first_200 or 'support' in answer_first_200 or 'maintain' in answer_first_200))
            )
            
            print(f"🟢 is_fact check: {is_fact}", flush=True)
            
            if is_myth:
                answer_type = "myth"
            elif is_fact:
                answer_type = "fact"
            else:
                # Look at the retrieved context to infer
                if chunks and len(chunks) > 0:
                    context_lower = context.lower()
                    if 'myth' in context_lower[:300] or 'false' in context_lower[:300]:
                        answer_type = "myth"
                    elif 'fact' in context_lower[:300] or 'true' in context_lower[:300]:
                        answer_type = "fact"
                    else:
                        answer_type = "general"
                else:
                    answer_type = "general"
            
            print(f"🏷️ FINAL Answer type detected: {answer_type}", flush=True)
            
            # Now let's create a fun little "myTake" summary for the avatar to say
            my_take_prompt = f"Based on this nutrition answer, write ONE SHORT sentence (max 15 words) that's a friendly personal take or key insight. Make it conversational and fun.\n\nAnswer: {answer[:200]}\n\nYour short take:"
            
            my_take_completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": my_take_prompt}
                ],
                temperature=0.7,
                max_tokens=50
            )
            
            my_take = my_take_completion.choices[0].message.content.strip()
            # Clean up any quotes around it
            my_take = my_take.strip('"\'')
            
            print(f"🏷️ Detected answer type: {answer_type}")
            print(f"💭 Generated myTake: {my_take}")
            print(f"📝 Answer preview: {answer[:100]}...")
            
            # Add the spell correction note at the top if we fixed anything
            if correction_note:
                answer = correction_note + answer
        else:
            # Uh oh, we couldn't find anything relevant in our database
            answer = f"{correction_note}🤔 Hmm, I don't have specific information about that topic in my nutrition database yet.\n\n**Try asking about:**\n• Common nutrition myths (carbs, fats, protein)\n• Specific foods (rice, chicken, fruits)\n• Weight management questions\n• Healthy eating tips\n\nI'm here to help separate nutrition facts from fiction! 💪"
            answer_type = "general"
            my_take = "Let me know what nutrition topic you'd like to explore!"
        
        return jsonify({
            "answer": answer,
            "type": answer_type,
            "myTake": my_take,
            "source": "groq_enhanced" if chunks else "fallback"
        })
    except Exception as e:
        print(f"!! ERROR in /api/chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "answer": "😅 Oops! I ran into a technical hiccup. Please try asking your nutrition question again!",
            "error": str(e)
        }), 500

# -------------------------
# START THE SERVER
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)

