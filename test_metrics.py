import asyncio
from dotenv import load_dotenv
load_dotenv()
from langfuse import observe, get_client

@observe()
def test_func():
    trace_id = get_client().get_current_trace_id()
    observation_id = get_client().get_current_observation_id()
    print(f"Trace ID: {trace_id}")
    print(f"Observation ID: {observation_id}")
    get_client().score_current_trace(name="test_score", value=1)
    get_client().score_current_trace(name="failure", value=0)

test_func()
get_client().flush()
