# This is where we give the parsed text to llm and ask to give the Skills and Projects


import json
import logging
from config import GEMINI_API_KEY
from schemas import ExtractedResumeData
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

parser = PydanticOutputParser(pydantic_object=ExtractedResumeData)

def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-3.6-flash", 
        temperature=0.1,
        google_api_key= GEMINI_API_KEY
    )

def extract_skills_and_projects(raw_text: str) -> ExtractedResumeData:
    # Truncate text slightly if excessively long to avoid token limits
    truncated_text = raw_text[:4000]

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert technical recruiter. Extract the technical skills and projects "
            "from the resume text. Return strictly valid JSON conforming to the schema.\n{format_instructions}"
        ),
        (
            "human",
            "Resume Text:\n{text}"
        )
    ])

    try:
        llm = get_llm()
        chain = prompt | llm | parser
        result = chain.invoke({
            "text": truncated_text,
            "format_instructions": parser.get_format_instructions()
        })
        return result
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        # Return an empty fallback schema so the pipeline does not crash
        return ExtractedResumeData(skills=[], projects=[])