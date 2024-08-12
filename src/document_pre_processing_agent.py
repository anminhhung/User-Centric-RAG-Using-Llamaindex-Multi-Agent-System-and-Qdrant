from dotenv import load_dotenv
load_dotenv()
from typing import List
import pprint
from colorama import Fore, Back, Style

from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI 
from llama_index.agent.openai import OpenAIAgent

import os
import json
import re
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader



def documents_transformation(input_dir: str):
    print(f"Input directory: {input_dir}")
    documents = SimpleDirectoryReader(input_dir=input_dir).load_data()
    print(f"Loaded {len(documents)} documents")
    transformed_documents = []
    for doc in documents:
        transformed_content = doc.get_content().lower()
        transformed_content = re.sub(r'\s+', ' ', transformed_content)
        transformed_content = re.sub(r'[^\w\s]', '', transformed_content)
        transformed_documents.append(Document(text=transformed_content, metadata=doc.metadata))
    print(f"Transformed {len(documents)} documents")
    return transformed_documents

def split_documents_into_nodes(documents, chunk_size, chunk_overlap):
    try:
        splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        nodes = splitter.get_nodes_from_documents(documents)
        return nodes
    except Exception as e:
        print(f"Error splitting documents into nodes: {e}")
        return []

def save_nodes(nodes):
    try:
        output_file = r"..\data\nodes.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        nodes_dict = [node.dict() for node in nodes]
        with open(output_file, 'w') as file:
            json.dump(nodes_dict, file, indent=4)
        print(f"Saved nodes to {output_file}")
    except Exception as e:
        print(f"Error saving nodes to file: {e}")
    
class preprocess_docs:
    def __init__(self, state: dict):
        self.state = state
        self.input_dir = state.get('input_dir')
        self.chunk_size = state.get('chunk_size')
        self.chunk_overlap = state.get('chunk_overlap')
        
    def process_documents(self) -> None:
        input_dir = rf"{self.input_dir}"
        documents = documents_transformation(self.input_dir)
        print("Document Transformation is done")
        nodes = split_documents_into_nodes(documents, self.chunk_size, self.chunk_overlap)
        print("Transformed into nodes")
        save_nodes(nodes)
        print("saved the nodes")

def DocumentPreprocessingAgent(state: dict) -> OpenAIAgent:

    def has_input_dir(input_dir) -> bool:
        """Useful for checking if the user has specified an input file directory."""
        print("Orchestrator checking if input file directory is specified")
        state['input_dir'] = input_dir
        return (state["input_dir"] is not None)

    def has_chunk_size(chunk_size) -> bool:
        """Useful for checking if the user has specified a chunk size."""
        print("Orchestrator checking if chunk size is specified")
        state['chunk_size'] = chunk_size
        return (state["chunk_size"] is not None)

    def has_chunk_overlap(chunk_overlap) -> bool:
        """Useful for checking if the user has specified a chunk overlap."""
        print("Orchestrator checking if chunk overlap is specified")
        state['chunk_overlap'] = chunk_overlap
        return (state["chunk_overlap"] is not None)

    def done() -> None:
        """When you saved node to the output file, call this tool."""
        print("Document preprocessing is complete")
        state["current_speaker"] = None
        state["just_finished"] = True
    
    doc_processor = preprocess_docs(state)
    tools = [
        FunctionTool.from_defaults(fn = has_input_dir),
        FunctionTool.from_defaults(fn = has_chunk_size),
        FunctionTool.from_defaults(fn = has_chunk_overlap),
        FunctionTool.from_defaults(fn=doc_processor.process_documents),
        FunctionTool.from_defaults(fn=done),
    ]

    system_prompt = (f"""
    You are a helpful assistant that is preprocessing documents for a retrieval-augmented generation (RAG) system.
    Your task is to preprocess the documents, split them into nodes, and save the nodes to a file.
    To do this, you need to know the path to the directory containing the PDF files, the chunk size, and the chunk overlap.
    * If they want to pre-process the documents, but has_input_dir, has_chunk_size, or has_chunk_overlap returns false, Then You can ask the user to supply these.
    
    If the user supplies the input_dir, chunk_size, and chunk_overlap, call the tool "doc_processor.process_documents" with these parameters to perform transformation of documents, split them into nodes, and save the nodes to a file.
    The current user state is:
    {pprint.pformat(state, indent=4)}
    When you have transformed the documents, split them into nodes, and saved the nodes to a file, call the tool "done" to signal that you are done.
    If the user asks to do anything other than preprocess the documents, call the tool "done" to signal some other agent should help.
    """)


    return OpenAIAgent.from_tools(
        tools,
        llm=OpenAI(model="gpt-3.5-turbo"),
        system_prompt=system_prompt,
    )


if __name__ == '__main__':
    state = {   
    }
    agent = DocumentPreprocessingAgent(state)
    response = agent.chat("I want to pre-process the documents in C:\\Users\\pavan\\Desktop\\Generative AI\\RAG-Automation-Using-Llamaindex-Agents-and-Qdrant\\data with a chunk size of 800 and a chunk overlap of 50")
