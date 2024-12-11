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
    def __init__(self, min_size: int = 500, max_size: int = 800):
        """
        初始化PDF切分器
        
        Args:
            min_size: 最小文本块大小（字符数），默认500
            max_size: 最大文本块大小（字符数），默认800
        """
        self.min_size = min_size
        self.max_size = max_size
        self.logger = setup_logging()
        self.logger.info(f"初始化PDF切分器: 最小块大小={min_size}, 最大块大小={max_size}")
        
    def process_pdf(self, pdf_path: Path, output_path: Path) -> None:
        """处理PDF文件并保存切分结果"""
        self.logger.info(f"开始处理PDF文件: {pdf_path}")
        
        # 提取文本和结构
        text_blocks = self._extract_text_blocks(pdf_path)
        
        # 保存结果
        self._save_blocks(text_blocks, output_path)
        
        self.logger.info(f"处理完成，共生成 {len(text_blocks)} 个文本块")
        
    def _extract_text_blocks(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """从PDF中提取文本块"""
        blocks = []
        current_title = {"h1": "", "h2": ""}
        current_block = []
        current_page = None
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            progress = ProgressBar(total_pages, prefix='提取PDF页面:', suffix='完成')
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                lines = text.split('\n')
                
                for line in lines:
                    # 检测标题
                    if self._is_h1_title(line):
                        # 保存当前块（如果长度合适）
                        if current_block:
                            block_text = '\n'.join(current_block)
                            if len(block_text) >= self.min_size:
                                blocks.append(self._create_block(
                                    current_block, current_title, current_page or page.page_number
                                ))
                                current_block = []
                        
                        current_title["h1"] = line
                        current_title["h2"] = ""
                        current_page = page.page_number
                        
                    elif self._is_h2_title(line):
                        # 保存当前块（如果长度合适）
                        if current_block:
                            block_text = '\n'.join(current_block)
                            if len(block_text) >= self.min_size:
                                blocks.append(self._create_block(
                                    current_block, current_title, current_page or page.page_number
                                ))
                                current_block = []
                        
                        current_title["h2"] = line
                        current_page = page.page_number
                        
                    else:
                        current_block.append(line)
                        block_text = '\n'.join(current_block)
                        
                        # 检查是否需要切分
                        if len(block_text) >= self.max_size:
                            # 尝试在句子边界切分
                            split_point = self._find_sentence_boundary(block_text, self.min_size)
                            if split_point > 0:
                                first_part = current_block[:split_point]
                                if len('\n'.join(first_part)) >= self.min_size:
                                    blocks.append(self._create_block(
                                        first_part, current_title, current_page or page.page_number
                                    ))
                                current_block = current_block[split_point:]
                                self.logger.debug(f"文本块已切分: {len(first_part)}字符")
                
                # 更新进度
                progress.print(i + 1)
                self.logger.info(f"第 {i+1}/{total_pages} 页: 已生成 {len(blocks)} 个文本块")
                current_page = page.page_number
        
        # 处理最后的文本块
        if current_block:
            block_text = '\n'.join(current_block)
            if len(block_text) >= self.min_size:
                blocks.append(self._create_block(
                    current_block, current_title, current_page
                ))
        
        # 显示切分结果统计
        self._show_blocks_stats(blocks)
        return blocks
    
    def _find_sentence_boundary(self, text: str, min_size: int) -> int:
        """在文本中找到合适的句子分割点"""
        # 句子结束标记
        sentence_ends = ['. ', '。', '！', '? ', '？', '\n\n']
        
        # 从min_size位置开始向后查找最近的句子结束点
        for i in range(min_size, len(text)):
            for end in sentence_ends:
                if text[i:i+len(end)] == end:
                    return i + len(end)
        
        # 如果找不到合适的分割点，返回-1
        return -1
    
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
    
    def _create_block(self, lines: List[str], titles: Dict[str, str], page: int) -> Dict[str, Any]:
        """创建文本块"""
        text = '\n'.join(lines)
        return {
            "text": text,
            "length": len(text),
            "page": page,
            "h1_title": titles["h1"],
            "h2_title": titles["h2"],
            "type": self._guess_block_type(text, titles)
        }
    
    def _guess_block_type(self, text: str, titles: Dict[str, str]) -> str:
        """猜测文本块类型"""
        # 可以根据标题和内容特征判断类型
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
    
    def _save_blocks(self, blocks: List[Dict[str, Any]], output_path: Path) -> None:
        """保存文本块"""
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "total_blocks": len(blocks),
                "blocks": blocks
            }, f, ensure_ascii=False, indent=2)
    
    def _show_blocks_stats(self, blocks: List[Dict[str, Any]]) -> None:
        """显示文本块统计信息"""
        total_blocks = len(blocks)
        total_chars = sum(block["length"] for block in blocks)
        avg_size = total_chars / total_blocks if total_blocks > 0 else 0
        
        self.logger.info(f"\n{'='*50}")
        self.logger.info("文本块统计信息:")
        self.logger.info(f"总块数: {total_blocks}")
        self.logger.info(f"总字符数: {total_chars}")
        self.logger.info(f"平均块大小: {avg_size:.2f} 字符")
        self.logger.info(f"最小块大小: {min(block['length'] for block in blocks)} 字符")
        self.logger.info(f"最大块大小: {max(block['length'] for block in blocks)} 字符")
        self.logger.info(f"{'='*50}\n")

def main():
    # 设置路径
    base_dir = Path(__file__).parent.parent
    pdf_path = base_dir / "data" / "annual" / "2023年报.pdf"
    output_path = base_dir / "data" / "cut.json"
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建切分器并处理
    cutter = PDFCutter()
    cutter.process_pdf(pdf_path, output_path)

if __name__ == "__main__":
    main() 