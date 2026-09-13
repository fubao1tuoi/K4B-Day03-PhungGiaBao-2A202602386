"""
Web Demo - Day 03 ReAct Agent
Chạy từ thư mục gốc của project:
    python web_demo.py

Mở:
    http://127.0.0.1:8000
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# Đảm bảo import được code trong src/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from app import run_react_agent  # noqa: E402
from mcp_server import MCPAcademicServer  # noqa: E402
from providers import get_llm_provider  # noqa: E402


HOST = "127.0.0.1"
PORT = 8000

# Conversation memory is kept in RAM and separated by browser/session ID.
# Only user/assistant final messages are stored -- never Thought/Action/Observation.
MAX_HISTORY_TURNS = 12
SESSION_TTL_SECONDS = 60 * 60 * 4

_session_lock = threading.Lock()
_sessions = {}

HTML = r"""
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meeting Room Assistant</title>
<style>
    :root {
        --bg: #eef7fb;
        --panel: #ffffff;
        --panel-soft: #f6fbfe;
        --primary: #168aad;
        --primary-dark: #126782;
        --primary-soft: #d9f1f8;
        --border: #cde5ee;
        --text: #173042;
        --muted: #6c8795;
        --user: #dff3fa;
        --assistant: #f4f9fb;
        --success: #2d8a6b;
        --warning: #b77a18;
    }

    * { box-sizing: border-box; }

    body {
        margin: 0;
        font-family: Inter, "Segoe UI", Arial, sans-serif;
        background: linear-gradient(135deg, #edf8fc 0%, #e4f3f9 100%);
        color: var(--text);
        height: 100vh;
        overflow: hidden;
    }

    .app {
        height: 100vh;
        display: flex;
        flex-direction: column;
    }

    .topbar {
        height: 72px;
        background: rgba(255,255,255,.94);
        border-bottom: 1px solid var(--border);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 22px;
        flex-shrink: 0;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .logo {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: grid;
        place-items: center;
        background: var(--primary-soft);
        color: var(--primary-dark);
        font-size: 21px;
        font-weight: 800;
    }

    .brand h1 {
        margin: 0;
        font-size: 18px;
        line-height: 1.2;
    }

    .brand p {
        margin: 3px 0 0;
        color: var(--muted);
        font-size: 12px;
    }

    .status {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border: 1px solid var(--border);
        border-radius: 999px;
        background: #f8fcfe;
        font-size: 12px;
        color: var(--muted);
    }

    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--success);
    }

    .workspace {
        flex: 1;
        min-height: 0;
        display: grid;
        grid-template-columns: minmax(0, 1.02fr) minmax(0, .98fr);
        gap: 14px;
        padding: 14px;
    }

    .panel {
        min-height: 0;
        background: rgba(255,255,255,.95);
        border: 1px solid var(--border);
        border-radius: 18px;
        box-shadow: 0 10px 28px rgba(27, 91, 112, .08);
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .panel-header {
        padding: 14px 16px;
        border-bottom: 1px solid var(--border);
        background: var(--panel-soft);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        flex-shrink: 0;
    }

    .panel-title {
        display: flex;
        align-items: center;
        gap: 9px;
        font-weight: 700;
        font-size: 14px;
    }

    .panel-title .badge {
        padding: 4px 8px;
        border-radius: 8px;
        background: var(--primary-soft);
        color: var(--primary-dark);
        font-size: 11px;
        font-weight: 700;
    }

    .messages {
        flex: 1;
        min-height: 0;
        overflow-y: auto;
        padding: 18px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        background: #fbfeff;
    }

    .welcome {
        padding: 16px;
        border: 1px dashed var(--border);
        border-radius: 14px;
        background: #f8fcfe;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.6;
    }

    .msg {
        max-width: 88%;
        padding: 11px 13px;
        border-radius: 14px;
        line-height: 1.5;
        font-size: 13px;
        white-space: pre-wrap;
        word-break: break-word;
    }

    .msg.user {
        align-self: flex-end;
        background: var(--user);
        border: 1px solid #c5e8f3;
        border-bottom-right-radius: 5px;
    }

    .msg.assistant {
        align-self: flex-start;
        background: var(--assistant);
        border: 1px solid var(--border);
        border-bottom-left-radius: 5px;
    }

    .msg.system {
        align-self: center;
        background: #fff8e9;
        border: 1px solid #f2dfb5;
        color: var(--warning);
        max-width: 95%;
    }

    .composer {
        border-top: 1px solid var(--border);
        padding: 12px;
        background: #fff;
        flex-shrink: 0;
    }

    .composer-row {
        display: flex;
        gap: 9px;
    }

    textarea {
        flex: 1;
        resize: none;
        height: 76px;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 11px 12px;
        font: inherit;
        font-size: 13px;
        outline: none;
        color: var(--text);
        background: #fbfeff;
    }

    textarea:focus {
        border-color: #88cddd;
        box-shadow: 0 0 0 3px rgba(22,138,173,.08);
    }

    button {
        border: 0;
        border-radius: 12px;
        padding: 0 18px;
        background: var(--primary);
        color: white;
        font-weight: 700;
        cursor: pointer;
        min-width: 95px;
    }

    button:hover { background: var(--primary-dark); }
    button:disabled { opacity: .55; cursor: wait; }

    .trace-toolbar {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .memory-badge {
        padding: 4px 8px;
        border-radius: 999px;
        background: #eaf7ef;
        color: #28764f;
        font-size: 10px;
        font-weight: 700;
    }

    .small-btn {
        background: white;
        color: var(--primary-dark);
        border: 1px solid var(--border);
        padding: 7px 10px;
        min-width: auto;
        font-size: 11px;
    }

    .trace {
        flex: 1;
        min-height: 0;
        overflow: auto;
        padding: 14px;
        background: #f7fcfe;
    }

    .trace-empty {
        color: var(--muted);
        text-align: center;
        padding: 48px 20px;
        font-size: 13px;
    }

    .trace-step {
        border: 1px solid var(--border);
        border-radius: 13px;
        background: white;
        margin-bottom: 10px;
        overflow: hidden;
    }

    .trace-step-head {
        padding: 10px 12px;
        background: #eef9fc;
        border-bottom: 1px solid var(--border);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
    }

    .step-label {
        font-weight: 800;
        font-size: 12px;
        color: var(--primary-dark);
    }

    .step-type {
        font-size: 10px;
        font-weight: 700;
        padding: 4px 7px;
        border-radius: 999px;
        background: var(--primary-soft);
        color: var(--primary-dark);
    }

    .trace-body {
        padding: 11px 12px;
    }

    .kv {
        margin: 0 0 9px;
    }

    .kv:last-child { margin-bottom: 0; }

    .k {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: .05em;
        color: var(--muted);
        margin-bottom: 3px;
        font-weight: 700;
    }

    .v {
        font-size: 12px;
        line-height: 1.5;
        white-space: pre-wrap;
        word-break: break-word;
    }

    pre {
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
        font-family: "Cascadia Code", Consolas, monospace;
        font-size: 11px;
        line-height: 1.5;
    }

    .footer-note {
        padding: 8px 14px;
        border-top: 1px solid var(--border);
        color: var(--muted);
        font-size: 10px;
        background: #fbfeff;
        flex-shrink: 0;
    }

    .layout {
        flex: 1;
        min-height: 0;
        display: grid;
        grid-template-columns: 255px minmax(0, 1fr);
        gap: 14px;
        padding: 14px;
    }

    .sidebar {
        min-height: 0;
        background: rgba(255,255,255,.95);
        border: 1px solid var(--border);
        border-radius: 18px;
        box-shadow: 0 10px 28px rgba(27, 91, 112, .08);
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .sidebar-header {
        padding: 14px;
        border-bottom: 1px solid var(--border);
        background: var(--panel-soft);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        flex-shrink: 0;
    }

    .sidebar-title {
        font-size: 14px;
        font-weight: 800;
    }

    .new-chat-btn {
        width: 100%;
        margin-top: 10px;
        padding: 10px 12px;
        min-width: 0;
    }

    .chat-list {
        flex: 1;
        overflow-y: auto;
        padding: 8px;
    }

    .chat-item {
        position: relative;
        padding: 10px 34px 10px 11px;
        border-radius: 11px;
        cursor: pointer;
        margin-bottom: 4px;
        border: 1px solid transparent;
        transition: background .15s ease, border-color .15s ease;
    }

    .chat-item:hover { background: #f0f8fb; border-color: var(--border); }
    .chat-item.active { background: var(--primary-soft); border-color: #b9dfeb; }

    .chat-item-title {
        font-size: 12px;
        font-weight: 700;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .chat-item-time {
        margin-top: 4px;
        font-size: 10px;
        color: var(--muted);
    }

    .delete-chat {
        position: absolute;
        right: 7px;
        top: 50%;
        transform: translateY(-50%);
        width: 24px;
        height: 24px;
        min-width: 0;
        padding: 0;
        border-radius: 7px;
        background: transparent;
        color: var(--muted);
        opacity: 0;
        font-size: 12px;
    }

    .chat-item:hover .delete-chat, .chat-item.active .delete-chat { opacity: 1; }
    .delete-chat:hover { background: #fff; color: var(--warning); }

    .empty-chats {
        padding: 20px 12px;
        text-align: center;
        color: var(--muted);
        font-size: 11px;
        line-height: 1.5;
    }

    .main-area {
        min-width: 0;
        min-height: 0;
        display: grid;
        grid-template-columns: minmax(0, 1.02fr) minmax(0, .98fr);
        gap: 14px;
    }

    @media (max-width: 1100px) {
        .layout { grid-template-columns: 210px minmax(0, 1fr); }
        .main-area { grid-template-columns: 1fr; }
        .main-area .panel:last-child { min-height: 420px; }
    }

    @media (max-width: 760px) {
        body { overflow: auto; }
        .layout { grid-template-columns: 1fr; height: auto; }
        .sidebar { min-height: 220px; max-height: 320px; }
        .main-area { grid-template-columns: 1fr; }
        .panel { min-height: 520px; }
        .topbar { position: sticky; top: 0; z-index: 2; }
    }
</style>
</head>
<body>
<div class="app">
    <header class="topbar">
        <div class="brand">
            <div class="logo">📅</div>
            <div>
                <h1>Meeting Room Assistant</h1>
                <p>Smart Meeting Room Booking · Chat &amp; Support</p>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <div class="status">
                <span class="dot"></span>
                <span id="providerStatus">Checking provider...</span>
            </div>
            <button class="small-btn" onclick="newChat()">New chat</button>
        </div>
    </header>

    <main class="layout">
        <aside class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-title">💬 Lịch sử chat</div>
            </div>
            <div style="padding: 0 10px 10px;">
                <button class="new-chat-btn" onclick="newChat()">＋ New chat</button>
            </div>
            <div class="chat-list" id="chatList">
                <div class="empty-chats">Chưa có cuộc trò chuyện nào.</div>
            </div>
        </aside>

        <div class="main-area">
            <section class="panel">
                <div class="panel-header">
                    <div class="panel-title">
                        💬 Chat
                        <span class="badge">User Query</span>
                    </div>
                    <button class="small-btn" onclick="clearCurrentChat()">Xóa chat</button>
                </div>

                <div class="messages" id="messages">
                    <div class="welcome" id="welcomeMessage">
                        <strong>Meeting Room Assistant</strong><br>
                        Gửi yêu cầu như: “Đặt phòng lúc 09:00 ngày 16/09/2026 cho 8 người, cần máy chiếu”.
                        Tôi hỗ trợ tìm kiếm và đặt phòng họp theo yêu cầu. Phần Chat chỉ hiển thị câu trả lời cuối cùng;
                        từng cuộc hội thoại được lưu riêng ở thanh Lịch sử chat.
                    </div>
                </div>

                <div class="composer">
                    <div class="composer-row">
                        <textarea id="input" placeholder="Nhập yêu cầu đặt phòng họp..."></textarea>
                        <button id="sendBtn" onclick="sendMessage()">Gửi</button>
                    </div>
                </div>
            </section>

            <section class="panel">
                <div class="panel-header">
                    <div class="panel-title">
                        🔎 Waterfall Trace
                        <span class="badge">Live Trace</span>
                    </div>
                    <div class="trace-toolbar">
                        <button class="small-btn" onclick="copyTrace()">Copy JSON</button>
                        <button class="small-btn" onclick="clearTrace()">Clear</button>
                    </div>
                </div>

                <div class="trace" id="trace">
                    <div class="trace-empty">
                        Chưa có trace.<br>
                        Gửi một câu lệnh ở panel Chat để bắt đầu.
                    </div>
                </div>

                <div class="footer-note">
                    Chat chỉ hiển thị Final Answer. ReAct trace chỉ nằm ở panel debug.
                </div>
            </section>
        </div>
    </main>
</div>

<script>
let latestTrace = [];

const SESSION_KEY = "facilities_agent_active_session";
const CONVERSATIONS_KEY = "facilities_agent_conversations_v1";

function makeId() {
    return (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + "-" + Math.random());
}

function getConversations() {
    try {
        return JSON.parse(localStorage.getItem(CONVERSATIONS_KEY) || "{}");
    } catch {
        return {};
    }
}

function saveConversations(conversations) {
    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations));
}

function getSessionId() {
    let id = localStorage.getItem(SESSION_KEY);
    if (!id) {
        id = makeId();
        localStorage.setItem(SESSION_KEY, id);
    }
    return id;
}

function ensureConversation(sessionId = getSessionId()) {
    const conversations = getConversations();
    if (!conversations[sessionId]) {
        conversations[sessionId] = {
            id: sessionId,
            title: "Cuộc trò chuyện mới",
            createdAt: Date.now(),
            updatedAt: Date.now(),
            messages: []
        };
        saveConversations(conversations);
    }
    return conversations[sessionId];
}

function formatTime(ts) {
    return new Date(ts).toLocaleString("vi-VN", {
        day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit"
    });
}

function escapeForAttr(value) {
    return escapeHtml(value).replaceAll("`", "&#096;");
}

function renderChatList() {
    const list = document.getElementById("chatList");
    const conversations = Object.values(getConversations())
        .sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));

    if (!conversations.length) {
        list.innerHTML = '<div class="empty-chats">Chưa có cuộc trò chuyện nào.</div>';
        return;
    }

    const activeId = getSessionId();
    list.innerHTML = conversations.map(chat => `
        <div class="chat-item ${chat.id === activeId ? "active" : ""}" onclick="openChat('${escapeForAttr(chat.id)}')">
            <div class="chat-item-title">${escapeHtml(chat.title || "Cuộc trò chuyện")}</div>
            <div class="chat-item-time">${escapeHtml(formatTime(chat.updatedAt || chat.createdAt || Date.now()))}</div>
            <button class="delete-chat" title="Xóa cuộc trò chuyện" onclick="deleteChat(event, '${escapeForAttr(chat.id)}')">×</button>
        </div>`).join("");
}

function saveCurrentMessage(role, content) {
    const sessionId = getSessionId();
    const conversations = getConversations();
    const chat = conversations[sessionId] || ensureConversation(sessionId);

    chat.messages = chat.messages || [];
    chat.messages.push({ role, content, time: Date.now() });
    chat.updatedAt = Date.now();

    if (role === "user" && chat.title === "Cuộc trò chuyện mới") {
        chat.title = content.length > 42 ? content.slice(0, 42).trim() + "…" : content;
    }

    conversations[sessionId] = chat;
    saveConversations(conversations);
    renderChatList();
}

function renderMessages(messages) {
    const box = document.getElementById("messages");
    if (!messages || !messages.length) {
        box.innerHTML = `
            <div class="welcome" id="welcomeMessage">
                <strong>Meeting Room Assistant</strong><br>
                Đây là một cuộc trò chuyện mới. Hãy nhập yêu cầu đầu tiên của bạn.
            </div>`;
        return;
    }

    box.innerHTML = "";
    messages.forEach(item => addMessage(item.content, item.role === "user" ? "user" : "assistant", false));
    box.scrollTop = box.scrollHeight;
}

function addMessage(text, type, save = true) {
    const box = document.getElementById("messages");
    const div = document.createElement("div");
    div.className = "msg " + type;
    div.textContent = text;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;

    if (save && (type === "user" || type === "assistant")) {
        saveCurrentMessage(type, text);
    }
}

function renderTrace(trace) {
    latestTrace = trace || [];
    const box = document.getElementById("trace");

    if (!latestTrace.length) {
        box.innerHTML = '<div class="trace-empty">Chưa có trace.</div>';
        return;
    }

    box.innerHTML = latestTrace.map((item) => {
        const type = item.action_type || "UNKNOWN";
        let body = "";

        if (item.thought) {
            body += `
                <div class="kv">
                    <div class="k">Thought</div>
                    <div class="v">${escapeHtml(item.thought)}</div>
                </div>`;
        }

        if (item.tool_name) {
            body += `
                <div class="kv">
                    <div class="k">Action</div>
                    <div class="v"><strong>${escapeHtml(item.tool_name)}</strong></div>
                </div>`;
        }

        if (item.arguments) {
            body += `
                <div class="kv">
                    <div class="k">Arguments</div>
                    <pre>${escapeHtml(JSON.stringify(item.arguments, null, 2))}</pre>
                </div>`;
        }

        if (item.observation !== undefined) {
            body += `
                <div class="kv">
                    <div class="k">Observation</div>
                    <pre>${escapeHtml(JSON.stringify(item.observation, null, 2))}</pre>
                </div>`;
        }

        if (item.output !== undefined) {
            body += `
                <div class="kv">
                    <div class="k">Final Answer</div>
                    <div class="v">${escapeHtml(item.output)}</div>
                </div>`;
        }

        body += `
            <div class="kv">
                <div class="k">Latency</div>
                <div class="v">${escapeHtml(String(item.latency_ms ?? 0))} ms</div>
            </div>`;

        return `
            <div class="trace-step">
                <div class="trace-step-head">
                    <span class="step-label">Step ${escapeHtml(String(item.step ?? ""))}</span>
                    <span class="step-type">${escapeHtml(type)}</span>
                </div>
                <div class="trace-body">${body}</div>
            </div>`;
    }).join("");

    box.scrollTop = 0;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function sendMessage() {
    const input = document.getElementById("input");
    const btn = document.getElementById("sendBtn");
    const query = input.value.trim();

    if (!query || btn.disabled) return;

    addMessage(query, "user");
    input.value = "";
    btn.disabled = true;
    btn.textContent = "Đang chạy...";

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                query,
                session_id: getSessionId()
            })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            addMessage("Lỗi: " + (data.error || "Không xác định"), "system");
            renderTrace([]);
            return;
        }

        addMessage(data.answer || "Agent không trả về nội dung.", "assistant");
        renderTrace(data.trace || []);
    } catch (error) {
        addMessage("Không thể kết nối tới web server: " + error.message, "system");
    } finally {
        btn.disabled = false;
        btn.textContent = "Gửi";
        input.focus();
    }
}

