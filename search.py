import streamlit as st

def search_web(query, max_results=8):
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(
                f"{query} harga jual vendor Jakarta",
                region="id-id",
                max_results=max_results,
            ))
        parsed = []
        for r in results:
            parsed.append({
                "title": r.get("title", ""),
                "body": r.get("body", ""),
                "url": r.get("href", ""),
            })
        return parsed
    except Exception as e:
        st.warning(f"Pencarian gagal: {e}")
        return []

def search_marketplace(query, max_results=5):
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(
                f"{query} site:tokopedia.com OR site:shopee.co.id OR site:bukalapak.com harga",
                region="id-id",
                max_results=max_results,
            ))
        parsed = []
        for r in results:
            parsed.append({
                "title": r.get("title", ""),
                "body": r.get("body", ""),
                "url": r.get("href", ""),
            })
        return parsed
    except Exception as e:
        st.warning(f"Pencarian marketplace gagal: {e}")
        return []
