import pdfplumber
from pathlib import Path
from typing import List, Generator
from .utils import ProgressBar, stream_output
import logging

class PDFProcessor:
    def __init__(self, chunk_size: int = 4000):
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)

    def extract_text(self, pdf_path: Path) -> str:
        """从PDF文件中提取文本"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                progress = ProgressBar(total_pages, prefix='提取PDF文本:', suffix='完成')
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    text += page_text
                    progress.print(i + 1)
                    stream_output(f"第{i+1}页: 提取了{len(page_text)}个字符")
                    
        except Exception as e:
            raise Exception(f"PDF处理错误: {str(e)}")
        return text

    def split_text(self, text: str) -> Generator[str, None, None]:
        """将文本分割成较小的块"""
        words = text.split()
        current_chunk = []
        current_length = 0

        total_words = len(words)
        progress = ProgressBar(total_words, prefix='分割文本:', suffix='完成')
        processed_words = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > self.chunk_size:
                chunk_text = ' '.join(current_chunk)
                stream_output(f"生成文本块: {len(chunk_text)}字符")
                yield chunk_text
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
            
            processed_words += 1
            progress.print(processed_words)

        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            stream_output(f"生成最后一个文本块: {len(chunk_text)}字符")
            yield chunk_text 