async function copyTrace() {
    try {
        await navigator.clipboard.writeText(JSON.stringify(latestTrace, null, 2));
        addMessage("Đã copy Waterfall Trace JSON.", "system");
    } catch {
        addMessage("Không thể copy trace vào clipboard.", "system");
    }
}

function clearTrace() {
    latestTrace = [];
    document.getElementById("trace").innerHTML =
        '<div class="trace-empty">Chưa có trace.</div>';
}

async function newChat() {
    const id = makeId();
    localStorage.setItem(SESSION_KEY, id);
    ensureConversation(id);
    renderMessages([]);
    clearTrace();
    renderChatList();
    document.getElementById("input").focus();
}

async function openChat(sessionId) {
    if (!sessionId || sessionId === getSessionId()) {
        const current = ensureConversation(getSessionId());
        renderMessages(current.messages || []);
        renderChatList();
        return;
    }

    localStorage.setItem(SESSION_KEY, sessionId);
    const conversations = getConversations();
    const localChat = conversations[sessionId];

    if (localChat) {
        renderMessages(localChat.messages || []);
    }

    clearTrace();
    renderChatList();
    document.getElementById("input").focus();

    // Lấy lại history từ server để đảm bảo memory phía agent vẫn đồng bộ.
    try {
        const response = await fetch("/history?session_id=" + encodeURIComponent(sessionId));
        const data = await response.json();
        if (response.ok && Array.isArray(data.messages)) {
            const current = conversations[sessionId] || ensureConversation(sessionId);
            current.messages = data.messages.map(item => ({
                role: item.role,
                content: item.content,
                time: Date.now()
            }));
            current.updatedAt = Date.now();
            conversations[sessionId] = current;
            saveConversations(conversations);
            renderMessages(current.messages);
            renderChatList();
        }
    } catch (_) {
        // Vẫn dùng bản history trong localStorage nếu server không phản hồi.
    }
}

