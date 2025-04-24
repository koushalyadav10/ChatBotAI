from flask import Flask, request, jsonify
from flask_cors import CORS
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Queue System Data
queues = {
    'account': ['A101', 'A102', 'A103', 'A104'],
    'loan': ['B201', 'B202', 'B203'],
    'card': ['C301', 'C302'],
    'general': ['G401', 'G402', 'G403']
}

counters = {
    1: {'current': 'A101', 'service': 'account', 'paused': False, 'staff': 'Mohan'},
    2: {'current': 'B205', 'service': 'loan', 'paused': False, 'staff': 'Chandan'},
    3: {'current': 'C301', 'service': 'card', 'paused': False, 'staff': 'Priya'}
}

current_token = None
current_customer_name = None
conversation_history = []

# Initialize with system message
conversation_history.append({
    "role": "system",
    "content": "You are a helpful queue assistant for a service center. "
               "The center has counters for Account Services, Loan Applications, "
               "Card Services, and General Inquiry. Help users with their queue "
               "status and provide friendly conversation while they wait."
})

@app.route('/api/generate_token', methods=['POST'])
def generate_token():
    data = request.json
    service_type = data.get('service_type')
    customer_name = data.get('customer_name')
    
    if not service_type or not customer_name:
        return jsonify({'error': 'Service type and customer name are required'}), 400
    
    # Generate token
    prefix = {
        'account': 'A',
        'loan': 'B',
        'card': 'C',
        'general': 'G'
    }.get(service_type, 'X')
    
    last_num = int(queues[service_type][-1][1:]) if queues[service_type] else 0
    new_token = f"{prefix}{last_num + 101}"
    
    # Update system state
    queues[service_type].append(new_token)
    global current_token, current_customer_name
    current_token = new_token
    current_customer_name = customer_name
    
    position = queues[service_type].index(new_token)
    wait_time = position * 5  # 5 minutes per position
    
    return jsonify({
        'token': new_token,
        'position': position + 1,
        'wait_time': wait_time,
        'message': f"Token {new_token} generated. Position: {position + 1}, Wait: {wait_time} min"
    })

@app.route('/api/call_next', methods=['POST'])
def call_next():
    data = request.json
    counter_num = data.get('counter_num')
    
    if counter_num not in counters:
        return jsonify({'error': 'Invalid counter number'}), 400
    
    counter = counters[counter_num]
    if counter['paused']:
        return jsonify({'error': 'Counter is paused'}), 400
    
    service_type = counter['service']
    if not queues[service_type]:
        return jsonify({'error': f'No tokens in {service_type} queue'}), 400
    
    # Get next token
    next_token = queues[service_type].pop(0)
    counter['current'] = next_token
    
    # Prepare response
    response = {
        'counter': counter_num,
        'token': next_token,
        'staff': counter['staff'],
        'message': f"Token {next_token} called to counter {counter_num}"
    }
    
    # Check if this was the current user's token
    global current_token
    if current_token == next_token:
        response['user_message'] = "Your token is being served now!"
    
    return jsonify(response)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '').strip().lower()
    
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": message
    })
    
    try:
        # First check for simple local responses
        response = check_local_response(message)
        if not response:
            # If no local response, generate AI response
            response = generate_ai_response(message)
        
        # Add bot response to history
        conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return jsonify({'response': response})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_local_response(message):
    # Simple greetings
    if any(word in message for word in ['hello', 'hi', 'hey']):
        return "Hello! I'm your Queue Assistant. How can I help you today?"
    
    # Thank you
    if any(word in message for word in ['thank', 'thanks', 'appreciate']):
        return "You're welcome! Is there anything else I can help with?"
    
    # Queue position
    if current_token and any(word in message for word in ['position', 'turn', 'wait', 'how long']):
        for service, tokens in queues.items():
            if current_token in tokens:
                position = tokens.index(current_token)
                wait_time = (position + 1) * 5
                return f"You're position {position + 1} in queue. Estimated wait: {wait_time} minutes"
        
        # Check if token is being served
        for counter_num, counter in counters.items():
            if counter['current'] == current_token:
                return f"Your token is being served at counter {counter_num}!"
        
        return "Token not found in queue. It may have been served already."
    
    return None

def generate_ai_response(message):
    # This would call your actual AI service in production
    # For demo purposes, we'll use enhanced local responses
    
    # Counter inquiries
    if 'counter' in message:
        for word in message.split():
            if word.isdigit():
                counter_num = int(word)
                if counter_num in counters:
                    counter = counters[counter_num]
                    status = " (PAUSED)" if counter['paused'] else ""
                    return f"Counter {counter_num} is serving {counter['current']} for {counter['service']}{status}. Staff: {counter['staff']}"
    
    # Service inquiries
    services = {
        'account': 'Account Services',
        'loan': 'Loan Applications',
        'card': 'Card Services',
        'general': 'General Inquiry'
    }
    
    for service, name in services.items():
        if service in message:
            count = len(queues[service])
            return f"There {'is' if count == 1 else 'are'} {count} {'person' if count == 1 else 'people'} waiting for {name}."
    
    # Jokes
    if any(word in message for word in ['joke', 'funny', 'laugh']):
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them!",
            "Why don't queues ever get angry? Because they know how to wait their turn!"
        ]
        return random.choice(jokes)
    
    # Default response
    return "I can help with queue positions, counter status, and wait times. What would you like to know?"

if __name__ == '__main__':
    app.run(debug=True, port=5000)