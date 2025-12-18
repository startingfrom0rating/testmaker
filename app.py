import os
import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

# App configuration
st.set_page_config(page_title="AI Tutor", page_icon="📚", layout="wide")

# Password for authentication
CORRECT_PASSWORD = os.getenv("APP_PASSWORD")


def init_session_state():
    """Initialize session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "api_key" not in st.session_state:
        st.session_state.api_key = None
    if "api_key_entry" not in st.session_state:
        st.session_state.api_key_entry = ""


def reset_api_state(message, details=None, clear_entry=True):
    """Clear API state and surface an error to the user."""
    st.session_state.model = None
    st.session_state.api_key = None
    if clear_entry:
        st.session_state.api_key_entry = ""
    st.error(message)
    if details:
        st.caption(details)
    if "model" not in st.session_state:
        st.session_state.model = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "guided_history" not in st.session_state:
        st.session_state.guided_history = []
    if "guided_topic" not in st.session_state:
        st.session_state.guided_topic = ""
    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = None
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}


def configure_model():
    """Configure the Gemini model once the user provides an API key."""
    if st.session_state.api_key:
        try:
            genai.configure(api_key=st.session_state.api_key)
            st.session_state.model = genai.GenerativeModel('gemini-1.5-flash')
        except GoogleAPIError as e:
            reset_api_state(
                "Failed to initialize Gemini model. Please re-enter a valid API key.",
                f"Initialization details: {e}",
            )
        except Exception as e:
            reset_api_state(
                "Unexpected error initializing Gemini model. Please try again.",
                f"Details: {e}",
                clear_entry=False,
            )


def login_screen():
    """Display the login screen."""
    st.title("🔐 AI Tutor Login")
    st.markdown("Please enter the password to access the AI Tutor.")
    
    if CORRECT_PASSWORD is None:
        st.error("Application password is not configured. Set the APP_PASSWORD environment variable.")
        return
    
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if password == CORRECT_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")


def guided_learning():
    """Guided Learning mode - Socratic tutor."""
    st.header("📖 Guided Learning")
    st.markdown("Learn any topic step-by-step with a Socratic tutor approach.")
    
    if not st.session_state.model:
        st.error("Model is not initialized. Please enter a valid API key to continue.")
        return
    
    # Topic input
    topic = st.text_input("Enter a topic you want to learn:", value=st.session_state.guided_topic)
    
    if topic != st.session_state.guided_topic:
        st.session_state.guided_topic = topic
        st.session_state.guided_history = []
    
    if st.button("Start Learning") and topic:
        st.session_state.guided_history = []
        system_prompt = f"""You are a Socratic tutor. The student wants to learn about: {topic}

Your task is to:
1. Explain the topic in small, digestible steps
2. After each explanation, ask the student a question to verify their understanding
3. Wait for their response before moving to the next concept
4. If they answer incorrectly, gently guide them to the correct understanding
5. Be encouraging and supportive

Start by introducing the topic and explaining the first concept, then ask a question."""
        
        try:
            response = st.session_state.model.generate_content(system_prompt)
            st.session_state.guided_history.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
    
    # Display conversation history
    for message in st.session_state.guided_history:
        if message["role"] == "assistant":
            st.markdown(f"**🤖 Tutor:** {message['content']}")
        else:
            st.markdown(f"**👤 You:** {message['content']}")
    
    # User response input
    if st.session_state.guided_history:
        user_response = st.text_input("Your response:", key="guided_response")
        
        if st.button("Send Response") and user_response:
            st.session_state.guided_history.append({"role": "user", "content": user_response})
            
            # Build conversation context
            conversation = f"Topic: {st.session_state.guided_topic}\n\n"
            for msg in st.session_state.guided_history:
                role = "Tutor" if msg["role"] == "assistant" else "Student"
                conversation += f"{role}: {msg['content']}\n\n"
            
            continuation_prompt = f"""{conversation}

Continue as a Socratic tutor. Based on the student's response:
- If correct, praise them and move to the next concept with a new question
- If incorrect, gently guide them toward understanding
- Keep explanations concise and ask questions to verify understanding"""
            
            try:
                response = st.session_state.model.generate_content(continuation_prompt)
                st.session_state.guided_history.append({"role": "assistant", "content": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")


def practice_tests():
    """Practice Tests mode - Quiz generator."""
    st.header("📝 Practice Tests")
    st.markdown("Generate quizzes to test your knowledge on any topic.")
    
    if not st.session_state.model:
        st.error("Model is not initialized. Please enter a valid API key to continue.")
        return
    
    topic = st.text_input("Enter a topic for the quiz:")
    
    if st.button("Generate Quiz") and topic:
        st.session_state.quiz_submitted = False
        st.session_state.user_answers = {}
        
        quiz_prompt = f"""Generate exactly 5 multiple-choice questions about: {topic}

Format your response EXACTLY as follows (use this exact format):

