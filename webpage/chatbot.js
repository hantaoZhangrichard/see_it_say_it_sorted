// ============================================================================
// Chatbot Functions
// ============================================================================


function sendChat() {
  const box = document.getElementById('chatbot-box');
  const input = document.getElementById('chatbot-input');
  const text = input.value.trim();
  const imageInput = document.getElementById('chatbot-image-input');
  console.log("Sending chat with text:", text);
  console.log("Image input files:", imageInput.files);

  let jsonText = '';
  let jsonDict = {};
  jsonText = document.getElementById('json-code').value;
  jsonDict = JSON.parse(jsonText);
  if (!text && (!imageInput.files || imageInput.files.length === 0)) return;

  const userBubble = document.createElement('div');
  userBubble.className = 'chat-bubble-user';
  userBubble.textContent = text;
  box.appendChild(userBubble);

  const botBubble = document.createElement('div');
  botBubble.className = 'chat-bubble-bot';
  botBubble.textContent = '…thinking';
  box.appendChild(botBubble);

  box.scrollTop = box.scrollHeight;
  input.value = "";

  // Send message and/or image to backend
  if (imageInput.files && imageInput.files.length > 0) {
    const file = imageInput.files[0];
    const formData = new FormData();
    formData.append('message', text);
    formData.append('svg_json', JSON.stringify(jsonDict));
    formData.append('image', file);
    fetch('http://localhost:8080/agent', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(async data => {
      if (data.reply) {
        botBubble.textContent = data.reply;
        if (data.shapes) {
          try {
            jsonDict = data.shapes;
            jsonText = JSON.stringify(jsonDict, null, 2);
            document.getElementById('json-code').value = jsonText;
            drawings = jsonDictToDrawings(jsonDict);
            redraw();
            selectedIndex = -1;
            tempShape = null;
            currentPath = null;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            redraw();
            await updateSVGPreview(jsonDict);
          } catch (error) {
            console.error('Error updating JSON:', error);
          }
        }
      } else if (data.error) {
        botBubble.textContent = 'Error: ' + data.error;
      }
      box.scrollTop = box.scrollHeight;
    })
    .catch(error => {
      botBubble.textContent = 'Connection error';
      console.error('Error:', error);
    });
    imageInput.value = "";
  } else {
    // Send text-only message to backend
    fetch('http://localhost:8080/agent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: text,
        svg_json: jsonDict})
    })
    .then(response => response.json())
    .then(async data => {
      if (data.reply) {
        botBubble.textContent = data.reply;
        if (data.shapes) {
          try {
            jsonDict = data.shapes;
            jsonText = JSON.stringify(jsonDict, null, 2);
            document.getElementById('json-code').value = jsonText;
            drawings = jsonDictToDrawings(jsonDict);
            redraw();
            selectedIndex = -1;
            tempShape = null;
            currentPath = null;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            redraw();
            await updateSVGPreview(jsonDict);
          } catch (error) {
            console.error('Error updating JSON:', error);
          }
        }
      } else if (data.error) {
        botBubble.textContent = 'Error: ' + data.error;
      }
      box.scrollTop = box.scrollHeight;
    })
    .catch(error => {
      botBubble.textContent = 'Connection error';
      console.error('Error:', error);
    });
  }
}

function setupChatbot() {
  const panel = document.querySelector('.chatbot-panel');
  const content = document.getElementById('chatbot-content');

  if (panel) {
    panel.style.display = 'flex';
    panel.style.position = '';
    panel.style.right = '';
    panel.style.bottom = '';
    panel.style.width = '';
    panel.style.zIndex = '';
    panel.style.cursor = 'default';
    panel.onmousedown = null;
  }
  if (content) {
    content.style.display = 'flex';
  }

  const input = document.getElementById('chatbot-input');
  if (input) {
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendChat();
      }
    });
  }
}

setupChatbot();


document.getElementById('chatbot-image-input').addEventListener('change', function(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(e) {
    const imgUrl = e.target.result;

    const box = document.getElementById('chatbot-box');
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble-user';
    
    const img = document.createElement('img');
    img.src = imgUrl;
    img.style.maxWidth = '150px';
    img.style.borderRadius = '8px';
    img.style.display = 'block';

    userBubble.appendChild(img);
    box.appendChild(userBubble);
    box.scrollTop = box.scrollHeight;
  };

  reader.readAsDataURL(file);

  // event.target.value = "";
});

