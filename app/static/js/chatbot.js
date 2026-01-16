document.addEventListener('DOMContentLoaded', () => {
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatWindow = document.getElementById('chat-window');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-message');
    const attachBtn = document.getElementById('attach-media');
    const fileInput = document.getElementById('file-input');

    // Controls
    const btnMin = document.getElementById('chat-min');
    const btnMax = document.getElementById('chat-max');
    const btnClose = document.getElementById('chat-close');
    const langSelect = document.getElementById('chat-lang');

    let isChatOpen = false;
    let selectedFile = null;

    // Trending Questions
    const trendingQuestions = [
        "Which state has the most enrollment?",
        "Analyze biometric update trends.",
        "Identify districts with low child enrollment.",
        "Show pincodes with high demographic updates.",
        "What are the key insights for disaster planning?"
    ];

    function renderTrending() {
        const id = 'trending-chips';
        if (document.getElementById(id)) return;

        const container = document.createElement('div');
        container.id = id;
        container.className = 'trending-container';
        container.innerHTML = `<div style="width:100%; font-size:12px; color:#666; margin-bottom:5px;">Trending Questions:</div>`;

        trendingQuestions.forEach(q => {
            const chip = document.createElement('div');
            chip.className = 'trending-chip';
            chip.innerText = q;
            chip.onclick = () => {
                chatInput.value = q;
                handleSend();
            };
            container.appendChild(chip);
        });

        // Add as a 'system' message or just append to top? 
        // Better to append to messages list as an initial view.
        // We only show it if chat is empty or on first open.
        if (chatMessages.children.length <= 1) { // 1 because of greeting
            chatMessages.appendChild(container);
        }
    }

    // Toggle Chat Window
    chatbotToggle.addEventListener('click', () => {
        isChatOpen = !isChatOpen;
        chatWindow.style.display = isChatOpen ? 'flex' : 'none';
        chatbotToggle.classList.toggle('active', isChatOpen);
        if (isChatOpen) {
            chatInput.focus();
            renderTrending();
        }
    });

    // Window Controls
    if (btnMin) btnMin.addEventListener('click', () => {
        isChatOpen = false;
        chatWindow.style.display = 'none';
        chatbotToggle.classList.remove('active');
    });

    if (btnClose) btnClose.addEventListener('click', () => {
        isChatOpen = false;
        chatWindow.style.display = 'none';
        chatbotToggle.classList.remove('active');
        // Optional: clear chat?
    });

    if (btnMax) btnMax.addEventListener('click', () => {
        chatWindow.classList.toggle('maximized');
        const icon = btnMax.querySelector('i');
        if (chatWindow.classList.contains('maximized')) {
            icon.classList.remove('fa-expand');
            icon.classList.add('fa-compress');
        } else {
            icon.classList.remove('fa-compress');
            icon.classList.add('fa-expand');
        }
    });

    // Handle File Attachment
    attachBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        selectedFile = e.target.files[0];
        if (selectedFile) {
            addMessage(`Selected image: ${selectedFile.name}`, 'user', null, true);
        }
    });

    // Send Message
    const handleSend = async () => {
        const text = chatInput.value.trim();
        if (!text && !selectedFile) return;

        // Remove trending if present to clean up view
        const trending = document.getElementById('trending-chips');
        if (trending) trending.remove();

        // Add user message
        addMessage(text, 'user');
        chatInput.value = '';

        // Add loading state
        const loadingId = addLoading();

        try {
            const formData = new FormData();
            formData.append('message', text);
            formData.append('language', langSelect.value); // Pass Language
            if (selectedFile) {
                formData.append('image', selectedFile);
            }

            const response = await fetch('/api/chat', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            removeLoading(loadingId);

            if (data.response) {
                addMessage(data.response, 'bot');
            } else {
                addMessage('Something went wrong. Please try again.', 'bot');
            }
        } catch (error) {
            removeLoading(loadingId);
            addMessage('Error connecting to the server.', 'bot');
        }

        selectedFile = null;
        fileInput.value = '';
    };

    sendBtn.addEventListener('click', handleSend);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });

    function addMessage(text, sender, imageSrc = null, system = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender} ${system ? 'system' : ''}`;

        let content = '';
        if (text) content += `<div class="text">${formatMarkdown(text)}</div>`;
        if (imageSrc) content += `<img src="${imageSrc}" class="image-preview" />`;

        if (sender === 'bot') {
            content += `<span class="copy-btn" title="Copy to clipboard">📋</span>`;
            // Add Animated Avatar
            content += `
             <div class="avatar">
                 <div class="ai-avatar-container" style="width: 24px; height: 24px; margin: 0;">
                     <div class="ai-ring" style="width: 14px; height: 14px; border-width: 1px;"></div>
                     <div class="ai-ring" style="width: 20px; height: 20px; border-width: 1px; animation-delay: 0.4s;"></div>
                     <div class="ai-core" style="width: 6px; height: 6px;"></div>
                 </div>
             </div>`;
        }

        messageDiv.innerHTML = content;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Add copy listener
        if (sender === 'bot') {
            const copyBtn = messageDiv.querySelector('.copy-btn');
            copyBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(text);
                copyBtn.innerText = '✅';
                setTimeout(() => copyBtn.innerText = '📋', 2000);
            });
        }
    }

    function addLoading() {
        const id = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = id;
        loadingDiv.className = 'message bot loading';
        loadingDiv.innerHTML = `
            <div class="loading-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeLoading(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function formatMarkdown(text) {
        // Simple markdown formatter
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }
});
