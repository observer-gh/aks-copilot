EXPLAIN_VIOLATION_TEMPLATE = """You are a Kubernetes migration assistant.\nExplain why the following rule matters and how to fix it succinctly.\nRule ID: {id}\nResource: {resource}\nFound: {found}\nExpected: {expected}\nReturn a concise paragraph (<= 8 sentences)."""

SUGGEST_IMPROVEMENT_TEMPLATE = """You are a Kubernetes migration assistant.\nGiven the violation details, emit ONLY a JSON object with keys: type, ops.\nEach op: {{"op":"add|replace", "path":"/json/pointer", "value": <object>}}.\nViolation: {violation_json}\nRespond with JSON only, no commentary."""
