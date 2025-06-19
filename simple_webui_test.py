#!/usr/bin/env python3
# ==============================================================================
# Simple WebUI Test Script
# ==============================================================================
# Description: Simple test to verify Streamlit is working with OpenAI Forward
# Author: Assistant
# Created: 2024-12-19
# ==============================================================================

import streamlit as st
import time
from datetime import datetime

st.set_page_config(
    page_title="OpenAI Forward WebUI",
    page_icon="🚀",
    layout="wide"
)

# Title and header
st.title("🚀 OpenAI Forward WebUI")
st.subheader("Configuration Management Interface")

# Test basic functionality
st.write(f"**Current Time**: {datetime.now().isoformat()}")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    selected_section = st.radio(
        "Select Configuration Section:",
        [
            "Forward Configuration",
            "API Key & Level",
            "Cache Settings", 
            "Rate Limiting",
            "Real-time Logs",
            "API Playground",
            "Statistics"
        ]
    )
    
    st.write("---")
    
    if st.button("🔄 Apply Configuration"):
        st.success("Configuration applied successfully!")
    
    if st.button("📥 Export Configuration"):
        st.info("Configuration exported!")

# Main content based on selection
if selected_section == "Forward Configuration":
    st.header("🔗 Forward Configuration")
    st.write("Configure OpenAI API forwarding endpoints")
    
    with st.expander("Current Configuration"):
        st.code("""
        Forward Rules:
        - OpenAI: https://api.openai.com -> /
        - DeepSeek: https://api.deepseek.com -> /deepseek  
        - LingyiWanwu: https://api.lingyiwanwu.com -> /lingyiwanwu
        - Ollama: http://ollama-server:11434 -> /ollama
        """)

elif selected_section == "API Key & Level":
    st.header("🔑 API Key & Level Management")
    st.write("Manage API keys and access levels")
    st.info("Configure API key permissions and access levels here")

elif selected_section == "Cache Settings":
    st.header("💾 Cache Settings")
    st.write("Configure response caching")
    st.info("Cache backend: MEMORY")

elif selected_section == "Rate Limiting":
    st.header("⏱️ Rate Limiting")
    st.write("Configure request rate limits")
    st.info("Current: 1000/minute (moving-window)")

elif selected_section == "Real-time Logs":
    st.header("📋 Real-time Logs")
    st.write("View live system logs")
    
    if st.button("🔄 Refresh Logs"):
        with st.spinner("Loading logs..."):
            time.sleep(1)
            st.text_area("System Logs", 
                        "2025-06-04 09:45:00 | INFO | OpenAI Forward started\n"
                        "2025-06-04 09:45:01 | INFO | WebUI interface ready\n"
                        "2025-06-04 09:45:02 | INFO | All services operational",
                        height=200)

elif selected_section == "API Playground":
    st.header("🧪 API Playground")
    st.write("Test API endpoints")
    
    endpoint = st.selectbox("Select Endpoint:", [
        "/v1/chat/completions",
        "/v1/embeddings", 
        "/healthz"
    ])
    
    if st.button("🚀 Test Endpoint"):
        st.success(f"Testing {endpoint}...")
        st.json({"status": "success", "endpoint": endpoint, "response_time": "0.5s"})

elif selected_section == "Statistics":
    st.header("📊 Statistics")
    st.write("View usage statistics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Requests", "1,234", "12%")
    with col2:
        st.metric("Cache Hits", "856", "8%")
    with col3:
        st.metric("Error Rate", "0.5%", "-0.1%")

# Footer
st.write("---")
st.write("🚀 **OpenAI Forward WebUI** - Real-time Configuration Management")
st.write("API Server: http://localhost:8000 | WebUI: http://localhost:8001") 