from typing import List

def chunk_text(
    text:str,
    chunk_size:int=500,
    overlap:int =100,
)-> List[str]:
    """
    Split text into overlapping chunks.

    Args:
    text: The text to chunk
    chunk_size: Number of words per chunk
    overlap: Number of words to overlap between chunks

    Returns:
    List of text chunks
    """

    words=text.split()
    chunks=[]

    start=0
    while start < len(words):
        end=start+chunk_size
        chunk=" ".join(words[start:end])
        chunks.append(chunk)
        start=end-overlap

    return chunks



