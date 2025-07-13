// // let userName = "";
// // let userId = "";

// // document.getElementById("chatForm").addEventListener("submit", async function (e) {
// //   e.preventDefault();

// //   const chatWindow = document.getElementById("chatWindow");
// //   const message = document.getElementById("message").value.trim();

// //   if (!userName || !userId) {
// //     if (message.toLowerCase().startsWith("my name is")) {
// //       userName = message.split("is")[1].trim();
// //       addMessage("user", message);
// //       addMessage("bot", `Hi ${userName}! Please tell me your User ID (say "My ID is ...")`);
// //     } else if (message.toLowerCase().startsWith("my id is")) {
// //       userId = message.split("is")[1].trim();
// //       addMessage("user", message);
// //       addMessage("bot", `Got it! Now you can type your work update.`);
// //     } else {
// //       addMessage("user", message);
// //       addMessage("bot", `Please introduce yourself. Say "My name is ..."`);
// //     }
// //     document.getElementById("message").value = "";
// //     return;
// //   }

// //   // Normal message processing
// //   addMessage("user", message);

// //   const res = await fetch("/submit", {
// //     method: "POST",
// //     headers: { "Content-Type": "application/json" },
// //     body: JSON.stringify({ name: userName, user_id: userId, message }),
// //   });

// //   const data = await res.json();

// //   addMessage("bot", `
// //     <b>Logged:</b><br>
// //     Date: ${data.data[2]}<br>
// //     Leave: ${data.data[3]}<br>
// //     WFH: ${data.data[4]}<br>
// //     Task: ${data.data[5]}<br>
// //     Login: ${data.data[6]}<br>
// //     Logout: ${data.data[7]}
// //   `);

// //   document.getElementById("message").value = "";
// // });

// // function addMessage(sender, text) {
// //   const chatWindow = document.getElementById("chatWindow");
// //   const msg = document.createElement("div");
// //   msg.className = sender;
// //   msg.innerHTML = text;
// //   chatWindow.appendChild(msg);
// //   chatWindow.scrollTop = chatWindow.scrollHeight;
// // }
// let userName = "";
// let chatStarted = false;

// document.getElementById("startChatBtn").addEventListener("click", () => {
//   const dropdown = document.getElementById("userDropdown");
//   userName = dropdown.value;

//   if (!userName) {
//     alert("Please select your name to start chat.");
//     return;
//   }

//   // Reset chat UI
//   document.getElementById("chatWindow").innerHTML = "";
//   chatStarted = true;

//   addMessage("bot", `Hello ${userName}! Please enter your complete work log in one message (Leave, WFH, Login, Logout, Work Done).`);
// });

// document.getElementById("chatForm").addEventListener("submit", async function (e) {
//   e.preventDefault();
//   const message = document.getElementById("message").value.trim();
//   if (!chatStarted || !userName) {
//     addMessage("bot", "Please select your name and click 'Start Chat' before messaging.");
//     return;
//   }

//   addMessage("user", message);

//   const res = await fetch("/submit", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({ name: userName, message }),
//   });

//   const data = await res.json();
// if (data.success) {
//   const info = data.data;
//   addMessage("bot", `
//     <b>Structured Info:</b><br>
//     Name: ${info[1]}<br>
//     Date: ${info[2]}<br>
//     Leave: ${info[3]}<br>
//     WFH: ${info[4]}<br>
//     Task: ${info[5]}<br>
//     Login: ${info[6]}<br>
//     Logout: ${info[7]}
//   `);
// } else {
//   addMessage("bot", "Sorry, I couldn’t extract the info. Please try again.");
// }


//   document.getElementById("message").value = "";
// });

// function addMessage(sender, text) {
//   const chatWindow = document.getElementById("chatWindow");
//   const msg = document.createElement("div");
//   msg.className = sender;
//   msg.innerHTML = text;
//   chatWindow.appendChild(msg);
//   chatWindow.scrollTop = chatWindow.scrollHeight;
// }
// let userName = "";
// let chatStarted = false;

// document.getElementById("startChatBtn").addEventListener("click", () => {
//   const dropdown = document.getElementById("userDropdown");
//   userName = dropdown.value;

//   if (!userName) {
//     alert("Please select your name to start chat.");
//     return;
//   }

//   document.getElementById("chatWindow").innerHTML = "";
//   chatStarted = true;

//   addMessage("bot", `Hello ${userName}! Please enter your complete work log in one message (Leave, WFH, Login, Logout, Work Done).`);
// });

// document.getElementById("chatForm").addEventListener("submit", async function (e) {
//   e.preventDefault();
//   const message = document.getElementById("message").value.trim();

//   if (!chatStarted || !userName) {
//     addMessage("bot", "Please select your name and click 'Start Chat' first.");
//     return;
//   }

//   addMessage("user", message);

//   const res = await fetch("/message", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({ name: userName, message })
//   });

//   const data = await res.json();
//   addMessage("bot", data.message);

//   document.getElementById("message").value = "";
// });

// function addMessage(sender, text) {
//   const chatWindow = document.getElementById("chatWindow");
//   const msg = document.createElement("div");
//   msg.className = sender;
//   msg.innerHTML = text;
//   chatWindow.appendChild(msg);
//   chatWindow.scrollTop = chatWindow.scrollHeight;
// }
let userName = "";
let chatStarted = false;

document.getElementById("startChatBtn").addEventListener("click", () => {
  userName = document.getElementById("userDropdown").value;
  if (!userName) return alert("Select a name to start chat");

  chatStarted = true;
  document.getElementById("chatWindow").innerHTML = "";
  addMessage("bot", `Hello ${userName}! Please enter your complete work log in one message (Leave, WFH, Login, Logout, Work Done).`);
});

document.getElementById("chatForm").addEventListener("submit", async function (e) {
  e.preventDefault();
  const message = document.getElementById("message").value.trim();
  if (!chatStarted) return alert("Start chat first");

  addMessage("user", message);

  const res = await fetch("/message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: userName, message })
  });

  const data = await res.json();
  addMessage("bot", data.message);
  document.getElementById("message").value = "";
});

function addMessage(sender, text) {
  const chatWindow = document.getElementById("chatWindow");
  const msg = document.createElement("div");
  msg.className = sender;
  msg.innerHTML = text;
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}
