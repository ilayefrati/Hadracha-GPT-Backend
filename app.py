import requests
from openai import OpenAI
from flask import Flask, jsonify, request
import json
from flask_cors import CORS

API_KEY = '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'

client = OpenAI(api_key=API_KEY)
ASSISTANT_ID = 'asst_gD47XKABIsB43nodR1e3lq02'
VECTOR_STORE_ID = 'vs_y0yhscNtVdVwQBQ0S1DXcVih'

app = Flask(__name__)
CORS(app)

# Define and initialize thread_id
thread_id = None

# Attach the vector store to the assistant
def attach_vector_store():
    try:
        # assistant = client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)
        client.beta.assistants.update(
            assistant_id=ASSISTANT_ID,
            tool_resources={"file_search": {"vector_store_ids": [VECTOR_STORE_ID]}}
        )
        print("Vector store successfully attached to the assistant.")
    except Exception as e:
        print(f"Error attaching vector store: {e}")

@app.route("/send-messages", methods=["POST"])
def send_messages():
    global thread_id

    # Get the user message from the request
    msg_content = request.json.get("message")
    if not msg_content:
        return jsonify({"error": "Message content is required"}), 400

    try:
        # Create a THREAD if this is the first request
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id

        # Send the user's message
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=msg_content
        )

        # Create a new run and use the ASSISTANT_ID
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID,
        )

        # Check the run status
        if run.status == 'completed':
            # Retrieve the assistant's response
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            assistant_message = next(
                (msg.content[0].text.value for msg in messages.data if msg.role == "assistant"),
                None
            )

            if assistant_message:
                return jsonify({"response": assistant_message}), 200
            else:
                return jsonify({"error": "No response from assistant."}), 500
        else:
            return jsonify({"error": f"Run not completed. Status: {run.status}" }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Attach the vector store before starting the Flask server
    attach_vector_store()
    app.run(debug=True)
