"""
RAG (Retrieval-Augmented Generation) document store and vector database management.

This module provides functionality for building and managing FAISS vector indexes
from documents and web content. It supports multiple document formats including
PDF files and handles text extraction, chunking, and embedding generation.

Key capabilities:
- Text extraction from PDF files using PyPDF2 and pdfplumber fallbacks
- Document chunking with RecursiveCharacterTextSplitter
- FAISS vector index creation and management
- URL content integration into existing indexes
- Uploaded file processing and text extraction
- OpenAI embeddings generation for semantic search

The service supports incremental index updates and provides robust error
handling for various file formats and processing scenarios.
"""

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import logging
import pathlib
import PyPDF2
import pdfplumber
from urllib.parse import urlparse


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text content from various file types.

    Supports PDF files with multiple extraction methods (PyPDF2 primary,
    pdfplumber fallback) and plain text files.

    Parameters
    ----------
    file_path : str
        Path to the file for text extraction

    Returns
    -------
    str
        Extracted text content from the file

    Raises
    ------
    Exception
        If file type is unsupported or text extraction fails
    """
    path = pathlib.Path(file_path)

    if path.suffix.lower() == ".pdf":
        try:

            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            try:

                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                raise ImportError(
                    "PDF support requires PyPDF2 or pdfplumber: pip install PyPDF2"
                )

    elif path.suffix.lower() in [".md", ".txt"]:
        return path.read_text(encoding="utf-8")

    else:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"Unsupported file type: {path.suffix}")


def build_faiss_from_documents(file_paths: list[str], index_path: str) -> str:
    """
    Build FAISS vector index from multiple document files.

    Creates a new FAISS index by extracting text from various document
    formats, chunking the content, and generating embeddings.

    Parameters
    ----------
    file_paths : list[str]
        List of file paths to process and add to the index
    index_path : str
        Directory path where the FAISS index will be saved

    Raises
    ------
    Exception
        If document processing or index creation fails
    """
    texts, metadatas = [], []
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=120)

    for file_path in file_paths:
        try:
            content = extract_text_from_file(file_path)
            if not content.strip():
                logging.warning(f"Warning: No content extracted from {file_path}")
                continue

            chunks = splitter.split_text(content)
            texts += chunks

            file_name = pathlib.Path(file_path).name
            file_type = (
                "user_document"
                if "knowledge_base/user" in file_path
                else "macro_education"
            )

            metadatas += [
                {
                    "source": file_name,
                    "full_path": file_path,
                    "type": file_type,
                    "chunk": i,
                    "total_chunks": len(chunks),
                }
                for i in range(len(chunks))
            ]

            logging.info(f"Processed {file_path}: {len(chunks)} chunks")

        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            continue

    if not texts:
        raise ValueError("No text content found in any files.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    vs = FAISS.from_texts(texts, OpenAIEmbeddings(), metadatas=metadatas)
    vs.save_local(index_path)

    logging.info(
        f"Built FAISS index with {len(texts)} chunks from {len(file_paths)} files"
    )
    return index_path


def add_url_content_to_index(url: str, content: str, index_path: str) -> bool:
    """
    Add web content to existing FAISS vector index.

    Processes web content by chunking it and adding the resulting
    embeddings to an existing FAISS index.

    Parameters
    ----------
    url : str
        Source URL for the content (used in metadata)
    content : str
        Text content to add to the index
    index_path : str
        Path to existing FAISS index directory

    Raises
    ------
    Exception
        If content processing or index update fails
    """
    try:
        existing_vs = FAISS.load_local(
            index_path, OpenAIEmbeddings(), allow_dangerous_deserialization=True
        )
    except FileNotFoundError:
        logging.error("No existing index found, cannot add URL content.")
        return False
    except Exception as e:
        logging.error(f"Error loading existing index: {e}")
        return False

    if not content.strip():
        logging.warning("Warning: No content to add from URL")
        return False

    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=120)
    chunks = splitter.split_text(content)
    domain = urlparse(url).netloc or url
    metadatas = [
        {
            "source": f"{domain}",
            "full_path": url,
            "type": "web_content",
            "chunk": i,
            "total_chunks": len(chunks),
        }
        for i in range(len(chunks))
    ]
    try:
        existing_vs.add_texts(chunks, metadatas=metadatas)
        existing_vs.save_local(index_path)
        logging.info(
            f"Successfully added {len(chunks)} chunks from URL: {url}. "
            f"Metadata: {metadatas}"
        )
        return True
    except Exception as e:
        logging.error(f"Error adding URL content to index: {e}")
        return False


def add_uploaded_files_to_index(uploaded_files: list, index_path: str) -> bool:
    """
    Process uploaded files and add to existing FAISS index.

    Handles file uploads directly from memory without requiring
    disk storage, supporting various file formats.

    Parameters
    ----------
    uploaded_files : list
        Streamlit uploaded file objects or similar file-like objects
    index_path : str
        Path to existing FAISS index directory

    Returns
    -------
    bool
        True if files were successfully processed, False otherwise
    """
    try:
        existing_vs = FAISS.load_local(
            index_path, OpenAIEmbeddings(), allow_dangerous_deserialization=True
        )
    except Exception as e:
        logging.error(f"Error loading existing index: {e}")
        return False

    texts, metadatas = [], []
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=120)

    for uploaded_file in uploaded_files:
        try:
            content = extract_text_from_uploaded_file(uploaded_file)

            if not content.strip():
                logging.warning(
                    f"Warning: No content extracted from {uploaded_file.name}"
                )
                continue

            chunks = splitter.split_text(content)
            texts += chunks

            metadatas += [
                {
                    "source": uploaded_file.name,
                    "full_path": f"uploaded:{uploaded_file.name}",
                    "type": "user_document",
                    "chunk": i,
                    "total_chunks": len(chunks),
                }
                for i in range(len(chunks))
            ]

            logging.info(f"Processed {uploaded_file.name}: {len(chunks)} chunks")

        except Exception as e:
            logging.error(f"Error processing {uploaded_file.name}: {e}")
            continue

    if not texts:
        return False

    try:
        existing_vs.add_texts(texts, metadatas=metadatas)
        existing_vs.save_local(index_path)
        logging.info(f"Successfully added {len(texts)} chunks from uploaded files")
        return True
    except Exception as e:
        logging.error(f"Error adding to index: {e}")
        return False


def extract_text_from_uploaded_file(uploaded_file) -> str:
    """
    Extract text from uploaded file object.

    Supports PDF and text files from Streamlit file upload widgets
    or similar file-like objects.

    Parameters
    ----------
    uploaded_file : Any
        File-like object with name attribute and content access

    Returns
    -------
    str
        Extracted text content from the uploaded file

    Raises
    ------
    ValueError
        If file type is unsupported or text extraction fails
    """
    file_extension = pathlib.Path(uploaded_file.name).suffix.lower()

    if file_extension == ".pdf":
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception:
            try:
                uploaded_file.seek(0)
                with pdfplumber.open(uploaded_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                    return text
            except Exception as e:
                raise ValueError(f"Failed to extract PDF text: {e}")

    elif file_extension in [".md", ".txt"]:
        return uploaded_file.read().decode("utf-8")

    else:
        try:
            return uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"Unsupported file type: {file_extension}")
