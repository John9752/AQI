// ==========================================
// GEMINI API CONFIGURATION
// ==========================================
const GEMINI_API_KEY = "AIzaSyDeUsCJVDdDVJxJjaIXzVhmD-802FxRmmA";

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
    const text = chatInput.value.trim();
    if (!text) return;

    appendMessage(text, 'user');
    chatInput.value = '';

    if (!GEMINI_API_KEY || GEMINI_API_KEY === "YOUR_GEMINI_API_KEY") {
        appendMessage('⚠️ Error: Please insert a valid key.', 'ai');
        return;
    }

    showTypingIndicator();

    // UPDATED: Using models that are confirmed available on your specific API Key
    const attempts = [
        { v: 'v1beta', m: 'gemini-2.0-flash' },
        { v: 'v1beta', m: 'gemini-flash-latest' },
        { v: 'v1beta', m: 'gemini-3-flash-preview' }
    ];

    let fullErrorLog = "";

    for (const attempt of attempts) {
        try {
            const context = window.appContext;
            let systemContext = `You are an expert AI Health Assistant. Concise answers (3 sentences). `;
            if (context && context.city) {
                systemContext += `City: ${context.city}, AQI: ${context.aqiSimulated} (${context.status}). Advice based on this.`;
            } else {
                systemContext += `Give general air quality advice.`;
            }

            const prompt = `${systemContext}\n\nUser Question: ${text}`;
            const url = `https://generativelanguage.googleapis.com/${attempt.v}/models/${attempt.m}:generateContent?key=${GEMINI_API_KEY}`;
            
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
            });

            const data = await response.json();

            if (response.status === 200 && data.candidates && data.candidates.length > 0) {
                removeTypingIndicator();
                appendMessage(data.candidates[0].content.parts[0].text, 'ai');
                return;
            } else {
                fullErrorLog += `[${attempt.m}]: ${data.error ? data.error.message : "Error"}\n`;
            }
        } catch (e) {
            fullErrorLog += `[${attempt.m}]: Fetch error\n`;
        }
    }

    removeTypingIndicator();
    appendMessage(`⚠️ <strong>Connection Error</strong><br><pre style="font-size:10px; background:rgba(0,0,0,0.5); padding:10px; white-space:pre-wrap;">${fullErrorLog}</pre>`, 'ai');
}

if (sendChatBtn) sendChatBtn.addEventListener('click', handleSendMessage);
if (chatInput) chatInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSendMessage(); });
