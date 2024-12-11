import pdfplumber
import json
import re
from pathlib import Path
from typing import List, Dict, Any
import sys
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils import ProgressBar, stream_output, setup_logging

class PDFCutter:
    def __init__(self):
        """初始化PDF切分器"""
        self.logger = setup_logging()
        self.logger.info("初始化PDF切分器")

    def process_pdf(self, pdf_path: Path, output_path: Path) -> None:
        """处理PDF文件并保存切分结果"""
        self.logger.info(f"开始处理PDF文件: {pdf_path}")
        text_blocks = self._extract_text_blocks(pdf_path)
        self._save_blocks(text_blocks, output_path)
        self.logger.info(f"处理完成，共生成 {len(text_blocks)} 个文本块")

    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本分割成句子"""
        sentence_ends = '。！？；!?;\n'
        text = text.replace('\r\n', '\n').strip()
        text = ' '.join(text.split())
        
        sentences = []
        start = 0
        
        for i, char in enumerate(text):
            if char in sentence_ends:
                sentence = text[start:i+1].strip()
                if sentence:
                    sentences.append(sentence)
                start = i + 1
        
        if start < len(text):
            sentence = text[start:].strip()
            if sentence:
                sentences.append(sentence)
        
        return sentences

    def _extract_text_blocks(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """从PDF中提取文本块"""
        blocks = []
        current_title = {"h1": "", "h2": ""}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                progress = ProgressBar(total_pages, prefix='提取PDF页面:', suffix='完成')
                
                for i, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text() or ""
                        lines = text.split('\n')
                        
                        for line in lines:
                            if self._is_h1_title(line):
                                current_title["h1"] = line
                                current_title["h2"] = ""
                                continue
                            
                            if self._is_h2_title(line):
                                current_title["h2"] = line
                                continue
                            
                            sentences = self._split_into_sentences(line)
                            for sentence in sentences:
                                if sentence:
                                    block = self._create_block(sentence, current_title, page.page_number)
                                    blocks.append(block)
                                    
                                    if len(blocks) % 100 == 0:
                                        self.logger.info(f"已生成 {len(blocks)} 个文本块")
                        
                        progress.print(i + 1)
                    except Exception as e:
                        self.logger.error(f"处理第 {i+1} 页时出错: {str(e)}")
                        continue
                
                self.logger.info(f"PDF处理完成，共生成 {len(blocks)} 个文本块")
        except Exception as e:
            self.logger.error(f"处理PDF文件时出错: {str(e)}")
            raise
        
        return blocks

    def _create_block(self, sentence: str, titles: Dict[str, str], page: int) -> Dict[str, Any]:
        """创建文本块"""
        text = self._clean_text(sentence)
        return {
            "text": text,
            "length": len(text),
            "page": page,
            "h1_title": titles["h1"],
            "h2_title": titles["h2"],
            "type": self._guess_block_type(text, titles)
        }

    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        text = ' '.join(text.split())
        punctuation_map = {
            ',': '，',
            '.': '。',
            ':': '：',
            ';': '；',
            '?': '？',
            '!': '！',
            '(': '（',
            ')': '）'
        }
        for en, cn in punctuation_map.items():
            text = text.replace(en, cn)
        return text.strip()

    def _save_blocks(self, blocks: List[Dict[str, Any]], output_path: Path) -> None:
        """保存文本块"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "total_blocks": len(blocks),
                "blocks": blocks
            }, f, ensure_ascii=False, indent=2)

    def _is_h1_title(self, line: str) -> bool:
        """判断是否为一级标题"""
        patterns = [
            r'^第[一二三四五六七八九十]+[章节]',
            r'^\d+\.\s*[A-Z\u4e00-\u9fa5]',
            r'^[一二三四五六七八九十]+、',
            r'^[（(]\s*[一二三四五六七八九十]+\s*[)）]'
        ]
        return any(re.match(pattern, line.strip()) for pattern in patterns)

    def _is_h2_title(self, line: str) -> bool:
        """判断是否为二级标题"""
        patterns = [
            r'^\d+\.\d+\s+',
            r'^（[一二三四五六七八九十]+）',
            r'^\([1-9]\)',
            r'^[（(]\s*\d+\s*[)）]'
        ]
        return any(re.match(pattern, line.strip()) for pattern in patterns)

    def _guess_block_type(self, text: str, titles: Dict[str, str]) -> str:
        """猜测文本块类型"""
        keywords = {
            "financial": ["财务", "收入", "利润", "资产", "负债"],
            "business": ["业务", "客户", "市场", "产品", "服务"],
            "risk": ["风险", "合规", "监管", "控制", "审计"],
            "strategy": ["战略", "规划", "目标", "展望", "计划"],
            "governance": ["治理", "董事会", "股东", "管理层", "组织"],
            "other": []
        }
        text_full = f"{titles['h1']} {titles['h2']} {text}"
        for type_name, type_keywords in keywords.items():
            if any(k in text_full for k in type_keywords):
                return type_name
        return "other"

def main():
    base_dir = Path(__file__).parent.parent
    pdf_path = base_dir / "data" / "annual" / "2023年报.pdf"
    output_path = base_dir / "data" / "cut.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cutter = PDFCutter()
    cutter.process_pdf(pdf_path, output_path)

if __name__ == "__main__":
    main() 