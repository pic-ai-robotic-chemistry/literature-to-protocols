from langchain.document_loaders import PyPDFLoader, UnstructuredFileLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import TokenTextSplitter, RecursiveCharacterTextSplitter, CharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain.document_loaders import WikipediaLoader
files_path = ["/mnt/d/Phd/llm_zero_to_hero/pdf-analysis/files/2404.02183v1.pdf","/mnt/d/Phd/llm_zero_to_hero/pdf-analysis/files/2409.03659v2.pdf"]
docs = []
for file_path in files_path:
    loader = PyPDFLoader(file_path)
    docs = docs + loader.load()

text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24) # 512 tokens per chunk, 24 token overlap
documents = text_splitter.split_documents(docs[:]) # Split the first 3 documents

#####################################################################################################
chunk_size = 20
chunk_overlap = 4

# 
r_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size, chunk_overlap=chunk_overlap)
c_splitter = CharacterTextSplitter(
    chunk_size=chunk_size, chunk_overlap=chunk_overlap)
 
text = "hello world, how about you? thanks, I am fine.  the machine learning class. So what I wanna do today is just spend a little time going over the logistics of the class, and then we'll start to talk a bit about machine learning"
rs = r_splitter.split_text(text)
print(type(rs))
print(len(rs))
for item in rs:
    print(item)
#####################################################################################################
text = "hello world, how about you? thanks, I am fine.  the machine learning class. So what I wanna do today is just spend a little time going over the logistics of the class, and then we'll start to talk a bit about machine learning"
token_splitter = TokenTextSplitter(chunk_size=20, chunk_overlap=5)
rs = token_splitter.split_text(text)
print(len(rs))
for item in rs:
    print(item)
#####################################################################################################
 
markdown_document = "# Intro \n\n    ## History \n\n Markdown[9] is a lightweight markup language for creating formatted text using a plain-text editor. John Gruber created Markdown in 2004 as a markup language that is appealing to human readers in its source code form.[9] \n\n Markdown is widely used in blogging, instant messaging, online forums, collaborative software, documentation pages, and readme files. \n\n ## Rise and divergence \n\n As Markdown popularity grew rapidly, many Markdown implementations appeared, driven mostly by the need for \n\n additional features such as tables, footnotes, definition lists,[note 1] and Markdown inside HTML blocks. \n\n #### Standardization \n\n From 2012, a group of people, including Jeff Atwood and John MacFarlane, launched what Atwood characterised as a standardisation effort. \n\n ## Implementations \n\n Implementations of Markdown are available for over a dozen programming languages."
 
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]
markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers = False
    )
rs = markdown_splitter.split_text(markdown_document)
# print(len(rs))
# for item in rs:
#     print(str(item))
#     print(type(str(item)))
#     break
for item in rs:
    print(item.metadata)
    (k,v), = item.metadata.items()
    print(k,v)
    print(item.page_content)
    break
# rs[0].metadata['Header 3']='1'
# rs[0].page_content='1'
# rs

#####################################################################################################
chunk_size = 1024
chunk_overlap = 30
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size, chunk_overlap=chunk_overlap
)
# Split
splits = text_splitter.split_documents(rs)
# for item in splits:
#     print(item)
splits
#####################################################################################################
# Read the wikipedia article
raw_documents = WikipediaLoader(query="Elizabeth I").load()
# Define chunking strategy

text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24) # 512 tokens per chunk, 24 token overlap
documents = text_splitter.split_documents(raw_documents[:3]) # Split the first 3 documents

documents