function deleteChat(event, sessionId) {
    event.stopPropagation();
    const conversations = getConversations();
    delete conversations[sessionId];
    saveConversations(conversations);

    if (sessionId === getSessionId()) {
        const remaining = Object.values(conversations).sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
        if (remaining.length) {
            localStorage.setItem(SESSION_KEY, remaining[0].id);
            renderMessages(remaining[0].messages || []);
            clearTrace();
        } else {
            const id = makeId();
            localStorage.setItem(SESSION_KEY, id);
            ensureConversation(id);
            renderMessages([]);
            clearTrace();
        }
    }
    renderChatList();
}

function clearCurrentChat() {
    const sessionId = getSessionId();
    const conversations = getConversations();
    if (!conversations[sessionId]) return;

    conversations[sessionId].messages = [];
    conversations[sessionId].title = "Cuộc trò chuyện mới";
    conversations[sessionId].updatedAt = Date.now();
    saveConversations(conversations);
    renderMessages([]);
    renderChatList();
    clearTrace();

    fetch("/reset", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({session_id: sessionId})
    }).catch(() => {});
}

document.getElementById("input").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

async function loadStatus() {
    try {
        const response = await fetch("/status");
        const data = await response.json();
        document.getElementById("providerStatus").textContent =
            "Provider: " + (data.provider || "Unknown");
    } catch {
        document.getElementById("providerStatus").textContent = "Server offline";
    }
}

