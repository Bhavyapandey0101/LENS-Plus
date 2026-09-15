let selectedLanguage = "English";

function selectLanguage(button, language) {
    document.querySelectorAll(".language").forEach(btn => {
        btn.classList.remove("active");
    });

    button.classList.add("active");
    selectedLanguage = language;
}

function addMessage(text, type) {
    const chat = document.getElementById("chatMessages");

    const message = document.createElement("div");

    message.classList.add(
        "message",
        type === "user" ? "user-message" : "bot-message"
    );

    message.innerHTML = text
    message.innerHTML = text
    .replace(/^### (.*?)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*?)$/gm, "<h3>$1</h3>")
    .replace(/^# (.*?)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.*?)$/gm, "• $1<br>")
    .replace(/\n/g, "<br>");

    chat.appendChild(message);
    chat.scrollTop = chat.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById("userInput");
    const message = input.value.trim();

    if (!message) {
        return;
    }

    addMessage(message, "user");
    input.value = "";

    addMessage("Thinking...", "bot");

    try {
        const response = await fetch(
            "https://lens-plus.onrender.com/chat",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: message,
                    language: selectedLanguage
                })
            }
        );

        const data = await response.json();

        const chat = document.getElementById("chatMessages");

        chat.lastChild.remove();

        if (data.success) {
            addMessage(data.message, "bot");
        } else {
            addMessage(
                "Sorry, I couldn't process your question.",
                "bot"
            );
        }

    } catch (error) {

        const chat = document.getElementById("chatMessages");

        chat.lastChild.remove();

        addMessage(
            "Backend connection failed. Please make sure the LENS+ backend is running.",
            "bot"
        );

        console.error(error);
    }
}


function handleEnter(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
}


async function handleFile(event) {

    const file = event.target.files[0];

    if (!file) {
        return;
    }

    addMessage(
        `📄 Uploaded: ${file.name}`,
        "user"
    );

    addMessage(
        "🔎 I'm analyzing your report...",
        "bot"
    );

    const formData = new FormData();

    formData.append("report", file);
    formData.append("language", selectedLanguage);

    try {

        const response = await fetch(
            "https://lens-plus.onrender.com/analyze",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        const chat = document.getElementById("chatMessages");

        chat.lastChild.remove();

        if (data.success) {

            addMessage(
                data.message,
                "bot"
            );

        } else {

            addMessage(
                data.message || "Unable to analyze the report.",
                "bot"
            );
        }

    } catch (error) {

        const chat = document.getElementById("chatMessages");

        chat.lastChild.remove();

        addMessage(
            "I couldn't connect to the LENS+ backend. Please make sure the backend is running.",
            "bot"
        );

        console.error(error);
    }
}


function newChat() {
    document.getElementById("chatMessages").innerHTML = "";
}


function toggleSidebar() {
    document
        .querySelector(".sidebar")
        .classList.toggle("open");
}
