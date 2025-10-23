(function () {
  const roomName = window.CHAT_ROOM_NAME;
  const chatLog = document.querySelector("#chat-log");
  const input = document.querySelector("#chat-message-input");
  const button = document.querySelector("#chat-message-submit");
  const usernameInput = document.querySelector("#username");

  // Build WebSocket URL (ws or wss depending on the page protocol)
  const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
  const endpoint = `${wsProtocol}://${window.location.host}/ws/chat/${roomName}/`;
  const socket = new WebSocket(endpoint);

  socket.onopen = function (e) {
    appendLog("Connected.");
  };

  socket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    const user = data.username || "anonymous";
    appendLog(`${user}: ${data.message}`);
  };

  socket.onclose = function (e) {
    appendLog("Disconnected.");
  };

  button.onclick = function (e) {
    sendMessage();
  };

  input.addEventListener("keypress", function (e) {
    if (e.key === "Enter") sendMessage();
  });

  function sendMessage() {
    const message = input.value;
    const username = usernameInput.value || "anonymous";
    if (!message) return;
    socket.send(JSON.stringify({ message: message, username: username }));
    input.value = "";
  }

  function appendLog(text) {
    const p = document.createElement("div");
    p.textContent = text;
    chatLog.appendChild(p);
    chatLog.scrollTop = chatLog.scrollHeight;
  }
})();