ensureConversation(getSessionId());
renderMessages(getConversations()[getSessionId()].messages || []);
renderChatList();
loadStatus();
</script>
</body>
</html>
"""


def _cleanup_sessions_locked():
    """Xóa session quá hạn. Hàm này phải được gọi khi đã giữ _session_lock."""
    now = time.time()
    expired = [
        sid for sid, data in _sessions.items()
        if now - data["updated_at"] > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        _sessions.pop(sid, None)


def get_session_history(session_id: str):
    """Lấy một bản sao history để không giữ lock trong khi gọi LLM."""
    with _session_lock:
        _cleanup_sessions_locked()
        data = _sessions.get(session_id)
        if not data:
            return []

        data["updated_at"] = time.time()
        return list(data["messages"][-(MAX_HISTORY_TURNS * 2):])


def append_session_turn(session_id: str, user_message: str, assistant_message: str):
    """Chỉ lưu User + Assistant final answer, không lưu ReAct trace."""
    with _session_lock:
        _cleanup_sessions_locked()

        data = _sessions.setdefault(
            session_id,
            {"messages": [], "updated_at": time.time()}
        )

        data["messages"].append({
            "role": "user",
            "content": user_message
        })
        data["messages"].append({
            "role": "assistant",
            "content": assistant_message
        })

        data["messages"] = data["messages"][-(MAX_HISTORY_TURNS * 2):]
        data["updated_at"] = time.time()


def reset_session(session_id: str):
    with _session_lock:
        _sessions.pop(session_id, None)


def build_contextual_query(current_query: str, history):
    """
    Đưa lịch sử hội thoại vào context của lượt hiện tại.

    Lưu ý:
    - Chỉ có User/Assistant final answer.
    - Không đưa Thought/Action/Observation vào history.
    """
    if not history:
        return current_query

    lines = [
        "CONVERSATION HISTORY (use this only as context for the current request):"
    ]

    for item in history:
        role = "User" if item["role"] == "user" else "Assistant"
        content = item["content"].strip()
        lines.append(f"{role}: {content}")

    lines.extend([
        "",
        "CURRENT USER REQUEST:",
        current_query,
        "",
        "IMPORTANT:",
        "- Treat the current user request as the newest instruction.",
        "- Use previous turns only when relevant.",
        "- Do not expose internal reasoning, Thought, Action, Observation, tool calls, or ReAct trace in the final answer.",
    ])

    return "\n".join(lines)


def _find_booking_code(value):
    """Tìm mã đặt phòng trong observation/output theo nhiều key phổ biến."""
    keys = {
        "booking_code", "booking_id", "reservation_code",
        "reservation_id", "confirmation_code", "confirmation_id",
        "booking_reference", "reservation_reference", "reference_code",
    }

    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).strip().lower() in keys and item not in (None, ""):
                return str(item).strip()
            found = _find_booking_code(item)
            if found:
                return found

    elif isinstance(value, (list, tuple)):
        for item in value:
            found = _find_booking_code(item)
            if found:
                return found

    elif isinstance(value, str):
        import re
        patterns = [
            r"(?:mã|ma)\s*(?:đặt\s*phòng|dat\s*phong|booking|reservation)?\s*[:#-]\s*([A-Za-z0-9_-]{4,})",
            r"(?:booking|reservation|confirmation)\s*(?:code|id|number|no\.?|reference)\s*[:#-]\s*([A-Za-z0-9_-]{4,})",
        ]
        for pattern in patterns:
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                return match.group(1).strip()

    return None


def extract_final_answer(trace):
    """
    Trả về câu trả lời sạch cho người dùng, đồng thời giữ lại mã đặt phòng
    nếu mã chỉ xuất hiện trong tool observation/trace mà FINAL_ANSWER không nhắc lại.
    """
    final_answer = ""

    for item in reversed(trace or []):
        if item.get("action_type") == "FINAL_ANSWER":
            final_answer = str(item.get("output", "") or "")
            break

    if not final_answer:
        for item in reversed(trace or []):
            output = item.get("output")
            if output:
                final_answer = str(output)
                break

    cleaned_lines = []
    protocol_prefixes = (
        "thought:", "action:", "action input:", "observation:",
        "final_answer:", "final answer:"
    )

    for line in final_answer.splitlines():
        stripped = line.strip().lower()
        if stripped.startswith(protocol_prefixes):
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines).strip()

    # Quan trọng: một số tool trả booking code trong observation chứ không đưa
    # lại vào FINAL_ANSWER. Khi đó vẫn phải hiển thị mã cho người dùng.
    booking_code = None
    for item in reversed(trace or []):
        for field in ("observation", "output", "arguments"):
            if field in item:
                booking_code = _find_booking_code(item.get(field))
                if booking_code:
                    break
        if booking_code:
            break

    if booking_code:
        normalized = (cleaned or "").lower()
        if booking_code.lower() not in normalized:
            cleaned = (cleaned + "\n\nMã đặt phòng: " + booking_code).strip()

    return cleaned or "Agent chưa tạo được câu trả lời."


class DemoHandler(BaseHTTPRequestHandler):
    provider = None
    mcp_server = None

    def _send_json(self, payload: dict, status: int = 200):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self):
        raw = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self._send_html()
            return

        if path == "/history":
            try:
                query = urlparse(self.path).query
                from urllib.parse import parse_qs
                params = parse_qs(query)
                session_id = str(params.get("session_id", [""])[0]).strip()
                history = get_session_history(session_id) if session_id else []
                self._send_json({"messages": history})
            except Exception as exc:
                self._send_json({"error": f"{type(exc).__name__}: {exc}"}, 500)
            return

        if path == "/status":
            with _session_lock:
                _cleanup_sessions_locked()
                session_count = len(_sessions)

            self._send_json({
                "provider": self.provider.__class__.__name__ if self.provider else "Unknown",
                "memory_sessions": session_count,
                "max_history_turns": MAX_HISTORY_TURNS
            })
            return

        self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        # Tạo một cuộc hội thoại mới / xóa memory của session hiện tại.
        if path == "/reset":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(content_length)
                body = json.loads(raw.decode("utf-8")) if raw else {}
                session_id = str(body.get("session_id", "")).strip()

                if session_id:
                    reset_session(session_id)

                self._send_json({"ok": True})
            except Exception as exc:
                self._send_json({
                    "error": f"{type(exc).__name__}: {exc}"
                }, 500)
            return

        if path != "/chat":
            self._send_json({"error": "Not found"}, 404)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length)
            body = json.loads(raw.decode("utf-8"))

            query = str(body.get("query", "")).strip()
            session_id = str(body.get("session_id", "")).strip()

            if not query:
                self._send_json({"error": "Query không được để trống."}, 400)
                return

            if not session_id:
                session_id = str(uuid.uuid4())

            # 1. Lấy context của các lượt chat trước.
            history = get_session_history(session_id)

            # 2. Gửi query + memory vào agent.
            contextual_query = build_contextual_query(query, history)

            trace = run_react_agent(
                contextual_query,
                self.provider,
                self.mcp_server
            )

            # 3. CHỈ lấy câu trả lời cuối để hiển thị cho user.
            final_answer = extract_final_answer(trace)

            # 4. Lưu đúng cặp User/Assistant vào memory.
            append_session_turn(
                session_id=session_id,
                user_message=query,
                assistant_message=final_answer
            )

            # trace vẫn có thể hiển thị ở panel debug,
            # nhưng không bao giờ được dùng làm nội dung chat.
            self._send_json({
                "answer": final_answer,
                "trace": trace,
                "session_id": session_id,
                "memory_turns": len(history) // 2 + 1
            })

        except Exception as exc:
            self._send_json({
                "error": f"{type(exc).__name__}: {exc}"
            }, 500)

    def log_message(self, format, *args):
        # Giảm log HTTP mặc định để terminal dễ theo dõi ReAct trace.
        return


def main():
    print("=" * 62)
    print("🌐 MEETING ROOM ASSISTANT WEB DEMO")
    print("=" * 62)

    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()

    DemoHandler.provider = provider
    DemoHandler.mcp_server = mcp_server

    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}")
    print(f"📦 Tools: {len(mcp_server.list_tools())}")
    print(f"🚀 Web Demo: http://{HOST}:{PORT}")
    print("-" * 62)
    print("Nhấn Ctrl+C để dừng server.")

    server = ThreadingHTTPServer((HOST, PORT), DemoHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Đã dừng Web Demo.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
