import os
import time
from shared_utils_app import get_gemini_client, get_chroma_collection

def ask_my_notes(user_query, api_key, db_path, model_name, collection_name="university_notes", history=None):
    """
    Handles chat history and RAG context with strict citation formatting 
    to trigger UI diagram buttons.
    """
    try:
        # 1. Initialize tools
        client = get_gemini_client(api_key)
        collection, _ = get_chroma_collection(client, db_path, collection_name)

        # 2. Retrieve relevant chunks (RAG)
        results = collection.query(
            query_texts=[user_query],
            n_results=5 # Increased slightly for better context
        )
        
        # 3. Combine text with strict Source and Page citations
        context_parts = []
        if results['documents']:
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                source = meta.get("source", "Unknown")
                page = meta.get("page", "?")
                # Format each chunk clearly for the AI
                context_parts.append(f"[SOURCE: {source}, PAGE/SLIDE: {page}]\n{doc}")
        
        relevant_context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant notes found."
        
        # 4. Construct System Instruction with Strict Citation Rule
        system_instruction = (
            "You are an expert academic tutor for a BSAI student. "
            "Use the provided lecture notes to answer the question. "
            "STRICT CITATION RULE: When you use information from the notes, you MUST include the citation "
            "in this exact format at the end of the relevant sentence: [SOURCE: filename, PAGE/SLIDE: number]. "
            "This format is required to trigger the student's diagram viewer. "
            "If you find OCR content labeled [Diagram Content], describe it to the student.\n\n"
            f"LECTURE NOTES CONTEXT:\n{relevant_context}"
        )

        # 5. Chat Session Loop
        while True:
            try:
                chat_session = client.chats.create(
                    model=model_name,
                    config={"system_instruction": system_instruction},
                    history=history if history else []
                )
                
                response = chat_session.send_message(user_query)
                return response.text
                
            except Exception as e:
                if "429" in str(e):
                    print("\n[Quota Reached] Pausing 60s...")
                    time.sleep(60)
                else:
                    return f"Generation Error: {e}"
                    
    except Exception as e:
        return f"Initialization Error: {e}. Check your API key and DB Path."