Q1: [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct: [A/B/C/D]
Explanation: [Brief explanation]

Q2: [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct: [A/B/C/D]
Explanation: [Brief explanation]

Q3: [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct: [A/B/C/D]
Explanation: [Brief explanation]

Q4: [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct: [A/B/C/D]
Explanation: [Brief explanation]

Q5: [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct: [A/B/C/D]
Explanation: [Brief explanation]"""
        
        try:
            response = st.session_state.model.generate_content(quiz_prompt)
            st.session_state.quiz_questions = parse_quiz(response.text)
        except Exception as e:
            st.error(f"Error generating quiz: {str(e)}")
    
    # Display quiz
    if st.session_state.quiz_questions:
        questions = st.session_state.quiz_questions
        
        with st.form("quiz_form"):
            for i, q in enumerate(questions):
                st.markdown(f"**Question {i+1}:** {q['question']}")
                options = [f"A) {q['A']}", f"B) {q['B']}", f"C) {q['C']}", f"D) {q['D']}"]
                st.session_state.user_answers[i] = st.radio(
                    f"Select your answer for Q{i+1}:",
                    options,
                    key=f"q_{i}",
                    label_visibility="collapsed"
                )
                st.markdown("---")
            
            submitted = st.form_submit_button("Submit Quiz")
            
            if submitted:
                st.session_state.quiz_submitted = True
        
        # Show results after submission
        if st.session_state.quiz_submitted:
            st.markdown("## Results")
            score = 0
            
            for i, q in enumerate(questions):
                user_answer = st.session_state.user_answers.get(i, "")
                user_letter = user_answer[0] if user_answer else ""
                correct = user_letter == q['correct']
                
                if correct:
                    score += 1
                    st.success(f"**Q{i+1}:** ✅ Correct!")
                else:
                    st.error(f"**Q{i+1}:** ❌ Incorrect. The correct answer is {q['correct']})")
                
                st.info(f"**Explanation:** {q['explanation']}")
                st.markdown("---")
            
            st.markdown(f"## Final Score: {score}/5")
            
            if score == 5:
                st.balloons()
                st.success("Perfect score! Excellent work! 🎉")
            elif score >= 3:
                st.success("Good job! Keep practicing! 👍")
            else:
                st.warning("Keep studying and try again! 📚")


def parse_quiz(quiz_text):
    """Parse the quiz text into structured questions."""
    questions = []
    lines = quiz_text.strip().split('\n')
    
    current_question = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith(('Q1:', 'Q2:', 'Q3:', 'Q4:', 'Q5:')):
            if current_question and 'question' in current_question:
                questions.append(current_question)
            current_question = {'question': line.split(':', 1)[1].strip()}
        elif line.startswith('A)'):
            current_question['A'] = line[2:].strip()
        elif line.startswith('B)'):
            current_question['B'] = line[2:].strip()
        elif line.startswith('C)'):
            current_question['C'] = line[2:].strip()
        elif line.startswith('D)'):
            current_question['D'] = line[2:].strip()
        elif line.startswith('Correct:'):
            current_question['correct'] = line.split(':')[1].strip()
        elif line.startswith('Explanation:'):
            current_question['explanation'] = line.split(':', 1)[1].strip()
    
    if current_question and 'question' in current_question:
        questions.append(current_question)
    
    # Ensure we have valid questions
    valid_questions = []
    for q in questions:
        if all(key in q for key in ['question', 'A', 'B', 'C', 'D', 'correct', 'explanation']):
            valid_questions.append(q)
    
    return valid_questions[:5]  # Return at most 5 questions


def free_chat():
    """Free Chat mode - Open-ended chat with Gemini."""
    st.header("💬 Free Chat")
    st.markdown("Ask any question or discuss any topic with the AI.")
    
    if not st.session_state.model:
        st.error("Model is not initialized. Please enter a valid API key to continue.")
        return
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"**👤 You:** {message['content']}")
        else:
            st.markdown(f"**🤖 AI:** {message['content']}")
    
    # User input
    user_input = st.text_input("Type your message:", key="chat_input")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        send = st.button("Send")
    with col2:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    if send and user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Build conversation context
        conversation = ""
        for msg in st.session_state.chat_history[-10:]:  # Keep last 10 messages for context
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation += f"{role}: {msg['content']}\n\n"
        
        prompt = f"""You are a helpful AI assistant. Continue the conversation naturally.

{conversation}
Assistant:"""
        
        try:
            response = st.session_state.model.generate_content(prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
            st.rerun()
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")


def main():
    """Main application function."""
    init_session_state()
    
    if not st.session_state.authenticated:
        login_screen()
    else:
        if not st.session_state.api_key:
            st.title("🔑 Enter your Google API Key")
            key_input = st.text_input("API Key", type="password", placeholder="Enter your Google Generative AI API key", key="api_key_entry")
            if st.button("Save API Key") and key_input:
                st.session_state.api_key = key_input.strip()
                configure_model()
                st.rerun()
            st.info("Your API key is only kept in this session and not stored.")
            return
        if not st.session_state.model:
            configure_model()
            if not st.session_state.model:
                st.error("Model could not be initialized. Please enter a valid API key.")
                return

        # Sidebar navigation
        st.sidebar.title("📚 AI Tutor")
        st.sidebar.markdown("Your personalized AI study platform")
        st.sidebar.markdown("---")
        
        mode = st.sidebar.radio(
            "Select Mode:",
            ["📖 Guided Learning", "📝 Practice Tests", "💬 Free Chat"]
        )
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.chat_history = []
            st.session_state.guided_history = []
            st.session_state.guided_topic = ""
            st.session_state.quiz_questions = None
            st.session_state.quiz_submitted = False
            st.session_state.user_answers = {}
            st.session_state.api_key = None
            st.session_state.api_key_entry = ""
            st.session_state.model = None
            st.rerun()
        
        # Display selected mode
        if mode == "📖 Guided Learning":
            guided_learning()
        elif mode == "📝 Practice Tests":
            practice_tests()
        elif mode == "💬 Free Chat":
            free_chat()


if __name__ == "__main__":
    main()
