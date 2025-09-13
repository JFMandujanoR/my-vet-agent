const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');

function appendMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = `bubble ${sender}`;
    bubbleDiv.textContent = text;
    messageDiv.appendChild(bubbleDiv);
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = userInput.value.trim();
    if (!question) return;
    appendMessage(question, 'user');
    userInput.value = '';
    appendMessage('Thinking...', 'agent');
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: question })
        });
        const data = await response.json();
        // Remove the 'Thinking...' message
        chatWindow.removeChild(chatWindow.lastChild);
        appendMessage(data.reply, 'agent');
    } catch (err) {
        chatWindow.removeChild(chatWindow.lastChild);
        appendMessage('Sorry, there was an error. Please try again.', 'agent');
    }
});
