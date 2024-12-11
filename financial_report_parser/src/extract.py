import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List
import sys
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils import setup_logging, stream_output, ProgressBar
from src.llm_processor import LLMProcessor
import colorama
from colorama import Fore, Style

class DataExtractor:
    def __init__(self, api_key: str, api_base: str, db_path: Path):
        self.logger = setup_logging()
        self.llm = LLMProcessor(api_key, api_base)
        self.db_path = db_path
        colorama.init()
        
        # 初始化数据库
        self._init_db()
        
    def process_blocks(self, cut_path: Path, prompts_path: Path, output_path: Path) -> None:
        """处理所有文本块"""
        # 加载数据
        with open(cut_path, 'r', encoding='utf-8') as f:
            blocks = json.load(f)["blocks"]
            
        with open(prompts_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
            
        # 准备输出数据
        output_data = {
            "structured": [],
            "unstructured": []
        }
        
        # 显示进度
        progress = ProgressBar(len(blocks), prefix='处理文本块:', suffix='完成')
        
        # 处理每个块
        for i, block in enumerate(blocks):
            self.logger.info(f"{Fore.GREEN}正在处理第 {i+1}/{len(blocks)} 个文本块{Style.RESET_ALL}")
            
            # 获取该块的提示词
            block_prompts = self._get_block_prompts(prompts, i)
            
            # 提取数据
            data = self._extract_block_data(block, block_prompts)
            
            # 保存数据
            self._save_data(data)
            
            # 更新输出
            if "structured" in data:
                output_data["structured"].extend(data["structured"])
            if "unstructured" in data:
                output_data["unstructured"].extend(data["unstructured"])
            
            progress.print(i + 1)
            
        # 保存输出文件
        self._save_output(output_data, output_path)
        
    def _init_db(self) -> None:
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 创建表
        c.execute('''CREATE TABLE IF NOT EXISTS structured_data
                    (id INTEGER PRIMARY KEY,
                     type TEXT,
                     name TEXT,
                     value REAL,
                     unit TEXT,
                     time TEXT,
                     block_id INTEGER)''')
                     
        c.execute('''CREATE TABLE IF NOT EXISTS unstructured_data
                    (id INTEGER PRIMARY KEY,
                     type TEXT,
                     content TEXT,
                     time TEXT,
                     block_id INTEGER)''')
                     
        conn.commit()
        conn.close()
        
    def _get_block_prompts(self, prompts: Dict[str, Any], block_id: int) -> Dict[str, Any]:
        """获取特定块的提示词"""
        for block_prompt in prompts["blocks"]:
            if block_prompt["block_id"] == block_id:
                return block_prompt["prompts"]
        return prompts["default"]
        
    def _extract_block_data(self, block: Dict[str, Any], prompts: Dict[str, Any]) -> Dict[str, Any]:
        """从文本块中提取数据"""
        self.logger.info(f"\n{Fore.YELLOW}开始处理文本块{Style.RESET_ALL}")
        stream_output(f"\n{Fore.CYAN}文本信息:{Style.RESET_ALL}")
        stream_output(f"标题: {block['h1_title']} - {block['h2_title']}")
        stream_output(f"类型: {block['type']}")
        stream_output(f"长度: {block['length']} 字符")
        
        # 显示使用的提示词
        stream_output(f"\n{Fore.CYAN}使用的提示词:{Style.RESET_ALL}")
        stream_output(json.dumps(prompts, ensure_ascii=False, indent=2))
        
        # 使用LLM提取数据
        stream_output(f"\n{Fore.GREEN}正在调用LLM提取数据...{Style.RESET_ALL}")
        response = self.llm._call_llm(prompts["analyze"]["messages"])
        
        stream_output(f"\n{Fore.GREEN}LLM返回结果:{Style.RESET_ALL}")
        stream_output(response)
        
        try:
            data = json.loads(response)
            normalized = self._normalize_data(data, block["type"])
            
            # 显示提取的数据
            stream_output(f"\n{Fore.CYAN}提取的结构化数据:{Style.RESET_ALL}")
            for item in normalized["structured"]:
                stream_output(f"- {item['name']}: {item['value']} {item['unit']} ({item['time']})")
            
            stream_output(f"\n{Fore.CYAN}提取的非结构化数据:{Style.RESET_ALL}")
            for item in normalized["unstructured"]:
                stream_output(f"- [{item['type']}] {item['content']} ({item['time']})")
            
            return normalized
        except json.JSONDecodeError:
            self.logger.error(f"{Fore.RED}JSON解析失败: {response}{Style.RESET_ALL}")
            return {"structured": [], "unstructured": []}
            
    def _normalize_data(self, data: Dict[str, Any], block_type: str) -> Dict[str, Any]:
        """标准化数据格式"""
        normalized = {
            "structured": [],
            "unstructured": []
        }
        
        # 处理结构化数据
        if "structured" in data:
            for item in data["structured"]:
                normalized["structured"].append({
                    "type": block_type,
                    "name": item.get("name", ""),
                    "value": item.get("value"),
                    "unit": item.get("unit", ""),
                    "time": item.get("time", "")
                })
                
        # 处理非结构化数据
        if "unstructured" in data:
            for item in data["unstructured"]:
                normalized["unstructured"].append({
                    "type": block_type,
                    "content": item.get("content", ""),
                    "time": item.get("time", "")
                })
                
        return normalized
        
    def _save_data(self, data: Dict[str, Any]) -> None:
        """保存数据到数据库"""
        stream_output(f"\n{Fore.YELLOW}正在保存数据到数据库...{Style.RESET_ALL}")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 保存结构化数据
        for item in data.get("structured", []):
            c.execute('''INSERT INTO structured_data
                        (type, name, value, unit, time)
                        VALUES (?, ?, ?, ?, ?)''',
                     (item["type"], item["name"], item["value"],
                      item["unit"], item["time"]))
            stream_output(f"保存结构化数据: {item['name']}")
        
        # 保存非结构化数据
        for item in data.get("unstructured", []):
            c.execute('''INSERT INTO unstructured_data
                        (type, content, time)
                        VALUES (?, ?, ?)''',
                     (item["type"], item["content"], item["time"]))
            stream_output(f"保存非结构化数据: {item['type']}")
        
        conn.commit()
        conn.close()
        stream_output(f"{Fore.GREEN}数据保存完成{Style.RESET_ALL}")
        
    def _save_output(self, data: Dict[str, Any], output_path: Path) -> None:
        """保存输出文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # 设置路径
    base_dir = Path(__file__).parent.parent
    cut_path = base_dir / "data" / "cut.json"
    prompts_path = base_dir / "data" / "prompts.json"
    output_path = base_dir / "data" / "output.json"
    db_path = base_dir / "data" / "extracted.db"
    
    # 从配置文件获取API配置
    from config.settings import API_KEY, API_BASE
    
    # 创建提取器并处理
    extractor = DataExtractor(API_KEY, API_BASE, db_path)
    extractor.process_blocks(cut_path, prompts_path, output_path)

if __name__ == "__main__":
    main() 