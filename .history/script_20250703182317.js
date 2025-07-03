document.addEventListener('DOMContentLoaded', async () => {
    // Initialize DOM elements and variables
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const newChatButton = document.getElementById('new-chat-button');
    const historyList = document.getElementById('history-list');
    const toggleSidebar = document.getElementById('toggle-sidebar');
    let currentChatId = null;
    let lastMessageCount = 0;
    let lastSentMessage = null;

    // Load NGROK_URL from config.json
    async function loadNgrokUrl() {
        try {
            const response = await fetch('/config.json', {
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const config = await response.json();
            const url = config.NGROK_URL || 'http://localhost:5001';
            console.log('✅ Loaded NGROK_URL:', url);
            return url;
        } catch (error) {
            console.error('⚠️ Error loading NGROK_URL:', error);
            return 'http://localhost:5001';
        }
    }

    const NGROK_URL = await loadNgrokUrl();

    // Check DOM elements
    if (!chatContainer || !messageInput || !sendButton || !newChatButton || !historyList || !toggleSidebar) {
        console.error('❌ Lỗi: Một hoặc nhiều phần tử DOM không tồn tại:', {
            chatContainer: !!chatContainer,
            messageInput: !!messageInput,
            sendButton: !!sendButton,
            newChatButton: !!newChatButton,
            historyList: !!historyList,
            toggleSidebar: !!toggleSidebar
        });
        alert('Lỗi: Không tìm thấy các thành phần giao diện. Vui lòng kiểm tra HTML.');
        return;
    }

    // Attach event listeners
    sendButton.addEventListener('click', () => {
        console.log('📌 Nút Gửi được nhấn');
        sendMessage();
    });
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            console.log('📌 Phím Enter được nhấn');
            e.preventDefault();
            sendMessage();
        }
    });
    newChatButton.addEventListener('click', () => {
        console.log('📌 Nút Tạo chat mới được nhấn');
        startNewChat();
    });
    toggleSidebar.addEventListener('click', toggleSidebarVisibility);

    // Load initial chat
    await loadInitialChat();

    async function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    async function checkServerStatus() {
        try {
            const response = await fetch(`${NGROK_URL}/health`, {
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });
            const text = await response.text();
            if (!response.ok || text.includes('<html') || text.includes('ngrok')) {
                console.error('❌ Server không hoạt động hoặc ngrok lỗi:', text.substring(0, 500));
                appendMessage('Lỗi: Không thể kết nối đến server. Vui lòng kiểm tra kết nối.', 'model-message');
                return false;
            }
            console.log('✅ Server hoạt động bình thường');
            return true;
        } catch (error) {
            console.error('❌ Lỗi kiểm tra server:', error);
            appendMessage('Lỗi: Không thể kết nối đến server. Vui lòng kiểm tra kết nối.', 'model-message');
            return false;
        }
    }

    async function retryFetch(url, options, maxRetries = 3, initialDelay = 2000) {
        let delay = initialDelay;
        for (let i = 0; i < maxRetries; i++) {
            try {
                const response = await fetch(url, options);
                const text = await response.text();
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                if (text.includes('<html') || text.includes('ngrok')) {
                    throw new Error('Phản hồi là HTML, có thể do ngrok hoặc server lỗi');
                }
                return { response, text };
            } catch (error) {
                if (i === maxRetries - 1) throw error;
                console.log(`⚠️ Thử lại sau ${delay / 1000} giây...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                delay *= 2;
            }
        }
    }

    function validateChatId(chatId) {
        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        return uuidRegex.test(chatId);
    }

    function showLoadingSpinner() {
        appendMessage('Đang xử lý yêu cầu...', 'model-message', false);
    }

    function hideLoadingSpinner() {
        const messages = document.querySelectorAll('.message.model-message');
        messages.forEach(msg => {
            if (msg.textContent === 'Đang xử lý yêu cầu...') {
                msg.remove();
            }
        });
    }

    async function sendMessage() {
        if (!(await checkServerStatus())) return;

        const message = messageInput.value.trim();
        if (!message || message === lastSentMessage) {
            console.log(`⏩ Bỏ qua tin nhắn trùng lặp hoặc rỗng: ${message}`);
            return;
        }

        if (!currentChatId) {
            console.log('⚠️ currentChatId rỗng, tạo chat mới');
            await startNewChat();
            if (!currentChatId) {
                console.error('❌ Không thể tạo chat mới');
                appendMessage('Lỗi: Không thể tạo hội thoại mới.', 'model-message');
                return;
            }
        }

        showLoadingSpinner();
        appendMessage(message, 'user-message');
        lastSentMessage = message;
        messageInput.value = '';

        try {
            console.log(`📤 Gửi yêu cầu tới /chatbot với chatId: ${currentChatId}, message: ${message}`);
            const { response, text } = await retryFetch(`${NGROK_URL}/chatbot`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({ message, chatId: currentChatId })
            });

            let data;
            try {
                data = JSON.parse(text);
            } catch (e) {
                throw new Error(`Invalid JSON response from /chatbot: ${text.substring(0, 500)}`);
            }

            if (data.error) {
                console.error('❌ Lỗi từ server:', data.error);
                appendMessage(data.error, 'model-message');
            } else {
                appendMessage(data.reply, 'model-message');
                console.log(`✅ Nhận phản hồi từ /chatbot: ${data.reply}`);
                await checkAndPollChat(currentChatId);
            }
        } catch (error) {
            console.error('❌ Lỗi trong khi gọi API /chatbot:', error);
            appendMessage(`Có lỗi xảy ra: ${error.message}`, 'model-message');
        } finally {
            hideLoadingSpinner();
        }
    }

    async function pollForKaggleResponse(chatId) {
        if (!validateChatId(chatId)) {
            console.error('❌ chatId không hợp lệ:', chatId);
            appendMessage('Lỗi: chatId không hợp lệ.', 'model-message');
            return;
        }

        let attempts = 0;
        const maxAttempts = 150;
        const pollInterval = 5000;

        while (attempts < maxAttempts) {
            try {
                console.log(`📥 Thăm dò /chat/${chatId}, lần ${attempts + 1}/${maxAttempts}`);
                const { response, text } = await retryFetch(`${NGROK_URL}/chat/${chatId}`, {
                    headers: {
                        'Content-Type': 'application/json',
                        'ngrok-skip-browser-warning': 'true'
                    }
                });

                let chat;
                try {
                    if (!text.trim()) {
                        console.log('⚠️ Phản hồi rỗng, thử lại...');
                        appendMessage('Lỗi: Phản hồi từ server rỗng, thử lại sau 5 giây', 'model-message');
                        await new Promise(resolve => setTimeout(resolve, 5000));
                        continue;
                    }
                    chat = JSON.parse(text);
                } catch (e) {
                    throw new Error(`Invalid JSON response from /chat: ${text.substring(0, 500)}`);
                }

                const messages = chat.messages || [];
                if (messages.length > lastMessageCount) {
                    const newMessages = messages.slice(lastMessageCount);
                    newMessages.forEach(msg => {
                        if (msg.className === 'model-message' && msg.text !== 'Đang chờ phản hồi từ Kaggle...') {
                            appendMessage(msg.text, 'model-message');
                            console.log('✅ Nhận câu trả lời từ LLM:', msg.text);
                        }
                    });
                    lastMessageCount = messages.length;
                    return;
                }
                console.log(`⏳ Chưa nhận được câu trả lời mới`);
            } catch (error) {
                console.error('❌ Lỗi khi thăm dò /chat:', error);
                appendMessage(`Lỗi khi thăm dò: ${error.message}`, 'model-message');
            }
            attempts++;
            await new Promise(resolve => setTimeout(resolve, pollInterval));
        }
        appendMessage('Lỗi: Không nhận được câu trả lời từ mô hình sau thời gian chờ', 'model-message');
        console.error('❌ Hết thời gian thăm dò, không nhận được câu trả lời');
    }

    async function loadChat(chatId) {
        if (!validateChatId(chatId)) {
            console.error('❌ chatId không hợp lệ:', chatId);
            appendMessage('Lỗi: chatId không hợp lệ.', 'model-message');
            return;
        }

        if (!(await checkServerStatus())) return;

        currentChatId = chatId;
        chatContainer.innerHTML = '';
        appendMessage('Đang tải lịch sử trò chuyện...', 'model-message', false);

        try {
            console.log(`📤 Gửi yêu cầu tới /chat/${chatId}`);
            const { response, text } = await retryFetch(`${NGROK_URL}/chat/${chatId}`, {
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                }
            });

            let chat;
            try {
                chat = JSON.parse(text);
            } catch (e) {
                throw new Error(`Invalid JSON response from /chat: ${text.substring(0, 500)}`);
            }

            lastMessageCount = chat.messages ? chat.messages.length : 0;
            console.log('✅ Đã tải tin nhắn cho chat:', chatId, chat.messages);
            chat.messages.forEach(msg => appendMessage(msg.text, msg.className, false));
            updateHistoryList();
        } catch (error) {
            console.error('❌ Lỗi khi tải tin nhắn từ server:', error);
            appendMessage(`Lỗi khi tải lịch sử chat: ${error.message}`, 'model-message');
        }
    }

    async function checkAndPollChat(chatId) {
        if (!validateChatId(chatId)) {
            console.error('❌ chatId không hợp lệ:', chatId);
            appendMessage('Lỗi: chatId không hợp lệ.', 'model-message');
            return;
        }

        try {
            console.log(`📤 Gửi yêu cầu tới /chat/${chatId}`);
            const { response, text } = await retryFetch(`${NGROK_URL}/chat/${chatId}`, {
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                }
            });

            let chatData;
            try {
                chatData = JSON.parse(text);
            } catch (e) {
                throw new Error(`Invalid JSON response from /chat: ${text.substring(0, 500)}`);
            }
            lastMessageCount = chatData.messages ? chatData.messages.length : 0;
            console.log(`✅ Current chatId: ${chatId}, Messages:`, chatData.messages);
            pollForKaggleResponse(chatId);
        } catch (error) {
            console.error('❌ Lỗi khi kiểm tra chat:', error);
            appendMessage(`Lỗi khi kiểm tra chat: ${error.message}`, 'model-message');
        }
    }

    function appendMessage(text, className, save = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
        
        // Thay \n bằng <br> để hiển thị xuống dòng trong HTML
        messageDiv.innerHTML = text.replace(/\n/g, '<br>');

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        if (save) {
            const chats = JSON.parse(localStorage.getItem('chats')) || {};
            if (!chats[currentChatId]) {
                chats[currentChatId] = { messages: [], title: `Chat ${Object.keys(chats).length + 1}` };
            }
            chats[currentChatId].messages.push({ text, className });
            localStorage.setItem('chats', JSON.stringify(chats));
            updateHistoryList();
        }
    }

    async function startNewChat() {
        try {
            console.log('📤 Gửi yêu cầu tới /chat/new');
            const response = await fetch(`${NGROK_URL}/chat/new`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                }
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const data = await response.json();
            currentChatId = data.chatId;
            chatContainer.innerHTML = '';
            lastMessageCount = 0;
            lastSentMessage = null;
            const chats = JSON.parse(localStorage.getItem('chats')) || {};
            chats[currentChatId] = { messages: [], title: `Chat ${Object.keys(chats).length + 1}` };
            localStorage.setItem('chats', JSON.stringify(chats));
            updateHistoryList();
            console.log(`✅ Tạo chat mới với chatId: ${currentChatId}`);
        } catch (error) {
            console.error('❌ Lỗi khi tạo chat mới:', error);
            appendMessage('Lỗi: Không thể tạo hội thoại mới.', 'model-message');
        }
    }

    async function deleteChat(chatId) {
        try {
            console.log(`📤 Gửi yêu cầu tới /chat/delete với chatId: ${chatId}`);
            await fetch(`${NGROK_URL}/chat/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify({ chatId })
            });
            const chats = JSON.parse(localStorage.getItem('chats')) || {};
            if (chats[chatId]) {
                delete chats[chatId];
                localStorage.setItem('chats', JSON.stringify(chats));
                if (chatId === currentChatId) {
                    await startNewChat();
                }
                updateHistoryList();
            }
        } catch (error) {
            console.error('❌ Lỗi khi xóa chat:', error);
            appendMessage('Lỗi: Không thể xóa hội thoại.', 'model-message');
        }
    }

    function updateHistoryList() {
        historyList.innerHTML = '';
        const chats = JSON.parse(localStorage.getItem('chats')) || {};
        if (Object.keys(chats).length === 0) {
            startNewChat(); // Ensure at least one chat exists
            return;
        }
        Object.keys(chats).forEach(chatId => {
            const historyItem = document.createElement('div');
            historyItem.className = `history-item ${chatId === currentChatId ? 'active' : ''}`;
            
            const titleSpan = document.createElement('span');
            titleSpan.textContent = chats[chatId].title;
            titleSpan.style.flex = '1';
            
            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Xóa';
            deleteButton.className = 'delete-button';
            deleteButton.addEventListener('click', (e) => {
                e.stopPropagation();
                console.log('📌 Nút Xóa được nhấn cho chatId:', chatId);
                deleteChat(chatId);
            });

            historyItem.appendChild(titleSpan);
            historyItem.appendChild(deleteButton);
            historyItem.addEventListener('click', () => {
                console.log('📌 Chọn lịch sử chat:', chatId);
                loadChat(chatId);
            });
            historyList.appendChild(historyItem);
        });
    }

    function toggleSidebarVisibility() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.toggle('open');
            toggleSidebar.textContent = sidebar.classList.contains('open') ? 'Ẩn' : 'Hiện';
            console.log('📌 Chuyển đổi sidebar:', sidebar.classList.contains('open') ? 'Mở' : 'Đóng');
        } else {
            console.error('❌ Sidebar element not found');
        }
    }

    async function loadInitialChat() {
        try {
            const response = await fetch(`${NGROK_URL}/chats`, {
                headers: { 'ngrok-skip-browser-warning': 'true' }
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const chats = await response.json();
            const localChats = JSON.parse(localStorage.getItem('chats')) || {};
            if (chats.length === 0 && Object.keys(localChats).length === 0) {
                console.log('⚠️ No chats found, creating a new chat');
                await startNewChat();
            } else {
                currentChatId = chats[0]?.chatId || Object.keys(localChats)[0];
                if (currentChatId) {
                    await loadChat(currentChatId);
                } else {
                    await startNewChat();
                }
            }
        } catch (error) {
            console.error('❌ Error loading initial chats:', error);
            appendMessage('Lỗi: Không thể tải danh sách hội thoại.', 'model-message');
            await startNewChat();
        }
    }
});