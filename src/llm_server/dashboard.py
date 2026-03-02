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
        'tpot_sum': 0.0,
        'e2e_count': 0,
        'e2e_sum': 0.0,
        'gen_tokens_count': 0,
        'gen_tokens_sum': 0.0,
        'prompt_cache_hit': 0.0,
        'prompt_compute': 0.0,
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

st.sidebar.header("设置 (Settings)")
refresh_interval = st.sidebar.selectbox(
    "刷新时间 (秒) / Refresh Interval",
    options=[5, 10, 15, 30, 60],
    index=2
)

metrics_text = fetch_metrics()
if metrics_text:
    df = parse_metrics(metrics_text)
    
    if not df.empty:
        st.subheader("Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        def get_metric_value(name, labels_contains=None):
            res = df[df['name'] == name]
            if labels_contains:
                res = res[res['labels'].str.contains(labels_contains)]
            if not res.empty:
                # In case there are multiple matching labels (e.g. multiple engines), we sum them up
                return res['value'].sum()
            return 0

        with col1:
            st.metric("Running Requests", int(get_metric_value("vllm:num_requests_running")))
        with col2:
            st.metric("Waiting Requests", int(get_metric_value("vllm:num_requests_waiting")))
        with col3:
            st.metric("GPU Cache Usage", f"{get_metric_value('vllm:gpu_cache_usage_perc') * 100:.1f}%")
        with col4:
            st.metric("CPU Cache Usage", f"{get_metric_value('vllm:cpu_cache_usage_perc') * 100:.1f}%")
            
        # Calculate TTFT, E2E latency, output tokens, and TPS for new requests
        current_ttft_count = get_metric_value("vllm:time_to_first_token_seconds_count")
        current_ttft_sum = get_metric_value("vllm:time_to_first_token_seconds_sum")
        # TPOT is recorded when a request *completes*, so its count may lag behind TTFT count
        current_tpot_count = get_metric_value("vllm:request_time_per_output_token_seconds_count")
        current_tpot_sum = get_metric_value("vllm:request_time_per_output_token_seconds_sum")
        current_e2e_count = get_metric_value("vllm:e2e_request_latency_seconds_count")
        current_e2e_sum = get_metric_value("vllm:e2e_request_latency_seconds_sum")
        current_gen_tokens_count = get_metric_value("vllm:request_generation_tokens_count")
        current_gen_tokens_sum = get_metric_value("vllm:request_generation_tokens_sum")
        
        # prefix caching tokens
        current_cache_hit = get_metric_value("vllm:prompt_tokens_by_source_total", "local_cache_hit")
        current_compute = get_metric_value("vllm:prompt_tokens_by_source_total", "local_compute")

        prev = st.session_state.prev_metrics

        new_ttft_reqs = current_ttft_count - prev['ttft_count']
        new_tpot_reqs = current_tpot_count - prev['tpot_count']

        # 只在有请求完全结束时才记录，将这期间的所有指标合并为一条输出
        if new_tpot_reqs > 0:
            ttft_diff = current_ttft_sum - prev['ttft_sum']
            tpot_diff = current_tpot_sum - prev['tpot_sum']
            e2e_count_diff = current_e2e_count - prev['e2e_count']
            e2e_diff = current_e2e_sum - prev['e2e_sum']
            gen_tokens_count_diff = current_gen_tokens_count - prev['gen_tokens_count']
            gen_tokens_sum_diff = current_gen_tokens_sum - prev['gen_tokens_sum']
            
            cache_hit_diff = current_cache_hit - prev['prompt_cache_hit']
            compute_diff = current_compute - prev['prompt_compute']

            # Avg TTFT uses TTFT count — recorded at first-token emission
            avg_ttft = ttft_diff / new_ttft_reqs if new_ttft_reqs > 0 else 0
            # Avg TPOT uses TPOT count — recorded only when a request fully completes
            avg_tpot = tpot_diff / new_tpot_reqs if new_tpot_reqs > 0 else 0
            # TPS = tokens per second per request = 1 / TPOT (TPOT is seconds per token)
            avg_tps = 1.0 / avg_tpot if avg_tpot > 0 else 0
            # Avg end-to-end latency per completed request
            avg_e2e = e2e_diff / e2e_count_diff if e2e_count_diff > 0 else 0
            # Avg output tokens per completed request
            avg_gen_tokens = gen_tokens_sum_diff / gen_tokens_count_diff if gen_tokens_count_diff > 0 else 0
            
            # Cache hits per request and cache hit rate
            avg_cache_hit = cache_hit_diff / new_tpot_reqs if new_tpot_reqs > 0 else 0
            avg_compute = compute_diff / new_tpot_reqs if new_tpot_reqs > 0 else 0
            cache_hit_rate = cache_hit_diff / (cache_hit_diff + compute_diff) if (cache_hit_diff + compute_diff) > 0 else 0.0

            # Add to recent requests
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.recent_requests.insert(0, {
                "Time": timestamp,
                "TTFT Reqs": int(new_ttft_reqs),
                "Completed Reqs": int(new_tpot_reqs),
                "Avg TTFT (ms)": round(avg_ttft * 1000, 2),
                "Avg E2E (s)": round(avg_e2e, 4),
                "Avg Output Tokens": round(avg_gen_tokens, 1),
                "Avg TPS (tok/s)": round(avg_tps, 2),
                "Avg Cached (tok)": round(avg_cache_hit, 1),
                "Avg Computed (tok)": round(avg_compute, 1),
                "Cache Hit Rate": f"{cache_hit_rate * 100:.1f}%",
            })

            # Keep only recent 100 records
            st.session_state.recent_requests = st.session_state.recent_requests[:100]

            # Update prev metrics
            st.session_state.prev_metrics = {
                'ttft_count': current_ttft_count,
                'ttft_sum': current_ttft_sum,
                'tpot_count': current_tpot_count,
                'tpot_sum': current_tpot_sum,
                'e2e_count': current_e2e_count,
                'e2e_sum': current_e2e_sum,
                'gen_tokens_count': current_gen_tokens_count,
                'gen_tokens_sum': current_gen_tokens_sum,
                'prompt_cache_hit': current_cache_hit,
                'prompt_compute': current_compute,
            }
        elif (current_ttft_count < prev['ttft_count']
              or current_tpot_count < prev['tpot_count']):
            # Server restarted — reset baselines
            st.session_state.prev_metrics = {
                'ttft_count': current_ttft_count,
                'ttft_sum': current_ttft_sum,
                'tpot_count': current_tpot_count,
                'tpot_sum': current_tpot_sum,
                'e2e_count': current_e2e_count,
                'e2e_sum': current_e2e_sum,
                'gen_tokens_count': current_gen_tokens_count,
                'gen_tokens_sum': current_gen_tokens_sum,
                'prompt_cache_hit': current_cache_hit,
                'prompt_compute': current_compute,
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

# 按照侧边栏设置的时间轮询
time.sleep(refresh_interval)
st.rerun()
