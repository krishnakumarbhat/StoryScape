import os

import requests


def generate_with_lang_stack(context: str, user_prompt: str) -> str:
    """Generate story text using LangGraph/LlamaIndex/Chroma when available.

    Falls back to deterministic template text if optional libraries are missing
    or runtime setup is incomplete.
    """
    gemini_key = os.getenv('GEMINI_API_KEY', '').strip()
    if gemini_key:
        prompt = (
            "You are a creative story engine. Continue the story in 3-6 lines.\n"
            f"Context:\n{context or 'No prior context.'}\n\n"
            f"User prompt:\n{user_prompt}"
        )

        model_candidates = [
            os.getenv('GEMINI_TEXT_MODEL', 'gemini-3-flash').strip(),
            os.getenv('GEMINI_TEXT_FALLBACK_MODEL', 'gemini-2.0-flash-exp').strip(),
        ]

        for model in model_candidates:
            if not model:
                continue
            endpoint = (
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                f"?key={gemini_key}"
            )
            payload = {
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'temperature': 0.9},
            }

            try:
                response = requests.post(endpoint, json=payload, timeout=30)
                if not response.ok:
                    continue
                data = response.json()
                candidates = data.get('candidates', [])
                for candidate in candidates:
                    parts = candidate.get('content', {}).get('parts', [])
                    for part in parts:
                        text = (part.get('text') or '').strip()
                        if text:
                            return text
            except Exception:
                continue

    try:
        import chromadb
        from llama_index.core import Document, VectorStoreIndex

        _ = chromadb.EphemeralClient()
        documents = [Document(text=context or "No prior context.")]
        index = VectorStoreIndex.from_documents(documents)
        query_engine = index.as_query_engine()
        answer = query_engine.query(f"Continue this story beat: {user_prompt}")
        generated = str(answer).strip()
        if generated:
            return generated
    except Exception:
        pass

    try:
        from langgraph.graph import END, StateGraph

        class State(dict):
            pass

        def compose_node(state: State):
            return {
                'output': (
                    "Story continuation based on prompt: "
                    f"{state['prompt']}. Context summary: {state['context'][:120]}"
                )
            }

        graph = StateGraph(State)
        graph.add_node('compose', compose_node)
        graph.set_entry_point('compose')
        graph.add_edge('compose', END)
        app = graph.compile()
        output = app.invoke({'prompt': user_prompt, 'context': context})
        if output.get('output'):
            return output['output']
    except Exception:
        pass

    return (
        f"Based on prior events ({context[:80]}...), "
        f"the story continues with: {user_prompt}."
    )
