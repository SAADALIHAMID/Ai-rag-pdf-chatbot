from typing import List, Dict, Any, AsyncGenerator, Optional
import os
import json
import logging
import asyncio
from groq import Groq
from app.config import settings

logger = logging.getLogger(__name__)

class GroqLLMClient:
    def __init__(self):
        self._client = None

    def get_client(self) -> Optional[Groq]:
        api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        if not api_key or api_key.strip() in ["your_groq_api_key_here", ""]:
            return None
        if self._client is None:
            self._client = Groq(api_key=api_key.strip())
        return self._client

    def format_prompt(self, query: str, top_chunks: List[Dict[str, Any]]) -> str:
        """
        Formats the strict guardrail prompt with verified Top 3 reranked context chunks.
        """
        formatted_chunks = []
        for i, chunk in enumerate(top_chunks):
            chunk_header = f"[Chunk {i+1} | Source: {chunk.get('filename')} | Page: {chunk.get('page_number', 'N/A')} | Score: {chunk.get('rerank_score', chunk.get('score', 0.0)):.3f}]"
            formatted_chunks.append(f"{chunk_header}\n{chunk.get('text', '')}")

        context_body = "\n---\n".join(formatted_chunks) if formatted_chunks else "NO CONTEXT AVAILABLE."

        prompt = settings.STRICT_PROMPT_TEMPLATE.format(
            context=context_body,
            query=query
        )
        return prompt

    async def stream_answer(
        self,
        query: str,
        top_chunks: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """
        Streams response tokens in real-time from Groq API using Llama-3.3-70b-versatile.
        Strictly obeys the absence rule and guardrail prompt, with conversational greeting handling.
        """
        # Conversational Greeting Handler: If user sends a greeting, reply politely instead of absence refusal
        clean_q = query.strip().lower()
        greetings = {"hi", "hy", "hello", "hey", "salam", "assalam o alaikum", "aoa", "greetings", "good morning", "good evening", "who are you", "help", "what can you do"}
        if clean_q in greetings or (len(clean_q.split()) <= 2 and any(clean_q.startswith(g) for g in ["hi", "hy", "hello", "hey", "salam"])):
            doc_name = top_chunks[0].get("filename") if top_chunks else "your document"
            greeting_msg = (
                f"Hello! 👋 I am your Document AI Assistant, operating under strict mathematical fact-grounding.\n\n"
                f"I am actively connected to **{doc_name}**. Ask me any question (e.g. summaries, key requirements, or specific prompt guidelines) and I will provide answers directly from the text with verified citations!"
            )
            for word in greeting_msg.split(" "):
                yield word + " "
                await asyncio.sleep(0.015)
            return

        # If no chunks were found at all
        if not top_chunks:
            yield "Mujhe is ka jawab uploaded document me nahi mila."
            return

        client = self.get_client()
        if client is None:
            # Helpful fallback stream for testing before putting key
            notice = (
                "[Notice: GROQ_API_KEY is not configured yet in .env]\n\n"
                "Top verified context retrieved from document:\n\n"
            )
            for token in notice.split(" "):
                yield token + " "
                await asyncio.sleep(0.02)

            for i, chunk in enumerate(top_chunks):
                excerpt = f"• **Page {chunk.get('page_number', '1')}**: \"{chunk.get('text', '')[:200]}...\"\n"
                for word in excerpt.split(" "):
                    yield word + " "
                    await asyncio.sleep(0.01)

            reminder = "\n\n👉 *Please add your free `GROQ_API_KEY` into the `.env` file to enable live Groq Llama-3.3-70b streaming responses!*"
            yield reminder
            return

        prompt = self.format_prompt(query, top_chunks)

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=settings.GROQ_MODEL,
                temperature=0.1,  # Low temperature for strict factual grounding & zero hallucination
                max_tokens=2048,
                stream=True,
            )

            for chunk in chat_completion:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except Exception as e:
            logger.error(f"Error invoking Groq API: {e}", exc_info=True)
            yield f"\n[Groq API Error: {str(e)}]"

# Global singleton
llm_client = GroqLLMClient()
