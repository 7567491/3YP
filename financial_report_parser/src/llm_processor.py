import os
import json
import requests
from typing import Dict, Any, List
from time import sleep
import logging
from .utils import stream_output, ProgressBar
from pathlib import Path

class LLMProcessor:
    def __init__(self, api_key: str, api_base: str, model: str = "moonshot-v1-8k", temperature: float = 0.1):
        self.logger = logging.getLogger(__name__)
        
        # API配置
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.temperature = temperature
        
        # 加载提示词配置
        prompt_path = Path(__file__).parent.parent / "data" / "prompt.json"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompts = json.load(f)
        
        self.logger.info(f"初始化LLM处理器: 模型={model}")

    def process_chunk(self, text: str, max_retries: int = 3) -> Dict[str, Any]:
        """处理单个文本块"""
        # 显示文本块信息
        self.logger.info("-" * 80)
        self.logger.info(f"文本块长度: {len(text)} 字符")
        stream_output("文本块内容预览:")
        stream_output(text[:200] + "..." if len(text) > 200 else text)
        self.logger.info("-" * 80)
        
        # 1. 首先分析文本块包含的信息类型
        stream_output("\n第一步：分析文本块包含的信息...")
        summary = self._call_llm(
            messages=self._format_messages(self.prompts["summarize"], text=text)
        )
        stream_output("\n文本分析结果:")
        stream_output(summary)
        
        # 2. 根据分析结果提取具体数据
        stream_output("\n第二步：提取具体数据...")
        data = self._call_llm(
            messages=self._format_messages(
                self.prompts["extract"],
                text=text
            )
        )
        
        # 3. 解析并返回数据
        return self._parse_response(data)

    def _call_llm(self, messages: List[Dict[str, str]], max_retries: int = 3) -> str:
        """调用LLM API"""
        for attempt in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                request_data = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": True  # 启用流式输出
                }
                
                # 显示请求信息
                stream_output("\n发送请求:")
                stream_output(f"URL: {self.api_base}")
                stream_output(f"模型: {self.model}")
                
                # 使用stream=True进行请求
                response = requests.post(
                    self.api_base,
                    headers=headers,
                    json=request_data,
                    stream=True
                )
                
                if response.status_code == 401:
                    raise Exception(f"API认证失败: {response.text}")
                
                response.raise_for_status()
                
                # 用于收集完整响应
                full_response = []
                
                # 流式处理响应
                for line in response.iter_lines():
                    if line:
                        # 移除 "data: " 前缀并解析JSON
                        json_str = line.decode('utf-8').replace('data: ', '')
                        if json_str.strip() == '[DONE]':
                            break
                        
                        try:
                            chunk = json.loads(json_str)
                            if chunk.get('choices') and chunk['choices'][0].get('delta', {}).get('content'):
                                content = chunk['choices'][0]['delta']['content']
                                stream_output(content, end='', delay=0)  # 实时输出，无延迟
                                full_response.append(content)
                        except json.JSONDecodeError:
                            continue
                
                stream_output('\n')  # 最后添加换行
                return ''.join(full_response)
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                self.logger.info(f"请求失败，{wait_time}秒后重试: {str(e)}")
                sleep(wait_time)

    def _format_messages(self, prompt_template: Dict[str, Any], **kwargs) -> List[Dict[str, str]]:
        """格式化消息模板"""
        messages = prompt_template["messages"].copy()
        for message in messages:
            if message["role"] == "user":
                try:
                    message["content"] = message["content"].format(**kwargs)
                except KeyError as e:
                    self.logger.error(f"格式化提示词失败: {str(e)}")
                    self.logger.error(f"提示词模板: {message['content']}")
                    self.logger.error(f"参数: {kwargs}")
                    raise
        return messages

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试解析JSON
            data = json.loads(content)
            
            # 标准化数据格式
            normalized = {
                "type": data.get("type", "unknown"),
                "data": data.get("data", [])
            }
            
            self.logger.debug(f"成功解析数据，类型: {normalized['type']}, 数量: {len(normalized['data'])}")
            return normalized
            
        except Exception as e:
            self.logger.error(f"解析失败: {str(e)}")
            self.logger.error(f"原始内容: {content}")
            raise Exception(f"解析失败: {str(e)}")