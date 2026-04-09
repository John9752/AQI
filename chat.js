(function() {
    // ==========================================
    // CHAT CONFIGURATION
    // ==========================================
    const BACKEND_ORIGINS = ['http://127.0.0.1:5000', 'http://localhost:5000'];
    const base_url = BACKEND_ORIGINS.includes(window.location.origin)
        ? '' // Same origin
        : 'http://127.0.0.1:5000'; // External origin

    const floatingChatBtn = document.getElementById('floatingChatBtn');
    const chatWidget = document.getElementById('chatWidget');
    const closeChatBtn = document.getElementById('closeChatBtn');
    const chatInput = document.getElementById('chatInput');
    const sendChatBtn = document.getElementById('sendChatBtn');
    const chatBody = document.getElementById('chatBody');

    let isChatOpen = false;

    // ==========================================
    // TOGGLE CHAT WIDGET
    // ==========================================
    if (floatingChatBtn && closeChatBtn && chatWidget) {
        floatingChatBtn.addEventListener('click', () => {
            isChatOpen = !isChatOpen;
            chatWidget.classList.toggle('active');
        });

        closeChatBtn.addEventListener('click', () => {
            isChatOpen = false;
            chatWidget.classList.remove('active');
        });
    }

    // ==========================================
    // HANDLING MESSAGES
    // ==========================================
    function appendMessage(text, sender) {
        if (!chatBody) return;
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        if (sender === 'user') messageDiv.classList.add('user-message');
        else messageDiv.classList.add('ai-message');
        
        // Support basic markup/formatting
        const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
        messageDiv.innerHTML = formattedText;
        chatBody.appendChild(messageDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    function showTypingIndicator() {
        if (!chatBody) return;
        const indicator = document.createElement('div');
        indicator.classList.add('typing-indicator');
        indicator.id = 'typingIndicator';
        indicator.innerText = 'AI is thinking...';
        chatBody.appendChild(indicator);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    }

    async function handleSendMessage() {
        if (!chatInput) return;
        const text = chatInput.value.trim();
        if (!text) return;

        appendMessage(text, 'user');
        chatInput.value = '';

        showTypingIndicator();

        try {
            const appContext = window.appContext || {};
            const response = await fetch(`${base_url}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: text,
                    context: {
                        city: appContext.city,
                        aqi: appContext.aqiSimulated,
                        status: appContext.status
                    }
                })
            });

            const data = await response.json();

            removeTypingIndicator();

            if (response.ok && data.response) {
                appendMessage(data.response, 'ai');
            } else {
                appendMessage(`⚠️ Error: ${data.error || 'Failed to get response from AI.'}`, 'ai');
            }
        } catch (e) {
            removeTypingIndicator();
            console.error("Chat error:", e);
            appendMessage('⚠️ Connection Error: Failed to reach the backend server.', 'ai');
        }
    }

    if (sendChatBtn) sendChatBtn.addEventListener('click', handleSendMessage);
    if (chatInput) chatInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSendMessage(); });

})();
