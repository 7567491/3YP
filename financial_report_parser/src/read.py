import json
from pathlib import Path
from typing import Dict, Any, List
import sys
import os
import sqlite3

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils import setup_logging, stream_output, ProgressBar
from src.llm_processor import LLMProcessor
import colorama
from colorama import Fore, Style

class TextAnalyzer:
    def __init__(self, api_key: str, api_base: str):
        self.logger = setup_logging()
        self.llm = LLMProcessor(api_key, api_base)
        colorama.init()
        
        # 初始化数据库连接
        db_path = Path(__file__).parent.parent / "data" / "analysis.db"
        self._init_db(db_path)
        
    def _init_db(self, db_path: Path) -> None:
        """初始化数据库"""
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 创建分析结果表
        c.execute('''CREATE TABLE IF NOT EXISTS block_analysis
                    (id INTEGER PRIMARY KEY,
                     block_id INTEGER,
                     h1_title TEXT,
                     h2_title TEXT,
                     text_type TEXT,
                     main_topic TEXT,
                     raw_analysis TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # 创建结构化数据表
        c.execute('''CREATE TABLE IF NOT EXISTS structured_data_analysis
                    (id INTEGER PRIMARY KEY,
                     block_id INTEGER,
                     name TEXT,
                     type TEXT,
                     format TEXT,
                     time_info TEXT,
                     importance INTEGER,
                     context TEXT,
                     FOREIGN KEY(block_id) REFERENCES block_analysis(block_id))''')
        
        # 创建非结构化数据表
        c.execute('''CREATE TABLE IF NOT EXISTS unstructured_data_analysis
                    (id INTEGER PRIMARY KEY,
                     block_id INTEGER,
                     type TEXT,
                     description TEXT,
                     importance INTEGER,
                     related_topics TEXT,
                     time_sensitivity TEXT,
                     FOREIGN KEY(block_id) REFERENCES block_analysis(block_id))''')
                     
        conn.commit()
        conn.close()

    def _fix_json(self, json_str: str) -> str:
        """尝试修复不完整的JSON"""
        try:
            # 首先尝试找到最后一个完整的对象
            last_complete_obj = -1
            open_count = 0
            in_string = False
            escape = False
            
            for i, char in enumerate(json_str):
                if char == '"' and not escape:
                    in_string = not in_string
                elif not in_string:
                    if char == '{':
                        open_count += 1
                    elif char == '}':
                        open_count -= 1
                        if open_count == 0:
                            last_complete_obj = i
                
                escape = char == '\\' and not escape
            
            if last_complete_obj > 0:
                # 找到最后一个完整的对象，截取到这里
                json_str = json_str[:last_complete_obj+1]
                
                # 检查是否需要补充结构
                if '"unstructured_data": [' in json_str and not '"extraction_suggestion"' in json_str:
                    # 补充unstructured_data数组的结束
                    json_str = json_str.rstrip('}') + '''
                ],
                "extraction_suggestion": {
                    "prompt_design": {
                        "system_role": "information_extractor",
                        "key_focus": "data_accuracy",
                        "special_requirements": "none"
                    },
                    "data_format": {
                        "suggested_structure": "json",
                        "field_definitions": "standard",
                        "validation_rules": "basic"
                    },
                    "extraction_strategy": {
                        "approach": "systematic",
                        "key_steps": ["identify", "extract", "validate"],
                        "potential_challenges": "none"
                    }
                }
            }'''
                
                # 验证修复后的JSON
                try:
                    json.loads(json_str)
                    self.logger.info(f"{Fore.GREEN}JSON修复成功{Style.RESET_ALL}")
                    return json_str
                except json.JSONDecodeError as e:
                    self.logger.warning(f"修复后的JSON仍然无效: {str(e)}")
            
            # 如果上述修复失败，尝试更简单的修复
            if '"structured_data": [' in json_str:
                # 找到最后一个完整的structured_data项
                last_item_end = json_str.rfind('},\n            {')
                if last_item_end > 0:
                    json_str = json_str[:last_item_end+1] + '''
                ],
                "unstructured_data": [],
                "extraction_suggestion": {
                    "prompt_design": {
                        "system_role": "information_extractor",
                        "key_focus": "data_accuracy",
                        "special_requirements": "none"
                    },
                    "data_format": {
                        "suggested_structure": "json",
                        "field_definitions": "standard",
                        "validation_rules": "basic"
                    },
                    "extraction_strategy": {
                        "approach": "systematic",
                        "key_steps": ["identify", "extract", "validate"],
                        "potential_challenges": "none"
                    }
                }
            }'''
            
            # 验证最终的JSON
            try:
                json.loads(json_str)
                self.logger.info(f"{Fore.GREEN}JSON修复成功（基础修复）{Style.RESET_ALL}")
                return json_str
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON修复失败: {str(e)}")
                self.logger.error(f"修复后的内容:\n{json_str}")
                raise
            
        except Exception as e:
            self.logger.error(f"JSON修复过程出错: {str(e)}")
            raise

    def _save_analysis_result(self, block_id: int, block: Dict[str, Any], analysis: Dict[str, Any]) -> None:
        """保存分析结果到数据库和JSON文件"""
        try:
            # 尝试解析LLM返回的JSON
            if isinstance(analysis.get("raw_analysis"), str):
                try:
                    parsed_analysis = json.loads(analysis["raw_analysis"])
                except json.JSONDecodeError as e:
                    self.logger.warning(f"{Fore.YELLOW}JSON解析失败，尝试修复...{Style.RESET_ALL}")
                    fixed_json = self._fix_json(analysis["raw_analysis"])
                    try:
                        parsed_analysis = json.loads(fixed_json)
                        self.logger.info(f"{Fore.GREEN}JSON修复成功{Style.RESET_ALL}")
                    except json.JSONDecodeError as e:
                        self.logger.error(f"{Fore.RED}JSON修复失败: {str(e)}{Style.RESET_ALL}")
                        self.logger.error(f"{Fore.RED}原始内容: {analysis['raw_analysis']}{Style.RESET_ALL}")
                        raise
            else:
                self.logger.error(f"{Fore.RED}无效的分析结果格式{Style.RESET_ALL}")
                return

            # 保存到JSON文件
            analysis_path = Path(__file__).parent.parent / "data" / "read.json"
            
            # 加载现有数据或创建新的
            if analysis_path.exists():
                with open(analysis_path, 'r', encoding='utf-8') as f:
                    all_analysis = json.load(f)
            else:
                all_analysis = {"blocks": []}
            
            # 添加新的分析结果
            block_analysis = {
                "block_id": block_id,
                "h1_title": block["h1_title"],
                "h2_title": block["h2_title"],
                "analysis": parsed_analysis
            }
            
            # 检查是否已存在相同block_id的分析
            for i, existing in enumerate(all_analysis["blocks"]):
                if existing["block_id"] == block_id:
                    all_analysis["blocks"][i] = block_analysis
                    break
            else:
                all_analysis["blocks"].append(block_analysis)
            
            # 保存到JSON文件
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(all_analysis, f, ensure_ascii=False, indent=2)
            
            # 保存到数据库
            conn = sqlite3.connect(Path(__file__).parent.parent / "data" / "analysis.db")
            c = conn.cursor()
            
            try:
                # 删除已存在的相同block_id的数据
                c.execute("DELETE FROM block_analysis WHERE block_id = ?", (block_id,))
                c.execute("DELETE FROM structured_data_analysis WHERE block_id = ?", (block_id,))
                c.execute("DELETE FROM unstructured_data_analysis WHERE block_id = ?", (block_id,))
                
                # 保存基本分析信息
                c.execute('''INSERT INTO block_analysis 
                            (block_id, h1_title, h2_title, text_type, main_topic, raw_analysis)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                         (block_id, block["h1_title"], block["h2_title"],
                          parsed_analysis["analysis"].get("text_type", ""),
                          parsed_analysis["analysis"].get("main_topic", ""),
                          analysis["raw_analysis"]))
                
                # 保存结构化数据分析
                for item in parsed_analysis["analysis"].get("structured_data", []):
                    c.execute('''INSERT INTO structured_data_analysis
                                (block_id, name, type, format, time_info, importance, context)
                                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                             (block_id, 
                              item.get("name", ""),
                              item.get("type", ""),
                              item.get("format", ""),
                              item.get("time_info", ""),
                              item.get("importance", 0),
                              item.get("context", "")))
                
                # 保存非结构化数据分析
                for item in parsed_analysis["analysis"].get("unstructured_data", []):
                    c.execute('''INSERT INTO unstructured_data_analysis
                                (block_id, type, description, importance, related_topics, time_sensitivity)
                                VALUES (?, ?, ?, ?, ?, ?)''',
                             (block_id,
                              item.get("type", ""),
                              item.get("description", ""),
                              item.get("importance", 0),
                              item.get("related_topics", ""),
                              item.get("time_sensitivity", "")))
                
                conn.commit()
                self.logger.info(f"{Fore.GREEN}分析结果已保存到数据库{Style.RESET_ALL}")
                
            except Exception as e:
                conn.rollback()
                self.logger.error(f"{Fore.RED}数据库操作失败: {str(e)}{Style.RESET_ALL}")
                raise
            finally:
                conn.close()
                
        except json.JSONDecodeError as e:
            self.logger.error(f"{Fore.RED}JSON解析失败: {str(e)}{Style.RESET_ALL}")
            self.logger.error(f"{Fore.RED}原始内容: {analysis.get('raw_analysis', '')}{Style.RESET_ALL}")
            raise
        except Exception as e:
            self.logger.error(f"{Fore.RED}保存分析结果失败: {str(e)}{Style.RESET_ALL}")
            raise

    def analyze_blocks(self, input_path: Path, output_path: Path) -> None:
        """分析文本块并生成提示词"""
        # 检查输入文件
        if not input_path.exists():
            raise FileNotFoundError(f"找不到输入文件: {input_path}")
        
        # 加载文本块
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        blocks = data["blocks"]
        
        # 加载或创建进度文件
        progress_path = output_path.parent / "read_progress.json"
        
        # 检查是否需要重新开始
        if self._should_restart(input_path, progress_path, output_path):
            self.logger.info(f"{Fore.YELLOW}检测到cut.json已更新，需要重新开始解析{Style.RESET_ALL}")
            user_input = input("是否要清理之前的所有分析结果并重新开始？(y/n): ")
            if user_input.lower() == 'y':
                self._clean_previous_files()
                prompts = self._create_new_prompts()
            else:
                self.logger.info(f"{Fore.YELLOW}继续使用现有的分析结果{Style.RESET_ALL}")
                prompts = self._load_progress(progress_path, output_path)
        else:
            prompts = self._load_progress(progress_path, output_path)
        
        # 获取已处理的块ID
        processed_blocks = {block["block_id"] for block in prompts["blocks"]}
        
        # 显示进度
        total_blocks = len(blocks)
        remaining_blocks = total_blocks - len(processed_blocks)
        self.logger.info(f"{Fore.CYAN}��计 {total_blocks} 个文本块，已处理 {len(processed_blocks)} 个，剩余 {remaining_blocks} 个{Style.RESET_ALL}")
        
        if remaining_blocks == 0:
            self.logger.info(f"{Fore.GREEN}所有文本块已处理完成{Style.RESET_ALL}")
            return
        
        progress = ProgressBar(remaining_blocks, prefix='分析文本块:', suffix='完成')
        processed_count = 0
        
        # 处理未分析的块
        for i, block in enumerate(blocks):
            if i in processed_blocks:
                self.logger.info(f"{Fore.YELLOW}跳过已处理的文本块 {i+1}/{total_blocks}{Style.RESET_ALL}")
                continue
                
            self.logger.info(f"{Fore.CYAN}正在分析第 {i+1}/{total_blocks} 个文本块{Style.RESET_ALL}")
            stream_output(f"标题: {block['h1_title']} - {block['h2_title']}")
            
            try:
                # 分析文本块
                analysis = self._analyze_block(block)
                
                # 保存分析结果
                self._save_analysis_result(i, block, analysis)
                
                # 生成该块的提示词
                block_prompts = self._generate_prompts(block, analysis)
                prompts["blocks"].append({
                    "block_id": i,
                    "type": block["type"],
                    "prompts": block_prompts
                })
                
                # 保存当前进度
                self._save_progress(prompts, progress_path, output_path)
                
                processed_count += 1
                progress.print(processed_count)
                
            except Exception as e:
                self.logger.error(f"{Fore.RED}处理文本块 {i+1} 时出错: {str(e)}{Style.RESET_ALL}")
                self.logger.error(f"{Fore.RED}保存当前进度并退出{Style.RESET_ALL}")
                self._save_progress(prompts, progress_path, output_path)
                raise
        
        # 处理完成后删除进度文件
        if progress_path.exists():
            progress_path.unlink()
        
        self.logger.info(f"{Fore.GREEN}所有文本块处理完成{Style.RESET_ALL}")
    
    def _should_restart(self, input_path: Path, progress_path: Path, output_path: Path) -> bool:
        """检查是否需要重新开始解析"""
        # 获取cut.json的修改时间
        cut_mtime = input_path.stat().st_mtime
        
        # 检查进度文件
        if progress_path.exists():
            progress_mtime = progress_path.stat().st_mtime
            if cut_mtime > progress_mtime:
                return True
        
        # 检查输出文件
        if output_path.exists():
            output_mtime = output_path.stat().st_mtime
            if cut_mtime > output_mtime:
                return True
        
        return False

    def _clean_previous_files(self) -> None:
        """清理之前的所有相关文件"""
        base_dir = Path(__file__).parent.parent / "data"
        files_to_clean = [
            "read_progress.json",
            "prompts.json",
            "read.json",
            "analysis.db"
        ]
        
        self.logger.info(f"{Fore.YELLOW}正在清理之前的文件...{Style.RESET_ALL}")
        for file_name in files_to_clean:
            file_path = base_dir / file_name
            if file_path.exists():
                try:
                    file_path.unlink()
                    self.logger.info(f"{Fore.GREEN}已删除: {file_name}{Style.RESET_ALL}")
                except Exception as e:
                    self.logger.error(f"{Fore.RED}删除 {file_name} 失败: {str(e)}{Style.RESET_ALL}")

    def _create_new_prompts(self) -> Dict[str, Any]:
        """创建新的提示词配置"""
        # 删除旧的进度文件（如果存在）
        progress_path = Path("data/read_progress.json")
        if progress_path.exists():
            progress_path.unlink()
        
        # 创建新的配置
        return {
            "version": "1.0",
            "default": self._get_default_prompts(),
            "blocks": []
        }

    def _load_progress(self, progress_path: Path, output_path: Path) -> Dict[str, Any]:
        """加载处理进度"""
        if progress_path.exists():
            # 如果有进度文件，加载之前的进度
            self.logger.info(f"{Fore.YELLOW}发现未完成的处理进度{Style.RESET_ALL}")
            with open(progress_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif output_path.exists():
            # 如果有输出文件，使用输出文件作为起点
            self.logger.info(f"{Fore.YELLOW}使用已有的输出文件{Style.RESET_ALL}")
            with open(output_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 创建新的提示词配置
            return self._create_new_prompts()
    
    def _save_progress(self, prompts: Dict[str, Any], progress_path: Path, output_path: Path) -> None:
        """保存处理进度"""
        # 保存进度文件
        with open(progress_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        
        # 同时更新输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"{Fore.GREEN}进度已保存{Style.RESET_ALL}")
    
    def _analyze_block(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """分析单个文本块"""
        # 显示分隔线和块信息
        self.logger.info(f"\n{Fore.YELLOW}{'='*100}{Style.RESET_ALL}")
        self.logger.info(f"{Fore.YELLOW}开始分析文本块{Style.RESET_ALL}")
        
        # 显示文本信息
        self.logger.info(f"\n{Fore.CYAN}【标题信息】{Style.RESET_ALL}")
        self.logger.info(f"一级标题: {block['h1_title']}")
        self.logger.info(f"二级标题: {block['h2_title']}")
        self.logger.info(f"页码: {block['page']}")
        self.logger.info(f"文本长度: {block['length']} 字符")
        
        # 显示完整文本内容
        self.logger.info(f"\n{Fore.CYAN}【文本内容】{Style.RESET_ALL}")
        self.logger.info(block['text'])
        
        # 构造分析提示词
        self.logger.info(f"\n{Fore.MAGENTA}【分析提示词】{Style.RESET_ALL}")
        analysis_prompt = {
            "messages": [
                {
                    "role": "system",
                    "content": """你是一个专业的文本分析专家，擅长从各类文本中提取有价值的信息。你需要：
1. 理解文本的上下文和主题
2. 识别所有可能的结构化数据（如数字、指标、比率等）
3. 提取重要的非结构化信息（如政策、战略、风险等）
4. 确保信息的完整性和准确性
5. 保持数据的时间属性

分析要求：
1. 结构化数据必须包含：
   - 具体的数值
   - 完整的时间信息
   - 准确的单位
   - 必要的上下文
   - 重要程度评估

2. 非结构化信息必须说明：
   - 信息类型
   - 具体内容
   - 重要程度
   - 时间敏感度
   - 相关主题

3. 特别注意：
   - 数值的精确性
   - 时间的连续性
   - 逻辑的完整性
   - 上下文的关联性"""
                },
                {
                    "role": "user",
                    "content": f"""请分析以下文本，并按照规定格式返回JSON结果：

标题信息：
一级标题：{block['h1_title']}
二级标题：{block['h2_title']}

文本内容：
{block['text']}

返回格式要求：
{{
    "analysis": {{
        "text_type": "文本的主要类型和特征",
        "main_topic": "文本的主要主题",
        "key_elements": ["关键要素1", "关键要素2", ...],
        "structured_data": [
            {{
                "name": "指标名称",
                "type": "指标类型",
                "format": "数据格式",
                "value": "具体数值",
                "unit": "单位",
                "time_info": "时间信息",
                "importance": "重要程度1-5",
                "context": "上下文说明"
            }}
        ],
        "unstructured_data": [
            {{
                "type": "信息类型",
                "content": "具体内容",
                "importance": "重要程度1-5",
                "time_sensitivity": "时间敏感度",
                "related_topics": ["相关主题1", "相关主题2"]
            }}
        ]
    }}
}}

注意事项：
1. 所有数值必须保持原始精度
2. 时间信息要标准化（如：2023年度、2023年12月末）
3. 重要程度使用1-5的整数表示
4. 相关主题使用数组形式
5. 确保JSON格式完整且有效"""
                }
            ]
        }
        
        # 显示提示词
        self.logger.info(json.dumps(analysis_prompt, ensure_ascii=False, indent=2))
        
        # 调用LLM并流式显示结果
        self.logger.info(f"\n{Fore.GREEN}【LLM分析结果】{Style.RESET_ALL}")
        response = self.llm._call_llm(analysis_prompt["messages"])
        
        # 流式输出LLM返回结果
        for char in response:
            stream_output(char, end='', delay=0.001)
        stream_output('\n')
        
        return {
            "raw_analysis": response,
            "block_type": block["type"]
        }
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """解析LLM的分析结果"""
        # 这里可以添加更复杂的解析逻辑
        return {
            "raw_analysis": response,
            "suggested_structure": self._extract_structure(response)
        }
    
    def _extract_structure(self, analysis: str) -> Dict[str, Any]:
        """从分析结果中提取建议的数据结构"""
        # 可以使用更复杂的逻辑来解析LLM的建议
        return {
            "structured_fields": [],
            "unstructured_fields": []
        }
    
    def _generate_prompts(self, block: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """为文本块生成专门的提示词"""
        self.logger.info(f"\n{Fore.YELLOW}正在生成提取提示词...{Style.RESET_ALL}")
        
        # 根据分析结果生成提示词
        system_prompt = self._get_system_prompt(block["type"])
        extraction_prompt = self._get_extraction_prompt(block["type"], analysis)
        
        prompts = {
            "analyze": {
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": extraction_prompt
                    }
                ]
            }
        }
        
        # 直接打印提示词，不使用流式输出
        self.logger.info(f"\n{Fore.GREEN}生成的提示词:{Style.RESET_ALL}")
        self.logger.info(json.dumps(prompts, ensure_ascii=False, indent=2))
        
        return prompts
    
    def _get_system_prompt(self, block_type: str) -> str:
        """获取系统提示词"""
        prompts = {
            "financial": """你是一个专业的财务数据分析师，具有以下专业能力：

1. 精确识别和提取财务报表中的各类数据
2. 理解财务指标的定义和计算方法
3. 识别数据的时间属性和计量单位
4. 理解财务数据之间的关联关系
5. 确保数据的准确性和一致性

你需要特别注意：
- 数值的精确性和单位统一
- 会计期间的明确界定
- 同比环比的变化情况
- 重要财务指标的完整性
- 特殊项目的说明和注释

请确保提取的数据：
- 保持原始数据的准确性
- 标注完整的时间信息
- 说明计量单位
- 保留必要的上下文
- 标注数据的重要程度""",

            "business": """你是一个业务分析专家，具有以下专业能力：

1. 理解业务发展战略和目标
2. 识别关键业务指标和数据
3. 分析市场和竞争情况
4. 评估业务风险和机遇
5. 理解客户需求和反馈

你需要特别注意：
- 业务增长的关键指标
- 市场份额的变化
- 客户数据的趋势
- 产品服务的发展
- 竞争态势的变化

请确保提取的信息：
- 量化指标的准确性
- 市场数据的时效性
- 竞争信息的可靠性
- 发展战略的清晰性
- 风险因素的完整性""",

            "risk": """你是一个风险管理专家，具有以下专业能力：

1. 识别各类风险因素
2. 评估风险影响程度
3. 分析风险控制措施
4. 监测风险指标变化
5. 预警潜在风险事件

你需要特别注意：
- 风险指标的变化趋势
- 风险事件的影响范围
- 控制措施的有效性
- 合规要求的满足情况
- 风险预警的及时性

请确保提取的信息：
- 风险指标的准确性
- 风险事件的完整描述
- 控制措施的具体内容
- 合规信息的及时性
- 预警信息的可操作性""",
            
            # ... 其他类型的提示词 ...
        }
        return prompts.get(block_type, """你是一个专业的信息提取专家，请仔细分析文本并提取有价值的信息...""")
    
    def _get_extraction_prompt(self, block_type: str, analysis: Dict[str, Any]) -> str:
        """生成提取提示词"""
        base_prompt = f"""请从以下文本中提取关键信息，并按照规定格式返回JSON：

文本内容：
{analysis.get('text', '')}

需要提取的信息类型：
"""

        prompts = {
            "financial": """1. 财务指标数据：
   - 具体的数值和单位
   - 同比/环比变化
   - 相关的时间信息
   - 重要程度评估

2. 财务分析信息：
   - 重要财务比率
   - 趋势分析
   - 风险指标
   - 业绩评价

返回格式：
{
    "financial_metrics": [
        {
            "name": "指标名称",
            "value": "具体数值",
            "unit": "单位",
            "change": "变化情况",
            "time": "时间信息",
            "importance": "重要程度1-5"
        }
    ],
    "financial_analysis": [
        {
            "type": "分析类型",
            "content": "分析内容",
            "key_points": ["要点1", "要点2"],
            "time_period": "分析时间范围"
        }
    ]
}""",

            "business": """1. 业务发展数据：
   - 业务规模指标
   - 市场份额数据
   - 客户相关指标
   - 产品服务数据

2. 战略发展信息：
   - 发展目标
   - 市场策略
   - 创新举措
   - 竞争优势

返回格式：
{
    "business_metrics": [
        {
            "name": "指标名称",
            "value": "具体数值",
            "unit": "单位",
            "time": "时间信息",
            "trend": "发展趋势"
        }
    ],
    "strategic_info": [
        {
            "aspect": "战略方面",
            "content": "具体内容",
            "timeline": "实施时间",
            "importance": "重要程度1-5"
        }
    ]
}""",

            "risk": """1. 风险指标数据：
   - 风险度量指标
   - 风险限额数据
   - 风险事件统计
   - 合规监管指标

2. 风险管理信息：
   - 风险政策
   - 控制措施
   - 应对策略
   - 预警信息

返回格式：
{
    "risk_metrics": [
        {
            "name": "指标名称",
            "value": "具体数值",
            "threshold": "限额/阈值",
            "status": "状态评估",
            "time": "时间信息"
        }
    ],
    "risk_management": [
        {
            "type": "风险类型",
            "measures": ["措施1", "措施2"],
            "effectiveness": "有效性评估",
            "period": "实施期间"
        }
    ]
}""",

            "governance": """1. 治理结构信息：
   - 组织架构
   - 人员任命
   - 制度建设
   - 决策机制

2. 公司治理实践：
   - 治理举措
   - 内控体系
   - 合规管理
   - 信息披露

返回格式：
{
    "governance_structure": [
        {
            "aspect": "治理方面",
            "details": "具体内容",
            "changes": "变动情况",
            "effective_date": "生效时间"
        }
    ],
    "governance_practice": [
        {
            "type": "实践类型",
            "content": "具体内容",
            "impact": "影响评估",
            "time_frame": "时间范围"
        }
    ]
}"""
        }

        # 获取对应类型的提示词，如果没有则使用默认提示词
        type_prompt = prompts.get(block_type, """1. 通用信息提取：
   - 关键数据指标
   - 重要事件信息
   - 发展动态
   - 相关说明

返回格式：
{
    "key_metrics": [
        {
            "name": "指标名称",
            "value": "具体值",
            "time": "时间信息",
            "notes": "相关说明"
        }
    ],
    "key_information": [
        {
            "type": "信息类型",
            "content": "具体内容",
            "importance": "重要程度1-5",
            "time": "相关时间"
        }
    ]
}""")

        return base_prompt + type_prompt
    
    def _get_default_prompts(self) -> Dict[str, Any]:
        """获取默认提示词"""
        return {
            "system": "你是一个专业的信息提取专家...",
            "user": "请分析以下文本并提取关键信息..."
        }
    
    def _save_prompts(self, prompts: Dict[str, Any], output_path: Path) -> None:
        """保存提示词配置"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)

def main():
    # 设置路径
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / "data" / "cut.json"
    output_path = base_dir / "data" / "prompts.json"
    
    # 从配置文件获取API配置
    from config.settings import API_KEY, API_BASE
    
    # 创建分析器并处理
    analyzer = TextAnalyzer(API_KEY, API_BASE)
    analyzer.analyze_blocks(input_path, output_path)

if __name__ == "__main__":
    main() 