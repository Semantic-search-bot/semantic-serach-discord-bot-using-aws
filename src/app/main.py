import os
import datetime
from flask import Flask, jsonify, request
from mangum import Mangum
from asgiref.wsgi import WsgiToAsgi
from discord_interactions import verify_key_decorator
from opensearchpy import OpenSearch

# Environment variables
DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY")
OPENSEARCH_ENDPOINT = os.environ.get("OPENSEARCH_ENDPOINT")

# Initialize Flask app
app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app)

# Initialize OpenSearch client
client = OpenSearch(
    hosts=[OPENSEARCH_ENDPOINT],
    http_auth=("admin", "Optimusbot*19"),  # Replace with actual credentials if needed
)

def ensure_index_exists(index_name):
    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name)
        print(f"Created index: {index_name}")

def log_to_opensearch(index_name, document):
    try:
        ensure_index_exists(index_name)
        if not isinstance(document, dict):
            raise ValueError("Document must be a dictionary.")
        response = client.index(index=index_name, body=document)
        print(f"Document indexed: {response['_id']}")
    except Exception as e:
        print(f"Failed to index document: {e}")


@app.route("/", methods=["POST"])
def interactions():
    print(f"👉 Request: {request.json}")
    raw_request = request.json
    return interact(raw_request)

@verify_key_decorator(DISCORD_PUBLIC_KEY)
def interact(raw_request):
    if raw_request["type"] == 1:  # PING
        response_data = {"type": 1}  # PONG
    else:
        data = raw_request["data"]
        command_name = data["name"]

        # Prepare message content
        if command_name == "hello":
            message_content = "Hello there!"
        elif command_name == "bye":
            message_content = "Bye now Akanksha and Omkar!"
        elif command_name == "echo":
            original_message = data["options"][0]["value"]
            message_content = f"Echoing: {original_message}"
        elif command_name == "search":
            message_content = "Search feature coming soon!"
        else:
            message_content = "Unknown command."

        # Log the interaction to OpenSearch
        log_to_opensearch("discord-commands", {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "command": command_name,
            "response": message_content,
        })

        response_data = {
            "type": 4,
            "data": {"content": message_content},
        }

    return jsonify(response_data)

# Sample endpoint to verify OpenSearch connection
@app.route("/test", methods=["GET"])
def add_test_document():
    log_to_opensearch("discord-commands", {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "test_message": "Testing OpenSearch connection.",
    })
    return jsonify({"status": "success", "message": "Test document added."})


if __name__ == "__main__":
    app.run(debug=True)
