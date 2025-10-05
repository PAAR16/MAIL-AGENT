# app.py
import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import gmail_tools

# --- UPDATED: Import from the correct SDK library ---
from cerebras.cloud.sdk import Cerebras
# --- End of Update ---

load_dotenv()

app = Flask(__name__)

# --- Configuration ---
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
if not CEREBRAS_API_KEY:
    raise ValueError("CEREBRAS_API_KEY not found in .env file. Please set it.")

MODEL_NAME = "llama-3.3-70b"

# --- UPDATED: Initialize the Cerebras client as per the documentation ---
try:
    # The SDK automatically uses the environment variable if not passed directly
    client = Cerebras() 
except Exception as e:
    raise RuntimeError(f"Failed to initialize Cerebras SDK: {e}")
# --- End of Update ---


# --- Tool Definition ---
AVAILABLE_TOOLS = {
    "list_last_n_mails": gmail_tools.list_last_n_mails,
    "search_and_group_mails": gmail_tools.search_and_group_mails,
    "draft_email": gmail_tools.draft_email,
}

SYSTEM_PROMPT = """
You are a helpful assistant with access to a user's Gmail account.
You can perform the following actions:
- `list_last_n_mails(n)`: List the last N emails.
- `search_and_group_mails(keywords_str)`: Search for emails with a comma-separated list of keywords.
- `draft_email(to, subject, body)`: Draft an email. For this, you MUST have the recipient's email, the subject, and the body content. If any are missing, ask the user for the missing information.

When a user asks you to do something, you must respond with a JSON object with two keys:
1. "thought": A short sentence explaining what you are about to do.
2. "tool_call": An object with "name" of the tool and "args" for its parameters.

Example user request: "show me my last 3 emails"
Your response:
{
    "thought": "The user wants to see their last 3 emails. I should use the `list_last_n_mails` tool with n=3.",
    "tool_call": {
        "name": "list_last_n_mails",
        "args": {
            "n": 3
        }
    }
}

If you don't need to call a tool, or if you need more information from the user, respond with a JSON object where "tool_call" is null.
"""

# --- FULLY REWRITTEN: call_cerebras_llm function using the correct SDK methods ---
def call_cerebras_llm(user_prompt):
    """Calls the Cerebras API using the official SDK to get the agent's decision."""
    try:
        # This structure matches the official documentation you provided
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        # Access the response content from the SDK's object structure
        return response.choices[0].message.content
    except Exception as e:
        # Catch any exceptions from the SDK (e.g., authentication, connection)
        print(f"Error calling Cerebras SDK: {e}")
        # Return a structured error message so the frontend can display it
        error_message = str(e)
        return json.dumps({
            "thought": f"An error occurred while contacting the AI model: {error_message}", 
            "tool_call": None
        })
# --- End of Rewritten Function ---


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    llm_decision_str = call_cerebras_llm(user_message)

    try:
        llm_decision = json.loads(llm_decision_str)
        tool_call = llm_decision.get("tool_call")
    except json.JSONDecodeError:
        return jsonify({"reply": llm_decision_str})

    if tool_call and tool_call.get("name") in AVAILABLE_TOOLS:
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})
        tool_function = AVAILABLE_TOOLS[tool_name]
        
        try:
            tool_output = tool_function(**tool_args)
            return jsonify({"tool_output": tool_output})
        except Exception as e:
            return jsonify({"tool_output": f"Error executing tool '{tool_name}': {e}"})
    
    else:
        reply = llm_decision.get("thought", "I'm not sure how to respond to that.")
        return jsonify({"reply": reply})

if __name__ == '__main__':
    print("Checking Gmail authentication...")
    gmail_tools.get_gmail_service()
    print("Authentication successful. Starting Flask server...")
    app.run(debug=True, port=5001)