import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from prometheus_client.parser import text_string_to_metric_families

st.set_page_config(page_title="vLLM Dashboard", layout="wide")

VLLM_METRICS_URL = "http://localhost:8845/metrics"

# Initialize session state for tracking requests
if 'prev_metrics' not in st.session_state:
    st.session_state.prev_metrics = {
        'ttft_count': 0,
        'ttft_sum': 0.0,
        'tpot_count': 0,
        'tpot_sum': 0.0
    }
if 'recent_requests' not in st.session_state:
    st.session_state.recent_requests = []

def fetch_metrics():
    try:
        response = requests.get(VLLM_METRICS_URL, timeout=2)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return None

def parse_metrics(metrics_text):
    metrics_data = []
    if not metrics_text:
        return metrics_data
    
    for family in text_string_to_metric_families(metrics_text):
        for sample in family.samples:
            metrics_data.append({
                "name": sample.name,
                "labels": str(sample.labels),
                "value": sample.value
            })
    return pd.DataFrame(metrics_data)

st.title("vLLM Monitoring Dashboard")

metrics_text = fetch_metrics()
if metrics_text:
    df = parse_metrics(metrics_text)
    
    if not df.empty:
        st.subheader("Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        def get_metric_value(name):
            res = df[df['name'] == name]
            if not res.empty:
                return res.iloc[0]['value']
            return 0

        with col1:
            st.metric("Running Requests", int(get_metric_value("vllm:num_requests_running")))
        with col2:
            st.metric("Waiting Requests", int(get_metric_value("vllm:num_requests_waiting")))
        with col3:
            st.metric("GPU Cache Usage", f"{get_metric_value('vllm:gpu_cache_usage_perc') * 100:.1f}%")
        with col4:
            st.metric("CPU Cache Usage", f"{get_metric_value('vllm:cpu_cache_usage_perc') * 100:.1f}%")
            
        # Calculate TTFT and TPS for new requests
        current_ttft_count = get_metric_value("vllm:time_to_first_token_seconds_count")
        current_ttft_sum = get_metric_value("vllm:time_to_first_token_seconds_sum")
        current_tpot_count = get_metric_value("vllm:request_time_per_output_token_seconds_count")
        current_tpot_sum = get_metric_value("vllm:request_time_per_output_token_seconds_sum")
        
        prev = st.session_state.prev_metrics
        
        if current_ttft_count > prev['ttft_count']:
            new_requests = int(current_ttft_count - prev['ttft_count'])
            ttft_diff = current_ttft_sum - prev['ttft_sum']
            tpot_diff = current_tpot_sum - prev['tpot_sum']
            
            avg_ttft = ttft_diff / new_requests if new_requests > 0 else 0
            avg_tpot = tpot_diff / new_requests if new_requests > 0 else 0
            avg_tps = 1.0 / avg_tpot if avg_tpot > 0 else 0
            
            # Add to recent requests
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.recent_requests.insert(0, {
                "Time": timestamp,
                "Requests": new_requests,
                "Avg TTFT (s)": round(avg_ttft, 4),
                "Avg TPS": round(avg_tps, 2)
            })
            
            # Keep only recent 100 requests
            st.session_state.recent_requests = st.session_state.recent_requests[:100]
            
            # Update prev metrics
            st.session_state.prev_metrics = {
                'ttft_count': current_ttft_count,
                'ttft_sum': current_ttft_sum,
                'tpot_count': current_tpot_count,
                'tpot_sum': current_tpot_sum
            }
        elif current_ttft_count < prev['ttft_count']:
            # Server restarted
            st.session_state.prev_metrics = {
                'ttft_count': current_ttft_count,
                'ttft_sum': current_ttft_sum,
                'tpot_count': current_tpot_count,
                'tpot_sum': current_tpot_sum
            }
            
        st.subheader("Recent Requests Performance (TTFT & TPS)")
        
        # Let user select N
        n_requests = st.slider("Show recent N records", min_value=5, max_value=100, value=10)
        
        if st.session_state.recent_requests:
            recent_df = pd.DataFrame(st.session_state.recent_requests[:n_requests])
            st.dataframe(recent_df, width='stretch')
        else:
            st.info("No new requests since dashboard started.")
            
        st.subheader("All Metrics")
        st.dataframe(df, width='stretch')
else:
    st.error(f"Failed to fetch metrics from {VLLM_METRICS_URL}. Is vLLM running?")

# Auto-refresh every 2 seconds
time.sleep(2)
st.rerun()
