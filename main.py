from flask import Flask, render_template_string, request, jsonify, session, Response
import requests
import json
import uuid
import os
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'

# إعدادات NVIDIA API
NVIDIA_API_KEY = "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"
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_NAME = "qwen/qwen3.5-397b-a17b"

# تخزين المحادثات والتدفقات النشطة
conversations = {}
active_streams = {}

def generate_professional_response(messages, stream_id):
    """توليد ردود احترافية مع تسريع الأداء"""
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    
    system_prompt = {
        "role": "system",
        "content": """أنت Abdo AI Pro - خبير محترف.
أجب بشكل مباشر واحترافي بدون مقدمات."""
    }
    
    # استخدام آخر 5 رسائل فقط للسرعة
    full_messages = [system_prompt] + messages[-5:]
    
    payload = {
        "model": MODEL_NAME,
        "messages": full_messages,
        "max_tokens": 2048,  # تقليل عدد التوكنز للسرعة
        "temperature": 0.60,
        "top_p": 0.95,
        "top_k": 20,
        "presence_penalty": 0,
        "repetition_penalty": 1,
        "stream": True
    }
    
    try:
        response = requests.post(
            NVIDIA_API_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=60  # زيادة المهلة
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if stream_id in active_streams and active_streams[stream_id].get('stopped', False):
                    break
                    
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data = line_text[6:]
                        if data and data != '[DONE]':
                            try:
                                json_data = json.loads(data)
                                if 'choices' in json_data:
                                    delta = json_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield delta['content']
                            except:
                                continue
        else:
            yield f"⚠️ خطأ {response.status_code}"
            
    except Exception as e:
        yield f"⚠️ خطأ: {str(e)}"

@app.route('/')
def index():
    """الصفحة الرئيسية - نسخة مبسطة وسريعة"""
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
        conversations[session['conversation_id']] = []
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abdo AI Pro</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Cairo', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .chat-container {
            width: 100%;
            max-width: 1000px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }

        .chat-header h1 {
            font-size: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }

        .message {
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
        }

        .message.user {
            align-items: flex-end;
        }

        .message.assistant {
            align-items: flex-start;
        }

        .message-content {
            max-width: 80%;
            padding: 15px;
            border-radius: 15px;
            position: relative;
            word-wrap: break-word;
        }

        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-left-radius: 5px;
        }

        .message.assistant .message-content {
            background: white;
            border: 1px solid #e9ecef;
            border-bottom-right-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .message-time {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
            margin-right: 10px;
        }

        .chat-input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e9ecef;
        }

        .input-wrapper {
            display: flex;
            gap: 10px;
        }

        textarea {
            flex: 1;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            font-size: 16px;
            resize: none;
            font-family: 'Cairo', sans-serif;
            transition: border-color 0.2s;
        }

        textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0 30px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }

        button:hover:not(:disabled) {
            transform: scale(1.02);
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .stop-btn {
            background: #dc3545;
        }

        .thinking {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 15px;
            background: white;
            border-radius: 15px;
            border: 1px solid #e9ecef;
        }

        .thinking-dots {
            display: flex;
            gap: 5px;
        }

        .thinking-dots span {
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            animation: thinking 1.2s infinite;
        }

        .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
        .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes thinking {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }

        .message pre {
            background: #f4f4f4;
            padding: 10px;
            border-radius: 8px;
            overflow-x: auto;
            direction: ltr;
        }

        .message code {
            font-family: 'Courier New', monospace;
        }

        .message table {
            border-collapse: collapse;
            width: 100%;
            margin: 10px 0;
        }

        .message th, .message td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: right;
        }

        .message th {
            background: #667eea20;
        }

        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #ffcdd2;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>
                <i class="fas fa-robot"></i>
                Abdo AI Pro - الخبير المحترف
            </h1>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message assistant">
                <div class="message-content">
                    👋 مرحباً! أنا خبير Abdo AI Pro. كيف يمكنني مساعدتك اليوم؟
                </div>
                <div class="message-time">{{ now.strftime('%H:%M') }}</div>
            </div>
        </div>
        
        <div class="chat-input-container">
            <div class="input-wrapper">
                <textarea 
                    id="messageInput" 
                    placeholder="اكتب سؤالك هنا..."
                    rows="2"
                    oninput="autoResize(this)"
                ></textarea>
                <button id="sendBtn" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
                <button id="stopBtn" class="stop-btn" onclick="stopGeneration()" style="display: none;">
                    <i class="fas fa-stop"></i>
                </button>
            </div>
            <div style="text-align: left; margin-top: 5px; color: #666; font-size: 12px;">
                <i class="fas fa-keyboard"></i> Enter للإرسال • Ctrl+Enter سطر جديد
            </div>
        </div>
    </div>

    <script>
        let currentConversationId = '{{ session.conversation_id }}';
        let isProcessing = false;
        let currentStreamId = null;
        let eventSource = null;

        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
        }

        function scrollToBottom() {
            const container = document.getElementById('chatMessages');
            container.scrollTop = container.scrollHeight;
        }

        function formatMessage(content) {
            // تحويل بسيط للنص
            let formatted = content
                .replace(/## (.*?)(?:\n|$)/g, '<h3>$1</h3>')
                .replace(/### (.*?)(?:\n|$)/g, '<h4>$1</h4>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>')
                .replace(/`(.*?)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
            return formatted;
        }

        function addMessage(role, content, isThinking = false) {
            const container = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            const time = new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' });
            
            if (isThinking) {
                messageDiv.innerHTML = `
                    <div class="message-content">
                        <div class="thinking">
                            <div class="thinking-dots">
                                <span></span><span></span><span></span>
                            </div>
                            <span>جاري التفكير...</span>
                        </div>
                    </div>
                    <div class="message-time">${time}</div>
                `;
            } else {
                messageDiv.innerHTML = `
                    <div class="message-content">${formatMessage(content)}</div>
                    <div class="message-time">${time}</div>
                `;
            }
            
            container.appendChild(messageDiv);
            scrollToBottom();
            return messageDiv;
        }

        function showError(message) {
            const container = document.getElementById('chatMessages');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                ${message}
            `;
            container.appendChild(errorDiv);
            scrollToBottom();
            
            // إخفاء الخطأ بعد 5 ثواني
            setTimeout(() => errorDiv.remove(), 5000);
        }

        function sendMessage() {
            if (isProcessing) return;
            
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // إضافة رسالة المستخدم
            addMessage('user', message);
            input.value = '';
            autoResize(input);
            
            // إضافة مؤشر التفكير
            addMessage('assistant', '', true);
            
            isProcessing = true;
            document.getElementById('sendBtn').disabled = true;
            document.getElementById('stopBtn').style.display = 'block';
            
            currentStreamId = Date.now() + '-' + Math.random();
            
            // إلغاء أي اتصال سابق
            if (eventSource) {
                eventSource.close();
            }
            
            // بدء الاتصال الجديد
            eventSource = new EventSource(`/api/chat/stream?message=${encodeURIComponent(message)}&stream_id=${currentStreamId}`);
            let fullResponse = '';
            let assistantMessage = null;
            
            // مؤقت للتحقق من الاستجابة
            const timeoutTimer = setTimeout(() => {
                if (isProcessing && !fullResponse) {
                    eventSource.close();
                    isProcessing = false;
                    document.getElementById('sendBtn').disabled = false;
                    document.getElementById('stopBtn').style.display = 'none';
                    
                    // إزالة مؤشر التفكير
                    const thinkingMsg = document.querySelector('.message.assistant:last-child');
                    if (thinkingMsg && thinkingMsg.querySelector('.thinking')) {
                        thinkingMsg.remove();
                    }
                    
                    showError('⚠️ لم يتم استلام رد من الخادم. يرجى المحاولة مرة أخرى.');
                }
            }, 30000); // 30 ثانية مهلة
            
            eventSource.onmessage = function(e) {
                clearTimeout(timeoutTimer);
                
                try {
                    const data = JSON.parse(e.data);
                    
                    if (data.chunk) {
                        // إزالة مؤشر التفكير
                        const thinkingMsg = document.querySelector('.message.assistant:last-child');
                        if (thinkingMsg && thinkingMsg.querySelector('.thinking')) {
                            thinkingMsg.remove();
                            assistantMessage = null;
                        }
                        
                        if (!assistantMessage) {
                            assistantMessage = addMessage('assistant', '');
                        }
                        
                        fullResponse += data.chunk;
                        
                        const contentDiv = assistantMessage.querySelector('.message-content');
                        if (contentDiv) {
                            contentDiv.innerHTML = formatMessage(fullResponse);
                        }
                        
                        scrollToBottom();
                    }
                    
                    if (data.done) {
                        eventSource.close();
                        isProcessing = false;
                        document.getElementById('sendBtn').disabled = false;
                        document.getElementById('stopBtn').style.display = 'none';
                    }
                    
                } catch (error) {
                    console.error('خطأ في معالجة البيانات:', error);
                }
            };
            
            eventSource.onerror = function() {
                clearTimeout(timeoutTimer);
                eventSource.close();
                
                if (isProcessing) {
                    isProcessing = false;
                    document.getElementById('sendBtn').disabled = false;
                    document.getElementById('stopBtn').style.display = 'none';
                    
                    // إزالة مؤشر التفكير
                    const thinkingMsg = document.querySelector('.message.assistant:last-child');
                    if (thinkingMsg && thinkingMsg.querySelector('.thinking')) {
                        thinkingMsg.remove();
                    }
                    
                    if (!fullResponse) {
                        showError('⚠️ عذراً، حدث خطأ في الاتصال. يرجى المحاولة مرة أخرى.');
                    }
                }
            };
        }

        function stopGeneration() {
            if (currentStreamId) {
                fetch('/api/chat/stop', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ stream_id: currentStreamId })
                }).then(() => {
                    if (eventSource) {
                        eventSource.close();
                    }
                    
                    isProcessing = false;
                    document.getElementById('sendBtn').disabled = false;
                    document.getElementById('stopBtn').style.display = 'none';
                    
                    // إزالة مؤشر التفكير
                    const thinkingMsg = document.querySelector('.message.assistant:last-child');
                    if (thinkingMsg && thinkingMsg.querySelector('.thinking')) {
                        thinkingMsg.remove();
                    }
                });
            }
        }

        // دعم الإرسال بالضغط على Enter
        document.getElementById('messageInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.ctrlKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // تحميل المحادثة السابقة
        window.onload = function() {
            fetch(`/api/conversation/${currentConversationId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.messages && data.messages.length > 0) {
                        const container = document.getElementById('chatMessages');
                        container.innerHTML = '';
                        
                        data.messages.forEach(msg => {
                            addMessage(msg.role, msg.content);
                        });
                    }
                });
        };
    </script>
</body>
</html>
    ''', now=datetime.now())

@app.route('/api/chat/stream')
def chat_stream():
    """نقطة نهاية التدفق"""
    message = request.args.get('message', '').strip()
    conversation_id = session.get('conversation_id')
    stream_id = request.args.get('stream_id', str(uuid.uuid4()))
    
    if not message:
        return jsonify({'error': 'الرجاء إدخال رسالة'}), 400
    
    active_streams[stream_id] = {'stopped': False}
    
    def generate():
        try:
            # حفظ رسالة المستخدم
            user_message = {
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            }
            
            if conversation_id not in conversations:
                conversations[conversation_id] = []
            
            conversations[conversation_id].append(user_message)
            
            # تجهيز الرسائل للـ API
            messages_for_api = []
            for msg in conversations[conversation_id][-10:]:  # آخر 10 رسائل فقط
                messages_for_api.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            full_response = ""
            
            # توليد الرد
            for chunk in generate_professional_response(messages_for_api, stream_id):
                if stream_id in active_streams and active_streams[stream_id].get('stopped', False):
                    break
                
                if chunk:
                    full_response += chunk
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            # حفظ الرد الكامل
            if full_response and not active_streams.get(stream_id, {}).get('stopped', False):
                assistant_message = {
                    'role': 'assistant',
                    'content': full_response,
                    'timestamp': datetime.now().isoformat()
                }
                conversations[conversation_id].append(assistant_message)
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if stream_id in active_streams:
                del active_streams[stream_id]
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

@app.route('/api/chat/stop', methods=['POST'])
def stop_chat():
    """إيقاف التوليد"""
    data = request.json
    stream_id = data.get('stream_id')
    
    if stream_id in active_streams:
        active_streams[stream_id]['stopped'] = True
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 404

@app.route('/api/conversation/<conversation_id>')
def get_conversation(conversation_id):
    """استرجاع المحادثة"""
    if conversation_id in conversations:
        return jsonify({'messages': conversations[conversation_id]})
    return jsonify({'messages': []})

if __name__ == '__main__':
    print("="*60)
    print("🚀 Abdo AI Pro - الخبير المحترف")
    print("="*60)
    print("✅ تم التبسيط والتسريع")
    print("✅ مهلة 30 ثانية للاستجابة")
    print("="*60)
    print("🌐 http://localhost:5000")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
