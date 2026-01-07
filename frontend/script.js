let sessionId = null;

function addMessage(sender, text) {
    const box = document.getElementById("chat-box");
    const div = document.createElement("div");
    div.className = `message ${sender}`;
    div.innerText = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function showTyping(show) {
    document.getElementById("typing").style.display = show ? "block" : "none";
}

async function sendMessage() {
    const input = document.getElementById("user-input");
    const msg = input.value.trim();
    if (!msg) return;

    addMessage("user", msg);
    input.value = "";
    showTyping(true);

    const res = await fetch("/chat", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
            message: msg,
            session_id: sessionId
        })
    });

    const data = await res.json();
    sessionId = data.session_id;
    showTyping(false);
    addMessage("bot", data.answer);
}

function handleEnter(e){
    if(e.key === "Enter") sendMessage();
}

function quick(text){
    document.getElementById("user-input").value = text;
    sendMessage();
}

function newSession(){
    sessionId = null;
    document.getElementById("chat-box").innerHTML = "";
}
